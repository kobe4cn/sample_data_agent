# data-preprocessing Specification (Delta)

## ADDED Requirements

### Requirement: Multi-Header Excel Normalization
系统 SHALL 提供可复用的多层表头解析能力，使 `load_dataset` 或独立 helper 能够自动跳过元信息行并锁定真实列名。

#### Scenario: Detect header row for lego.xlsx
- **GIVEN** 用户调用 `load_dataset('lego')`
- **WHEN** 数据加载器读取 `backend/data/lego.xlsx`
- **THEN** 系统 SHALL 自动跳过前 5 行元数据、识别第 6 行作为列名，并删除空白/合并导致的 `Unnamed` 列

#### Scenario: Merge stacked headers
- **GIVEN** Excel 列名由两行组成（如上层为 `Passion`，下层为具体指标）
- **WHEN** 启用 `multiheader_depth=2`
- **THEN** 系统 SHALL 将多层列名扁平化为单个字符串（如 `Passion-互动%`），并 strip 空格、统一大小写

### Requirement: Dataset-Specific Cleaning Hooks
数据加载器 SHALL 允许在 `DatasetConfig` 中指定 header 行、列映射、需删除列等信息，并在加载完成后自动应用。

#### Scenario: Drop redundant columns
- **WHEN** 数据集配置了 `drop_columns=('Unnamed: 0',)`
- **THEN** `load_dataset` SHALL 在返回 DataFrame 前移除这些列

#### Scenario: Column rename map
- **WHEN** 配置 `column_mapping={'Passion互动%': 'passion_rate'}` 或启用统一 `str.lower().replace(' ', '_')`
- **THEN** 返回的 DataFrame SHALL 使用清洗后的列名，消除大小写和空格差异

### Requirement: Helper Exposure for Custom Files
系统 SHALL 暴露公开函数（例如 `load_multiheader_excel(path, header_row=..., multiheader_depth=...)`），供 AI/用户处理自定义多层表头 Excel。

#### Scenario: User-provided multi-header file
- **GIVEN** 用户上传 `data/custom_report.xlsx`，表头在第 4 行
- **WHEN** 调用 helper 并传入 `header_row=3`
- **THEN** helper SHALL 返回清洗后的 DataFrame，且列名与 `df.columns.tolist()` 中展示一致

#### Scenario: Helper respects explicit options
- **WHEN** helper 被调用时指定 `drop_unnamed=False`
- **THEN** 系统 SHALL 保留用户需要的空列或 index 列，而非强制删除
