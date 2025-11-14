import sys
sys.path.insert(0, 'src')

# 重置沙箱
import tools
tools._sandbox_instance = None

from tools import python_inter

code = """
import pandas as pd
df = pd.read_csv('data/telco_data.csv')
df.head(10)
"""

result = python_inter.invoke({"python_code": code})
print(result)