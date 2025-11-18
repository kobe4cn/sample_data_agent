# 实施任务清单

## MVP 核心功能（已完成） ✅

## 1. 环境准备和依赖安装 ✅
- [x] 1.1 在 `backend/requirements.txt` 中添加 `RestrictedPython>=6.0` 依赖
- [x] 1.2 在 `backend/requirements.txt` 中添加 `psutil>=5.9.0` 依赖（资源监控）
- [ ] 1.3 运行 `pip install -r requirements.txt` 安装依赖 (用户需手动执行)
- [ ] 1.4 验证 RestrictedPython 正确安装（`python -c "import RestrictedPython"`）(用户需手动执行)

## 2. 沙箱配置模块实现 ✅
- [x] 2.1 创建配置文件 `backend/src/config/sandbox_config.py`
- [x] 2.2 定义 `SandboxConfig` 类包含资源限制配置
- [x] 2.3 定义模块白名单 `ALLOWED_MODULES`
- [x] 2.4 定义禁止的内置函数列表 `BLOCKED_BUILTINS`
- [x] 2.5 添加配置验证逻辑
- [x] 2.6 支持从环境变量读取配置（如 `SANDBOX_MAX_EXECUTION_TIME`）

## 3. 文件系统沙箱模块实现 ✅
- [x] 3.1 创建沙箱工作目录 `backend/sandbox_workspace/`
- [x] 3.2 创建文件系统模块 `backend/src/sandbox_filesystem.py`
- [x] 3.3 实现 `SandboxFileSystem` 类基础结构
- [x] 3.4 实现 `_resolve_path()` 方法（路径解析和映射）
- [x] 3.5 实现 `_is_safe_path()` 方法（路径安全检查）
- [x] 3.6 实现 `safe_open()` 方法（受限的 open 函数）
- [x] 3.7 实现路径遍历攻击防护（处理 `..` 和符号链接）
- [ ] 3.8 实现 pathlib.Path 的沙箱包装 (MVP 未实现)
- [ ] 3.9 添加单元测试验证文件系统沙箱 (未来改进)

## 4. 沙箱核心模块实现 ✅ (简化版MVP)
- [x] 4.1 创建沙箱模块 `backend/src/sandbox.py`
- [x] 4.2 实现 `PythonSandbox` 类基础结构
- [x] 4.3 实现 `_create_safe_builtins()` 方法（受限内置函数 + 沙箱 open）
- [x] 4.4 实现 `_init_globals()` 方法（安全全局命名空间 + 通用库）
- [ ] 4.5 实现自定义导入钩子 `SafeImportHook`（扩展的模块白名单）(未来改进)
- [ ] 4.6 实现 `_compile_restricted()` 方法（使用 RestrictedPython 编译代码）(未来改进)
- [x] 4.7 实现超时控制机制（支持 Unix）
- [ ] 4.8 实现内存监控机制（使用 `tracemalloc`）(未来改进)
- [x] 4.9 实现 `execute()` 方法整合所有安全机制
- [x] 4.10 实现异常处理和错误转换（提供友好的错误消息）

## 5. 全局变量管理 ✅
- [x] 5.1 在 `PythonSandbox` 中实现全局变量存储（`sandbox_globals`）
- [x] 5.2 实现 `get_global(name)` 方法获取全局变量
- [x] 5.3 实现 `set_global(name, value)` 方法设置全局变量
- [ ] 5.4 实现变量类型验证（只允许安全类型：DataFrame, ndarray, 基础类型）(未来改进)
- [x] 5.5 实现变量名保护（禁止覆盖 `pd`, `plt`, `sns` 等内置）
- [x] 5.6 实现变量清理机制（防止内存泄漏）

## 6. 工具函数集成（双层架构） ✅
- [x] 6.1 修改 `python_inter()` 函数使用 `PythonSandbox.execute()`
- [x] 6.2 修改 `fig_inter()` 函数实现双层架构：
  - [x] 6.2.1 在沙箱内执行绘图代码生成 Figure 对象
  - [x] 6.2.2 从沙箱全局变量中提取 Figure 对象（`sandbox.get_global(fname)`）
  - [x] 6.2.3 在工具函数层（沙箱外）保存图像到 `backend/src/images/`
  - [x] 6.2.4 确保沙箱内代码不能直接访问 `images/` 目录
- [ ] 6.3 修改 `extract_data()` 函数将 DataFrame 存储到沙箱全局变量 (未来改进)
- [x] 6.4 确保全局变量在工具间正确共享
- [x] 6.5 保持工具函数的原有接口不变（向后兼容）
- [x] 6.6 添加错误处理和用户友好的错误消息
- [ ] 6.7 添加工具函数层的访问日志（记录从沙箱提取对象和保存文件的操作）(未来改进)

## 未来改进任务（可选）

