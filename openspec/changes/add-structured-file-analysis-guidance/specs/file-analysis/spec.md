# file-analysis Specification

## Purpose

定义 AI 代理在分析和处理复杂数据文件（特别是 Excel 多层表头、包含元信息的表格等）时应遵循的系统化流程和最佳实践。确保模型能够：
1. 系统地检查文件结构而非猜测
2. 正确识别多层表头、元信息行等复杂模式
3. 制定合理的数据清洗策略
4. 提供可复现的分析流程

## Requirements

### Requirement: 5 阶段文件分析流程

AI 代理在处理数据文件时 SHALL 遵循标准化的 5 阶段分析流程：文件初检 → 结构识别 → 问题诊断 → 策略制定 → 执行验证。每个阶段有明确的输入/输出和验证标准。

#### Scenario: Excel 多层表头文件完整分析流程

- **GIVEN** 用户上传 `data/lego.xlsx` 包含多层表头
- **WHEN** AI 开始分析该文件
- **THEN** AI SHALL 依次执行：
  - **阶段 1（文件初检）**：使用 `pd.read_excel(file, header=None)` 读取原始数据，显示前 10 行
  - **阶段 2（结构识别）**：识别元信息行位置、表头行范围（如第 2-5 行）、数据起始行
  - **阶段 3（问题诊断）**：检测列名冲突、`Unnamed` 列、数据类型不匹配
  - **阶段 4（策略制定）**：确定使用 `load_multiheader_excel(path, header_row=2, depth=3)` 或手动参数
  - **阶段 5（执行验证）**：执行清洗代码，验证 `df.columns.tolist()` 和 `df.dtypes`
- **AND** AI SHALL 在每个阶段向用户报告进度和发现

#### Scenario: 简单 CSV 文件快速路径

- **GIVEN** 用户上传简单的单层表头 CSV 文件（`data/simple.csv`）
- **WHEN** AI 评估文件复杂度
- **THEN** AI SHALL 识别为低复杂度（评分 ≤2）
- **AND** AI MAY 跳过详细的结构识别，直接使用 `pd.read_csv` 读取
- **AND** AI SHALL 仍然执行基本的列名检查（阶段 5）

#### Scenario: 阶段失败时的错误恢复

- **GIVEN** AI 在阶段 4 制定的策略执行后产生错误（如列名不匹配）
- **WHEN** 错误发生
- **THEN** AI SHALL 回退到阶段 2 重新识别结构
- **AND** AI SHALL 向用户说明错误原因和调整策略
- **AND** AI SHALL 最多重试 2 次，如仍失败则请求用户确认

---

### Requirement: 复杂度自动评估

AI 代理 SHALL 在分析文件之前自动评估文件复杂度（0-10 分），并根据复杂度等级选择合适的分析流程深度。

#### Scenario: 复杂度评分规则

- **GIVEN** AI 完成文件初检（阶段 1）
- **WHEN** AI 评估复杂度
- **THEN** AI SHALL 根据以下规则计算分数：
  - 检测到多层表头（≥2 层）：+3 分
  - 检测到跨列表头结构：+2 分
  - 检测到元信息行（表头前的说明）：+1 分
  - 文件大小 >10MB：+2 分
  - 宽表格式（需要 melt 转换）：+1 分
  - 混合数据类型（同一列既有数字又有文本）：+1 分
- **AND** 总分范围为 0-10 分

#### Scenario: 复杂度等级分类

- **GIVEN** AI 已计算出复杂度分数
- **WHEN** AI 确定分析策略
- **THEN** AI SHALL 按以下规则分类：
  - 0-2 分：简单级别，使用快速流程（可跳过详细结构分析）
  - 3-5 分：中等级别，使用标准 5 阶段流程
  - 6-10 分：复杂级别，使用严格 5 阶段流程 + 查阅专家指导文档
- **AND** AI SHALL 向用户说明当前复杂度等级和原因

#### Scenario: 复杂度升级触发

- **GIVEN** AI 初始评估为简单级别（2 分）
- **WHEN** 执行过程中遇到意外错误（如列名不存在）
- **THEN** AI SHALL 将复杂度升级到中等级别
- **AND** AI SHALL 重新执行完整的 5 阶段流程
- **AND** AI SHALL 记录升级原因

---

### Requirement: 专家指导文档集成

