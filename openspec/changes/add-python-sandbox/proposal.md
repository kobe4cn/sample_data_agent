# Python 代码沙箱执行提案

## Why

当前系统在 `backend/src/tools.py` 中的 `python_inter` 和 `fig_inter` 工具直接使用 `exec()` 执行用户提供的 Python 代码，存在严重的安全风险：

- 可以执行任意系统命令（如 `os.system()`, `subprocess`）
- 可以访问和修改文件系统（读取敏感文件、删除数据）
- 可以导入任何 Python 模块，包括危险模块
- 可以无限制地消耗系统资源（CPU、内存、磁盘）
- 可以进行网络请求，可能泄露数据或发起攻击

这些风险在生产环境中是不可接受的，需要实现安全的沙箱执行环境。

## What Changes

- **新增**: Python 代码沙箱执行模块，使用 RestrictedPython 限制代码执行
- **新增**: 资源限制机制（CPU 时间、内存、执行超时）
- **新增**: 模块导入白名单（支持数据分析、文本处理、日期时间、算法等通用 Python 库）
- **新增**: 受限文件系统访问（允许读写沙箱工作目录，禁止访问系统敏感目录）
- **新增**: 双层文件访问架构（沙箱内生成对象，工具层处理输出文件）
- **修改**: `python_inter` 工具使用沙箱执行代码，支持通用 Python 功能
- **修改**: `fig_inter` 工具使用沙箱执行绘图代码
- **新增**: 安全策略配置（可配置允许的模块、资源限制、文件访问范围）
- **新增**: 审计日志记录（记录执行的代码、文件访问和结果）

## Impact

### 受影响的规范
- 新增规范: `code-execution` (代码执行安全)

### 受影响的代码
- `backend/src/tools.py`: 修改 `python_inter` 和 `fig_inter` 函数（双层架构实现）
  - `fig_inter`: 沙箱内生成图像对象 → 工具层保存到 `images/` 目录
- `backend/requirements.txt`: 添加 `RestrictedPython` 依赖
- 新增文件: `backend/src/sandbox.py` (沙箱执行模块)
- 新增文件: `backend/src/config/sandbox_config.py` (沙箱配置)
- 新增文件: `backend/src/sandbox_filesystem.py` (受限文件系统访问)
- 新增目录: `backend/sandbox_workspace/` (沙箱工作目录)
- 保留目录: `backend/src/images/` (工具层输出目录，沙箱外)

### 性能影响
- 代码执行时间可能增加 10-50ms（安全检查开销）
- 内存开销增加约 5-10MB（沙箱环境）

### 向后兼容性
- **完全兼容**: 现有合法的数据分析代码仍可正常执行
- **部分兼容**: 通用 Python 代码大部分可执行，但有以下限制：
  - 文件访问仅限于沙箱工作目录 (`backend/sandbox_workspace/`)
  - 禁止系统命令执行（`subprocess`, `os.system()` 等）
  - 禁止网络访问（`socket`, `urllib`, `requests` 等）
- **迁移**: 需要文件访问的代码需调整路径到沙箱工作目录

### 风险
- 沙箱绕过风险（需要定期更新 RestrictedPython）
- 可能误杀一些边缘合法用例（需要白名单配置）
- 资源限制可能导致长时间运行的分析任务失败（需要合理配置超时）
