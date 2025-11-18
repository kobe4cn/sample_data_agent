# Implementation Tasks - Chinese Font Support

## 1. Font Detection and Configuration

- [x] 1.1 在 `backend/src_agent/sandbox.py` 中创建字体检测函数 `_detect_chinese_font()`
  - 检测当前操作系统（platform.system()）
  - 为每个操作系统定义候选字体列表
  - 使用 matplotlib.font_manager 检查字体可用性
  - 返回第一个可用的中文字体名称或 None

- [x] 1.2 在 `PythonSandbox.__init__()` 中调用字体检测并配置 matplotlib
  - 在沙箱初始化时调用 `_detect_chinese_font()`
  - 如果找到中文字体，设置 matplotlib rcParams:
    - `font.sans-serif` 添加检测到的字体
    - `axes.unicode_minus` 设置为 False（修复负号显示问题）
  - 如果未找到字体，记录警告日志但继续初始化

## 2. Documentation Updates

- [x] 2.1 更新 `backend/src_agent/tools.py` 中 `fig_inter` 的文档字符串
  - 移除第 267 行关于"必须使用英文描述"的限制
  - 添加说明：现在支持中文和英文文本
  - 保留其他最佳实践建议（tight_layout 等）

- [x] 2.2 更新 `FigCodeInput` 的 `py_code` 字段描述
  - 移除英文限制
  - 说明支持中文字符

## 3. Testing

- [x] 3.1 创建测试用例：测试中文标签绘图
  - 使用 python_inter 创建包含中文列名的测试数据
  - 使用 fig_inter 生成包含中文标签的图表
  - 验证图像成功生成且无错误

- [x] 3.2 创建测试用例：测试混合中英文
  - 生成包含中英文混合标签的图表
  - 验证两种语言都正确显示

- [x] 3.3 创建测试用例：测试无中文字体时的降级行为
  - 模拟无可用中文字体的场景（可选，如果可行）
  - 验证系统记录警告但继续工作

- [x] 3.4 回归测试：验证现有英文图表不受影响
  - 运行现有的英文绘图示例
  - 确认输出与之前相同

## 4. Logging and Error Handling

- [x] 4.1 添加适当的日志记录
  - 记录检测到的中文字体（INFO 级别）
  - 如果未找到中文字体，记录警告（WARNING 级别）
  - 如果字体配置失败，记录错误但不中断初始化

## 5. Documentation

- [x] 5.1 更新 README.md（如果需要）
  - 在功能说明中提到支持中文字符
  - 可选：添加关于字体支持的说明
  - 注：项目没有顶层 README，已更新 SANDBOX_IMPLEMENTATION.md

- [x] 5.2 更新 SANDBOX_IMPLEMENTATION.md（如果存在）
  - 记录字体配置逻辑
  - 说明跨平台字体选择策略

## 6. Validation and Cleanup

- [x] 6.1 运行完整的测试套件确保无回归
- [x] 6.2 验证所有修改符合代码风格规范
- [x] 6.3 更新任务清单，标记所有项为完成