## 7. 单元测试
- [ ] 6.1 创建测试文件 `backend/tests/test_sandbox.py`
- [ ] 6.2 测试合法代码执行（pandas 操作）
- [ ] 6.3 测试合法代码执行（matplotlib 绘图）
- [ ] 6.4 测试禁止的模块导入（`import subprocess`, `import socket`）
- [ ] 6.5 测试禁止的内置函数（`eval()`, `exec()`）
- [ ] 6.6 测试受限的文件操作（沙箱内允许，沙箱外拒绝）
- [ ] 6.7 测试通用 Python 功能（re, datetime, json, collections）
- [ ] 6.8 测试资源限制（超时、内存）
- [ ] 6.9 测试全局变量共享机制
- [ ] 6.10 测试沙箱绕过尝试（各种攻击向量）
- [ ] 6.11 测试错误消息的友好性
- [ ] 6.12 代码覆盖率达到 > 90%

## 8. 集成测试
- [ ] 7.1 创建测试文件 `backend/tests/test_tools_with_sandbox.py`
- [ ] 7.2 测试 `python_inter` 工具端到端执行
- [ ] 7.3 测试 `fig_inter` 双层架构工作流程：
  - [ ] 7.3.1 验证沙箱内代码生成 Figure 对象
  - [ ] 7.3.2 验证工具函数成功提取 Figure 对象
  - [ ] 7.3.3 验证图像保存到 `backend/src/images/` 目录
  - [ ] 7.3.4 验证沙箱内代码无法直接访问 `images/` 目录
  - [ ] 7.3.5 验证返回的 URL 正确且可访问
- [ ] 7.4 测试 `extract_data` + `python_inter` 组合场景
- [ ] 7.5 测试 `extract_data` + `fig_inter` 组合场景
- [ ] 7.6 测试多个工具调用的全局变量共享
- [ ] 7.7 测试现有示例代码的兼容性
- [ ] 7.8 测试中间文件在沙箱内的读写
- [ ] 7.9 性能基准测试（执行开销 < 100ms）

## 9. 安全测试
- [ ] 8.1 创建安全测试套件 `backend/tests/test_sandbox_security.py`
- [ ] 8.2 测试路径遍历攻击（`../../etc/passwd`）
- [ ] 8.3 测试访问系统敏感目录（`/etc/`, `/usr/`, `~/.ssh/`）
- [ ] 8.4 测试符号链接安全（指向沙箱外的链接）
- [ ] 8.5 测试系统命令执行尝试（`os.system()`, `subprocess`）
- [ ] 8.6 测试网络访问尝试（`socket`, `urllib`, `requests`）
- [ ] 8.7 测试代码注入尝试（`eval()`, `exec()`, `compile()`）
- [ ] 8.8 测试反射机制绕过尝试（`getattr`, `__import__`）
- [ ] 8.9 测试资源耗尽攻击（死循环、内存炸弹）
- [ ] 8.10 测试沙箱逃逸技术（已知 CVE）
- [ ] 8.11 使用模糊测试生成攻击向量
- [ ] 8.12 文档化所有测试用例和预期结果

## 10. 审计日志
- [ ] 9.1 在 `backend/src/sandbox.py` 中添加日志记录
- [ ] 9.2 记录所有代码执行请求（代码哈希、时间戳）
- [ ] 9.3 记录安全策略违规（被拒绝的代码、原因）
- [ ] 9.4 记录资源使用情况（执行时间、内存消耗）
- [ ] 9.5 记录异常和错误
- [ ] 9.6 实现日志轮转和保留策略
- [ ] 9.7 支持配置日志级别（DEBUG, INFO, WARNING, ERROR）

## 11. 文档和配置
- [ ] 10.1 创建 `backend/docs/sandbox_security.md` 安全文档
- [ ] 10.2 文档化允许和禁止的操作
- [ ] 10.3 提供常见错误和解决方案
- [ ] 10.4 添加配置示例到 `.env.example`
- [ ] 10.5 更新 `README.md` 说明沙箱功能
- [ ] 10.6 编写沙箱配置调优指南
- [ ] 10.7 提供安全最佳实践建议

## 12. 部署准备
- [ ] 11.1 添加配置开关支持沙箱启用/禁用（`ENABLE_SANDBOX=true`）
- [ ] 11.2 实现降级方案（沙箱失败时回退到原始实现）
- [ ] 11.3 添加健康检查端点验证沙箱状态
- [ ] 11.4 配置监控告警（沙箱拒绝率、执行延迟）
- [ ] 11.5 准备灰度发布配置
- [ ] 11.6 编写部署清单和回滚计划

## 13. 验收和发布
- [ ] 12.1 执行完整测试套件（单元 + 集成 + 安全）
- [ ] 12.2 性能测试验证开销在可接受范围
- [ ] 12.3 代码审查通过
- [ ] 12.4 安全审计通过
- [ ] 12.5 更新 CHANGELOG
- [ ] 12.6 创建发布标签
- [ ] 12.7 部署到测试环境验证
- [ ] 12.8 灰度发布到生产环境（10% 流量）
- [ ] 12.9 监控 24 小时无异常后全量发布
- [ ] 12.10 发布公告和用户通知
