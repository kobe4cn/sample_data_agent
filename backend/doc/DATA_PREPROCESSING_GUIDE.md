# 数据预处理最佳实践指南

## 问题背景

当 AI 分析复杂的 Excel 文件时，常见以下问题：

1. **列名不匹配**：pandas 读取多层表头会产生 `Unnamed: X`
2. **数据结构混乱**：元信息、表头、数据混在一起
3. **编码问题**：UTF-8 BOM、不同字符集
4. **数据类型错误**：数字存成文本、日期格式不统一
5. **宽表绘图困难**：需要先转换成长表格式

## 通用解决方案

### 架构设计

```
┌─────────────────┐
│ 1. 数据上传     │
│   - 自动检测格式│
│   - 显示预览    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 数据验证     │
│   - 检查编码    │
│   - 识别表头    │
│   - 发现问题    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 交互式清洗   │
│   - 用户确认操作│
│   - 预览结果    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. 保存清洗结果 │
│   - 标准格式    │
│   - AI 可读     │
└─────────────────┘
```

### 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **方案 A：AI 自动处理** | 零人工干预 | 成功率低，难以处理复杂格式 | 简单标准的 CSV |
| **方案 B：用户手动清洗** | 完全可控 | 用户负担重，容易出错 | 一次性分析 |
| **方案 C：半自动清洗** | 平衡易用性和准确性 | 需要开发清洗工具 | 推荐，适合大多数场景 |
| **方案 D：数据规范强制** | 避免问题 | 限制用户，可能不现实 | 企业内部系统 |

## 实施建议

### 短期方案（立即可用）

#### 1. 增强 AI Prompt - 数据清洗指导

在 `prompt.py` 中添加数据处理指南：

```python
DATA_HANDLING_GUIDE = """
# 数据处理最佳实践

## 读取 Excel 文件时的注意事项

1. **检查文件结构**：
   ```python
   # 先查看原始数据
   df_raw = pd.read_excel('file.xlsx', header=None)
   print(df_raw.head(10))  # 查看前 10 行，识别真正的表头位置
   ```

2. **处理多层表头**：
   ```python
   # 如果表头在第 5 行（索引 4）
   df = pd.read_excel('file.xlsx', header=4)

   # 或者跳过前面的说明行
   df = pd.read_excel('file.xlsx', skiprows=5)
   ```

3. **清理列名**：
   ```python
   # 移除 BOM 和特殊字符
   df.columns = df.columns.str.strip()

   # 处理 Unnamed 列
   df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
   ```

4. **数据类型转换**：
   ```python
   # 转换数值列
   numeric_cols = ['销售额', '数量']
   df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

   # 转换日期列
   df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
   ```

## 绘图前的数据准备

1. **宽表转长表**（用于 seaborn 绘图）：
   ```python
   # 宽表格式
   # | 产品 | 1月销售额 | 2月销售额 | 3月销售额 |
   # 转换为长表
   df_long = df.melt(
       id_vars=['产品'],
       value_vars=['1月销售额', '2月销售额', '3月销售额'],
       var_name='月份',
       value_name='销售额'
   )
   ```

2. **检查数据完整性**：
   ```python
   # 检查缺失值
   print(df.isnull().sum())

   # 检查数据类型
   print(df.dtypes)

   # 检查唯一值
   print(df['类别'].value_counts())
   ```

3. **常见错误修复**：
   ```python
   # 错误：列名包含空格或特殊字符
   df.columns = df.columns.str.replace(' ', '_').str.lower()

   # 错误：数值列包含逗号、百分号等
   df['金额'] = df['金额'].str.replace(',', '').astype(float)
   df['比例'] = df['比例'].str.rstrip('%').astype(float) / 100
   ```

## 绘图时的列名使用

❌ **错误示例**：
```python
sns.barplot(data=df, x='passion_系列', y='销售额')
# 错误：列名不存在
```

✅ **正确做法**：
```python
# 1. 先检查可用的列名
print("可用列名:", df.columns.tolist())

# 2. 使用实际存在的列名
sns.barplot(data=df, x='系列', y='销售额')

# 3. 如果需要创建新列
df['passion_系列'] = df['passion_人群'] + '_' + df['系列']
```
"""
```

#### 2. 提供数据清洗模板

创建可复用的清洗函数：

