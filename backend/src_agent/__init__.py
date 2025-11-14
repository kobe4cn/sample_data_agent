"""
src_agent 包初始化模块

提供对关键对象的延迟加载，以避免模块间的循环导入。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .graph import agent as agent  # noqa: F401  # 供类型检查使用

__all__ = ["agent"]


def __getattr__(name: str):
    """延迟加载导出的对象，避免在导入时触发循环依赖。"""
    if name == "agent":
        from .graph import agent  # 延迟导入

        return agent
    raise AttributeError(f"module 'src_agent' has no attribute {name!r}")


def __dir__() -> list[str]:
    """确保 dir() 输出包含导出的符号。"""
    return sorted(__all__)
