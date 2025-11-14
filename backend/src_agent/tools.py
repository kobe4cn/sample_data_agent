"""
工具模块 (tools.py)

本模块定义了AI代理可以使用的各种工具函数，包括：
- 数据库查询工具 (sql_inter): 执行SQL查询并返回结果
- 数据提取工具 (extract_data): 从MySQL数据库提取数据到pandas DataFrame
- Python代码执行工具 (python_inter): 执行Python代码
- 数据可视化工具 (fig_inter): 执行Python绘图代码并保存图像
- 网络搜索工具 (search_tool): 使用Tavily进行网络搜索

这些工具通过LangChain的@tool装饰器注册，供AI代理在对话过程中调用。
"""

import os
from datetime import date, datetime
from decimal import Decimal
from dotenv import load_dotenv
from langchain.tools import tool
from pydantic import BaseModel, Field
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import json
import pandas as pd
import pymysql
from langchain_tavily import TavilySearch

# 加载环境变量（覆盖已存在的变量）
load_dotenv(override=True)

# 导入沙箱模块
from src_agent.sandbox import PythonSandbox, SandboxExecutionError
from src_agent.config.sandbox_config import SandboxConfig

# 创建全局沙箱实例（在工具间共享）
_sandbox_instance = None


def get_sandbox() -> PythonSandbox:
    """获取全局沙箱实例"""
    global _sandbox_instance
    if _sandbox_instance is None:
        config = SandboxConfig.from_env()
        _sandbox_instance = PythonSandbox(config)
    return _sandbox_instance


def _json_default(value):
    """JSON 序列化回退函数，处理数据库中常见的特殊类型。"""
    if isinstance(value, Decimal):
        # 将 Decimal 转换为浮点数，保持数值语义
        return float(value)
    if isinstance(value, (datetime, date)):
        # 日期 / 时间类型使用 ISO8601 字符串
        return value.isoformat()
    # 其他无法识别的类型转换为字符串
    return str(value)


# 初始化Tavily网络搜索工具
# max_results: 最大返回结果数量
# topic: 搜索主题类型（general表示通用搜索）
search_tool = TavilySearch(max_results=5, topic="general")


# ==================== 数据库查询工具 ====================

# SQL查询工具的描述信息，用于AI代理理解何时使用此工具
description = """
当用户进行数据库查询时，请调用该函数。
该函数用户在指定的MYSQL服务器上运行一段SQL代码，完成数据查询工作。
并且当前方法使用pymysql进行数据库连接。
⚠️ 仅在用户明确提到“数据库 / SQL / MySQL”等需求时才可调用本工具；当用户提到 CSV、Excel、JSON 或 telco_data.csv
等本地文件时，必须改用 python_inter 读取 data/ 目录下的文件，本工具无法访问本地文件。
本函数只负责执行SQL代码进行数据查询，如果需要进行数据提取数据分析，请使用另外一个方法 extract_data 进行数据提取和分析。
"""


class SQLQuerySchema(BaseModel):
    """
    SQL查询工具的参数模式定义
    
    用于验证和描述sql_inter工具所需的输入参数。
    """
    sql_query: str = Field(description=description)


@tool(args_schema=SQLQuerySchema)
def sql_inter(sql_query: str) -> str:
    """
    SQL数据库查询工具
    
    当用户需要进行数据库查询工作时，请调用该方法。
    该方法用于在执行的MYSQL服务器上运行一段SQL代码，完成数据查询工作。
    本函数只负责运行SQL代码，如果需要进行数据提取数据分析，请使用另外一个方法 extract_data 进行数据提取和分析。
    
    Args:
        sql_query: 需要执行的SQL查询语句
        
    Returns:
        str: SQL查询结果的JSON字符串格式，如果查询失败则返回错误信息
    """
    # 从环境变量读取MySQL数据库连接配置
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),  # MySQL主机地址
        port=int(os.getenv("MYSQL_PORT") or "3306"),  # MySQL端口，默认3306
        user=os.getenv("MYSQL_USER"),  # MySQL用户名
        password=os.getenv("MYSQL_PASSWORD"),  # MySQL密码
        database=os.getenv("MYSQL_DATABASE"),  # 数据库名称
        charset="utf8",  # 字符集编码
    )
    
    try:
        # 使用上下文管理器确保游标正确关闭
        with conn.cursor() as cursor:
            cursor.execute(sql_query)  # 执行SQL查询
            result = cursor.fetchall()  # 获取所有查询结果
    except pymysql.Error as e:
        # 捕获数据库错误并返回错误信息
        return f"SQL查询失败: {str(e)}"
    finally:
        # 确保数据库连接被关闭
        conn.close()

    # 将查询结果转换为JSON字符串返回（确保中文字符正确显示）
    return json.dumps(result, ensure_ascii=False, default=_json_default)


