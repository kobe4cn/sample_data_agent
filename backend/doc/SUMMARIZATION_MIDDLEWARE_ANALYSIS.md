# SummarizationMiddleware 与通义千问 API 兼容性分析

## 问题概述

当启用 `SummarizationMiddleware` 时，通义千问 API 返回以下错误：

```
ValueError: request_id: xxx
 status_code: 400
 code: InvalidParameter
 message: <400> InternalError.Algo.InvalidParameter:
 An assistant message with "tool_calls" must be followed by tool messages
 responding to each "tool_call_id". The following tool_call_ids did not
 have response messages: message[5].role
```

## 根本原因分析

### 1. SummarizationMiddleware 的工作机制

**触发条件**：
- 当消息总 token 数超过 `max_tokens_before_summary`（默认 4000）时触发

**执行流程**：
```python
# 1. 计算安全切割点（不分离 AI message 和 ToolMessage）
cutoff_index = self._find_safe_cutoff(messages)

# 2. 分割消息
messages_to_summarize = messages[:cutoff_index]  # 旧消息，将被总结
preserved_messages = messages[cutoff_index:]     # 保留的新消息

# 3. 生成摘要并重建消息列表
return {
    "messages": [
        RemoveMessage(id=REMOVE_ALL_MESSAGES),  # 删除所有旧消息
        HumanMessage(content=f"摘要: {summary}"),  # 添加摘要
        *preserved_messages,  # 保留最近的消息
    ]
}
```

### 2. 通义千问 API 的消息验证规则

通义千问严格验证消息序列，要求：

1. **tool_call 必须紧跟 tool_response**：
   - AIMessage 中的每个 `tool_call_id` 必须在后续消息中有对应的 ToolMessage
   - 中间不能插入其他消息类型

2. **消息角色序列规则**：
   ```
   正确: user -> assistant(tool_calls) -> tool -> assistant -> user
   错误: user -> assistant(tool_calls) -> user -> tool  # 插入了其他消息
   ```

3. **不支持 RemoveMessage**：
   - 通义千问 API 不识别 LangGraph 的 `RemoveMessage` 类型
   - 在消息被发送到 API 之前，LangGraph 应该已经处理掉 RemoveMessage

### 3. 问题发生的时序

```
时序 1: 正常情况（无摘要）
┌─────────┐     ┌──────────┐     ┌─────────────┐
│ Agent   │────>│ LangGraph│────>│ Tongyi API  │
│ 调用工具 │     │ 消息队列 │     │ 验证消息    │
└─────────┘     └──────────┘     └─────────────┘
                                      ✅ 验证通过

时序 2: 启用摘要时的问题
┌─────────┐     ┌──────────┐     ┌─────────────┐     ┌─────────────┐
│ Agent   │────>│Middleware│────>│ LangGraph   │────>│ Tongyi API  │
│ 调用工具 │     │ 修改消息 │     │ 处理Remove  │     │ 验证消息    │
└─────────┘     └──────────┘     └─────────────┘     └─────────────┘
                     │
                     v
                RemoveMessage(REMOVE_ALL_MESSAGES)
                + HumanMessage(摘要)
                + preserved_messages
                     │
                     v
            ❌ 可能破坏 tool_call/tool_response 配对
```

### 4. 具体失败场景

**场景 A：切割点计算错误**

虽然 `_find_safe_cutoff` 尝试保持 tool_call/tool_response 配对，但在某些情况下可能失败：

```python
# 原始消息序列
messages = [
    HumanMessage("分析数据"),           # index 0
    AIMessage(tool_calls=[...]),       # index 1  <- 有 tool_calls
    ToolMessage(tool_call_id="1"),     # index 2
    AIMessage("分析完成"),              # index 3
    HumanMessage("继续分析"),           # index 4
    AIMessage(tool_calls=[...]),       # index 5  <- 有 tool_calls
    ToolMessage(tool_call_id="2"),     # index 6
]

# 如果 cutoff_index = 4（保留最近 3 条消息）
preserved_messages = messages[4:]  # [4, 5, 6]
# index 5 的 AIMessage 有 tool_calls
# index 6 的 ToolMessage 是响应
# ✅ 看起来没问题

# 但如果删除所有消息后重建：
new_messages = [
    RemoveMessage(REMOVE_ALL_MESSAGES),
    HumanMessage("摘要: ..."),          # 新插入的摘要
    HumanMessage("继续分析"),            # index 4
    AIMessage(tool_calls=[...]),        # index 5
    ToolMessage(tool_call_id="2"),      # index 6
]

# 在 LangGraph 处理 RemoveMessage 之前，
# 如果通义千问 API 看到这个序列，会报错！
```

**场景 B：RemoveMessage 处理时机问题**

