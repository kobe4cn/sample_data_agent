# 共享数据目录

此目录用于存放用户上传的数据文件，供沙箱内的 Python 代码只读访问。

## 用途
- 用户上传的 CSV、Excel、JSON 等数据文件
- AI 可以在 python_inter 中自由读取这些文件进行数据分析

## 访问权限
- **沙箱内代码**: 只读（建议）
- **工具函数层**: 读写

## 安全建议

### 生产环境配置
为了确保数据安全，**强烈建议**在生产环境设置文件系统只读权限：

```bash
# 设置目录为只读（可列出文件，但不能创建/删除）
chmod 555 data/

# 设置所有数据文件为只读
chmod 444 data/*.csv
chmod 444 data/*.xlsx
chmod 444 data/*.json
```

### 开发环境
开发环境可以保持正常权限（755/644），方便添加和修改测试数据。

## 示例
```python
# ✅ 在 python_inter 中读取数据
df = pd.read_csv('data/sales.csv')
df2 = pd.read_excel('data/users.xlsx')

# ❌ 不要尝试写入此目录
df.to_csv('data/output.csv')  # 生产环境会被文件系统权限阻止
```

## 当前文件
- `telco_data.csv`: 电信客户流失数据集（977,505 bytes）
- `telco_data_encoded.csv`: 编码后的数据集（1,054,273 bytes）
