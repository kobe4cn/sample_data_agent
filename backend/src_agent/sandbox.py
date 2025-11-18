"""
Python 代码沙箱执行模块

使用 RestrictedPython 提供安全的代码执行环境。
"""

import logging
import platform
import signal
import threading
from contextlib import contextmanager
from typing import Any

import matplotlib.font_manager as fm

import src_agent.data_loader as data_loader
from src_agent.config.sandbox_config import SandboxConfig
from src_agent.sandbox_filesystem import SandboxFileSystem, SecurityError

logger = logging.getLogger(__name__)


class SandboxExecutionError(Exception):
    """沙箱执行错误"""
    pass


class SandboxTimeoutError(SandboxExecutionError):
    """沙箱执行超时"""
    pass


def _detect_chinese_font() -> str | None:
    """检测系统可用的中文字体

    根据操作系统自动选择合适的中文字体。

    Returns:
        找到的第一个可用中文字体名称，如果没有找到则返回 None
    """
    system = platform.system()

    # 定义不同操作系统的候选字体列表
    font_candidates = {
        "Darwin": [  # macOS
            "PingFang SC",
            "Heiti TC",
            "STHeiti",
            "Arial Unicode MS",
        ],
        "Windows": [
            "Microsoft YaHei",
            "SimHei",
            "SimSun",
            "FangSong",
        ],
        "Linux": [
            "WenQuanYi Micro Hei",
            "Droid Sans Fallback",
            "Noto Sans CJK SC",
        ],
    }

    # 获取当前系统的候选字体列表
    candidates = font_candidates.get(system, [])

    # 获取系统所有可用字体
    available_fonts = {f.name for f in fm.fontManager.ttflist}

    # 查找第一个可用的中文字体
    for font_name in candidates:
        if font_name in available_fonts:
            logger.info(f"检测到中文字体: {font_name}")
            return font_name

    logger.warning(
        f"未找到支持中文的字体。已尝试的字体列表: {candidates}。"
        "图表中的中文字符可能无法正常显示。"
    )
    return None