class ExtractDataSchema(BaseModel):
    """
    数据提取工具的参数模式定义
    
    用于验证和描述extract_data工具所需的输入参数。
    """
    sql_query: str = Field(description="用于从 MYSQL 提取数据的 SQL 查询语句.")
    df_name: str = Field(
        description="指定用户保存结果的 pandas DataFrame 的名称 (字符串形式)."
    )


@tool(args_schema=ExtractDataSchema)
def extract_data(sql_query: str, df_name: str) -> str:
    """
    用于在MySQL数据库中提取一张表到当前Python环境中，注意，本函数只负责数据表的提取，
    并不负责数据查询，若需要在MySQL中进行数据查询，请使用sql_inter函数。
    如果需要进行文件的读取之后进行数据分析，请使用python_inter函数进行数据分析。
    同时需要注意，编写外部函数的参数消息时，必须是满足json格式的字符串，
    :param sql_query: 字符串形式的SQL查询语句，用于提取MySQL中的某张表。
    :param df_name: 将MySQL数据库中提取的表格进行本地保存时的变量名，以字符串形式表示。
    :return：表格读取和保存结果
    """
    # 从环境变量读取MySQL数据库连接配置
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT") or "3306"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        charset="utf8",
    )
    try:
        # 使用pandas读取SQL查询结果到DataFrame
        df = pd.read_sql(sql_query, conn)
        # 将DataFrame保存到沙箱全局变量，以便后续Python代码使用
        sandbox = get_sandbox()
        sandbox.set_global(df_name, df)
        return f"成功将表格 {df_name} 保存到当前Python环境中。"
    except (pymysql.Error, pd.errors.DatabaseError) as e:
        # 捕获数据库或pandas错误
        return f"表格读取和保存失败: {str(e)}"
    finally:
        # 确保数据库连接被关闭
        conn.close()


class PythonCodeInputSchema(BaseModel):
    """
    Python代码执行工具的参数模式定义
    
    用于验证和描述python_inter工具所需的输入参数。
    """
    python_code: str = Field(
        description="用于执行的Python代码。该代码必须满足Python代码的语法规则，并且必须使用Python 3.10 或更高版本。"
    )


@tool(args_schema=PythonCodeInputSchema)
def python_inter(python_code: str):
    """
    Python代码执行工具（沙箱模式）
    当用户需要执行一段Python代码时，请调用该方法。
    该方法在安全的沙箱环境中执行Python代码，限制危险操作和资源使用。
    同时需要注意，本方法只能执行非绘图类的代码，若是绘图相关的代码，则需要调用fig_inter 方法进行绘图。

    文件访问权限：
    1. data/ 目录（只读）：可以读取用户上传的数据文件
       示例：df = pd.read_csv('data/telco_data.csv')
             df = pd.read_excel('data/sales.xlsx')
       对项目内置数据，可使用 load_dataset('telco') 获取带自动类型清洗的DataFrame。

    2. 工作目录（读写）：可以读写临时文件和中间结果
       示例：df.to_csv('temp_cleaned.csv')
             result = pd.read_csv('temp_cleaned.csv')

    3. 禁止访问系统其他目录（如 /etc/, /usr/ 等）

    Args:
        python_code: 需要执行的Python代码字符串

    Returns:
        str: 代码执行结果或错误信息
    """
    try:
        # 获取全局沙箱实例
        sandbox = get_sandbox()

        # 在沙箱中执行代码
        result = sandbox.execute(python_code)

        # 返回结果
        if result is None:
            return "Python代码执行成功。"
        return str(result)

    except Exception as e:
        return f"Python代码执行失败: {str(e)}"


def _format_fig_inter_error(message: str) -> str:
    """根据常见错误模式生成更具指导性的绘图错误提示。"""
    normalized = message.lower()
    if "loop of ufunc" in normalized and "type str" in normalized:
        return (
            "❌ 绘图代码执行失败: 检测到在字符串/分类列上执行数学函数。"
            "请先使用 `load_dataset(...)` 或 `pd.to_numeric(..., errors='coerce')` "
            "将相关列转换为数值类型，并将清洗后的 DataFrame 传给绘图代码。"
        )
    return f"❌ 绘图代码执行失败: {message}"


