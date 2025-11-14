# Python 沙箱执行设计文档

## Context

当前系统需要执行 AI 代理生成的 Python 代码以完成数据分析和可视化任务。直接使用 `exec()` 存在严重安全风险，需要实现安全的沙箱执行环境，同时保持数据分析功能的完整性。

**约束条件:**
- 必须支持 pandas、matplotlib、seaborn 等数据分析库
- 必须保持现有工具的接口兼容性
- 执行延迟应控制在可接受范围（< 100ms 开销）
- 需要支持多用户并发执行

**利益相关者:**
- 开发团队：需要维护和配置沙箱
- 最终用户：期望数据分析功能正常工作
- 安全团队：要求消除代码注入风险

## Goals / Non-Goals

### Goals
1. **安全隔离**: 阻止危险操作（系统调用、网络请求、敏感目录访问）
2. **资源限制**: 防止资源耗尽（CPU、内存、执行时间）
3. **功能完整**: 支持通用 Python 代码执行（数据分析、文本处理、算法、文件操作等）
4. **受控文件访问**: 允许在沙箱工作目录内读写文件，禁止访问系统敏感路径
5. **可配置性**: 支持灵活配置白名单和限制策略
6. **可观测性**: 记录执行日志用于审计和调试

### Non-Goals
1. **不支持**: 系统命令执行（subprocess, os.system 等）
2. **不支持**: 网络访问（socket, urllib, requests 等）
3. **不支持**: 多进程/多线程代码执行
4. **不追求**: 100% 防护（承认沙箱可能被绕过，但大幅提高攻击门槛）
5. **不优化**: 极端性能场景（优先考虑安全而非性能）

## Decisions

### 决策 1: 使用 RestrictedPython 作为核心沙箱

**选择**: RestrictedPython + 自定义安全策略

**理由**:
- RestrictedPython 是 Zope 项目维护的成熟库，有多年生产验证
- 提供编译时代码检查，可以在执行前拦截危险操作
- 支持自定义安全策略（`__builtins__`, `__import__`）
- 比 subprocess 隔离性能开销更小

**替代方案**:
1. **Docker 容器隔离**
   - 优点: 完全隔离、资源限制完善
   - 缺点: 启动开销大（>100ms）、需要 Docker 守护进程、部署复杂
   - 不选择原因: 性能开销过大，不适合频繁执行短代码

2. **subprocess + ulimit**
   - 优点: 进程级隔离、可使用系统资源限制
   - 缺点: 跨进程通信开销、难以共享全局变量（如 DataFrame）
   - 不选择原因: 破坏现有架构（全局变量共享）

3. **代码静态分析 (AST)**
   - 优点: 零运行时开销
   - 缺点: 难以覆盖所有攻击向量、容易被绕过
   - 不选择原因: 安全性不足

### 决策 2: 三层防御策略

**架构**:
```
Layer 1: 编译时检查 (RestrictedPython)
  ↓ 拒绝危险语法（import os, eval, exec）
Layer 2: 运行时隔离 (受限 builtins + import hook)
  ↓ 限制可用函数和模块
Layer 3: 资源限制 (timeout + signal)
  ↓ 防止资源耗尽
```

**理由**: 多层防御提供纵深安全，即使一层被绕过，其他层仍可提供保护。

### 决策 3: 模块白名单（宽松模式）

**允许的模块**:
```python
ALLOWED_MODULES = {
    # 数据处理
    'pandas', 'numpy', 'scipy',
    # 可视化
    'matplotlib', 'matplotlib.pyplot', 'seaborn',
    # 文件和路径（受限）
    'pathlib', 'os.path', 'glob', 'fnmatch',
    # 数据格式
    'json', 'csv', 'xml', 'xml.etree', 'xml.etree.ElementTree',
    # 文本处理
    're', 'string', 'textwrap', 'difflib',
    # 日期时间
    'datetime', 'time', 'calendar',
    # 算法和数据结构
    'collections', 'itertools', 'functools', 'heapq', 'bisect', 'queue',
    # 数学和统计
    'math', 'statistics', 'random', 'decimal', 'fractions',
    # 其他工具
    'uuid', 'hashlib', 'base64', 'copy', 'pprint',
    # 类型和元编程
    'typing', 'dataclasses', 'enum', 'abc'
}
```

**禁止的模块/功能**:
- 系统调用: `subprocess`, `os.system`, `os.exec*`, `os.spawn*`
- 网络: `socket`, `urllib`, `requests`, `http`, `ftplib`, `smtplib`
- 代码执行: `eval`, `exec`, `compile` (在用户代码中)
- 危险的内置函数: `__import__` (动态导入), `input()` (交互输入)

**受限但允许的功能**:
- `open()`: 允许，但路径被重定向到沙箱工作目录
- `os.path.*`: 允许路径操作函数
- `pathlib.Path`: 允许，但所有路径操作限制在沙箱目录内

