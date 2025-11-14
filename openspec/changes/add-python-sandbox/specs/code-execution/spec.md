# 代码执行安全规范

## ADDED Requirements

### Requirement: Python 代码沙箱执行
系统 SHALL 在受限的沙箱环境中执行所有用户提供的 Python 代码，以防止恶意操作和资源滥用。

#### Scenario: 执行合法的数据分析代码
- **WHEN** 用户通过 `python_inter` 工具提交合法的 pandas 数据分析代码（如 `df.groupby('col').mean()`）
- **THEN** 代码应在沙箱中成功执行并返回正确结果
- **AND** 执行时间应在配置的超时限制内
- **AND** 内存使用应在配置的限制内

#### Scenario: 执行合法的数据可视化代码（双层架构）
- **WHEN** 用户通过 `fig_inter` 工具提交合法的 matplotlib 绘图代码（如 `fig = plt.figure(); plt.plot([1,2,3])`）
- **THEN** 代码应在沙箱中成功执行并生成 Figure 对象
- **AND** 工具函数应从沙箱中提取 Figure 对象
- **AND** 工具函数应在沙箱外将图像保存到 `backend/src/images/` 目录
- **AND** 返回图像的访问 URL（如 `http://localhost:2024/images/fig_20250111_123456_abc12345.png`）
- **AND** 沙箱内代码不应直接访问 `backend/src/images/` 目录

#### Scenario: 允许沙箱内文件读写
- **WHEN** 用户提交在沙箱工作目录内读写文件的代码（如 `open('data.txt', 'w')`）
- **THEN** 代码应成功执行
- **AND** 文件应被创建或读取在 `backend/sandbox_workspace/` 目录内
- **AND** 相对路径应自动映射到沙箱工作目录

#### Scenario: 拒绝访问沙箱外文件
- **WHEN** 用户提交访问沙箱外文件的代码（如 `open('/etc/passwd', 'r')` 或 `open('../../../etc/passwd')`）
- **THEN** 沙箱 SHALL 拒绝该操作
- **AND** 返回安全错误消息，说明路径不在沙箱目录内
- **AND** 记录该违规尝试到审计日志

#### Scenario: 拒绝系统命令执行
- **WHEN** 用户提交包含系统命令的代码（如 `os.system('rm -rf /')` 或 `subprocess.run(['ls'])`）
- **THEN** 沙箱 SHALL 拒绝执行该代码
- **AND** 返回安全错误消息，说明系统命令执行被禁止
- **AND** 记录该违规尝试到审计日志

#### Scenario: 拒绝网络访问
- **WHEN** 用户提交包含网络操作的代码（如 `import requests; requests.get('http://evil.com')`）
- **THEN** 沙箱 SHALL 拒绝执行该代码
- **AND** 返回安全错误消息，说明网络访问被禁止
- **AND** 记录该违规尝试到审计日志

#### Scenario: 拒绝危险的代码执行函数
- **WHEN** 用户提交包含 `eval()`, `exec()`, 或 `compile()` 的代码
- **THEN** 沙箱 SHALL 拒绝执行该代码
- **AND** 返回安全错误消息，说明动态代码执行被禁止
- **AND** 记录该违规尝试到审计日志

#### Scenario: 超时保护
- **WHEN** 用户提交的代码执行时间超过配置的超时限制（默认 30 秒）
- **THEN** 沙箱 SHALL 强制终止代码执行
- **AND** 返回超时错误消息，包含实际执行时长
- **AND** 释放所有相关资源

#### Scenario: 内存限制保护
- **WHEN** 用户提交的代码尝试分配超过限制的内存（默认 512MB）
- **THEN** 沙箱 SHALL 终止代码执行
- **AND** 返回内存超限错误消息
- **AND** 释放已分配的内存

### Requirement: 模块导入白名单
系统 SHALL 只允许导入预定义白名单中的 Python 模块，拒绝所有其他模块的导入。

#### Scenario: 允许导入白名单模块
- **WHEN** 用户代码导入白名单中的模块（如 `import pandas`, `import matplotlib.pyplot`, `import numpy`）
- **THEN** 导入应成功完成
- **AND** 模块的所有合法功能应可用

