# Fix Chinese Font Rendering in Matplotlib Visualizations

## Why

当前的 `fig_inter` 工具在生成包含中文字段（如列名、标签、标题等）的图表时会出现乱码问题。这是因为 matplotlib 默认字体不支持中文字符，导致中文显示为方框或乱码。这个问题影响了数据可视化的可用性，特别是在处理包含中文字段名的数据集时。

虽然当前在 `tools.py:267` 有一个临时解决方案（要求用户将中文翻译成英文），但这并不是一个用户友好的解决方案，增加了额外的工作负担并可能导致语义丢失。

## What Changes

- 在沙箱初始化时配置 matplotlib 使用支持中文的字体
- 自动检测系统可用的中文字体（如 SimHei、Microsoft YaHei、PingFang SC 等）
- 提供优雅的降级机制：如果没有中文字体可用，记录警告但不影响绘图功能
- 移除 `tools.py:267` 中要求将中文翻译成英文的限制
- 更新工具文档以反映对中文字符的支持

## Impact

### Affected Specs
- `visualization` (新增或修改)

### Affected Code
- `backend/src_agent/sandbox.py` - 添加字体配置逻辑
- `backend/src_agent/config/sandbox_config.py` - 可选：添加字体配置选项
- `backend/src_agent/tools.py` - 更新 `fig_inter` 文档字符串（移除中文限制）

### User Impact
- **正面影响**: 用户可以直接在图表中使用中文标签、标题和图例，无需额外翻译
- **兼容性**: 不影响现有的英文图表，完全向后兼容
- **跨平台**: 自动检测不同操作系统（Windows、macOS、Linux）上的可用字体

### Migration
无需用户迁移。现有代码将继续工作，并自动获得中文支持。