```python
# LangGraph 的消息处理流程
1. Middleware.before_model() 返回新消息
2. LangGraph 将新消息加入队列
3. 消息 reducer 处理 RemoveMessage
4. 调用模型 API

# 问题：在步骤 2-3 之间，消息序列可能不完整
# 如果通义千问在步骤 2 就开始验证消息，会失败
```

## 解决方案

### 方案 1：自定义消息处理中间件（推荐）

创建一个兼容通义千问的摘要中间件，不使用 RemoveMessage。

```python
# backend/src_agent/middleware/tongyi_summarization.py

from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langgraph.runtime import Runtime
from typing import Any

class TongyiSummarizationMiddleware(AgentMiddleware):
    """通义千问兼容的摘要中间件

    不使用 RemoveMessage，而是直接替换整个消息列表。
    """

    def __init__(
        self,
        model,
        max_tokens_before_summary: int = 4000,
        messages_to_keep: int = 20,
    ):
        super().__init__()
        self.model = model
        self.max_tokens_before_summary = max_tokens_before_summary
        self.messages_to_keep = messages_to_keep

    def before_model(
        self,
        state: AgentState,
        runtime: Runtime
    ) -> dict[str, Any] | None:
        """在模型调用前处理消息"""
        messages = state["messages"]

        # 检查是否需要摘要
        from langchain_core.messages.utils import count_tokens_approximately
        total_tokens = count_tokens_approximately(messages)

        if total_tokens < self.max_tokens_before_summary:
            return None

        # 找到安全的切割点
        cutoff_index = self._find_safe_cutoff(messages)
        if cutoff_index <= 0:
            return None

        # 分割消息
        messages_to_summarize = messages[:cutoff_index]
        preserved_messages = messages[cutoff_index:]

        # 生成摘要
        summary = self._create_summary(messages_to_summarize)

        # 关键：直接返回完整的新消息列表，不使用 RemoveMessage
        new_messages = [
            HumanMessage(
                content=f"## 对话历史摘要\n\n{summary}"
            ),
            *preserved_messages,
        ]

        # 返回完整替换的消息列表
        return {"messages": new_messages}

    def _find_safe_cutoff(self, messages: list) -> int:
        """找到安全的切割点，确保 tool_call/tool_response 配对"""
        if len(messages) <= self.messages_to_keep:
            return 0

        target_cutoff = len(messages) - self.messages_to_keep

        # 从目标切割点往前搜索，找到第一个安全点
        for i in range(target_cutoff, -1, -1):
            if self._is_safe_cutoff_point(messages, i):
                return i

        return 0

    def _is_safe_cutoff_point(self, messages: list, cutoff_index: int) -> bool:
        """检查切割点是否安全"""
        if cutoff_index >= len(messages):
            return True

        # 检查 cutoff 前后 5 条消息范围内的 tool_call 配对
        search_range = 5
        search_start = max(0, cutoff_index - search_range)
        search_end = min(len(messages), cutoff_index + search_range)

        for i in range(search_start, search_end):
            msg = messages[i]
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                # 获取所有 tool_call_id
                tool_call_ids = {
                    tc['id'] if isinstance(tc, dict) else tc.id
                    for tc in msg.tool_calls
                }

                # 检查是否会分离 tool_call 和 tool_response
                for j in range(i + 1, len(messages)):
                    from langchain_core.messages import ToolMessage
                    if isinstance(messages[j], ToolMessage):
                        if messages[j].tool_call_id in tool_call_ids:
                            # 检查是否在切割点两侧
                            ai_before_cutoff = i < cutoff_index
                            tool_before_cutoff = j < cutoff_index
                            if ai_before_cutoff != tool_before_cutoff:
                                return False  # 会分离配对，不安全

        return True

    def _create_summary(self, messages: list) -> str:
        """生成消息摘要"""
        if not messages:
            return "无历史对话记录。"

        # 准备摘要提示词
        summary_prompt = """请简要总结以下对话的关键信息：

{messages}

请用简洁的语言总结对话的主要内容、完成的任务和重要结论。"""

        try:
            # 格式化消息
            messages_text = "\n\n".join([
                f"{msg.type}: {msg.content}"
                for msg in messages
            ])

            # 调用模型生成摘要
            response = self.model.invoke(
                summary_prompt.format(messages=messages_text)
            )

            return response.content.strip()
        except Exception as e:
            return f"生成摘要时出错: {str(e)}"
```

### 方案 2：配置 LangGraph 消息处理顺序

确保 RemoveMessage 在发送到 API 之前被完全处理。

