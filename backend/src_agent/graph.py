"""
LangGraph代理配置模块 (graph.py)

本模块负责创建和配置LangGraph AI代理，包括：
- 导入所有可用的工具函数
- 配置AI模型（主模型和摘要模型）
- 设置系统提示词
- 配置中间件（如消息摘要中间件）
- 创建代理实例

代理可以使用以下工具：
- sql_inter: SQL数据库查询
- extract_data: 数据提取到pandas DataFrame
- python_inter: Python代码执行
- fig_inter: 数据可视化绘图
- search_tool: 网络搜索
"""

from src_agent.tools import (
    sql_inter,
    extract_data,
    python_inter,
    fig_inter,
    search_tool,
)
from src_agent.prompt import prompt
from src_agent.model import ModelFactory
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware

# from memory.pgmemory import PGMemory

import os

# ==================== 模型配置 ====================
# 从环境变量读取模型类型配置
model_type = os.getenv("DEFAULT_MODEL")  # 主模型类型（用于对话和推理）
summary_model_type = os.getenv("SUMMARY_MODEL")  # 摘要模型类型（用于消息摘要）

# ==================== 工具配置 ====================
# 定义代理可用的所有工具列表
# 这些工具将在代理需要时被自动调用
tools = [sql_inter, extract_data, python_inter, fig_inter, search_tool]

# ==================== 模型实例化 ====================
# 使用ModelFactory创建主模型实例
model = ModelFactory(model_type).model
# 使用ModelFactory创建摘要模型实例（用于SummarizationMiddleware）
summary_model = ModelFactory(model_type).get_summary_model(summary_model_type)

# ==================== 持久化内存配置（已注释） ====================
# 如果需要启用对话历史持久化，可以取消注释以下代码
# db_uri=os.getenv("CHECKERPOINTER_URI")
# with PGMemory(db_uri).checkpointer as checkpointer:
#     checkpointer.setup()

# ==================== 代理创建 ====================
# 创建LangGraph代理实例
agent = create_agent(
    model=model,  # 主AI模型，用于理解和生成回复
    tools=tools,  # 代理可用的工具列表
    system_prompt=prompt,  # 系统提示词，定义代理的行为和角色
    middleware=[
        # 消息摘要中间件：当对话历史过长时自动进行摘要
        # ⚠️ 已禁用：前端 SDK 版本不支持 "remove" 类型消息，且可能导致通义千问 API 消息序列错误
        # 等待前端升级到支持该消息类型的版本后可重新启用
        # SummarizationMiddleware(
        #     model=summary_model,  # 用于生成摘要的模型
        #     max_tokens_before_summary=4000,  # 当消息达到4000 tokens时触发摘要
        #     messages_to_keep=20,  # 摘要后保留最近20条消息
        # )
    ],
    # checkpointer=checkpointer,  # 持久化检查点（已注释）
)
