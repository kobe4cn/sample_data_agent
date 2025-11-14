# 数据分析 AI Agent (Data Analysis AI Agent)

> 基于 LangChain V1.0 和 LangGraph 构建的智能数据分析助手,集成 SQL 查询、数据处理、可视化和网络搜索功能。

## 📑 目录

- [项目概述](#-项目概述)
- [核心特性](#-核心特性)
- [安全特性](#-安全特性)
- [技术栈](#-技术栈)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [使用指南](#-使用指南)
- [数据管理](#-数据管理)
- [核心功能](#-核心功能)
- [开发指南](#-开发指南)
- [环境变量配置](#-环境变量配置)
- [部署说明](#-部署说明)
- [故障排查](#-故障排查)
- [许可证](#-许可证)

## 🎯 项目概述

本项目是一个智能数据分析 AI Agent,通过自然语言交互帮助用户完成数据查询、分析和可视化任务。Agent 能够自主调用多种工具,包括 SQL 数据库查询、Python 代码执行、数据可视化和网络搜索,为用户提供一站式数据分析体验。

**主要应用场景:**
- 通过自然语言查询数据库
- 自动生成数据分析报告和可视化图表
- 执行复杂的数据处理和统计分析
- 获取实时信息补充数据分析

## ✨ 核心特性

- 🗣️ **自然语言交互** - 用中文与 AI 对话,无需编写 SQL 或 Python 代码
- 🔍 **智能 SQL 查询** - 自动生成并执行 SQL 查询,获取数据库数据
- 📊 **数据可视化** - 自动生成专业的数据图表和统计图形
- 🐍 **Python 代码执行** - 执行任意 Python 代码进行数据处理和分析
- 🌐 **网络搜索** - 集成 Tavily 搜索获取实时信息
- 💾 **对话记忆** - 智能摘要中间件,自动管理长对话上下文(4000 tokens 自动触发)
- 🎨 **现代化 UI** - 基于 Next.js 的响应式 Web 界面
- 🔒 **企业级安全** - Python 代码沙箱隔离执行,文件系统访问控制

### 对话记忆机制

**当前实现:**

1. **SummarizationMiddleware (已启用)**
   - 自动监控对话长度
   - 超过 **4000 tokens** 时自动触发摘要
   - 保留最近 **20 条消息**
   - 使用专用摘要模型 (如 `qwen-flash`) 提高速度

2. **工作原理:**
   ```
   对话流程:
   消息 1-10 → 正常存储
   消息 11-30 → 继续存储
   消息 31+ (超过 4000 tokens)
     → 触发摘要
     → 压缩历史消息为简短摘要
     → 保留最近 20 条原始消息
     → 节省 token 使用,保持上下文
   ```

3. **配置:**
   ```bash
   # 在 backend/src/graph.py 中配置
   SUMMARY_TRIGGER_TOKENS = 4000  # 触发阈值
   KEEP_RECENT_MESSAGES = 20      # 保留消息数
   ```

**可选:PostgreSQL Checkpointer (未启用)**

如需持久化对话状态到数据库:

1. **取消注释代码:**
   ```python
   # 编辑 backend/src/graph.py
   # 找到并取消注释以下代码:
   db_uri = os.getenv("CHECKERPOINTER_URI")
   with PGMemory(db_uri).checkpointer as checkpointer:
       checkpointer.setup()
   ```

2. **配置环境变量:**
   ```bash
   # 在 backend/.env 中添加
   CHECKERPOINTER_URI=postgresql://postgres:postgres@localhost:5432/checkpointer?sslmode=disable
   ```

3. **启动 PostgreSQL:**
   ```bash
   # 使用 Docker
   docker run -d \
     --name postgres-checkpointer \
     -e POSTGRES_PASSWORD=postgres \
     -p 5432:5432 \
     postgres:15

   # 创建数据库
   docker exec postgres-checkpointer \
     psql -U postgres -c "CREATE DATABASE checkpointer;"
   ```

4. **重启应用:**
   ```bash
   make dev-backend
   ```

**对比:**

| 特性 | SummarizationMiddleware | PostgreSQL Checkpointer |
|------|------------------------|-------------------------|
| 当前状态 | ✅ 已启用 | ⚠️ 未启用 (代码已准备) |
| 持久化 | ❌ 仅内存 | ✅ 数据库持久化 |
| 重启后保留 | ❌ 丢失 | ✅ 保留 |
| 性能 | ⭐⭐⭐⭐⭐ 快速 | ⭐⭐⭐⭐ 稍慢 |
| 资源占用 | 低 | 中等 (需 PostgreSQL) |
| 适用场景 | 单次会话,开发测试 | 生产环境,多用户 |

**建议:**
- 开发环境: 使用 SummarizationMiddleware (已默认启用)
- 生产环境: 同时启用两者,获得最佳体验

## 🔒 安全特性

### Python 沙箱执行环境

本项目实现了企业级的 Python 代码沙箱,确保用户代码安全执行,是系统的核心安全基础设施。

**核心安全机制:**

#### 1. 模块访问控制

**允许的模块(白名单):**
- 数据处理: `pandas`, `numpy`, `scipy`
- 可视化: `matplotlib`, `seaborn`
- 标准库: `json`, `re`, `datetime`, `math`, `collections`, `itertools`, `pathlib`

**禁止的操作(黑名单):**
- 系统调用: `subprocess`, `os.system`, `socket`
- 危险函数: `eval`, `exec`, `compile`, `__import__`
- 文件操作: 受限的 `open()` (仅允许指定目录)

#### 2. 文件系统隔离

**双目录架构:**

1. **data/ 目录 (只读)** - 共享数据文件
   ```python
   # ✅ 允许读取
   df = pd.read_csv('data/telco_data.csv')
   df = pd.read_excel('data/lego.xlsx')

   # ❌ 禁止写入
   df.to_csv('data/output.csv')  # SecurityError
   ```

2. **工作目录 (读写)** - 临时文件和中间结果
   ```python
   # ✅ 允许读写
   df.to_csv('temp_result.csv')
   result = pd.read_csv('temp_result.csv')
   ```

**安全防护:**
- ✅ 路径遍历攻击防护 (`../`, `./`)
- ✅ 绝对路径拦截 (`/etc/passwd`, `/usr/bin/`)
- ✅ 只读目录写入拦截
- ✅ 路径规范化和验证

#### 3. 执行资源限制

**超时控制:**
```bash
# 默认超时: 30 秒
SANDBOX_MAX_EXECUTION_TIME=30
```

**内存限制:**
```bash
# 最大内存: 512MB (配置项)
SANDBOX_MAX_MEMORY_MB=512
```

#### 4. 安全的函数替换

沙箱自动替换危险函数:
```python
# open() → safe_open() (路径验证)
# __import__() → safe_import() (模块白名单)
```

### 内置数据加载器

为了进一步提升安全性和易用性,系统提供了 `load_dataset()` 函数:

**功能特性:**
- ✅ 自动数据类型转换 (数值列、日期列)
- ✅ 防止类型错误导致的绘图失败
- ✅ 统一的数据访问接口
- ✅ 数据副本隔离,防止污染

**使用示例:**
```python
# 在 python_inter 或 fig_inter 中使用
telco_df = load_dataset('telco')      # 自动清洗
lego_df = load_dataset('lego')        # Excel 格式
nongfu_df = load_dataset('nongfu')    # 大型数据集

# 列出所有可用数据集
datasets = list_datasets()
```

### 安全最佳实践

**生产环境建议:**

1. **文件系统权限:**
   ```bash
   # 设置数据目录为只读
   chmod 555 backend/data/
   chmod 444 backend/data/*
   ```

2. **资源监控:**
   - 监控沙箱执行时间
   - 跟踪内存使用情况
   - 记录文件访问日志

3. **定期审计:**
   - 审查沙箱配置
   - 检查模块白名单
   - 验证文件访问规则

**已知限制:**

> ⚠️ **注意事项**
>
> - pandas/numpy 底层 C 代码可能绕过部分文件访问检查
> - 超时控制仅支持 Unix 系统 (使用 `signal.alarm`)
> - 内存监控配置已就绪但需额外实现
> - 生产环境建议配合操作系统级别的安全策略

## 🛠️ 技术栈

### 后端技术

- **语言:** Python 3.10+
- **AI 框架:**
  - [LangChain](https://www.langchain.com/) - AI 应用开发框架
  - [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent 编排和状态管理
- **Web 框架:**
  - [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
  - [Uvicorn](https://www.uvicorn.org/) - ASGI 服务器
- **数据处理:**
  - [Pandas](https://pandas.pydata.org/) - 数据分析
  - [Matplotlib](https://matplotlib.org/) / [Seaborn](https://seaborn.pydata.org/) - 数据可视化
- **数据库:**
  - [PyMySQL](https://pymysql.readthedocs.io/) - MySQL 连接器
  - [PostgreSQL](https://www.postgresql.org/) - Checkpointer 存储

### 前端技术

- **框架:** [Next.js 16](https://nextjs.org/) (React 19)
- **语言:** TypeScript 5.7
- **UI 组件:**
  - [Radix UI](https://www.radix-ui.com/) - 无障碍组件库
  - [Tailwind CSS](https://tailwindcss.com/) - CSS 框架
- **LangGraph SDK:**
  - [@langchain/langgraph-sdk](https://www.npmjs.com/package/@langchain/langgraph-sdk) - LangGraph 客户端

### AI 模型和服务

**当前支持的模型:**
- **通义千问 (Qwen)** - 阿里云 DashScope
  - 主模型: `qwen3-max`
  - 摘要模型: `qwen-flash` (高速模型)
- **DeepSeek**
  - 主模型: `deepseek-chat`

**计划支持的模型:**
- OpenAI (GPT 系列) - 需扩展 `backend/src/model.py`
- Anthropic Claude - 需扩展 `backend/src/model.py`

**搜索服务:**
- [Tavily](https://tavily.com/) - AI 搜索 API (max_results=5)

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Next.js)                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Chat UI  │  Markdown Render  │  Image Display  │  │
│  └──────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/WebSocket
                        │ LangGraph SDK
┌───────────────────────▼─────────────────────────────────┐
│                 后端 (FastAPI + LangGraph)               │
│  ┌──────────────────────────────────────────────────┐  │
│  │            LangGraph Agent                       │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────┐ │  │
│  │  │   Router   │→ │   Tools    │→ │  Response │ │  │
│  │  └────────────┘  └────────────┘  └───────────┘ │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │                  工具集 (Tools)                   │  │
│  │  • sql_inter      - SQL 查询                     │  │
│  │  • extract_data   - 数据提取                     │  │
│  │  • python_inter   - Python 执行                  │  │
│  │  • fig_inter      - 图表生成                     │  │
│  │  • search_tool    - 网络搜索                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼─────┐ ┌──────▼──────┐
│    MySQL     │ │ AI Models  │ │   Tavily    │
│   Database   │ │  (Qwen等)  │ │   Search    │
└──────────────┘ └────────────┘ └─────────────┘
```

**工作流程:**

1. 用户通过 Web UI 发送自然语言查询
2. LangGraph Agent 接收请求并分析意图
3. Agent 根据需求自动调用相应的工具:
   - 需要数据 → 调用 `sql_inter` 或 `extract_data`
   - 需要分析 → 调用 `python_inter`
   - 需要可视化 → 调用 `fig_inter`
   - 需要实时信息 → 调用 `search_tool`
4. 工具执行完成后返回结果给 Agent
5. Agent 整合结果并生成友好的回复
6. 前端展示结果(文本、图表、表格等)

## 🚀 快速开始

### 环境要求

- **Python:** 3.10 或更高版本
- **Node.js:** 18.x 或更高版本
- **包管理器:** pnpm (推荐) 或 npm
- **数据库:** MySQL 5.7+ (用于数据查询)
- **操作系统:** macOS, Linux, Windows

### 1. 克隆项目

```bash
git clone <repository-url>
cd sample_data_agent
```

### 2. 后端安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 前端安装

```bash
# 进入前端目录
cd agent-chat-ui

# 安装依赖
pnpm install
# 或使用 npm
# npm install
```

### 4. 数据库设置

启动 MySQL 数据库:

```bash
# 使用 Docker Compose 启动 MySQL
cd backend
docker-compose up -d

# 或手动启动 MySQL 服务
# 确保 MySQL 运行在 localhost:3306
```

导入示例数据(可选):
```bash
# 项目包含 telco_data.csv 示例数据
# 可以手动导入到 MySQL 数据库中
```

### 5. 环境变量配置

在 `backend` 目录创建 `.env` 文件:

```bash
cd backend
cp .env.example .env  # 如果有 .env.example
# 或直接创建 .env 文件
```

编辑 `.env` 文件,配置必要的环境变量(参见[环境变量配置](#-环境变量配置)章节)。

### 6. 启动应用

#### 使用 Makefile (推荐)

```bash
# 从项目根目录同时启动前后端
make dev

# 或分别启动
make dev-backend   # 启动后端 (端口: 2024)
make dev-frontend  # 启动前端 (端口: 3000)
```

#### 手动启动

**启动后端:**
```bash
cd backend
source .venv/bin/activate  # 激活虚拟环境
langgraph dev              # 启动 LangGraph 开发服务器
```

**启动前端:**
```bash
cd agent-chat-ui
pnpm dev                   # 启动 Next.js 开发服务器
```

### 7. 访问应用

- **前端 UI:** http://localhost:3000
- **后端 API:** http://localhost:2024
- **LangGraph Studio:** http://localhost:2024 (如果启用)

## 📖 使用指南

### 基本对话

1. 打开浏览器访问 http://localhost:3000
2. 在对话框中输入您的问题,例如:
   - "查询数据库中所有表"
   - "显示 customers 表的前 10 条数据"
   - "统计订单总数"
   - "绘制销售额趋势图"

### 示例查询

**SQL 查询:**
```
请查询 customers 表中所有的客户信息
```

**数据分析:**
```
提取 orders 表的数据,计算每个月的销售总额
```

**数据可视化:**
```
绘制产品销量的柱状图
```

**复杂分析:**
```
分析客户流失率,并生成可视化报告
```

## 📁 数据管理

### 内置数据集

项目预置了多个数据集,可直接使用 `load_dataset()` 函数快速加载:

| 数据集名称 | 文件格式 | 数据规模 | 描述 |
|-----------|---------|---------|------|
| `telco` | CSV | 7044 行 | 客户流失数据,包含客户信息和流失标签 |
| `telco_data_encoded` | CSV | 7044 行 | 编码后的客户流失数据 |
| `lego` | Excel | 中等规模 | LEGO 产品销售数据 |
| `nongfu` | Excel | 大规模 | 农夫山泉业务数据 |

**使用方法:**

```python
# 在 python_inter 或 fig_inter 中使用

# 1. 加载单个数据集
telco_df = load_dataset('telco')
print(telco_df.info())  # 数值列已自动转换为正确类型

# 2. 加载不同格式的数据
lego_df = load_dataset('lego')      # Excel 格式自动识别
nongfu_df = load_dataset('nongfu')  # 大型数据集

# 3. 列出所有可用数据集
available = list_datasets()
print(available)  # ['telco', 'telco_data_encoded', 'lego', 'nongfu']
```

**自动数据清洗:**

`load_dataset()` 会自动处理常见的数据类型问题:

```python
# ✅ 自动转换数值列
# 'TotalCharges' 中的空字符串 → NaN
# 字符串数字 "100.5" → float 100.5

# ✅ 自动转换日期列
# "2024-01-01" → datetime64

# ✅ 防止绘图错误
# 避免 "unsupported operand type(s) for +: 'int' and 'str'" 错误
```

### 自定义数据集

**添加新数据文件:**

1. 将数据文件放入 `backend/data/` 目录:
   ```bash
   cp your_data.csv backend/data/
   cp your_data.xlsx backend/data/
   ```

2. 在代码中访问(使用相对路径):
   ```python
   # 方式 1: 使用 pandas 直接读取
   df = pd.read_csv('data/your_data.csv')
   df = pd.read_excel('data/your_data.xlsx')
   df = pd.read_json('data/your_data.json')

   # 方式 2: 注册到 data_loader.py (推荐)
   # 编辑 backend/src/data_loader.py 中的 DATASET_CATALOG
   ```

3. 注册到数据加载器(可选但推荐):
   ```python
   # 在 backend/src/data_loader.py 中添加
   DATASET_CATALOG = {
       "telco": "telco_data.csv",
       "lego": "../lego.xlsx",
       "nongfu": "../nongfu.xlsx",
       "your_data": "your_data.csv",  # 添加这行
   }
   ```

**支持的文件格式:**
- ✅ CSV (`.csv`)
- ✅ Excel (`.xlsx`, `.xls`)
- ✅ JSON (`.json`)
- ✅ Parquet (`.parquet`) - 需要安装 `pyarrow`

### 数据访问规则

**文件路径规范:**

```python
# ✅ 正确 - 使用 'data/' 前缀访问共享数据
df = pd.read_csv('data/telco_data.csv')

# ✅ 正确 - 相对路径访问工作目录
df.to_csv('temp_output.csv')
result = pd.read_csv('temp_output.csv')

# ❌ 错误 - 不要使用绝对路径
df = pd.read_csv('/Users/kevin/backend/data/telco_data.csv')

# ❌ 错误 - 不要尝试写入 data/ 目录
df.to_csv('data/output.csv')  # SecurityError: 只读目录
```

**目录结构:**

```
backend/
├── data/                    # 共享数据目录 (只读)
│   ├── telco_data.csv      # ✅ 可读
│   ├── lego.xlsx
│   └── README.md
│
├── sandbox_workspace/       # 沙箱工作目录 (读写)
│   ├── temp_*.csv          # ✅ 可读写
│   └── intermediate_*.json
│
└── src/
    ├── images/              # 生成的图像 (自动管理)
    └── ...
```

### 数据处理最佳实践

**1. 优先使用 load_dataset():**
```python
# ❌ 不推荐 - 可能遇到类型错误
df = pd.read_csv('data/telco_data.csv')
df.plot()  # 可能报错: 字符串列无法绘图

# ✅ 推荐 - 自动清洗
df = load_dataset('telco')
df.plot()  # 正常工作
```

**2. 跨工具数据共享:**
```python
# Step 1: 在 extract_data 中提取数据
extract_data("SELECT * FROM customers", "customers_df")

# Step 2: 在 python_inter 中处理
# customers_df 已自动注入到全局变量
cleaned_df = customers_df.dropna()
cleaned_df.to_csv('cleaned_customers.csv')

# Step 3: 在 fig_inter 中绘图
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
cleaned_df['age'].hist(ax=ax)
```

**3. 处理大型数据集:**
```python
# 分块读取大文件
chunks = []
for chunk in pd.read_csv('data/large_file.csv', chunksize=10000):
    processed = chunk[chunk['value'] > 0]
    chunks.append(processed)

result = pd.concat(chunks)
```

## 🔧 核心功能

### 1. SQL 数据库查询工具 (`sql_inter`)

**功能:** 执行 SQL 查询并返回结果

**使用场景:**
- 查询数据库表结构
- 检索特定数据
- 执行聚合查询

**示例:**
```
用户: "查询 products 表中价格最高的 5 个产品"
Agent: 调用 sql_inter("SELECT * FROM products ORDER BY price DESC LIMIT 5")
```

### 2. 数据提取工具 (`extract_data`)

**功能:** 将 MySQL 数据提取到 Python pandas DataFrame

**使用场景:**
- 需要在 Python 中进一步处理数据
- 复杂的数据分析任务

**示例:**
```
用户: "把 sales 表的数据提取到 Python 中进行分析"
Agent: 调用 extract_data("SELECT * FROM sales", "sales_df")
```

### 3. Python 代码执行工具 (`python_inter`)

**功能:** 在安全沙箱中执行 Python 代码进行数据处理和分析

**安全特性:**
- ✅ 隔离沙箱执行环境
- ✅ 模块白名单限制 (pandas, numpy, matplotlib 等)
- ✅ 文件访问控制 (只读 data/, 读写工作目录)
- ✅ 超时控制 (默认 30 秒)
- ✅ 禁止危险操作 (eval, exec, subprocess 等)

**使用场景:**
- 数据清洗和转换
- 统计计算
- 数据处理逻辑
- 使用 `load_dataset()` 加载预清洗数据

**示例:**
```
用户: "计算销售数据的平均值和标准差"
Agent: 调用 python_inter("sales_df['amount'].mean(), sales_df['amount'].std()")
```

**文件访问:**
```python
# ✅ 允许 - 读取共享数据
df = pd.read_csv('data/telco_data.csv')

# ✅ 允许 - 读写临时文件
df.to_csv('temp_result.csv')

# ❌ 禁止 - 写入共享数据目录
df.to_csv('data/output.csv')  # SecurityError
```

**注意:**
- 此工具不支持绘图,绘图请使用 `fig_inter`
- 优先使用 `load_dataset()` 避免类型转换问题

### 4. 图表生成工具 (`fig_inter`)

**功能:** 在沙箱中执行 Python 绘图代码并自动保存图像

**双层架构设计:**
1. **沙箱层**: 执行绘图代码,生成 Figure 对象
2. **保存层**: 在沙箱外安全保存图像文件

**使用场景:**
- 数据可视化
- 生成统计图表
- 趋势分析图

**示例:**
```
用户: "绘制月度销售额的折线图"
Agent: 调用 fig_inter(绘图代码, "fig")
```

**支持的绘图库:**
- Matplotlib
- Seaborn

**图像文件管理:**
```
文件命名格式: fig_YYYYMMDD_HHMMSS_UUID.png
示例: fig_20251113_154753_163212da.png

存储位置: backend/src/images/
访问路径: http://localhost:2024/images/fig_xxx.png
```

**绘图要求:**
- ✅ 必须创建 `fig` 对象: `fig = plt.figure()` 或 `fig, ax = plt.subplots()`
- ✅ 建议使用 `fig.tight_layout()` 优化布局
- ❌ 不要使用 `plt.show()` (沙箱环境无显示)
- ⚠️ 图表文本建议使用英文 (避免中文字体问题)

**完整示例:**
```python
import matplotlib.pyplot as plt
import pandas as pd

# 加载数据
df = load_dataset('telco')

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))
df['tenure'].hist(bins=30, ax=ax)
ax.set_xlabel('Tenure (months)')
ax.set_ylabel('Count')
ax.set_title('Customer Tenure Distribution')
fig.tight_layout()

# 返回 fig 对象供工具保存
# 不要调用 plt.show()
```

### 5. 网络搜索工具 (`search_tool`)

**功能:** 使用 Tavily API 进行网络搜索

**使用场景:**
- 获取实时信息
- 补充数据分析背景知识
- 查询外部资料

**示例:**
```
用户: "最新的数据分析趋势是什么?"
Agent: 调用 search_tool("latest data analysis trends 2024")
```

## 👨‍💻 开发指南

### 项目结构

```
sample_data_agent/
├── backend/                    # 后端应用
│   ├── src/                    # 源代码
│   │   ├── graph.py           # LangGraph Agent 定义
│   │   ├── tools.py           # 工具函数实现
│   │   ├── model.py           # AI 模型配置
│   │   ├── prompt.py          # System Prompt
│   │   ├── app.py             # FastAPI 应用
│   │   ├── sandbox.py         # Python 沙箱核心 🔒
│   │   ├── sandbox_filesystem.py  # 文件系统沙箱 🔒
│   │   ├── data_loader.py     # 数据加载器 📊
│   │   ├── config/
│   │   │   └── sandbox_config.py  # 沙箱配置 🔒
│   │   ├── memory/            # 记忆和 Checkpointer
│   │   │   └── pgmemory.py    # PostgreSQL 记忆存储
│   │   └── images/            # 生成的图像文件 📈
│   │       └── fig_*.png      # 时间戳 + UUID 命名
│   │
│   ├── data/                  # 共享数据目录 (只读) 📁
│   │   ├── telco_data.csv     # 客户流失数据 (7044 行)
│   │   ├── telco_data_encoded.csv
│   │   └── README.md
│   │
│   ├── sandbox_workspace/     # 沙箱工作目录 (读写) 🔧
│   │   └── temp_*.csv         # 临时和中间文件
│   │
│   ├── lego.xlsx              # LEGO 数据集
│   ├── nongfu.xlsx            # 农夫山泉数据集
│   ├── langgraph.json         # LangGraph 配置
│   ├── requirements.txt       # Python 依赖
│   ├── .env                   # 环境变量 (gitignored)
│   ├── docker-compose.yml     # MySQL Docker 配置
│   ├── SANDBOX_IMPLEMENTATION.md  # 沙箱实现文档
│   └── TROUBLESHOOTING.md     # 故障排查指南
│
├── agent-chat-ui/             # 前端应用
│   ├── src/                   # 源代码
│   │   ├── app/               # Next.js App Router
│   │   │   └── page.tsx       # 主页面
│   │   ├── components/        # React 组件
│   │   │   ├── thread/        # 对话组件
│   │   │   ├── ui/            # UI 组件库
│   │   │   └── icons/         # 图标
│   │   ├── providers/         # Context Providers
│   │   └── lib/               # 工具函数
│   ├── package.json           # Node.js 依赖
│   └── next.config.mjs        # Next.js 配置
│
├── Makefile                   # 开发命令
├── README.md                  # 项目文档
└── .gitignore                 # Git 忽略文件
```

### 添加新工具

1. **在 `backend/src/tools.py` 中定义工具函数:**

```python
from langchain.tools import tool
from pydantic import BaseModel, Field

class MyToolSchema(BaseModel):
    param: str = Field(description="参数描述")

@tool(args_schema=MyToolSchema)
def my_tool(param: str) -> str:
    """工具功能描述"""
    # 实现工具逻辑
    return "结果"
```

2. **在 `backend/src/graph.py` 中注册工具:**

```python
from tools import my_tool

tools = [sql_inter, extract_data, python_inter, fig_inter, search_tool, my_tool]
```

3. **更新 System Prompt (`backend/src/prompt.py`):**

添加工具使用说明,告诉 Agent 何时以及如何使用新工具。

### 开发工作流

1. **后端开发:**
   - 修改代码后,LangGraph dev 会自动重载
   - 查看日志: 终端输出
   - 调试: 使用 Python debugger 或日志

2. **前端开发:**
   - 支持热重载 (Hot Reload)
   - 组件开发: 在 `src/components/` 中创建
   - 样式: 使用 Tailwind CSS

3. **测试:**
   - 后端: 使用 pytest (待添加测试)
   - 前端: 使用 Jest/React Testing Library (待添加测试)

## 🔐 环境变量配置

在 `backend/.env` 文件中配置以下环境变量:

### AI 模型配置

```bash
# OpenAI API (兼容模式,用于通义千问)
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-your-api-key

# 阿里云 DashScope (通义千问)
DASHSCOPE_API_KEY=sk-your-dashscope-key

# DeepSeek API
DEEPSEEK_API_KEY=sk-your-deepseek-key

# Anthropic Claude (可选)
ANTHROPIC_API_KEY=sk-ant-your-key

# 默认模型选择 (tongyi / deepseek / openai)
DEFAULT_MODEL=tongyi

# 摘要模型 (用于对话摘要)
SUMMARY_MODEL=qwen-flash
```

### 搜索服务配置

```bash
# Tavily 搜索 API
TAVILY_API_KEY=tvly-your-tavily-key
```

### 数据库配置

```bash
# MySQL 配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=classicmodels

# PostgreSQL (Checkpointer,可选)
POSTGRES_URI_CUSTOM=postgresql://postgres:postgres@localhost:5432/checkpointer?sslmode=disable
CHECKERPOINTER_URI=postgresql://postgres:postgres@localhost:5432/checkpointer?sslmode=disable
```

### 应用配置

```bash
# 后端 API URL
API_URL=http://localhost:2024

# 前端 URL
FRONTEND_URL=http://localhost:3000

# LangSmith (可选,用于调试和追踪)
LANGSMITH_API_KEY=lsv2_pt_your-langsmith-key
LANGSMITH_TRACING_V2=true
LANGSMITH_PROJECT=data-agent  # 项目名称
```

### 沙箱配置 (可选)

```bash
# Python 沙箱执行限制
SANDBOX_MAX_EXECUTION_TIME=30  # 最大执行时间 (秒)
SANDBOX_MAX_MEMORY_MB=512      # 最大内存限制 (MB,配置项但需额外实现监控)

# 文件系统路径 (默认值,通常不需要修改)
SANDBOX_DATA_DIR=backend/data              # 共享数据目录 (只读)
SANDBOX_WORKSPACE_DIR=backend/sandbox_workspace  # 工作目录 (读写)

# 安全选项
ENABLE_SANDBOX=true           # 启用沙箱 (默认: true)
SANDBOX_STRICT_MODE=true      # 严格模式 (默认: true)
```

### 获取 API Keys

- **通义千问:** https://dashscope.aliyun.com/
- **DeepSeek:** https://platform.deepseek.com/
- **Tavily:** https://tavily.com/
- **LangSmith:** https://smith.langchain.com/

> ⚠️ **安全提示:**
> - 不要将 `.env` 文件提交到 Git 仓库
> - 不要在代码中硬编码 API keys
> - 生产环境使用环境变量或密钥管理服务

## 🚢 部署说明

### Docker 部署

#### 1. MySQL 数据库部署

项目已包含 `docker-compose.yml` 用于快速启动 MySQL 数据库。

**启动 MySQL:**
```bash
cd backend
docker-compose up -d

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

**docker-compose.yml 配置说明:**
```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: sample_data_agent_mysql
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: classicmodels
    volumes:
      - mysql_data:/var/lib/mysql
    restart: unless-stopped

volumes:
  mysql_data:
```

**验证 MySQL 连接:**
```bash
# 方式 1: 使用 mysql 客户端
mysql -h127.0.0.1 -P3306 -uroot -proot classicmodels

# 方式 2: 使用 Docker exec
docker exec -it sample_data_agent_mysql \
  mysql -uroot -proot -e "SHOW DATABASES;"

# 方式 3: 测试连接
docker exec -it sample_data_agent_mysql \
  mysql -uroot -proot classicmodels -e "SELECT 1;"
```

**导入示例数据:**
```bash
# 如果有 SQL 导入文件
docker exec -i sample_data_agent_mysql \
  mysql -uroot -proot classicmodels < your_data.sql

# 或使用 Python 脚本导入 CSV
# (telco_data.csv 已在 backend/data/ 目录)
```

**停止和清理:**
```bash
# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 完全清理 (包括数据卷)
docker-compose down -v
```

#### 2. PostgreSQL Checkpointer 部署 (可选)

如需启用持久化对话存储:

```bash
# 启动 PostgreSQL
docker run -d \
  --name postgres-checkpointer \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=checkpointer \
  -p 5432:5432 \
  -v postgres_checkpointer_data:/var/lib/postgresql/data \
  postgres:15

# 验证连接
docker exec postgres-checkpointer \
  psql -U postgres -d checkpointer -c "\l"
```

#### 3. 应用容器化部署 (未实现,计划中)

**未来计划:**
- 为后端 FastAPI 创建 Dockerfile
- 为前端 Next.js 创建 Dockerfile
- 统一的 docker-compose.yml 包含所有服务
- 生产环境的 Docker 镜像优化

**临时方案 - 本地开发:**
```bash
# 当前推荐使用 Makefile
make dev  # 启动前后端

# 或分别启动
make dev-backend
make dev-frontend
```

### 生产环境配置

1. **环境变量:**
   - 使用环境变量而非 `.env` 文件
   - 使用密钥管理服务(如 AWS Secrets Manager)

2. **数据库:**
   - 使用云数据库服务(如阿里云 RDS)
   - 配置数据库备份和监控
   - 使用连接池优化性能

3. **API 服务:**
   - 使用 Gunicorn 或 Uvicorn workers
   - 配置 Nginx 反向代理
   - 启用 HTTPS/SSL

4. **前端:**
   - 构建生产版本: `pnpm build`
   - 使用 CDN 加速静态资源
   - 配置服务器端渲染(SSR)

## 🐛 故障排查

### 常见问题和解决方案

#### 1. 数据库连接问题

**问题:** 启动后端时报错 "找不到 MySQL 连接" 或 "Access denied"

**解决方案:**
```bash
# 1. 检查 MySQL 是否运行
docker ps | grep mysql
# 或
mysql -h127.0.0.1 -P3306 -uroot -proot

# 2. 验证 .env 配置
cat backend/.env | grep MYSQL

# 3. 测试连接
mysql -h${MYSQL_HOST} -P${MYSQL_PORT} -u${MYSQL_USER} -p${MYSQL_PASSWORD}

# 4. 重启 MySQL
cd backend
docker-compose restart
```

#### 2. 图表无法显示

**问题:** Agent 生成图表但前端无法显示图像

**解决方案:**
```bash
# 1. 检查 images 目录是否存在
ls -la backend/src/images/

# 2. 如果目录不存在,创建它
mkdir -p backend/src/images/
chmod 755 backend/src/images/

# 3. 验证 FastAPI 静态文件服务
curl http://localhost:2024/images/

# 4. 检查图像文件是否生成
ls -lh backend/src/images/*.png

# 5. 验证前端访问
# 浏览器打开: http://localhost:2024/images/fig_xxx.png
```

**根本原因:**
- 目录权限问题
- FastAPI app.py 未正确挂载静态文件
- 图像保存失败(检查沙箱日志)

#### 3. 沙箱执行超时

**问题:** Python 代码执行超时,报错 "Execution timeout"

**解决方案:**
```bash
# 1. 增加超时时间 (在 .env 中)
SANDBOX_MAX_EXECUTION_TIME=60  # 默认 30 秒

# 2. 优化代码,减少计算量
# 示例:分批处理大型数据集
for chunk in pd.read_csv('data/large.csv', chunksize=10000):
    process(chunk)

# 3. 检查死循环或阻塞操作
# 避免: while True, input(), time.sleep(1000)
```

#### 4. 文件访问被拒绝

**问题:** SecurityError: "Cannot access file outside allowed directories"

**解决方案:**
```python
# ❌ 错误的文件路径
df = pd.read_csv('/Users/kevin/data.csv')  # 绝对路径
df = pd.read_csv('../../../etc/passwd')    # 路径遍历
df.to_csv('data/output.csv')              # 写入只读目录

# ✅ 正确的文件路径
df = pd.read_csv('data/telco_data.csv')   # 读取共享数据
df.to_csv('temp_output.csv')              # 写入工作目录
df = load_dataset('telco')                # 使用数据加载器
```

**目录权限说明:**
- `data/` → 只读 (共享数据)
- 工作目录 → 读写 (临时文件)
- 其他目录 → 禁止访问

#### 5. Agent 响应很慢

**问题:** 每次对话需要等待很长时间

**解决方案:**
```bash
# 1. 使用更快的模型
DEFAULT_MODEL=tongyi
SUMMARY_MODEL=qwen-flash  # 快速摘要模型

# 2. 检查 API 响应时间
curl -w "\nTime: %{time_total}s\n" \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation

# 3. 启用 LangSmith 追踪分析瓶颈
LANGSMITH_API_KEY=lsv2_pt_xxx
LANGSMITH_TRACING_V2=true

# 4. 优化 System Prompt 长度
# 减少不必要的工具描述
```

#### 6. 对话上下文丢失

**问题:** Agent 忘记之前的对话内容

**解决方案:**
```bash
# 1. 检查摘要中间件是否启用
# 查看 backend/src/graph.py:
# SummarizationMiddleware 应该已配置

# 2. 可选:启用 PostgreSQL Checkpointer
# 取消注释 graph.py 中的 checkpointer 代码
# 配置 .env:
CHECKERPOINTER_URI=postgresql://postgres:postgres@localhost:5432/checkpointer

# 3. 检查对话长度
# 超过 4000 tokens 会触发自动摘要

# 4. 验证 thread_id 是否一致
# 前端应保持同一个 thread_id 持续对话
```

#### 7. 模块导入失败

**问题:** ModuleNotFoundError 或 "Module not allowed"

**解决方案:**
```bash
# 1. 检查模块是否在白名单中
# 查看 backend/src/config/sandbox_config.py

# 2. 添加新模块到白名单 (谨慎!)
# 编辑 ALLOWED_MODULES 列表

# 3. 安装缺失的依赖
cd backend
source .venv/bin/activate
pip install <module-name>

# 4. 重启服务
make dev-backend
```

**允许的模块列表:**
- pandas, numpy, scipy
- matplotlib, seaborn
- json, re, datetime, math
- collections, itertools, pathlib

#### 8. 类型转换错误

**问题:** TypeError: "unsupported operand type(s) for +: 'int' and 'str'"

**解决方案:**
```python
# ❌ 直接读取可能导致类型错误
df = pd.read_csv('data/telco_data.csv')
df['TotalCharges'].sum()  # 错误: 字符串列

# ✅ 使用 load_dataset() 自动清洗
df = load_dataset('telco')
df['TotalCharges'].sum()  # 正常工作

# 或手动转换
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
```

#### 9. 前端无法连接后端

**问题:** 前端显示 "Failed to connect" 或网络错误

**解决方案:**
```bash
# 1. 检查后端是否运行
curl http://localhost:2024/health
# 或
lsof -i :2024

# 2. 检查前端配置
# agent-chat-ui/.env.local:
NEXT_PUBLIC_API_URL=http://localhost:2024

# 3. 检查 CORS 配置
# backend/src/app.py 应包含 CORS 中间件

# 4. 重启服务
make dev
```

#### 10. LangGraph 启动失败

**问题:** `langgraph dev` 命令报错

**解决方案:**
```bash
# 1. 检查虚拟环境
cd backend
source .venv/bin/activate
which python  # 应该指向 .venv/bin/python

# 2. 重新安装依赖
pip install -r requirements.txt

# 3. 验证 langgraph.json 配置
cat langgraph.json

# 4. 检查环境变量
cat .env | grep -E "API_KEY|MODEL"

# 5. 清理缓存
rm -rf src/__pycache__
find . -name "*.pyc" -delete

# 6. 重启
langgraph dev --port 2024
```

### 日志查看

**后端日志:**
```bash
# LangGraph 日志
cd backend
langgraph dev 2>&1 | tee langgraph.log

# 查看最近错误
grep -i "error" langgraph.log
```

**前端日志:**
```bash
# Next.js 日志
cd agent-chat-ui
pnpm dev 2>&1 | tee nextjs.log

# 浏览器控制台
# 打开 F12 Developer Tools → Console
```

### 性能调优

**1. 减少响应时间:**
- 使用 `qwen-flash` 作为摘要模型
- 启用 LangSmith 缓存
- 优化 System Prompt 长度

**2. 降低内存使用:**
```bash
# 限制沙箱内存
SANDBOX_MAX_MEMORY_MB=256

# 分批处理大数据集
chunks = pd.read_csv('data/large.csv', chunksize=5000)
```

**3. 优化数据库查询:**
```sql
-- 添加索引
CREATE INDEX idx_customer_id ON customers(id);

-- 限制结果数量
SELECT * FROM orders LIMIT 1000;
```

### 获取帮助

如果问题仍未解决:

1. **查看文档:**
   - `backend/SANDBOX_IMPLEMENTATION.md` - 沙箱实现细节
   - `backend/TROUBLESHOOTING.md` - 详细故障排查

2. **检查日志:**
   - LangGraph 输出日志
   - 浏览器控制台错误

3. **社区支持:**
   - LangChain Discord: https://discord.gg/langchain
   - GitHub Issues: 提交 bug 报告

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出改进建议!

### 贡献流程

1. Fork 本仓库
2. 创建功能分支: `git checkout -b feature/your-feature`
3. 提交更改: `git commit -m "Add your feature"`
4. 推送到分支: `git push origin feature/your-feature`
5. 提交 Pull Request

### 代码规范

- **Python:** 遵循 PEP 8 规范
- **TypeScript:** 遵循 ESLint 配置
- **提交信息:** 使用语义化提交信息 (feat/fix/docs/chore 等)

---

**开发者:** AI Engineer Training Project

**最后更新:** 2025-01-13 (完整更新:新增安全特性、数据管理、故障排查等章节)