```python
# backend/src_agent/graph.py

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware

# 方案 2A: 使用 LangGraph 的状态修改器
from langgraph.graph import StateGraph
from typing import Annotated
from operator import add

def custom_message_reducer(
    current: list,
    update: list
) -> list:
    """自定义消息 reducer，立即处理 RemoveMessage"""
    from langchain_core.messages import RemoveMessage, REMOVE_ALL_MESSAGES

    # 检查是否有 RemoveMessage
    has_remove_all = any(
        isinstance(msg, RemoveMessage) and msg.id == REMOVE_ALL_MESSAGES
        for msg in update
    )

    if has_remove_all:
        # 立即清空并返回新消息（排除 RemoveMessage）
        return [
            msg for msg in update
            if not isinstance(msg, RemoveMessage)
        ]

    # 正常情况，追加消息
    return current + update

# 使用自定义 reducer
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=prompt,
    middleware=[
        SummarizationMiddleware(
            model=summary_model,
            max_tokens_before_summary=4000,
            messages_to_keep=20,
        )
    ],
    # 使用自定义消息 reducer
    state_modifier={"messages": custom_message_reducer},
)
```

### 方案 3：切换到支持 RemoveMessage 的模型

使用更兼容 LangGraph 的模型（如 OpenAI、DeepSeek）：

```python
# backend/src_agent/model.py

class ModelFactory:
    def _get_model(self):
        match self.model_type:
            case "tongyi":
                # 为通义千问禁用某些功能
                return ChatTongyi(
                    model=os.getenv("DASHSCOPE_MODEL"),
                    temperature=0.0,
                    # 添加配置以提高兼容性
                )
            case "openai":
                # OpenAI 对消息序列更宽容
                return ChatOpenAI(
                    model=os.getenv("OPENAI_MODEL"),
                    temperature=0.0,
                )
```

### 方案 4：调整摘要触发阈值

避免摘要功能过早触发：

```python
# backend/src_agent/graph.py

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=prompt,
    middleware=[
        SummarizationMiddleware(
            model=summary_model,
            max_tokens_before_summary=8000,  # 提高阈值，减少触发频率
            messages_to_keep=30,  # 保留更多消息
        )
    ],
)
```

## 推荐实施步骤

### 步骤 1：实施方案 1（自定义中间件）

1. 创建 `backend/src_agent/middleware/tongyi_summarization.py`
2. 实现上述 `TongyiSummarizationMiddleware`
3. 在 `graph.py` 中替换：

```python
# from langchain.agents.middleware import SummarizationMiddleware
from src_agent.middleware.tongyi_summarization import TongyiSummarizationMiddleware

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=prompt,
    middleware=[
        TongyiSummarizationMiddleware(
            model=summary_model,
            max_tokens_before_summary=4000,
            messages_to_keep=20,
        )
    ],
)
```

### 步骤 2：测试验证

```python
# 测试脚本
def test_summarization_with_tools():
    # 模拟长对话触发摘要
    for i in range(30):
        response = agent.invoke({
            "messages": [HumanMessage(f"请分析数据集 {i}")]
        })
        print(f"Round {i}: {len(response['messages'])} messages")

    # 验证 tool_call/tool_response 配对
    messages = response['messages']
    for i, msg in enumerate(messages):
        if isinstance(msg, AIMessage) and msg.tool_calls:
            print(f"AI message at {i} has tool_calls")
            # 检查后续是否有对应的 ToolMessage
            for j in range(i+1, len(messages)):
                if isinstance(messages[j], ToolMessage):
                    print(f"  -> ToolMessage at {j}")
```

### 步骤 3：监控和调优

添加日志记录摘要触发情况：

```python
class TongyiSummarizationMiddleware(AgentMiddleware):
    def before_model(self, state, runtime):
        messages = state["messages"]
        total_tokens = count_tokens_approximately(messages)

        logger.info(
            f"Messages: {len(messages)}, "
            f"Tokens: {total_tokens}, "
            f"Threshold: {self.max_tokens_before_summary}"
        )

        if total_tokens < self.max_tokens_before_summary:
            return None

        logger.warning(
            f"Triggering summarization: {total_tokens} tokens exceeds threshold"
        )

        # ... 执行摘要逻辑
```

## 总结

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| 方案 1：自定义中间件 | 完全兼容通义千问，可控性强 | 需要自己实现摘要逻辑 | ⭐⭐⭐⭐⭐ |
| 方案 2：自定义 reducer | 使用原生中间件，改动小 | 可能仍有时序问题 | ⭐⭐⭐ |
| 方案 3：切换模型 | 简单直接 | 需要更换 API | ⭐⭐ |
| 方案 4：调整阈值 | 零改动 | 只是延缓问题，不解决 | ⭐⭐ |

**最终建议**：实施方案 1（自定义中间件），这是最稳定和可控的方案。
