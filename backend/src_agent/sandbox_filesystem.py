"""
文件系统沙箱模块

提供受限的文件系统访问，支持多个目录和只读权限控制。
"""

from pathlib import Path
from typing import Any


class SecurityError(Exception):
    """安全错误异常"""
    pass


class SandboxFileSystem:
    """沙箱文件系统

    支持两种目录访问模式：
    1. 工作目录（读写）: 用于临时文件和中间结果
    2. 共享数据目录（只读）: 用于访问用户上传的数据文件

    防止路径遍历攻击和未授权的文件访问。
    """

    def __init__(self, workspace_dir: str, shared_data_dir: str | None = None):
        """
        Args:
            workspace_dir: 沙箱工作目录的绝对路径（读写权限）
            shared_data_dir: 共享数据目录的绝对路径（只读权限），可选
        """
        self.workspace = Path(workspace_dir).resolve()
        # 确保工作目录存在
        self.workspace.mkdir(parents=True, exist_ok=True)

        # 共享数据目录（只读）
        self.shared_data_dir = (
            Path(shared_data_dir).resolve() if shared_data_dir else None
        )
        if self.shared_data_dir:
            self.shared_data_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str | Path) -> Path:
        """解析路径

        路径解析规则：
        1. 以 'data/' 开头的相对路径 → 映射到共享数据目录
        2. 其他相对路径 → 映射到工作目录
        3. 绝对路径 → 直接解析

        Args:
            path: 用户提供的路径

        Returns:
            解析后的绝对路径
        """
        p = Path(path)
        if not p.is_absolute():
            # 检查是否访问共享数据目录
            if self.shared_data_dir and str(path).startswith("data/"):
                # 去掉 'data/' 前缀，映射到共享数据目录
                relative_path = str(path)[5:]  # 去掉 "data/"
                return (self.shared_data_dir / relative_path).resolve()
            else:
                # 其他相对路径映射到沙箱工作目录
                return (self.workspace / p).resolve()
        return p.resolve()

    def _is_safe_path(self, path: Path) -> tuple[bool, bool]:
        """检查路径是否安全

        检查路径是否在允许的目录内（工作目录或共享数据目录）。

        Args:
            path: 要检查的路径

        Returns:
            (is_safe, is_readonly):
                - is_safe: 路径是否在允许的目录内
                - is_readonly: 路径是否在只读目录中
        """
        # 检查是否在工作目录内（读写）
        try:
            path.relative_to(self.workspace)
            return (True, False)  # 安全，且可写
        except ValueError:
            pass

        # 检查是否在共享数据目录内（只读）
        if self.shared_data_dir:
            try:
                path.relative_to(self.shared_data_dir)
                return (True, True)  # 安全，但只读
            except ValueError:
                pass

        return (False, False)  # 不安全

    def safe_open(self, path: str | Path, mode: str = "r", **kwargs) -> Any:
        """安全的文件打开函数

        只允许打开允许的目录内的文件，并根据目录权限控制读写操作。

        Args:
            path: 文件路径
            mode: 打开模式 ('r', 'w', 'a', 等)
            **kwargs: 传递给内置open()的其他参数

        Returns:
            文件对象

        Raises:
            SecurityError: 如果路径不安全或尝试在只读目录中写入
        """
        resolved_path = self._resolve_path(path)
        is_safe, is_readonly = self._is_safe_path(resolved_path)

        # 检查路径是否在允许的目录内
        if not is_safe:
            allowed_dirs = [str(self.workspace)]
            if self.shared_data_dir:
                allowed_dirs.append(f"{self.shared_data_dir} (只读)")
            raise SecurityError(
                f"访问被拒绝: 路径 '{path}' 不在允许的目录内。\n"
                f"允许访问的目录: {', '.join(allowed_dirs)}"
            )

        # 检查是否尝试在只读目录中写入
        is_write_mode = any(m in mode for m in ["w", "a", "x", "+"])
        if is_readonly and is_write_mode:
            raise SecurityError(
                f"访问被拒绝: 路径 '{path}' 在只读目录中，不允许写入操作。\n"
                f"只读目录: {self.shared_data_dir}\n"
                f"提示: 如需写入文件，请使用工作目录（相对路径）或保存到沙箱工作目录。"
            )

        # 如果是写入模式，确保父目录存在
        if is_write_mode:
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

        return open(resolved_path, mode, **kwargs)

    def validate_path(self, path: str | Path) -> Path:
        """验证路径是否安全

        Args:
            path: 要验证的路径

        Returns:
            解析后的安全路径

        Raises:
            SecurityError: 如果路径不在允许的目录内
        """
        resolved_path = self._resolve_path(path)
        is_safe, _ = self._is_safe_path(resolved_path)

        if not is_safe:
            allowed_dirs = [str(self.workspace)]
            if self.shared_data_dir:
                allowed_dirs.append(f"{self.shared_data_dir} (只读)")
            raise SecurityError(
                f"访问被拒绝: 路径 '{path}' 不在允许的目录内。\n"
                f"允许访问的目录: {', '.join(allowed_dirs)}"
            )

        return resolved_path