对于复杂度 ≥6 的文件，AI 代理 SHALL 查阅专家指导文档（`doc/file_analysis_guide.md`）获取最佳实践和详细检查清单。

#### Scenario: 自动触发专家指导查阅

- **GIVEN** AI 评估文件复杂度为 8 分（检测到 3 层表头 + 跨列结构 + 元信息行）
- **WHEN** AI 进入阶段 2（结构识别）
- **THEN** AI SHALL 查阅 `doc/file_analysis_guide.md` 中的 "Excel 多层表头分析" 章节
- **AND** AI SHALL 使用文档中的 10 点检查清单验证结构识别
- **AND** AI SHALL 参考文档中的 Pandas 参数选择矩阵

#### Scenario: 常见错误模式匹配

- **GIVEN** AI 遇到 `KeyError: 'passion_系列'` 错误
- **WHEN** AI 查阅专家指导文档的"常见错误模式库"
- **THEN** AI SHALL 找到匹配的错误症状："列名不存在错误"
- **AND** AI SHALL 应用文档中的解决方案：先检查 `df.columns.tolist()`，再创建新列或使用现有列
- **AND** AI SHALL 向用户解释根因和修复方案

#### Scenario: 宽表转换指导

- **GIVEN** AI 识别出宽表格式（列名包含时间序列如 `Q1销售额`, `Q2销售额`）
- **WHEN** 用户要求绘制趋势图
- **THEN** AI SHALL 查阅专家指导文档的"宽表/长表转换"章节
- **AND** AI SHALL 使用文档中的 `melt` 参数指南确定转换逻辑
- **AND** AI SHALL 向用户解释为什么需要转换（seaborn 需要长表格式）

---

### Requirement: 结构化检查清单

AI 代理 SHALL 在关键阶段使用结构化检查清单确保不遗漏重要步骤。

#### Scenario: 阶段 2 结构识别检查清单

- **GIVEN** AI 进入阶段 2（结构识别）
- **WHEN** 分析 Excel 文件
- **THEN** AI SHALL 依次检查：
  1. 前 N 行是否为标题/说明（元信息）？
  2. 表头从哪一行开始（索引几）？
  3. 表头跨越几行（单层或多层）？
  4. 是否存在跨列合并的表头？
  5. 数据从哪一行开始？
  6. 是否存在汇总行（总计/平均）？
  7. 列名是否包含特殊字符或 BOM？
  8. 是否存在完全空白的列？
- **AND** AI SHALL 记录每个检查点的结果

#### Scenario: 阶段 5 执行验证检查清单

- **GIVEN** AI 执行完数据清洗代码
- **WHEN** 进入验证阶段
- **THEN** AI SHALL 检查：
  1. `df.shape`：行列数是否符合预期？
  2. `df.columns.tolist()`：列名是否清晰无 `Unnamed`？
  3. `df.dtypes`：数据类型是否正确（数值列为 float/int）？
  4. `df.isnull().sum()`：缺失值是否在可接受范围？
  5. `df.head(3)` 和 `df.tail(3)`：数据是否正确加载？
- **AND** 如果任何检查失败，AI SHALL 报告并调整策略

---

### Requirement: Prompt 集成指导

系统 prompt（`prompt.py`）SHALL 集成文件分析流程指导，使模型自动遵循最佳实践。

#### Scenario: Prompt 包含 5 阶段框架

- **GIVEN** `prompt.py` 已更新
- **WHEN** AI 处理文件分析请求
- **THEN** prompt SHALL 包含：
  - 5 阶段流程概述（每阶段 1-2 句描述）
  - 复杂度评估标准和阈值
  - 何时查阅专家指导文档的触发条件
  - 关键检查清单引用
- **AND** prompt 长度增加 SHALL NOT 超过 100 行

#### Scenario: 条件性详细指导

- **GIVEN** Prompt 中包含复杂度分支逻辑
- **WHEN** AI 评估为简单级别
- **THEN** AI SHALL 看到简化版指导（"快速检查列名和数据类型"）
- **WHEN** AI 评估为复杂级别
- **THEN** AI SHALL 看到完整版指导（"遵循严格 5 阶段流程并查阅文档"）

---

### Requirement: 用户交互与透明度

AI 代理 SHALL 在分析过程中向用户报告进度、发现和决策，确保用户理解分析逻辑。

