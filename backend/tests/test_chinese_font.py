"""
测试中文字体渲染功能

此脚本测试 matplotlib 中文字体配置是否正常工作。
"""

import sys
sys.path.insert(0, 'src_agent')

# 重置沙箱实例以确保使用最新配置
import tools
tools._sandbox_instance = None

from tools import python_inter, fig_inter

def test_chinese_labels():
    """测试中文标签绘图"""
    print("=" * 60)
    print("测试 1: 中文标签绘图")
    print("=" * 60)

    # 创建测试数据
    code = """
import pandas as pd
import numpy as np

# 创建包含中文列名的测试数据
data = {
    '月份': ['一月', '二月', '三月', '四月', '五月', '六月'],
    '销售额': [120, 135, 148, 155, 170, 185],
    '利润': [30, 35, 40, 42, 48, 55]
}
test_df = pd.DataFrame(data)
test_df
"""

    result = python_inter.invoke({"python_code": code})
    print("数据创建结果:")
    print(result)

    # 绘制中文标签图表
    plot_code = """
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
x = range(len(test_df))
ax.plot(x, test_df['销售额'], marker='o', label='销售额')
ax.plot(x, test_df['利润'], marker='s', label='利润')
ax.set_xlabel('月份')
ax.set_ylabel('金额（万元）')
ax.set_title('月度销售额与利润趋势')
ax.set_xticks(x)
ax.set_xticklabels(test_df['月份'])
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
"""

    result = fig_inter.invoke({"py_code": plot_code, "fname": "fig"})
    print("\n绘图结果:")
    print(result)
    print()


def test_mixed_chinese_english():
    """测试中英文混合"""
    print("=" * 60)
    print("测试 2: 中英文混合标签")
    print("=" * 60)

    plot_code = """
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6))
categories = ['Category A', 'Category B', 'Category C', 'Category D']
values = [85, 92, 78, 95]
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']

bars = ax.bar(categories, values, color=colors, alpha=0.8)
ax.set_xlabel('Product Category 产品类别')
ax.set_ylabel('Score 得分')
ax.set_title('Product Performance 产品表现评估')
ax.set_ylim(0, 100)

# 添加数值标签
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.0f}分',
            ha='center', va='bottom')

fig.tight_layout()
"""

    result = fig_inter.invoke({"py_code": plot_code, "fname": "fig"})
    print("绘图结果:")
    print(result)
    print()


def test_english_plot_regression():
    """回归测试：确保英文图表不受影响"""
    print("=" * 60)
    print("测试 3: 英文图表回归测试")
    print("=" * 60)

    plot_code = """
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6))
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)

ax.plot(x, y1, label='Sine Wave', linewidth=2)
ax.plot(x, y2, label='Cosine Wave', linewidth=2)
ax.set_xlabel('X Axis')
ax.set_ylabel('Y Axis')
ax.set_title('Trigonometric Functions')
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()
"""

    result = fig_inter.invoke({"py_code": plot_code, "fname": "fig"})
    print("绘图结果:")
    print(result)
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("开始测试中文字体渲染功能")
    print("=" * 60 + "\n")

    try:
        test_chinese_labels()
        test_mixed_chinese_english()
        test_english_plot_regression()

        print("=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