### 决策 4: 双层文件访问架构

**核心原则**: 沙箱内生成对象，工具层处理文件

**架构图**:
```
用户请求
  ↓
工具函数 (fig_inter, python_inter)  ← 可信层，可访问所有目录
  ↓
沙箱执行 (PythonSandbox.execute)   ← 受限层，只能访问 sandbox_workspace/
  ↓
返回数据对象 (Figure, DataFrame, dict)
  ↓
工具函数处理输出 (保存到 images/, 格式化返回)
```

**两种文件访问模式**:

1. **模式 A: 对象传递（用于图像、处理结果）**
   - 沙箱内代码生成数据对象（不直接保存文件）
   - 工具函数在沙箱外处理对象并保存到指定目录
   - 示例: `fig_inter` 生成图像对象 → 工具保存到 `backend/src/images/`

2. **模式 B: 沙箱内文件（用于中间数据、临时文件）**
   - 沙箱内代码可以在 `sandbox_workspace/` 内读写文件
   - 用于中间数据存储、CSV 处理等
   - 示例: `df.to_csv('temp.csv')` → 保存到 `sandbox_workspace/temp.csv`

### 决策 5: 文件系统沙箱实现

**架构**: 路径重写 + 权限检查 + 受信任输出目录

**实现方案**:
```python
class SandboxFileSystem:
    def __init__(self, workspace_dir: str):
        # 沙箱工作目录: backend/sandbox_workspace/
        self.workspace = Path(workspace_dir).resolve()

    def safe_open(self, path, mode='r', **kwargs):
        # 1. 解析路径
        resolved = self._resolve_path(path)
        # 2. 检查是否在沙箱内
        if not self._is_safe_path(resolved):
            raise SecurityError(f"访问被拒绝: {path} 不在沙箱目录内")
        # 3. 执行实际操作
        return open(resolved, mode, **kwargs)

    def _resolve_path(self, path):
        # 相对路径自动映射到沙箱目录
        if not Path(path).is_absolute():
            return (self.workspace / path).resolve()
        return Path(path).resolve()

    def _is_safe_path(self, path):
        # 检查路径是否在沙箱内
        try:
            path.relative_to(self.workspace)
            return True
        except ValueError:
            return False
```

**安全措施**:
- 所有相对路径自动映射到 `backend/sandbox_workspace/`
- 绝对路径必须在沙箱目录内，否则拒绝
- 防止路径遍历攻击（`../../../etc/passwd`）
- 使用 `Path.resolve()` 解析符号链接和 `..`

**允许的文件操作**:
- 读文件: `open('data.txt', 'r')`
- 写文件: `open('output.txt', 'w')`
- 追加文件: `open('log.txt', 'a')`
- CSV/JSON读写: `pd.read_csv()`, `json.load()`
- 目录操作: `pathlib.Path.mkdir()`, `Path.glob()`

**禁止的文件操作**:
- 访问系统目录: `/etc/`, `/usr/`, `/var/`, `/sys/`
- 访问用户目录: `~/.ssh/`, `~/.aws/`
- 删除沙箱外文件
- 创建符号链接指向沙箱外

**受信任输出目录（可选配置）**:
```python
# 配置文件中定义
TRUSTED_OUTPUT_DIRS = [
    'backend/src/images',      # 图像输出目录
    'backend/outputs',         # 通用输出目录（如果需要）
]
```

**使用场景**:
- **不推荐**: 让沙箱代码直接写入受信任目录（安全风险）
- **推荐**: 工具函数从沙箱提取对象后，在可信层保存到输出目录

**fig_inter 工作流程示例**:
```python
def fig_inter(py_code, fname):
    # 1. 在沙箱中执行绘图代码
    sandbox = PythonSandbox()
    result = sandbox.execute(py_code)  # 沙箱内，无文件访问权限

    # 2. 从沙箱提取图像对象（在可信层）
    fig = sandbox.get_global(fname)

    # 3. 在可信层保存图像到 images 目录（沙箱外）
    img_dir = 'backend/src/images'
    fig.savefig(os.path.join(img_dir, filename))

    return image_url
```

### 决策 6: 资源限制配置

```python
RESOURCE_LIMITS = {
    'max_execution_time': 30,      # 秒
    'max_memory_mb': 512,           # MB
    'max_output_size': 10_000,      # 字符数
}
```

**实现**:
- 超时: 使用 `signal.alarm()` (Unix) 或 `threading.Timer` (跨平台)
- 内存: 使用 `tracemalloc` 监控 + 定期检查
- 输出: 截断超长输出

### 决策 7: 全局变量共享策略

**挑战**: `extract_data` 工具将 DataFrame 保存到全局变量，后续代码需要访问。

