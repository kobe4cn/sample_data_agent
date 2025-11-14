# 共享数据目录

此目录用于存放用户上传的数据文件，供沙箱内的 Python 代码只读访问。

## 用途
- 用户上传的 CSV、Excel、JSON 等数据文件
- AI 可以在 python_inter 中自由读取这些文件进行数据分析

## 访问权限
- 沙箱内代码：**只读**
- 工具函数层：**读写**

## 示例
```python
# 在 python_inter 中读取数据
df = pd.read_csv('data/sales.csv')
df2 = pd.read_excel('data/users.xlsx')
```