#### Scenario: 拒绝导入危险模块
- **WHEN** 用户代码尝试导入不在白名单中的模块（如 `import os`, `import subprocess`, `import socket`）
- **THEN** 沙箱 SHALL 拒绝导入
- **AND** 返回导入错误消息，说明该模块不在白名单中
- **AND** 提供白名单模块列表供参考

#### Scenario: 拒绝动态导入
- **WHEN** 用户代码尝试使用 `__import__()` 动态导入模块
- **THEN** 沙箱 SHALL 拒绝执行
- **AND** 返回安全错误消息

### Requirement: 全局变量安全管理
系统 SHALL 维护一个隔离的全局变量命名空间，用于在多次代码执行之间共享数据，同时防止污染和恶意操作。

#### Scenario: 创建和访问全局变量
- **WHEN** 用户代码创建全局变量（如 `df = pd.DataFrame(...)`）
- **THEN** 变量应存储在沙箱的隔离命名空间中
- **AND** 后续代码执行应能访问该变量
- **AND** 变量类型应被验证为安全类型（DataFrame, ndarray, 基础类型等）

#### Scenario: 保护内置变量
- **WHEN** 用户代码尝试覆盖内置变量（如 `pd = None`, `plt = "evil"`）
- **THEN** 沙箱 SHALL 拒绝该操作
- **AND** 返回错误消息，说明内置变量被保护
- **AND** 保持原始内置变量不变

#### Scenario: 全局变量在工具间共享
- **WHEN** 用户使用 `extract_data` 工具提取数据到 DataFrame `df1`
- **AND** 随后使用 `python_inter` 工具执行 `df1.describe()`
- **THEN** `python_inter` 应能访问 `df1`
- **AND** 返回正确的描述性统计结果

#### Scenario: 全局变量类型验证
- **WHEN** 用户代码尝试创建不安全类型的全局变量（如函数对象、类对象）
- **THEN** 沙箱 SHALL 拒绝该操作
- **AND** 返回类型错误消息，列出允许的类型

### Requirement: 审计日志记录
系统 SHALL 记录所有代码执行活动、安全违规和资源使用情况，用于审计和调试。

#### Scenario: 记录成功的代码执行
- **WHEN** 代码在沙箱中成功执行
- **THEN** 系统 SHALL 记录以下信息：
  - 代码内容的 SHA-256 哈希
  - 执行时间戳
  - 执行耗时
  - 内存使用量
  - 返回值类型

#### Scenario: 记录安全违规
- **WHEN** 代码因安全策略被拒绝执行
- **THEN** 系统 SHALL 记录以下信息：
  - 被拒绝的代码内容（完整或摘要）
  - 违规类型（禁止模块、禁止函数、资源超限等）
  - 时间戳
  - 用户标识（如果可用）
  - 请求来源

#### Scenario: 记录异常和错误
- **WHEN** 代码执行过程中发生异常
- **THEN** 系统 SHALL 记录以下信息：
  - 异常类型和消息
  - 堆栈跟踪
  - 代码内容
  - 时间戳

#### Scenario: 日志级别配置
- **WHEN** 管理员设置日志级别为 `DEBUG`
- **THEN** 所有详细调试信息应被记录
- **WHEN** 管理员设置日志级别为 `ERROR`
- **THEN** 只有错误和严重问题应被记录

### Requirement: 可配置的安全策略
系统 SHALL 支持通过配置文件或环境变量调整沙箱的安全策略和资源限制。

#### Scenario: 配置执行超时
- **WHEN** 管理员设置环境变量 `SANDBOX_MAX_EXECUTION_TIME=60`
- **THEN** 所有代码执行的超时限制应为 60 秒
- **AND** 超过 60 秒的执行应被终止

#### Scenario: 配置内存限制
- **WHEN** 管理员在配置文件中设置 `max_memory_mb: 1024`
- **THEN** 代码执行的内存限制应为 1024MB
- **AND** 超过该限制的执行应被终止

#### Scenario: 配置模块白名单
- **WHEN** 管理员在配置文件中添加新模块到白名单（如 `scikit-learn`）
- **THEN** 用户代码应能导入该模块
- **AND** 模块的所有功能应可用

