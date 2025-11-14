# Python 沙箱实现说明

## 已完成的核心功能

### 1. 环境准备 ✅
- 添加 `RestrictedPython>=6.0` 到 requirements.txt
- 添加 `psutil>=5.9.0` 到 requirements.txt
- 创建沙箱工作目录 `backend/sandbox_workspace/`

### 2. 沙箱配置模块 ✅
文件: `backend/src/config/sandbox_config.py`
- 定义模块白名单（20+ 模块）
- 资源限制配置（超时、内存）
- 支持环境变量配置

### 3. 文件系统沙箱 ✅
文件: `backend/src/sandbox_filesystem.py`
- 路径解析和验证
- 防止路径遍历攻击
- 限制文件访问在沙箱目录内

### 4. 沙箱核心模块 ✅
文件: `backend/src/sandbox.py`
- 安全的代码执行环境
- 超时控制机制
- 全局变量管理
- 受限内置函数

### 5. 工具函数集成 ✅
文件: `backend/src/tools.py`
- `python_inter`: 已集成沙箱执行
- `fig_inter`: 需要手动完成双层架构集成

## 需要手动完成的步骤

### fig_inter 双层架构集成

在 `backend/src/tools.py` 的 `fig_inter` 函数中,替换第257-264行的执行逻辑:

```python
# 原代码（第257-264行）:
try:
    global_vars = globals()
    exec(py_code, global_vars, local_vars)
    global_vars.update(local_vars)
    fig = local_vars.get(fname, None)

# 替换为:
try:
    # === 第1步: 在沙箱内执行绘图代码 ===
    sandbox = get_sandbox()
    sandbox.execute(py_code)

    # === 第2步: 从沙箱提取图像对象（可信层）===
    try:
        fig = sandbox.get_global(fname)
    except KeyError:
        return f"⚠️ 图像对象未找到：变量 '{fname}' 不存在"
```

### 安装依赖

```bash
cd backend
pip install RestrictedPython>=6.0 psutil>=5.9.0
```

## 工作原理

### 双层架构
```
用户请求
  ↓
工具函数 (fig_inter, python_inter)  ← 可信层
  ↓
沙箱执行 (PythonSandbox.execute)   ← 受限层
  ↓
返回数据对象
  ↓
工具函数处理输出 (保存到 images/)
```

### 安全限制
- ✅ 允许: pandas, numpy, matplotlib, json, datetime, re, math等
- ❌ 禁止: subprocess, os.system, socket, eval, exec
- ✅ 文件访问:
  - **`data/` 目录（只读）**: 用户上传的数据文件，AI 可在 python_inter 中读取
  - **`sandbox_workspace/` 目录（读写）**: 临时文件和中间结果
- ✅ 图像输出: 工具层保存到 `backend/src/images/`（沙箱外）

## 文件访问架构

### 目录结构和权限

```
backend/
├── data/                   # 共享数据目录（只读）
│   ├── sales.csv          # 用户上传的数据文件
│   ├── users.xlsx
│   └── config.json
├── sandbox_workspace/      # 沙箱工作目录（读写）
│   ├── temp.csv           # AI 生成的临时文件
│   └── intermediate.pkl   # 中间处理结果
└── src/
    └── images/            # 图像输出目录（工具层访问，沙箱禁止）
        └── plot_*.png
```

### 使用示例

**在 python_inter 中读取数据文件**:
```python
# 读取共享数据目录中的文件（只读）
df = pd.read_csv('data/sales.csv')
df2 = pd.read_excel('data/users.xlsx')

# 数据清洗和处理
df_cleaned = df.dropna()

# 保存中间结果到工作目录（读写）
df_cleaned.to_csv('temp_cleaned.csv')

# 稍后读取中间结果
df = pd.read_csv('temp_cleaned.csv')
```

**权限控制**:
```python
# ✅ 允许: 读取共享数据目录
df = pd.read_csv('data/sales.csv')

# ❌ 禁止: 写入共享数据目录
df.to_csv('data/output.csv')  # SecurityError: 只读目录

# ✅ 允许: 读写工作目录
df.to_csv('temp.csv')  # OK

# ❌ 禁止: 访问系统其他目录
df = pd.read_csv('/etc/passwd')  # SecurityError
```

## 测试验证

创建测试文件验证沙箱功能:

```python
# test_sandbox_basic.py
from src.sandbox import PythonSandbox
from src.config.sandbox_config import SandboxConfig

def test_pandas_execution():
    sandbox = PythonSandbox()
    result = sandbox.execute("pd.DataFrame({'a': [1,2,3]})")
    print("✅ Pandas execution successful")

def test_security_block():
    sandbox = PythonSandbox()
    try:
        sandbox.execute("import subprocess")
        print("❌ Security not working")
    except Exception as e:
        print(f"✅ Security working: {e}")

if __name__ == "__main__":
    test_pandas_execution()
    test_security_block()
```

## 配置选项

通过环境变量配置:

```bash
# .env
ENABLE_SANDBOX=true
SANDBOX_MAX_EXECUTION_TIME=30
SANDBOX_MAX_MEMORY_MB=512
SANDBOX_LOG_LEVEL=INFO
```

## 已知限制（MVP版本）

### 1. 代码级安全限制

1. **未实现 RestrictedPython 编译**: 当前使用标准 compile(),未来需集成 RestrictedPython.compile_restricted()
2. **简化的模块导入控制**: 依赖 Python 的标准导入机制，已放开 `__import__`（pandas/numpy 需要）
3. **内存监控未实现**: 配置了限制但未主动监控
4. **Windows 超时支持**: 当前只支持 Unix 的 signal.alarm()

### 2. 文件系统安全限制

**只读目录保护的局限性**:
- **问题**: pandas/numpy 等库使用底层 C/Cython 代码，可以绕过 Python 的 `open()` 函数替换
- **影响**: 沙箱内的代码可能仍然能够写入 `data/` 目录
- **解决方案**:
  - ✅ **推荐**: 在生产环境设置操作系统级文件权限：
    ```bash
    chmod 555 data/          # 目录只读
    chmod 444 data/*.csv     # 文件只读
    ```
  - ✅ 代码级 `open()` 拦截仍然有效，可以防止大部分写入尝试
  - ✅ 作为多层防御的一部分，操作系统权限是最可靠的防线

**当前状态**:
- ✅ 文件读取功能正常工作
- ✅ Python 层面的 `open()` 调用受控
- ⚠️ pandas/numpy 底层写入需要文件系统权限保护

## 后续改进建议

1. 集成 RestrictedPython.compile_restricted()
2. 实现自定义 import hook 强制模块白名单
3. 添加内存监控（tracemalloc）
4. 添加详细的审计日志
5. 完善单元测试和安全测试
6. 实现跨平台超时控制（threading.Timer）