class FigCodeInput(BaseModel):
    """
    数据可视化工具的参数模式定义
    
    用于验证和描述fig_inter工具所需的输入参数。
    """
    py_code: str = Field(
        description="用于执行的Python绘图代码，必须使用 matplotlib/seaborn 创建图像并赋值给变量 fig。该代码必须满足Python代码的语法规则，并且必须使用Python 3.10 或更高版本。"
    )
    fname: str = Field(description="图像对象的变量名，用户从代码中提取并保存为图片")


@tool(args_schema=FigCodeInput)
def fig_inter(py_code: str, fname: str) -> str:
    """
    数据可视化工具 - 执行Python绘图代码并保存图像（双层架构）

    当用户需要使用 Python 进行可视化绘图任务时，请调用该函数。
    本工具采用双层架构：沙箱内执行绘图代码生成Figure对象，工具层在沙箱外保存图像。

    注意：
    1. 所有绘图代码必须创建一个图像对象，并将其赋值为指定变量名（例如 `fig`）。
    2. 必须使用 `fig = plt.figure()` 或 `fig, ax = plt.subplots()`。
    3. 不要使用 `plt.show()`。
    4. 不要在代码中使用 `fig.savefig()`，工具会自动保存。
    5. 请确保代码最后调用 `fig.tight_layout()`。
    6. 所有绘图代码中，坐标轴标签（xlabel、ylabel）、标题（title）、图例（legend）等文本内容，如果是中文描述，请翻译成对应的英文进行展示，必须使用英文描述。
    7. 在绘图前确保数据已经清洗：可在 `python_inter` 中使用 `load_dataset` 或自定义逻辑创建 `*_df` 变量，再在绘图代码中引用该变量；不要直接对尚未转换为数值类型的列执行数学运算。

    示例代码：
    fig = plt.figure(figsize=(10,6))
    plt.plot([1,2,3], [4,5,6])
    fig.tight_layout()

    Args:
        py_code: 需要执行的Python绘图代码字符串
        fname: 图像对象的变量名，用于从沙箱中提取图像

    Returns:
        str: 图像生成结果，包含Markdown格式的图片链接，或错误信息
    """
    # 保存当前matplotlib后端，以便后续恢复
    current_backend = matplotlib.get_backend()
    # 切换到非交互式后端（Agg），用于生成图像文件
    matplotlib.use("Agg")

    # 获取图像保存目录路径（工具层，沙箱外）
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, "images")
    # 确保图像目录存在
    os.makedirs(img_dir, exist_ok=True)

    try:
        # === 第1步: 在沙箱内执行绘图代码 ===
        sandbox = get_sandbox()
        sandbox.execute(py_code)

        # === 第2步: 从沙箱提取图像对象（可信层）===
        try:
            fig = sandbox.get_global(fname)
        except KeyError:
            return f"⚠️ 图像对象未找到：变量 '{fname}' 不存在。请确认代码中创建了该变量。"

        if fig is None:
            return f"⚠️ 图像对象为空：变量 '{fname}' 存在但值为 None。"

        # === 第3步: 在工具层保存图像到 images/ 目录（沙箱外）===
        if fig:
            # 使用时间戳和 UUID 生成唯一文件名，避免文件名冲突
            from datetime import datetime
            import uuid

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 时间戳格式：YYYYMMDD_HHMMSS
            unique_id = str(uuid.uuid4())[:8]  # UUID的前8位作为唯一标识
            images_filename = f"{fname}_{timestamp}_{unique_id}.png"

            # 构建图像的绝对保存路径
            abs_path = os.path.join(img_dir, images_filename)
            # 保存图像：bbox_inches="tight"确保图像边界紧凑，dpi=300提供高分辨率
            fig.savefig(abs_path, bbox_inches="tight", dpi=300)

            # 生成完整的图像访问URL
            api_url = os.getenv("API_URL", "http://localhost:2024")
            image_url = f"{api_url}/images/{images_filename}"

            # 返回 Markdown 格式的图片引用，便于在对话中显示图像
            return f"✅ 图像已生成: ![{fname}]({image_url})"
        else:
            return "⚠️ 图像对象未找到，请确认变量名正确并为 matplotlib 图对象。"

    except SandboxExecutionError as e:
        return _format_fig_inter_error(str(e))
    except Exception as e:
        # 捕获所有其他异常并返回错误信息
        return f"❌ 绘图代码执行失败: {str(e)}"
    finally:
        # 清理所有matplotlib图形，释放内存
        plt.close("all")
        # 恢复原来的matplotlib后端
        matplotlib.use(current_backend)