```python
# backend/src_agent/utils/data_cleaner.py

def clean_excel_data(file_path: str, **options) -> pd.DataFrame:
    """
    通用 Excel 数据清洗函数

    自动处理常见问题：
    - BOM 字符
    - 多层表头
    - 空列
    - 数据类型转换
    """
    # 1. 检测编码
    df = pd.read_excel(file_path, header=None)

    # 2. 自动识别表头位置
    header_row = detect_header_row(df)

    # 3. 重新读取
    df = pd.read_excel(file_path, header=header_row)

    # 4. 清理列名
    df = clean_column_names(df)

    # 5. 删除空列和空行
    df = remove_empty_rows_cols(df)

    # 6. 类型推断和转换
    df = infer_and_convert_types(df)

    return df
```

### 中期方案（需要开发）

#### 1. 数据预处理 Web 界面

```
功能：
- 上传文件
- 预览数据（显示原始格式和清洗后格式）
- 交互式配置（选择表头行、删除列、重命名列）
- 导出清洗后的数据
```

#### 2. 数据质量检查 API

```python
POST /api/data/validate
{
  "file_path": "data/lego.xlsx",
  "checks": ["encoding", "header", "types", "missing_values"]
}

返回：
{
  "issues": [
    {
      "type": "encoding",
      "severity": "warning",
      "message": "文件包含 UTF-8 BOM",
      "suggestion": "使用 encoding='utf-8-sig' 读取"
    },
    {
      "type": "header",
      "severity": "error",
      "message": "检测到多层表头（行 2-5）",
      "suggestion": "使用 header=[2,3,5] 或手动处理"
    }
  ]
}
```

### 长期方案（战略规划）

#### 1. 智能数据助手

```
功能：
- 自动学习用户的数据清洗模式
- 提供清洗脚本建议
- 支持版本控制（清洗前后对比）
```

#### 2. 数据目录和元数据管理

```
建立数据目录：
- 记录每个数据集的结构和含义
- 提供数据字典
- 自动生成清洗脚本
```

## 延展场景考虑

### 场景 1：多种数据源

```python
# CSV、Excel、数据库、API 等
class UniversalDataLoader:
    def load(self, source: str, **options):
        if source.endswith('.csv'):
            return self._load_csv(source, **options)
        elif source.endswith('.xlsx'):
            return self._load_excel(source, **options)
        elif source.startswith('http'):
            return self._load_api(source, **options)
        elif 'mysql://' in source:
            return self._load_db(source, **options)
```

### 场景 2：大文件处理

```python
# 分块读取
def load_large_file(file_path: str, chunk_size: int = 10000):
    chunks = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # 清洗每个 chunk
        chunk = clean_data(chunk)
        chunks.append(chunk)
    return pd.concat(chunks)
```

### 场景 3：实时数据验证

```python
# 数据验证规则
validation_rules = {
    '销售额': {
        'type': 'numeric',
        'min': 0,
        'max': 1000000,
        'required': True
    },
    '日期': {
        'type': 'datetime',
        'format': '%Y-%m-%d',
        'range': ('2020-01-01', '2025-12-31')
    }
}
```

### 场景 4：数据血缘和审计

```python
# 记录数据转换历史
transformation_log = {
    'original_file': 'lego.xlsx',
    'operations': [
        {'step': 1, 'action': 'remove_bom', 'affected_columns': ['all']},
        {'step': 2, 'action': 'set_header', 'row': 5},
        {'step': 3, 'action': 'melt', 'id_vars': ['分类', '系列']},
    ],
    'output_file': 'lego_cleaned.csv'
}
```

## 实施优先级

| 优先级 | 任务 | 工作量 | 影响范围 |
|--------|------|--------|----------|
| P0 | 增强 AI Prompt（数据处理指导） | 1天 | 立即改善 AI 处理能力 |
| P0 | 文档（用户数据准备指南） | 1天 | 减少用户困惑 |
| P1 | 通用清洗函数库 | 3天 | 提供可复用工具 |
| P1 | 数据验证 API | 2天 | 自动发现问题 |
| P2 | Web 预处理界面 | 5天 | 提升用户体验 |
| P3 | 智能数据助手 | 2周+ | 长期愿景 |

## 推荐行动计划

### 第 1 步：立即改进（本周）

1. 更新 `prompt.py`，添加数据处理指导
2. 创建用户文档 `DATA_PREPARATION.md`
3. 在错误信息中添加清洗建议

### 第 2 步：工具开发（下周）

1. 创建 `data_cleaner.py`（通用清洗函数）
2. 更新 `data_loader.py`（集成清洗逻辑）
3. 添加单元测试

### 第 3 步：用户教育（持续）

1. 提供示例数据和清洗脚本
2. 录制视频教程
3. 收集用户反馈，迭代改进
