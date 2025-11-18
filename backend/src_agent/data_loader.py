"""
数据加载与清洗工具。

该模块集中管理 data/ 目录下的数据集元信息，并提供统一的读取/清洗流程，
以便 python_inter 和 fig_inter 在同一份干净的数据上工作。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

# 项目根目录下的共享数据目录
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


@dataclass(frozen=True)
class DatasetConfig:
    """描述单个数据集的元信息。"""

    filename: str
    description: str = ""
    reader_kwargs: Mapping[str, Any] | None = None
    numeric_columns: tuple[str, ...] = ()
    datetime_columns: tuple[str, ...] = ()
    header_row: int | None = None
    header_rows: tuple[int, ...] | None = None
    multiheader_depth: int | None = None
    skiprows: int | tuple[int, ...] | None = None
    drop_columns: tuple[str, ...] = ()
    column_mapping: Mapping[str, str] | None = None
    drop_unnamed_columns: bool = False

    def resolve_path(self) -> Path:
        """返回数据文件的绝对路径。"""
        return (DATA_DIR / self.filename).resolve()


# 预置数据集配置，可按需扩展
DATASET_CATALOG: dict[str, DatasetConfig] = {
    
}


class DatasetNotFoundError(FileNotFoundError):
    """指定数据集不存在。"""


def list_datasets() -> list[str]:
    """返回当前已注册的数据集名称列表。"""
    return sorted(DATASET_CATALOG.keys())


def get_dataset_config(name: str) -> DatasetConfig:
    """获取数据集配置，不存在时抛出 DatasetNotFoundError。"""
    key = name.lower()
    if key not in DATASET_CATALOG:
        raise DatasetNotFoundError(
            f"未找到名为 '{name}' 的数据集，请在 data/ 目录下确认文件存在。"
        )
    return DATASET_CATALOG[key]


def _stringify_column_part(value: Any) -> str:
    """将任意列标签片段转换为干净的字符串。"""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if text.lower().startswith("unnamed"):
        return ""
    return text


def _flatten_column_label(label: Any) -> str:
    """将可能的 MultiIndex 列名转换为单一字符串。"""
    if isinstance(label, tuple):
        parts = [_stringify_column_part(part) for part in label]
        parts = [part for part in parts if part]
        return "_".join(parts)
    return _stringify_column_part(label)


def _clean_dataframe_columns(
    df: pd.DataFrame, *, drop_unnamed: bool = True
) -> pd.DataFrame:
    """按需删除空列并应用 flatten/strip 逻辑。"""
    cleaned_names: list[str] = []
    keep_mask: list[bool] = []
    for label in df.columns:
        flattened = _flatten_column_label(label)
        if drop_unnamed and not flattened:
            keep_mask.append(False)
            continue
        cleaned_names.append(flattened or str(label).strip())
        keep_mask.append(True)
    if keep_mask and not all(keep_mask):
        df = df.loc[:, keep_mask]
    if cleaned_names:
        df.columns = cleaned_names
    return df


def load_multiheader_excel(
    path: str | Path,
    *,
    header_row: int | None = None,
    header_rows: Sequence[int] | None = None,
    depth: int | None = None,
    drop_unnamed: bool = True,
    reader_kwargs: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    """
    读取包含多层表头的 Excel 文件，并将列名扁平化。

    Args:
        path: 文件路径。
        header_row: 表头起始行（0-index），与 depth 配合使用。
        header_rows: 显式指定多个表头行（优先级高于 header_row/depth）。
        depth: 需要合并的表头层数，默认为 1。
        drop_unnamed: 是否删除空列/Unnamed 列。
        reader_kwargs: 透传给 pandas.read_excel 的其他参数。
    """
    path = Path(path)
    if header_rows:
        header = list(header_rows)
    elif header_row is not None:
        actual_depth = depth or 1
        header = list(range(header_row, header_row + actual_depth))
    else:
        raise ValueError("必须提供 header_rows 或 header_row 参数")

    kwargs = dict(reader_kwargs or {})
    kwargs["header"] = header if len(header) > 1 else header[0]

    df = pd.read_excel(path, **kwargs)
    df = _clean_dataframe_columns(df, drop_unnamed=drop_unnamed)
    return df


def _read_with_config(config: DatasetConfig, **kwargs) -> pd.DataFrame:
    """根据文件后缀自动选择 pandas 读取方法。"""
    path = config.resolve_path()
    if not path.exists():
        raise DatasetNotFoundError(
            f"数据文件 '{config.filename}' 不存在，请检查 data/ 目录。"
        )

    reader_kwargs = dict(config.reader_kwargs or {})
    reader_kwargs.update(kwargs)

    suffix = path.suffix.lower()
    header_rows: tuple[int, ...] | None = config.header_rows
    if header_rows is None and config.header_row is not None and config.multiheader_depth:
        header_rows = tuple(
            range(config.header_row, config.header_row + config.multiheader_depth)
        )

    use_multiheader_helper = suffix in {".xls", ".xlsx"} and header_rows is not None
    if use_multiheader_helper:
        df = load_multiheader_excel(
            path,
            header_rows=header_rows,
            drop_unnamed=config.drop_unnamed_columns,
            reader_kwargs=reader_kwargs,
        )
    else:
        if config.skiprows is not None and "skiprows" not in reader_kwargs:
            reader_kwargs["skiprows"] = config.skiprows
        if config.header_row is not None and "header" not in reader_kwargs:
            reader_kwargs["header"] = config.header_row

        if suffix in {".csv", ".txt"}:
            df = pd.read_csv(path, **reader_kwargs)
        elif suffix in {".xls", ".xlsx"}:
            df = pd.read_excel(path, **reader_kwargs)
        elif suffix == ".json":
            df = pd.read_json(path, **reader_kwargs)
        else:
            raise ValueError(f"暂不支持读取后缀为 '{suffix}' 的文件：{path}")

        if isinstance(df.columns, pd.MultiIndex) or config.drop_unnamed_columns:
            df = _clean_dataframe_columns(
                df, drop_unnamed=config.drop_unnamed_columns or False
            )

    df = _apply_column_config(df, config)
    return df


def _coerce_numeric_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """将指定列转换为数值类型，无法转换的值设为 NaN。"""
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _coerce_datetime_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """将指定列转换为日期/时间类型，无法转换的值设为 NaT。"""
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def _apply_column_config(df: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    """根据配置删除或重命名列。"""
    df = df.copy()
    if config.drop_columns:
        existing = [col for col in config.drop_columns if col in df.columns]
        if existing:
            df = df.drop(columns=existing)
    if config.column_mapping:
        df = df.rename(columns=config.column_mapping)
    return df


def prepare_dataframe(df: pd.DataFrame, config: DatasetConfig) -> pd.DataFrame:
    """根据配置对 DataFrame 进行清洗。"""
    df = df.copy()
    df = _coerce_numeric_columns(df, config.numeric_columns)
    df = _coerce_datetime_columns(df, config.datetime_columns)
    return df


def load_dataset(name: str, *, copy: bool = True, **reader_kwargs) -> pd.DataFrame:
    """
    读取指定名称的数据集，并根据配置进行清洗。

    Args:
        name: 数据集名称（DATASET_CATALOG 的键）。
        copy: 是否返回副本，默认 True。
        **reader_kwargs: 透传给 pandas 读取函数的其他参数。
    """
    config = get_dataset_config(name)
    df = _read_with_config(config, **reader_kwargs)
    df = prepare_dataframe(df, config)
    if copy:
        df = df.copy()
    return df


__all__ = [
    "DATASET_CATALOG",
    "DatasetConfig",
    "DatasetNotFoundError",
    "get_dataset_config",
    "list_datasets",
    "load_dataset",
    "prepare_dataframe",
    "load_multiheader_excel",
]