class PythonSandbox:
    """Python 代码沙箱

    提供安全的 Python 代码执行环境，限制危险操作和资源使用。
    """

    def __init__(self, config: SandboxConfig | None = None):
        """
        Args:
            config: 沙箱配置，如果为None则使用默认配置
        """
        self.config = config or SandboxConfig.from_env()
        self.config.validate()

        # 文件系统沙箱（支持工作目录和共享数据目录）
        self.filesystem = SandboxFileSystem(
            self.config.sandbox_workspace,
            self.config.shared_data_dir,
        )

        # 配置 matplotlib 中文字体支持
        self._configure_matplotlib_fonts()

        # 全局变量命名空间（在工具间共享）
        self.sandbox_globals: dict[str, Any] = {}
        self._init_globals()

    def _configure_matplotlib_fonts(self) -> None:
        """配置 matplotlib 以支持中文字体显示"""
        try:
            import matplotlib.pyplot as plt

            # 检测可用的中文字体
            chinese_font = _detect_chinese_font()

            if chinese_font:
                # 配置 matplotlib 使用检测到的中文字体
                plt.rcParams["font.sans-serif"] = [chinese_font] + plt.rcParams[
                    "font.sans-serif"
                ]
                # 解决负号 '-' 显示为方块的问题
                plt.rcParams["axes.unicode_minus"] = False
                logger.info(f"已配置 matplotlib 使用中文字体: {chinese_font}")
            else:
                logger.warning(
                    "未配置中文字体，matplotlib 将使用默认字体。"
                    "中文字符可能显示为方框。"
                )
        except Exception as e:
            logger.error(f"配置 matplotlib 中文字体时出错: {e}，将继续使用默认配置")

    def _init_globals(self) -> None:
        """初始化全局变量命名空间"""
        # 导入允许的模块
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        import json
        import re
        import datetime
        import math
        import collections
        import itertools
        from pathlib import Path

        # 创建受限的内置函数字典
        safe_builtins = self._create_safe_builtins()

        # 初始化全局命名空间
        self.sandbox_globals = {
            "__builtins__": safe_builtins,
            # 数据分析库
            "pd": pd,
            "np": np,
            "plt": plt,
            "sns": sns,
            # 通用库
            "json": json,
            "re": re,
            "datetime": datetime,
            "math": math,
            "collections": collections,
            "itertools": itertools,
            "Path": Path,
            # 数据加载工具
            "load_dataset": data_loader.load_dataset,
            "list_datasets": data_loader.list_datasets,
            "DATASET_CATALOG": data_loader.DATASET_CATALOG,
            "data_loader": data_loader,
        }

    def _create_safe_builtins(self) -> dict[str, Any]:
        """创建安全的内置函数字典"""
        import builtins

        # 复制所有内置函数
        safe_builtins = {}
        for name in dir(builtins):
            # 跳过私有函数，但保留 __import__（pandas/numpy 需要）
            if name.startswith("_") and name != "__import__":
                continue
            if name in self.config.blocked_builtins:
                continue
            safe_builtins[name] = getattr(builtins, name)

        # 替换 open 为安全版本
        safe_builtins["open"] = self.filesystem.safe_open

        return safe_builtins

    @contextmanager
    def _timeout_context(self, timeout: int):
        """超时上下文管理器"""
        # signal 只能在主解释器的主线程中使用；LangGraph 在工具执行时可能运行于工作线程。
        if threading.current_thread() is not threading.main_thread():
            logger.debug(
                "沙箱运行在非主线程，无法启用 signal 超时控制；此段代码将不设置超时。"
            )
            yield
            return

        def timeout_handler(signum, frame):
            raise SandboxTimeoutError(
                f"代码执行超时（超过 {timeout} 秒）"
            )

        # 设置超时信号（仅Unix系统）
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            yield
        finally:
            signal.alarm(0)  # 取消超时

    def execute(self, code: str, timeout: int | None = None) -> Any:
        """执行 Python 代码

        Args:
            code: 要执行的 Python 代码
            timeout: 超时时间（秒），如果为None则使用配置的默认值

        Returns:
            代码执行结果

        Raises:
            SandboxExecutionError: 代码执行失败
            SandboxTimeoutError: 代码执行超时
            SecurityError: 安全策略违规
        """
        if not self.config.enabled:
            # 如果沙箱被禁用，直接执行（仅用于调试）
            logger.warning("沙箱已禁用，直接执行代码（不安全）")
            exec(code, self.sandbox_globals)  # noqa: S102
            return None

        timeout = timeout or self.config.max_execution_time
        local_vars: dict[str, Any] = {}
        result = None

        try:
            # 尝试作为表达式执行（返回值）
            try:
                expression_code = compile(
                    f"__sandbox_result__ = ({code})",
                    "<sandbox>",
                    "exec",
                )
                # 使用超时执行
                with self._timeout_context(timeout):
                    exec(expression_code, self.sandbox_globals, local_vars)  # noqa: S102
                result = local_vars.get("__sandbox_result__")
                return result
            except SyntaxError:
                # 不是表达式，作为语句执行
                pass

            # 作为语句执行
            compiled_code = compile(code, "<sandbox>", "exec")

            # 记录执行前的全局变量
            globals_before = set(self.sandbox_globals.keys())

            with self._timeout_context(timeout):
                exec(compiled_code, self.sandbox_globals, local_vars)  # noqa: S102

            # 合并局部变量到全局变量（用于跨工具共享）
            self.sandbox_globals.update(local_vars)

            # 检测新创建的全局变量
            globals_after = set(self.sandbox_globals.keys())
            new_vars = globals_after - globals_before

            if new_vars:
                # 返回新变量的字典
                result = {var: self.sandbox_globals[var] for var in new_vars}
                return result

            return None

        except SandboxTimeoutError:
            raise
        except SecurityError:
            raise
        except Exception as e:
            raise SandboxExecutionError(f"代码执行失败: {str(e)}") from e

    def get_global(self, name: str) -> Any:
        """获取全局变量

        Args:
            name: 变量名

        Returns:
            变量值

        Raises:
            KeyError: 变量不存在
        """
        if name not in self.sandbox_globals:
            raise KeyError(f"全局变量 '{name}' 不存在")
        return self.sandbox_globals[name]

    def set_global(self, name: str, value: Any) -> None:
        """设置全局变量

        Args:
            name: 变量名
            value: 变量值

        Raises:
            SecurityError: 尝试覆盖受保护的内置变量
        """
        # 检查是否尝试覆盖受保护的变量
        protected_vars = {"pd", "np", "plt", "sns", "__builtins__"}
        if name in protected_vars:
            raise SecurityError(
                f"禁止覆盖受保护的内置变量: {name}"
            )

        self.sandbox_globals[name] = value

    def clear_user_variables(self) -> None:
        """清理用户创建的变量（保留内置变量）"""
        protected_vars = {
            "__builtins__",
            "pd",
            "np",
            "plt",
            "sns",
            "json",
            "re",
            "datetime",
            "math",
            "collections",
            "itertools",
            "Path",
        }

        # 删除不在保护列表中的变量
        user_vars = [k for k in self.sandbox_globals if k not in protected_vars]
        for var in user_vars:
            del self.sandbox_globals[var]
