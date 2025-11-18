# Implementation Tasks - Enhance Multi-Header Excel Loading

## 1. Baseline Analysis
1.1 - [x] 使用 `python_inter` / 本地脚本重新检查 `backend/data/lego.xlsx`，确认元数据行数、真实表头位置、空列/合并单元格等结构特征，记录在设计文档  
1.2 - [x] 统计常见的 pandas 报错（如 `Columns must be same length as key`）触发的具体代码路径，明确需要捕获的错误模式

## 2. Data Loader Enhancements
2.1 - [x] 为 `DatasetConfig` 增加可选的 `header_row`、`skiprows`、`drop_columns`、`column_mapping`、`multiheader` 标记等参数（保持向后兼容）  
2.2 - [x] 实现多层表头解析 helper（如 `load_multiheader_excel(path, header_row, drop_unnamed=True)`)，完成：  
&nbsp;&nbsp;&nbsp;&nbsp;a) 自动跳过元信息行  
&nbsp;&nbsp;&nbsp;&nbsp;b) 删除 `Unnamed` 列与空列  
&nbsp;&nbsp;&nbsp;&nbsp;c) 统一列名（strip、lower、可选映射）  
2.3 - [x] 更新 `load_dataset('lego')` 以复用上述 helper，并暴露一个清洗后的 DataFrame（e.g. `lego_clean_df`）供图表直接使用  
2.4 - [x] 为 helper 编写 docstring / README 片段，说明何时适合自定义 header 参数

## 3. Tooling & Error Handling
3.1 - [x] 扩展 `_format_fig_inter_error`，针对 `Columns must be same length as key`、`Length mismatch` 等 pandas 提示输出可操作的指引（建议先清理列名或使用 helper）  
3.2 - [x] 确保新的错误提示会在 `fig_inter` 返回值中呈现 Markdown 友好的说明

## 4. Testing
4.1 - [x] 新增单元测试验证 `load_dataset('lego')` 输出：  
&nbsp;&nbsp;&nbsp;&nbsp;- 实际列名集合  
&nbsp;&nbsp;&nbsp;&nbsp;- 无 `Unnamed` 列，且数据行数匹配  
4.2 - [x] 测试 helper 在自定义 header 参数下的行为（包含异常路径）  
4.3 - [x] 添加端到端测试：构造最小绘图脚本，确认在 `fig_inter` 中不再触发 `Columns must be same length as key`  
4.4 - [x] 运行 `pytest`/`unittest` 并记录命令

## 5. Documentation & Prompt Updates
5.1 - [x] 更新 README（数据管理 / 数据预处理章节），强调 LEGO 现已预清洗，示例使用 `load_dataset('lego')` 或 helper  
5.2 - [x] 在 `backend/doc/DATA_PREPARATION.md` 增加“系统自动处理多层表头”的说明及人工覆盖方式  
5.3 - [x] 若 prompt 需要提醒“可直接调用 `lego_df = load_dataset('lego', cleaned=True)`”等新 API，则同步更新 `prompt.py`

## 6. Validation
6.1 - [x] `python -m unittest`（或 `pytest`）全部通过  
6.2 - [x] `openspec validate enhance-multiheader-excel-loading --strict`
