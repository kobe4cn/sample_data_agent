"""
数据加载与清洗工具。

该模块集中管理 data/ 目录下的数据集元信息，并提供统一的读取/清洗流程，
以便 python_inter 和 fig_inter 在同一份干净的数据上工作。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

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

    def resolve_path(self) -> Path:
        """返回数据文件的绝对路径。"""
        return (DATA_DIR / self.filename).resolve()


# 预置数据集配置，可按需扩展
DATASET_CATALOG: dict[str, DatasetConfig] = {
    "telco": DatasetConfig(
        filename="telco_data.csv",
        description="Telco Customer Churn 数据集（CSV）",
        numeric_columns=("tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"),
    ),
    "telco_data": DatasetConfig(
        filename="telco_data.csv",
        description="Telco Customer Churn 数据集（CSV）",
        numeric_columns=("tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"),
    ),
    "telco_data_encoded": DatasetConfig(
        filename="telco_data_encoded.csv",
        description="编码后的 Telco Customer Churn 数据集（CSV）",
    ),
    "lego": DatasetConfig(
        filename="lego.xlsx",
        description="LEGO 销售示例数据（Excel）",
    ),
    "nongfu": DatasetConfig(
        filename="nongfu.xlsx",
        description="农夫山泉示例数据（Excel）",
    ),
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
    if suffix in {".csv", ".txt"}:
        df = pd.read_csv(path, **reader_kwargs)
    elif suffix in {".xls", ".xlsx"}:
        df = pd.read_excel(path, **reader_kwargs)
    elif suffix == ".json":
        df = pd.read_json(path, **reader_kwargs)
    else:
        raise ValueError(f"暂不支持读取后缀为 '{suffix}' 的文件：{path}")
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
]
