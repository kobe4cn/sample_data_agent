"""
沙箱配置模块

定义Python代码沙箱的安全策略和资源限制配置。
"""

import os
from dataclasses import dataclass, field
from typing import Set


# 允许导入的模块白名单（宽松模式）
ALLOWED_MODULES: Set[str] = {
    # 数据处理
    "pandas",
    "numpy",
    "scipy",
    # 可视化
    "matplotlib",
    "matplotlib.pyplot",
    "seaborn",
    # 文件和路径（受限）
    "pathlib",
    "os.path",
    "glob",
    "fnmatch",
    # 数据格式
    "json",
    "csv",
    "xml",
    "xml.etree",
    "xml.etree.ElementTree",
    
    # 文本处理
    "re",
    "string",
    "textwrap",
    "difflib",
    # 日期时间
    "datetime",
    "time",
    "calendar",
    # 算法和数据结构
    "collections",
    "itertools",
    "functools",
    "heapq",
    "bisect",
    "queue",
    # 数学和统计
    "math",
    "statistics",
    "random",
    "decimal",
    "fractions",
    # 其他工具
    "uuid",
    "hashlib",
    "base64",
    "copy",
    "pprint",
    # 类型和元编程
    "typing",
    "dataclasses",
    "enum",
    "abc",
}

# 禁止的内置函数
# 注意：不阻止 __import__，因为 pandas/numpy 等库运行时需要动态导入模块
# 模块导入的安全性通过 ALLOWED_MODULES 白名单控制
BLOCKED_BUILTINS: Set[str] = {
    "eval",
    "exec",
    "compile",
    # "__import__",  # 不阻止，否则 pandas 无法工作
    "input",
    "help",
    "breakpoint",
    "exit",
    "quit",
}


@dataclass
class SandboxConfig:
    """沙箱配置类"""

    # 资源限制
    max_execution_time: int = 30  # 最大执行时间（秒）
    max_memory_mb: int = 512  # 最大内存使用（MB）
    max_output_size: int = 10_000  # 最大输出大小（字符数）

    # 模块白名单
    allowed_modules: Set[str] = field(default_factory=lambda: ALLOWED_MODULES.copy())

    # 禁止的内置函数
    blocked_builtins: Set[str] = field(default_factory=lambda: BLOCKED_BUILTINS.copy())

    # 沙箱工作目录（读写权限）
    sandbox_workspace: str = field(
        default_factory=lambda: os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "sandbox_workspace",
        )
    )

    # 共享数据目录（只读权限）- 用于存放用户上传的数据文件
    shared_data_dir: str = field(
        default_factory=lambda: os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
        )
    )

    # 日志级别
    log_level: str = "INFO"

    # 是否启用沙箱
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "SandboxConfig":
        """从环境变量读取配置"""
        return cls(
            max_execution_time=int(
                os.getenv("SANDBOX_MAX_EXECUTION_TIME", "30")
            ),
            max_memory_mb=int(os.getenv("SANDBOX_MAX_MEMORY_MB", "512")),
            max_output_size=int(os.getenv("SANDBOX_MAX_OUTPUT_SIZE", "10000")),
            log_level=os.getenv("SANDBOX_LOG_LEVEL", "INFO"),
            enabled=os.getenv("ENABLE_SANDBOX", "true").lower() == "true",
        )

    def validate(self) -> None:
        """验证配置有效性"""
        if self.max_execution_time <= 0:
            raise ValueError("max_execution_time must be positive")
        if self.max_memory_mb <= 0:
            raise ValueError("max_memory_mb must be positive")
        if self.max_output_size <= 0:
            raise ValueError("max_output_size must be positive")

        # 确保沙箱工作目录存在
        if not os.path.exists(self.sandbox_workspace):
            os.makedirs(self.sandbox_workspace, exist_ok=True)

        # 确保共享数据目录存在
        if not os.path.exists(self.shared_data_dir):
            os.makedirs(self.shared_data_dir, exist_ok=True)


# 默认配置实例
DEFAULT_CONFIG = SandboxConfig()
