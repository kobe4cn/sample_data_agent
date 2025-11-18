from __future__ import annotations

import unittest
from pathlib import Path

import matplotlib
import pandas as pd

from src_agent.data_loader import load_dataset, load_multiheader_excel
from src_agent.tools import _format_fig_inter_error

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class LegoDataPreprocessingTests(unittest.TestCase):
    def test_load_dataset_returns_clean_columns(self) -> None:
        df = load_dataset("lego")
        self.assertIn("人群", df.columns)
        self.assertIn("系列", df.columns)
        self.assertGreater(len(df.columns), 10)
        self.assertTrue(all("Unnamed" not in col for col in df.columns))
        self.assertFalse(df.empty)

    def test_cleaned_lego_dataframe_supports_plotting(self) -> None:
        df = load_dataset("lego")
        subset = df[["系列", "孩子_Passion互动%"]].dropna(subset=["系列"])
        grouped = subset.groupby("系列")["孩子_Passion互动%"].mean()

        fig, ax = plt.subplots()
        grouped.plot(kind="bar", ax=ax)
        ax.set_title("LEGO Passion 指标（清洗后）")
        plt.close(fig)


class MultiHeaderExcelTests(unittest.TestCase):
    def test_reads_excel_after_skipping_metadata(self) -> None:
        raw = pd.read_excel(DATA_DIR / "test_multiheader.xlsx", header=None)
        self.assertEqual(raw.iloc[0, 0], "季度销售报告（示例数据）")
        self.assertEqual(raw.iloc[3, 0], "产品类别")

        df = pd.read_excel(DATA_DIR / "test_multiheader.xlsx", header=3)
        self.assertListEqual(df.columns.tolist(), ["产品类别", "渠道", "Q1销售额"])
        self.assertEqual(df.shape, (4, 3))

    def test_helper_flattens_lego_multiheader(self) -> None:
        df = load_multiheader_excel(DATA_DIR / "lego.xlsx", header_rows=(2, 5))
        self.assertIn("Passion/人群_指标", df.columns)
        self.assertFalse(any(col.startswith("Unnamed") for col in df.columns))
        self.assertEqual(df.shape[1], 76)

    def test_helper_supports_custom_header_row(self) -> None:
        df = load_multiheader_excel(
            DATA_DIR / "test_multiheader.xlsx", header_row=3, depth=1
        )
        self.assertListEqual(df.columns.tolist(), ["产品类别", "渠道", "Q1销售额"])
        self.assertEqual(df.shape, (4, 3))


class WideToLongConversionTests(unittest.TestCase):
    def test_converts_wide_csv_to_long_format(self) -> None:
        df = pd.read_csv(DATA_DIR / "test_wide.csv")
        df_long = df.melt(
            id_vars=["产品"],
            value_vars=["Q1", "Q2", "Q3", "Q4"],
            var_name="季度",
            value_name="销售额",
        )

        self.assertEqual(df_long.shape, (8, 3))
        self.assertSetEqual(set(df_long["季度"]), {"Q1", "Q2", "Q3", "Q4"})
        self.assertTrue((df_long["销售额"] > 0).all())


class TelcoRegressionTests(unittest.TestCase):
    def test_telco_dataset_loads_cleanly(self) -> None:
        df = load_dataset("telco")
        required_columns = {"customerID", "MonthlyCharges", "TotalCharges", "Churn"}
        self.assertTrue(required_columns.issubset(df.columns))
        self.assertFalse(df.empty)
        self.assertTrue(pd.api.types.is_numeric_dtype(df["MonthlyCharges"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(df["TotalCharges"]))


class FigInterErrorMessageTests(unittest.TestCase):
    def test_length_mismatch_error_message_provides_guidance(self) -> None:
        msg = _format_fig_inter_error("Columns must be same length as key")
        self.assertIn("列名数量", msg)
        self.assertIn("load_dataset('lego')", msg)


if __name__ == "__main__":
    unittest.main()