#### Scenario: 启用/禁用沙箱
- **WHEN** 管理员设置 `ENABLE_SANDBOX=false`
- **THEN** 系统 SHALL 回退到不使用沙箱的执行方式
- **AND** 记录警告日志说明沙箱已禁用
- **WHEN** 管理员设置 `ENABLE_SANDBOX=true`（默认）
- **THEN** 所有代码执行 SHALL 在沙箱中进行

### Requirement: 友好的错误消息
系统 SHALL 为用户提供清晰、可操作的错误消息，说明为什么代码被拒绝以及如何修正。

#### Scenario: 模块导入错误消息
- **WHEN** 用户尝试导入禁止的模块 `import os`
- **THEN** 错误消息应包含：
  - 明确说明 `os` 模块不在白名单中
  - 说明原因（安全限制）
  - 提供允许的模块列表
  - 建议替代方案（如使用 `pathlib` 代替 `os.path`，但 `pathlib` 也需在白名单）

#### Scenario: 资源限制错误消息
- **WHEN** 代码执行超时
- **THEN** 错误消息应包含：
  - 明确说明执行超时
  - 实际执行时长
  - 配置的超时限制
  - 优化代码的建议

#### Scenario: 语法错误消息
- **WHEN** 用户提交的代码存在 Python 语法错误
- **THEN** 错误消息应包含：
  - Python 解释器的原始错误消息
  - 错误位置（行号、列号）
  - 代码片段高亮错误位置

### Requirement: 向后兼容性
系统 SHALL 确保现有合法的数据分析和可视化代码无需修改即可在沙箱中正常运行。

#### Scenario: 兼容现有 pandas 代码
- **WHEN** 用户运行现有的 pandas 数据分析代码
- **THEN** 代码应在沙箱中成功执行
- **AND** 返回结果应与非沙箱环境一致
- **AND** 性能下降应 < 10%

#### Scenario: 兼容现有 matplotlib 代码
- **WHEN** 用户运行现有的 matplotlib 绘图代码
- **THEN** 代码应在沙箱中成功执行
- **AND** 生成的图像应与非沙箱环境一致
- **AND** 性能下降应 < 10%

#### Scenario: 保持工具接口不变
- **WHEN** 客户端调用 `python_inter` 或 `fig_inter` 工具
- **THEN** 工具的输入参数和返回值格式应保持不变
- **AND** 客户端代码无需修改

### Requirement: 通用 Python 功能支持
系统 SHALL 支持通用 Python 代码执行，包括字符串处理、日期时间操作、数据格式解析、算法等常见功能。

#### Scenario: 字符串和正则表达式处理
- **WHEN** 用户提交字符串处理代码（如 `import re; re.findall(r'\d+', 'abc123')`）
- **THEN** 代码应成功执行
- **AND** 返回正确的匹配结果

#### Scenario: 日期时间操作
- **WHEN** 用户提交日期时间代码（如 `from datetime import datetime; datetime.now()`）
- **THEN** 代码应成功执行
- **AND** 返回当前日期时间对象

#### Scenario: JSON 数据处理
- **WHEN** 用户提交 JSON 处理代码（如 `import json; json.dumps({'key': 'value'})`）
- **THEN** 代码应成功执行
- **AND** 返回正确的 JSON 字符串

#### Scenario: XML 数据处理
- **WHEN** 用户提交 XML 解析代码（如 `import xml.etree.ElementTree as ET; ET.fromstring('<root/>')`）
- **THEN** 代码应成功执行
- **AND** 返回 XML 元素对象

#### Scenario: CSV 文件读写
- **WHEN** 用户提交 CSV 操作代码（如 `import csv; csv.reader(open('data.csv'))`）
- **THEN** 代码应成功执行
- **AND** CSV 文件应在沙箱目录内被读取

#### Scenario: 算法和数据结构
- **WHEN** 用户提交算法代码（如 `from collections import Counter; Counter([1,1,2,3])`）
- **THEN** 代码应成功执行
- **AND** 返回正确的计数结果

