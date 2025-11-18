## MODIFIED Requirements

### Requirement: Python 代码沙箱执行
系统在执行绘图/分析代码时 SHALL 针对可识别的 pandas 异常给出明确的诊断信息，避免只返回通用错误文本。

#### Scenario: Column length mismatch guidance
- **WHEN** `fig_inter` 在执行绘图代码时捕获 pandas 抛出的 `Columns must be same length as key` / `Length mismatch` 等异常
- **THEN** 工具层 SHALL 捕获该错误并返回附带解决思路的提示（例如建议先使用清洗后的 DataFrame、展示 `df.columns.tolist()`、或调用 multi-header helper）
- **AND** 错误信息 SHALL 指明是列名数量不一致导致，而非笼统的“代码执行失败”
