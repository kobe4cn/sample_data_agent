# data-analysis Specification

## Purpose
定义 AI 代理在数据分析和可视化过程中的数据预处理能力，确保能够正确处理复杂格式的数据文件（如多层表头的 Excel、包含特殊字符的 CSV 等），并在绘图前验证数据完整性，防止因列名不存在等问题导致执行失败。

---

## ADDED Requirements

### Requirement: 数据文件结构检查
AI 代理 SHALL 在读取复杂格式的数据文件（特别是 Excel 文件）之前，主动检查文件的原始结构，识别元信息行、多层表头和实际数据的起始位置。

#### Scenario: 检查 Excel 文件结构
- **GIVEN** 用户请求分析一个 Excel 文件（如 `data/lego.xlsx`）
- **WHEN** AI 代理开始处理该请求
- **THEN** AI SHALL 首先使用 `pd.read_excel(file, header=None)` 读取原始数据
- **AND** AI SHALL 显示前 10 行数据以识别文件结构
- **AND** AI SHALL 识别元信息行、表头位置和数据起始行
- **AND** AI SHALL 向用户报告检测到的结构信息

#### Scenario: 检测多层表头
- **GIVEN** Excel 文件包含多层表头（如行 2-5）
- **WHEN** AI 检查文件结构
- **THEN** AI SHALL 识别出存在多层表头
- **AND** AI SHALL 确定真正的列名所在行
- **AND** AI SHALL 建议使用 `header=X` 参数或 `skiprows=Y` 参数重新读取

#### Scenario: 检测元信息行
- **GIVEN** Excel 文件顶部包含元信息（如公司名称、报告日期）
- **WHEN** AI 检查文件结构
- **THEN** AI SHALL 识别元信息行的数量
- **AND** AI SHALL 建议使用 `skiprows` 参数跳过这些行

---

### Requirement: 多层表头处理
AI 代理 SHALL 能够正确处理包含多层表头的 Excel 文件，使用合适的 pandas 参数读取数据，确保列名正确。

#### Scenario: 使用 header 参数指定表头行
- **GIVEN** 表头在第 5 行（索引 4）
- **WHEN** AI 重新读取文件
- **THEN** AI SHALL 使用 `pd.read_excel(file, header=4)`
- **AND** DataFrame 的列名 SHALL 为第 5 行的内容
- **AND** 数据 SHALL 从第 6 行开始

#### Scenario: 使用 skiprows 跳过说明行
- **GIVEN** 文件前 3 行是说明文字，第 4 行是表头
- **WHEN** AI 读取文件
- **THEN** AI SHALL 使用 `pd.read_excel(file, skiprows=3)`
- **AND** 第 4 行成为列名
- **AND** 数据从第 5 行开始

#### Scenario: 处理真正的多层表头
- **GIVEN** 文件有 2-3 行组成的复合表头
- **WHEN** AI 读取文件
- **THEN** AI MAY 使用 `header=[0, 1, 2]` 读取多层表头
- **OR** AI MAY 选择最底层的表头行作为列名
- **AND** AI SHALL 向用户说明选择的理由

---

### Requirement: 列名验证和清理
AI 代理 SHALL 在使用列名进行任何操作（特别是绘图）之前，先验证列名是否存在于 DataFrame 中，并提供清理列名的能力。

#### Scenario: 绘图前验证列名存在 ⭐
- **GIVEN** AI 准备生成绘图代码（如 `sns.barplot(data=df, x='passion_系列', y='销售额')`）
- **WHEN** AI 编写绘图代码之前
- **THEN** AI SHALL 首先检查 DataFrame 的实际列名（`df.columns.tolist()`）
- **AND** AI SHALL 验证要使用的列名（`'passion_系列'`, `'销售额'`）是否在实际列名中
- **AND** 如果列名不存在，AI SHALL NOT 生成使用该列名的代码
- **AND** AI SHALL 改为使用存在的列名，或先创建需要的列

#### Scenario: 处理 Unnamed 列
- **GIVEN** DataFrame 包含 `Unnamed: 0`, `Unnamed: 1` 等列名（pandas 默认行为）
- **WHEN** AI 检查列名
- **THEN** AI SHALL 识别这些列为无效列名
- **AND** AI SHALL 建议删除这些列：`df = df.loc[:, ~df.columns.str.contains('^Unnamed')]`
- **AND** AI SHALL 执行删除操作

#### Scenario: 清理列名中的 BOM 和特殊字符
- **GIVEN** 列名包含 UTF-8 BOM 或首尾空格
- **WHEN** AI 读取数据后
- **THEN** AI SHALL 使用 `df.columns = df.columns.str.strip()` 清理列名
- **AND** AI SHALL 移除不可见字符和多余空格

