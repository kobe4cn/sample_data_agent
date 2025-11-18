# 问题排查指南

## 问题：AI 无法读取 CSV 文件

### 症状
- 用户请求："请提取目录下 telco_data.csv 数据集前10条记录"
- AI 回复："无法读取 data 目录"、"线程错误"、"需要导入数据库"

### 根本原因
**LangGraph 缓存了旧的对话历史**，其中包含失败的尝试和错误信息。即使代码已修复，AI 仍然基于旧的上下文做出决策。

---

## ✅ 解决方案

### 步骤 1: 停止服务并清理缓存

```bash
cd /Users/kevin/dev/ai/ai-engineer-training/sample_data_agent/backend

# 运行重置脚本
chmod +x reset_and_restart.sh
./reset_and_restart.sh
```

或者手动执行：

```bash
# 停止服务（在运行 make dev-backend 的终端按 Ctrl+C）

# 删除缓存
rm -rf .langgraph_api/

# 删除测试文件（可选）
rm -f test_*.py diagnose_*.py simulate_*.py final_*.py
```

### 步骤 2: 重新启动服务

```bash
make dev-backend
```

等待看到类似信息：
```
LangGraph API server is running
Listening on http://localhost:2024
```

### 步骤 3: **重要！开始新对话**

⚠️ **不要使用旧的对话窗口**

在前端：
1. 点击"新建对话"或"清空历史"
2. 或者刷新页面重新开始

### 步骤 4: 测试

发送测试请求：
```
请提取目录下 telco_data.csv 数据集前10条记录
```

**期望结果：**
- ✅ AI 调用 `python_inter` 工具
- ✅ 执行代码：`pd.read_csv('data/telco_data.csv')`
- ✅ 返回包含 customerID、gender、Churn 等字段的前 10 行数据

---

## 📊 验证代码正常工作

如果您想确认代码层面没有问题，可以运行：

```bash
cd /Users/kevin/dev/ai/ai-engineer-training/sample_data_agent/backend
../.venv/bin/python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

# 重置沙箱
import tools
tools._sandbox_instance = None

from tools import python_inter

code = """
import pandas as pd
df = pd.read_csv('data/telco_data.csv')
df.head(10)
"""

result = python_inter.invoke({"python_code": code})
print(result)
EOF
```

**应该看到：**
- 包含 7043 行 × 21 列数据
- 前 10 行记录
- customerID、gender、SeniorCitizen 等字段

如果这个测试通过，说明**代码完全正常，问题在于 AI 的对话上下文**。

---

## 🔍 诊断检查清单

如果问题仍然存在，检查以下项目：

### 1. 文件系统
```bash
ls -lh data/telco_data.csv
# 应该显示: -rw-r--r-- ... 977505 ... telco_data.csv
```

### 2. 配置
```bash
../.venv/bin/python3 -c "
import sys; sys.path.insert(0, 'src')
from config.sandbox_config import SandboxConfig
config = SandboxConfig.from_env()
print(f'共享数据目录: {config.shared_data_dir}')
import os
print(f'目录存在: {os.path.exists(config.shared_data_dir)}')
"
```

### 3. Prompt
```bash
../.venv/bin/python3 -c "
import sys; sys.path.insert(0, 'src')
from prompt import prompt
print('包含 data/ 说明:', 'data/' in prompt)
print('包含 telco_data 示例:', 'telco_data' in prompt)
"
```

### 4. LangGraph 进程
```bash
ps aux | grep "langgraph dev" | grep -v grep
```

---

## 📝 关键修改总结

为了让 AI 能够读取 CSV 文件，我们做了以下修改：

1. **配置路径修复** (`src/config/sandbox_config.py`)
   - 修正 `sandbox_workspace` 和 `shared_data_dir` 路径

2. **恢复 `__import__`** (`src/sandbox.py`)
   - pandas/numpy 需要动态导入

3. **工具描述更新** (`src/tools.py`)
   - 在 `python_inter` 的 docstring 中添加文件访问说明

4. **系统提示词更新** (`src/prompt.py`)
   - 明确告诉 AI 如何读取 CSV 文件
   - 提供具体示例

5. **数据文件移动**
   - `telco_data.csv` → `data/telco_data.csv`

---

## ❓ 常见问题

### Q: 为什么需要清理缓存？
A: LangGraph 会保存对话历史，包括工具调用结果。旧的失败记录会影响 AI 的判断。

### Q: 清理缓存会丢失数据吗？
A: 只会清理对话历史，不会影响数据文件（`data/` 目录）和代码。

### Q: 如果还是不行怎么办？
A:
1. 确认使用的是**新对话**（不是旧对话窗口）
2. 检查浏览器是否缓存了前端代码（硬刷新：Ctrl+Shift+R）
3. 查看 LangGraph 服务日志，看工具调用情况

---

## 🎯 成功标志

当一切正常时，您会看到：

**用户**："请提取目录下 telco_data.csv 数据集前10条记录"

**AI**：
```
我已成功提取 telco_data.csv 数据集的前10条记录。

数据集包含 7043 行，21 列，以下是前10条记录的关键信息：

| customerID | gender | SeniorCitizen | Churn |
|------------|--------|---------------|-------|
| 7590-VHVEG | Female | 0             | No    |
| 5575-GNVDE | Male   | 0             | No    |
| ...        | ...    | ...           | ...   |

[显示完整的 DataFrame]
```

---

✅ 所有代码修改已完成并验证通过
✅ 所有测试都成功
✅ 只需清理缓存并使用新对话即可