**方案**: 维护受控的全局变量命名空间
```python
# 沙箱维护一个隔离的全局变量字典
sandbox_globals = {
    '__builtins__': safe_builtins,
    'pd': pandas,
    'plt': matplotlib.pyplot,
    'sns': seaborn,
    # ... 用户创建的 DataFrame
}
```

**安全措施**:
- 只允许创建 DataFrame、Series、ndarray 等数据类型的全局变量
- 禁止覆盖内置变量（如 `pd`, `plt`）
- 定期清理未使用的变量（防止内存泄漏）

## Risks / Trade-offs

### 风险 1: 沙箱绕过
- **风险**: RestrictedPython 可能存在未知漏洞
- **缓解**:
  - 定期更新依赖版本
  - 订阅安全公告
  - 实施额外的代码审查
  - 添加异常行为检测（如大量 CPU 使用）

### 风险 2: 误杀合法代码
- **风险**: 过于严格的限制可能阻止合法分析代码
- **缓解**:
  - 提供清晰的错误消息，说明哪个操作被禁止
  - 记录被拒绝的代码用于白名单调整
  - 提供配置选项供管理员调整策略

### 风险 3: 性能影响
- **风险**: 安全检查增加执行延迟
- **缓解**:
  - 缓存编译后的安全代码
  - 优化导入钩子实现
  - 对简单代码使用快速路径

### 权衡 1: 安全 vs 灵活性
- **选择**: 平衡安全和灵活性（宽松模式）
- **影响**:
  - 允许: 文件操作（沙箱目录内）、通用 Python 库
  - 禁止: 系统命令、网络请求
- **理由**: 通用代码执行需求 + 可接受的安全风险

### 权衡 2: 性能 vs 隔离性
- **选择**: 使用进程内沙箱而非进程/容器隔离
- **影响**: 理论上存在沙箱逃逸风险
- **理由**: 性能要求高，且多层防御足以应对大部分威胁

## Migration Plan

### 阶段 1: 实现沙箱模块（第1周）
1. 安装 RestrictedPython 依赖
2. 实现 `backend/src/sandbox.py` 核心模块
3. 实现配置管理 `backend/src/config/sandbox_config.py`
4. 编写单元测试验证沙箱功能

### 阶段 2: 集成现有工具（第2周）
1. 修改 `python_inter` 使用沙箱
2. 修改 `fig_inter` 使用沙箱
3. 确保全局变量共享机制正常工作
4. 集成测试验证现有功能

### 阶段 3: 测试和验证（第3周）
1. 安全测试：尝试各种攻击场景
2. 功能测试：验证数据分析用例
3. 性能测试：测量执行开销
4. 用户验收测试

### 阶段 4: 部署和监控（第4周）
1. 灰度发布（10% 流量）
2. 监控错误日志和性能指标
3. 调整配置优化误杀率
4. 全量发布

### 回滚计划
- 保留原始 `exec()` 实现作为降级方案
- 通过配置开关快速切换
- 回滚条件：
  - 误杀率 > 5%
  - 性能下降 > 100ms
  - 出现严重 bug

## Open Questions

1. **Q**: 是否需要支持用户自定义模块导入？
   - **待讨论**: 可能需要为高级用户提供申请白名单的流程

2. **Q**: 如何处理大数据集的内存限制？
   - **建议**: 根据实际使用情况调整，初期设为 512MB

3. **Q**: 是否需要记录所有执行的代码？
   - **隐私考虑**: 可能包含敏感业务逻辑，需要明确数据保留策略

4. **Q**: 是否需要支持多租户隔离？
   - **未来扩展**: 当前单租户，未来可能需要为不同用户设置不同配置

## Implementation Notes

### 核心代码结构

```python
# backend/src/sandbox.py
class PythonSandbox:
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.safe_globals = self._create_safe_globals()

    def execute(self, code: str, timeout: int = 30) -> Any:
        # 1. 编译检查
        compiled = self._compile_restricted(code)
        # 2. 设置超时
        with timeout_context(timeout):
            # 3. 执行代码
            result = self._execute_safe(compiled)
        return result

    def _compile_restricted(self, code: str):
        from RestrictedPython import compile_restricted
        return compile_restricted(code, '<sandbox>', 'exec')

    def _create_safe_globals(self):
        # 受限的 builtins + 白名单模块
        pass
```

### 测试用例

```python
# 应该成功的代码
assert sandbox.execute("df = pd.DataFrame({'a': [1,2,3]})")
assert sandbox.execute("fig, ax = plt.subplots()")

# 应该被拒绝的代码
with pytest.raises(SecurityError):
    sandbox.execute("import os; os.system('ls')")
with pytest.raises(SecurityError):
    sandbox.execute("open('/etc/passwd').read()")
with pytest.raises(SecurityError):
    sandbox.execute("__import__('subprocess').run(['ls'])")
```