#### Scenario: 简化列名格式
- **GIVEN** 列名包含空格或大小写不一致
- **WHEN** 用户要求简化列名或 AI 建议优化
- **THEN** AI MAY 使用 `df.columns.str.replace(' ', '_').str.lower()` 简化列名
- **AND** AI SHALL 向用户说明修改后的列名映射

#### Scenario: 创建需要的新列
- **GIVEN** 绘图需要的列名不存在（如 `'passion_系列'`）
- **AND** AI 识别可以通过组合现有列创建该列
- **WHEN** AI 准备绘图
- **THEN** AI SHALL 首先创建新列：`df['passion_系列'] = df['人群'] + '_' + df['系列']`
- **AND** 然后使用新列进行绘图

---

### Requirement: 数据类型转换
AI 代理 SHALL 能够检测和转换数据类型，确保数值列、日期列等类型正确，以支持后续的计算和绘图操作。

#### Scenario: 检查数据类型
- **GIVEN** AI 读取了数据文件
- **WHEN** 准备进行数值计算或绘图
- **THEN** AI SHALL 使用 `df.dtypes` 检查各列的数据类型
- **AND** AI SHALL 识别应该是数值但显示为 `object` 的列

#### Scenario: 转换数值列
- **GIVEN** 某列应该是数值，但类型为 `object`（可能包含逗号、货币符号等）
- **WHEN** AI 准备使用该列进行计算或绘图
- **THEN** AI SHALL 使用 `pd.to_numeric(df['列'], errors='coerce')` 转换
- **AND** 如果存在特殊字符，AI SHALL 先清理：`df['列'].str.replace(',', '')`

#### Scenario: 转换日期列
- **GIVEN** 某列应该是日期，但类型为 `object`
- **WHEN** AI 准备进行时间序列分析
- **THEN** AI SHALL 使用 `pd.to_datetime(df['列'], errors='coerce')` 转换
- **AND** AI SHALL 检查转换后的 NaT（Not a Time）数量

#### Scenario: 处理百分比数据
- **GIVEN** 某列包含百分比文本（如 `"25%"`）
- **WHEN** AI 需要使用该列进行数值计算
- **THEN** AI SHALL 使用 `df['列'].str.rstrip('%').astype(float) / 100` 转换

---

### Requirement: 数据完整性检查
AI 代理 SHALL 在执行分析或绘图之前，检查数据的完整性，包括缺失值、数据类型、唯一值等。

#### Scenario: 检查缺失值
- **GIVEN** DataFrame 可能包含缺失值
- **WHEN** AI 准备进行分析
- **THEN** AI SHALL 使用 `df.isnull().sum()` 检查每列的缺失值数量
- **AND** 如果关键列缺失值过多，AI SHALL 向用户报告
- **AND** AI MAY 建议删除或填充缺失值

#### Scenario: 检查唯一值（分类列）
- **GIVEN** 某列用作分类变量（如绘图的 `hue` 参数）
- **WHEN** AI 准备使用该列
- **THEN** AI SHALL 使用 `df['列'].value_counts()` 检查唯一值
- **AND** AI SHALL 验证唯一值数量合理（如不超过 20 个用于颜色区分）

#### Scenario: 报告数据形状
- **GIVEN** AI 读取了数据
- **WHEN** 向用户报告数据概况
- **THEN** AI SHALL 显示 DataFrame 的形状：`df.shape`（行数 × 列数）
- **AND** AI SHALL 列出所有列名

---

### Requirement: 宽表转长表转换
AI 代理 SHALL 能够识别宽表格式的数据，并在需要时转换为长表（tidy data）格式，以支持 seaborn 等库的绘图需求。

#### Scenario: 识别宽表格式
- **GIVEN** DataFrame 的列名包含多个时间点或类别（如 `Q1销售额`, `Q2销售额`, `Q3销售额`）
- **WHEN** 用户要求绘制趋势图或对比图
- **THEN** AI SHALL 识别这是宽表格式
- **AND** AI SHALL 建议转换为长表

#### Scenario: 使用 melt 转换宽表
- **GIVEN** 宽表数据：`| 产品 | Q1 | Q2 | Q3 |`
- **WHEN** AI 准备绘制趋势图
- **THEN** AI SHALL 使用 `df.melt()` 转换：
  ```python
  df_long = df.melt(
      id_vars=['产品'],
      value_vars=['Q1', 'Q2', 'Q3'],
      var_name='季度',
      value_name='销售额'
  )
  ```
- **AND** 结果应为长表格式：`| 产品 | 季度 | 销售额 |`
- **AND** AI 使用长表进行绘图