#### Scenario: 阶段进度报告

- **GIVEN** AI 正在执行 5 阶段流程
- **WHEN** 完成每个阶段
- **THEN** AI SHALL 向用户输出：
  - "✅ 阶段 1 完成：文件包含 15 行，检测到前 3 行为元信息"
  - "✅ 阶段 2 完成：识别出 3 层表头（第 4-6 行），数据从第 7 行开始"
  - "✅ 阶段 3 完成：发现 2 个 `Unnamed` 列，销售额列类型为 object（需转换）"
  - "✅ 阶段 4 完成：策略为使用 `load_multiheader_excel(path, header_row=3, depth=3)`"
  - "✅ 阶段 5 完成：数据清洗成功，DataFrame 形状为 (10, 8)"

#### Scenario: 复杂度评估透明化

- **GIVEN** AI 计算出复杂度为 7 分
- **WHEN** 向用户报告
- **THEN** AI SHALL 输出：
  - "📊 文件复杂度评估：7 分（复杂级别）"
  - "  - 多层表头（3 层）：+3 分"
  - "  - 跨列结构：+2 分"
  - "  - 元信息行：+1 分"
  - "  - 混合数据类型：+1 分"
  - "  → 将使用严格分析流程并查阅专家指导文档"

#### Scenario: 策略调整说明

- **GIVEN** AI 初始策略失败
- **WHEN** 调整策略重新尝试
- **THEN** AI SHALL 向用户解释：
  - "⚠️ 初始策略失败：使用 `header=4` 导致列名包含 NaN"
  - "🔄 调整策略：重新分析发现表头实际在第 5-7 行，改用 `header=[4,5,6]`"
  - "✅ 重试成功：列名已正确提取"

---

### Requirement: 向后兼容性

所有文件分析增强功能 SHALL 向后兼容，不影响现有简单文件的处理流程和性能。

#### Scenario: 现有 telco 数据集无影响

- **GIVEN** 用户请求分析 `telco` 数据集（现有功能）
- **WHEN** AI 处理请求
- **THEN** AI SHALL 识别为低复杂度（0 分）
- **AND** AI SHALL 直接使用 `load_dataset('telco')` 加载
- **AND** 处理时间 SHALL NOT 增加 >10%
- **AND** 行为与之前完全一致

#### Scenario: 简单 CSV 文件性能不降级

- **GIVEN** 用户上传标准单层表头 CSV 文件
- **WHEN** AI 分析和处理该文件
- **THEN** 复杂度评估开销 SHALL <100ms
- **AND** AI MAY 跳过详细的结构分析
- **AND** 总处理时间 SHALL NOT 显著增加

---

### Requirement: 可扩展性

文件分析系统 SHALL 设计为可扩展，支持未来添加新文件类型、新分析策略和新评估标准。

#### Scenario: 添加新文件类型指导

- **GIVEN** 未来需要支持 PPT 文件分析
- **WHEN** 开发者添加 PPT 分析指导
- **THEN** 只需在 `doc/file_analysis_guide.md` 添加新章节
- **AND** 在复杂度评估中添加 PPT 特定规则
- **AND** 无需修改 5 阶段流程框架

#### Scenario: 复杂度评分规则优化

- **GIVEN** 收集到用户反馈和成功率数据
- **WHEN** 优化复杂度评分算法
- **THEN** 可以调整分数权重（如多层表头从 +3 改为 +4）
- **AND** 可以添加新的评分因子（如检测到公式单元格：+1）
- **AND** 无需修改流程框架

---

### Requirement: 性能与效率

文件分析流程 SHALL 在保证质量的前提下优化性能，避免不必要的重复操作。

#### Scenario: 缓存文件初检结果

- **GIVEN** AI 在阶段 1 已读取文件原始结构
- **WHEN** 后续阶段需要引用原始数据
- **THEN** AI SHALL 复用已读取的 DataFrame（避免重复读取文件）
- **AND** AI MAY 在沙箱中保存 `df_raw` 变量供后续使用

#### Scenario: 增量验证

- **GIVEN** AI 在阶段 5 验证数据清洗结果
- **WHEN** 大部分检查通过，仅个别列类型错误
- **THEN** AI SHALL 仅修复有问题的列（如转换 1 个数值列）
- **AND** AI SHALL NOT 重新执行整个清洗流程
