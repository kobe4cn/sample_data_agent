# Design: Enhance Multi-Header Excel Loading

## Current State
- `load_dataset('lego')` 仅调用 `pd.read_excel('lego.xlsx')`，默认把第 1 行视为表头，导致获得 70+ 列的多重索引和 `Unnamed` 列。
- AI 需要在 prompt 中手动尝试 `header=None` / `skiprows`，一旦推断错误，后续 `df.columns = [...]` 或 `df[['col']] = ...` 就会抛出 `Columns must be same length as key`。
- `fig_inter` 遇到上述异常只返回原始 ValueError，用户不知道该清理列名还是修改数据。

## Baseline Findings (2025-11-18)
- `backend/data/lego.xlsx` 实际数据：30 行 × 77 列。前 5 行为空或元信息，第 6 行（索引 5）包含中文列标签（`指标`、`人群交Passion曝光base` 等），但 pandas 默认读取后仍残留大量 `Unnamed:*` 列以及 `Passion互动%.*` 重复列。
- `pd.read_excel(path, header=None).head(12)` 显示行 2-5 为多层标题（`Passion/人群`、`BASE` 等），需要在程序内跳过。
- 复现列名长度报错：
  ```python
  df = pd.read_excel(path, header=5)
  df.columns = ['系列', '人群', '数值']
  # ValueError: Length mismatch: Expected axis has 77 elements, new values have 3 elements
  ```
  AI 常尝试将列名重命名为 2-3 个字段用于绘图，触发 `Columns must be same length as key` 或 `Length mismatch`。
- 另一个高频错误是在未删除 `Unnamed` 列的情况下执行 `df[['Passion互动%']] = ...`，导致 pandas 将多列赋值到单键，也会引发同类异常；因此后续错误提示需要明确指导用户先使用清洗后的列名。

## Goals
1. 为多层表头 Excel（起码 LEGO）提供“开箱即用”的清洗结果：
   - 自动跳过 5 行元信息，读取真正的表头
   - 合并两行/多行标题为单层列名（例如使用下方行覆盖上方 NaN）
   - 删除 `Unnamed`、空列，strip 空白，必要时提供映射
2. 允许未来其他数据集通过 `DatasetConfig` 参数就能启用同样的行为。
3. `fig_inter` 能识别“列长度不匹配”这类 pandas 错误并返回修复建议。

## Proposed Solution
### Data Loader
- 扩展 `DatasetConfig`：
  ```python
  @dataclass(frozen=True)
  class DatasetConfig:
      filename: str
      reader_kwargs: Mapping[str, Any] | None = None
      numeric_columns: tuple[str, ...] = ()
      datetime_columns: tuple[str, ...] = ()
      header_row: int | None = None          # e.g. 5 -> 0-indexed
      skiprows: int | tuple[int, ...] | None = None
      drop_columns: tuple[str, ...] = ()
      column_mapping: Mapping[str, str] | None = None
      multiheader_depth: int | None = None   # >1 表示需要合并多行表头
  ```
- 新 helper：`def load_multiheader_excel(path, *, header_row, multiheader_depth=1, drop_unnamed=True) -> pd.DataFrame`
  - 先整体读取（`header=list(range(header_row, header_row + depth))`）
  - 把多层列 tuple 通过 `"-".join(filter(None, ...))` 扁平化
  - 删除 `Unnamed` 与全部 NaN 的列
  - 应用 `column_mapping` / `str.strip().lower()` 等
- `load_dataset` 在检测到 `header_row` 或 `multiheader_depth` 时，调用 helper → `prepare_dataframe`.

### Error Handling
- `_format_fig_inter_error` 新增分支：
  - 匹配 `"columns must be same length as key"` 或 `"Length mismatch"` → 提示“请确认列名数量匹配 / 先使用 load_dataset('lego', cleaned=True) 或 helper 来拍平多层表头”。
  - 可以附加 `df.columns.tolist()` 建议。

### Documentation / Prompt
- README “数据预处理指南”示例：`lego_df = load_dataset('lego', cleaned=True)`（或默认 clean）+ `lego_df.head()`。
- `DATA_PREPARATION.md`：强调系统已经为内置复杂 Excel 做了清洗，只需复用结果；如果用户上传自己的多层表头文件，可调用 `load_multiheader_excel('data/custom.xlsx', header_row=4)`。
- Prompt Section 4 增加“若系统已提供 cleaned dataset，则直接加载，不要重复尝试 `df.columns = ...`”的提示。

## Alternatives Considered
1. **仅在 prompt 中补充更多示例**：已在 `improve-data-preprocessing-robustness` 中实现，但问题依旧，说明需要代码级别的保障。
2. **预先提供 CSV 副本**：会引入额外同步成本（若原始 Excel 有更新需手动维护），不如提供程序化清洗逻辑复用。
3. **在 fig_inter 前自动运行清洗脚本**：难以保证上下文数据来源和变量名，容易过度耦合；因此选择把清洗逻辑放在数据加载 helper 中，由 AI 明确调用。

## Risks & Mitigations
- **误处理简单 Excel**：默认仅对显式配置的数据集启用 multiheader 模式；其他数据集保持原行为。
- **性能开销**：LEGO 数据规模可控；helper 主要在加载阶段运行，影响有限。
- **错误模板匹配不足**：单元测试将模拟 ValueError，通过 `_format_fig_inter_error` 确认提示内容。