#### Scenario: 数学计算
- **WHEN** 用户提交数学计算代码（如 `import math; math.sqrt(16)`）
- **THEN** 代码应成功执行
- **AND** 返回正确的计算结果

### Requirement: 双层文件访问架构
系统 SHALL 采用双层架构：沙箱内代码只能访问 `sandbox_workspace/`，工具函数在可信层可以处理输出文件到其他目录（如 `images/`）。

#### Scenario: 工具函数保存输出到沙箱外目录
- **WHEN** `fig_inter` 工具执行绘图代码生成 Figure 对象
- **THEN** 沙箱应成功执行代码并返回 Figure 对象
- **AND** 工具函数应能在可信层访问该对象
- **AND** 工具函数应能将图像保存到 `backend/src/images/` 目录（沙箱外）
- **AND** 沙箱内代码不应直接访问 `images/` 目录

#### Scenario: 沙箱内代码尝试直接保存到沙箱外目录
- **WHEN** 用户在沙箱内代码中尝试保存文件到沙箱外（如 `fig.savefig('../images/test.png')`）
- **THEN** 沙箱 SHALL 解析路径并检测其在沙箱外
- **AND** 拒绝该文件操作
- **AND** 返回安全错误消息

### Requirement: 文件系统沙箱
系统 SHALL 提供受限的文件系统访问，允许在沙箱工作目录内进行文件操作，同时防止访问系统敏感路径。

#### Scenario: 相对路径自动映射
- **WHEN** 用户使用相对路径操作文件（如 `open('output.txt', 'w')`）
- **THEN** 路径应自动映射到 `backend/sandbox_workspace/output.txt`
- **AND** 文件操作应成功完成

#### Scenario: 路径遍历攻击防护
- **WHEN** 用户尝试使用路径遍历（如 `open('../../sensitive.txt')`）
- **THEN** 沙箱 SHALL 检测并解析实际路径
- **AND** 如果解析后的路径在沙箱外，拒绝访问
- **AND** 返回安全错误消息

#### Scenario: 符号链接安全
- **WHEN** 用户尝试访问指向沙箱外的符号链接
- **THEN** 沙箱 SHALL 解析符号链接的实际目标
- **AND** 如果目标在沙箱外，拒绝访问

#### Scenario: pathlib 路径操作
- **WHEN** 用户使用 pathlib 进行路径操作（如 `from pathlib import Path; Path('data').mkdir()`）
- **THEN** 操作应限制在沙箱目录内
- **AND** 目录应在 `backend/sandbox_workspace/data/` 创建

#### Scenario: 目录遍历和 glob 模式
- **WHEN** 用户使用 glob 匹配文件（如 `from pathlib import Path; list(Path('.').glob('*.txt'))`）
- **THEN** 应返回沙箱目录内匹配的文件
- **AND** 不应访问沙箱外的文件系统

#### Scenario: 中间文件存储在沙箱内
- **WHEN** 用户代码需要保存中间数据文件（如 `df.to_csv('intermediate_data.csv')`）
- **THEN** 文件应成功保存到 `backend/sandbox_workspace/intermediate_data.csv`
- **AND** 后续代码应能读取该文件（如 `pd.read_csv('intermediate_data.csv')`）
- **AND** 文件应只在沙箱目录内可见

### Requirement: 性能要求
系统 SHALL 确保沙箱的安全检查开销不显著影响代码执行性能。

#### Scenario: 编译开销
- **WHEN** 执行简单的 pandas 代码（如 `df.head()`）
- **THEN** 沙箱的编译和检查开销应 < 50ms

#### Scenario: 执行开销
- **WHEN** 执行计算密集型代码（如 `df.groupby().agg()`）
- **THEN** 沙箱的运行时开销应 < 5% 的总执行时间

#### Scenario: 内存开销
- **WHEN** 沙箱环境初始化
- **THEN** 额外的内存开销应 < 10MB

#### Scenario: 并发性能
- **WHEN** 同时执行 10 个代码请求
- **THEN** 每个请求的平均响应时间应 < 单个请求的 1.5 倍
- **AND** 系统应能处理并发请求而不崩溃
