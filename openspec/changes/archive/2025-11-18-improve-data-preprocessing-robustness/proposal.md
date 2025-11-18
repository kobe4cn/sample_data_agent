# Proposal: Improve Data Preprocessing Robustness

## Problem Statement

当 AI 代理分析复杂的 Excel 文件（如 `backend/data/lego.xlsx`）并生成可视化图表时，经常遇到以下错误：

```
代码执行失败: Could not interpret value `passion_系列` for `x`.
An entry with this name does not appear in `data`.
```

### 根本原因

1. **多层表头问题**：Excel 文件包含多层表头（行 2-5），pandas 默认读取会导致所有列名变成 `Unnamed: 0`, `Unnamed: 1` 等
2. **AI 生成的代码使用不存在的列名**：AI 尝试使用 `passion_系列` 等列名，但这些列名在 DataFrame 中并不存在
3. **缺乏数据预处理指导**：AI 在绘图前没有检查文件结构、清理列名或验证列是否存在

### 影响范围

- 用户上传复杂格式的 Excel 文件时，绘图和分析经常失败
- 错误信息对用户不友好，无法自助解决
- 需要手动预处理数据，降低了用户体验

## Proposed Solution

通过增强 AI Prompt 和提供用户文档，让 AI 代理能够：

1. **主动检查数据文件结构**：在读取 Excel 前先查看原始格式
2. **识别和处理多层表头**：自动或引导用户处理多层表头问题
3. **清理列名**：移除 BOM、特殊字符、处理 Unnamed 列
4. **绘图前验证列名**：确保使用的列名在 DataFrame 中存在
5. **提供数据转换指导**：宽表转长表、类型转换等

### 实施方式

#### 1. 增强 AI Prompt（`backend/src_agent/prompt.py`）

添加"数据预处理与清洗"章节，包括：
- 检查文件结构的代码模板
- 处理多层表头的方法
- 列名清理的最佳实践
- 数据类型转换
- 绘图前的数据验证（**关键**：防止使用不存在的列名）
- 宽表转长表转换

#### 2. 创建用户文档（`backend/DATA_PREPARATION.md`）

提供用户友好的指南：
- 常见问题和快速解决方案
- 数据准备检查清单
- 详细的处理步骤（附 AI 交互示例）
- 实际场景案例
- 常见错误及修复方法

## Success Criteria

1. ✅ AI 能够主动检查 Excel 文件结构并识别多层表头
2. ✅ AI 在绘图前会验证列名是否存在
3. ✅ 用户遇到数据格式问题时能通过文档自助解决
4. ✅ 复杂 Excel 文件的分析成功率提升 80%+
5. ✅ 现有合法代码无需修改即可正常运行（向后兼容）

## Out of Scope

- 自动化的数据清洗 API（留待 P1 阶段）
- Web 界面的交互式数据预处理（留待 P2 阶段）
- 通用清洗函数库（`data_cleaner.py`）（留待 P1 阶段）

## Related Changes

- `fix-chinese-font-rendering`：已完成的中文字体支持
- `code-execution`：Python 沙箱执行规格

## References

- `backend/DATA_PREPROCESSING_GUIDE.md`：技术实施方案（完整架构设计）
- `backend/DATA_PREPROCESSING_P0_IMPLEMENTATION.md`：P0 实施总结