#### Scenario: 解释宽表和长表的区别
- **GIVEN** 用户对数据格式转换不熟悉
- **WHEN** AI 执行 melt 操作
- **THEN** AI SHALL 向用户解释：
  - 宽表：每个时间点/类别是一列
  - 长表：时间点/类别作为一列的值
  - 为什么 seaborn 通常需要长表格式

---

### Requirement: 友好的错误提示
当数据预处理或验证失败时，AI 代理 SHALL 提供清晰、可操作的错误信息，帮助用户理解问题并提供解决方案。

#### Scenario: 列名不存在错误
- **GIVEN** AI 尝试使用列名 `'passion_系列'`，但该列不存在
- **WHEN** 验证失败
- **THEN** AI SHALL NOT 直接执行代码导致 KeyError
- **AND** AI SHALL 向用户说明：
  - 列名 `'passion_系列'` 不在 DataFrame 中
  - 实际可用的列名列表
  - 建议的解决方案（使用现有列或创建新列）

#### Scenario: 数据类型转换失败
- **GIVEN** 数值列包含大量非数字文本，转换后产生过多 NaN
- **WHEN** AI 执行类型转换
- **THEN** AI SHALL 检测转换后的 NaN 比例
- **AND** 如果 NaN 比例过高（如 >20%），AI SHALL 警告用户
- **AND** AI SHALL 显示部分无法转换的值示例

#### Scenario: 多层表头识别困难
- **GIVEN** Excel 文件结构非常复杂，AI 难以自动识别表头
- **WHEN** AI 检查文件结构
- **THEN** AI SHALL 显示前 10-15 行原始数据
- **AND** AI SHALL 请用户确认：表头在哪一行？
- **AND** AI SHALL 根据用户反馈重新读取

---

### Requirement: 向后兼容性
所有数据预处理功能 SHALL 是可选的和非侵入式的，确保现有合法的数据分析代码无需修改即可正常运行。

#### Scenario: 简单 CSV 文件无额外处理
- **GIVEN** 用户上传标准的 CSV 文件（单层表头，UTF-8 编码，无特殊字符）
- **WHEN** AI 读取并分析数据
- **THEN** AI MAY 跳过复杂的预处理步骤
- **AND** AI 直接进行分析和绘图
- **AND** 性能无明显下降

#### Scenario: 现有 telco 数据集分析
- **GIVEN** 用户请求分析 `telco` 数据集（已有的功能）
- **WHEN** AI 处理请求
- **THEN** AI SHALL 使用 `load_dataset('telco')` 正常加载
- **AND** 所有现有分析和绘图功能 SHALL 正常工作
- **AND** 行为与之前完全一致

#### Scenario: Prompt 增强不破坏现有逻辑
- **GIVEN** prompt.py 已添加数据预处理章节
- **WHEN** AI 处理各种请求
- **THEN** 新的指导 SHALL 只在需要时被应用
- **AND** 对于不需要预处理的场景，AI 行为 SHALL 保持不变
- **AND** 现有工具（`python_inter`, `fig_inter`）的接口 SHALL 不变

---

## MODIFIED Requirements

无。本提案不修改现有 Requirements，仅添加新的数据预处理能力。

---

## REMOVED Requirements

无。本提案不移除任何现有 Requirements。

---

## Related Specifications

- `code-execution`：Python 沙箱执行能力（本提案的数据预处理在沙箱内执行）
- `visualization`（如果存在）：图表生成能力（本提案改进绘图前的数据准备）

---

## Implementation Notes

### Prompt Engineering Approach
- 所有能力通过增强 `backend/src_agent/prompt.py` 实现
- 不修改任何 Python 代码（工具函数、沙箱等）
- 完全依赖 AI 的理解和执行能力

### Key Code Examples in Prompt
Prompt 包含 16 个代码示例，覆盖：
- 检查文件结构：`pd.read_excel(header=None)`
- 处理多层表头：`header=X`, `skiprows=Y`
- 清理列名：`str.strip()`, `str.contains('^Unnamed')`
- 类型转换：`pd.to_numeric()`, `pd.to_datetime()`
- 列名验证：`df.columns.tolist()`
- 宽表转长表：`df.melt()`

### User Documentation
`backend/DATA_PREPARATION.md` 提供用户友好的指南：
- 常见问题快速查找
- 具体的 AI 交互示例（用户可直接复制使用）
- 完整的场景案例（如 LEGO 数据分析）

### Success Metrics
- LEGO 数据分析成功率：100%（之前失败）
- 复杂 Excel 分析成功率提升：80%+
- 用户数据准备时间减少：50%+
- 向后兼容性：100%（现有功能无回归）
