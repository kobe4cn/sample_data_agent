# Proposal: Enhance Multi-Header Excel Loading

## Why
- 用户在分析 `backend/data/lego.xlsx` 时依然会触发 `Columns must be same length as key`，导致 `fig_inter` 绘图失败，说明当前的 `load_dataset('lego')` 及相关数据准备流程并未真正清理多层表头。
- 现有提示仅存在于 prompt 和文档层，缺乏可复用的代码工具/预清洗数据，使得 AI 每次都要重新推断 header 行，极易出错。
- `fig_inter` 的错误提示缺乏针对性，遇到列名不匹配或多重 index 赋值失败时只返回原始异常，用户无法得到具体修复建议。

## What Changes
1. **数据加载增强**
   - 扩展 `src_agent/data_loader.py`：支持为数据集配置 `header_row` / `skiprows` / `drop_columns` / `column_renames` 等参数，并针对 `lego` 提供多层表头解析与列名清洗逻辑。
   - 增加专用的多层表头解析 helper（例如 `load_multiheader_excel(...)`），确保返回的 DataFrame 只有单层列名且无 `Unnamed` 列，必要时自动展开宽表中的指标列。
2. **自动化验证**
   - 新增单元测试覆盖 `load_dataset('lego')`、多层表头 helper、以及与 `fig_inter` 协同的最小绘图流程，防止回归。
3. **错误提示改进**
   - 更新 `fig_inter` 的异常格式化逻辑，针对 `Columns must be same length as key` 等典型 pandas 错误给出明确的修复提示（如“请检查列名长度”“调用 multiheader helper”）。
4. **体验与文档**
   - 在 README 与 `DATA_PREPARATION.md` 补充“内置 LEGO 已预清洗”的说明及使用示例，提示如需自定义多层表头，可引用新的 helper 或 API。

## Impact
- AI 与用户可以直接复用 `load_dataset('lego')` 或新的 helper，无需在 prompt 循环猜测表头。
- `fig_inter` 在遇到列名问题时能直接给出指向性建议，减少排查时间。
- 改动集中在数据加载与工具层，不影响其他数据集；针对性测试避免引入回归。
