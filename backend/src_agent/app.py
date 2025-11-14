"""
FastAPI应用模块 (app.py)

本模块定义了FastAPI Web应用，主要功能包括：
- 创建FastAPI应用实例
- 配置静态文件服务，用于提供图像文件的访问
- 设置图像路由，使前端可以通过HTTP访问生成的图像

注意：本模块主要用于图像文件的静态服务，LangGraph的API路由由LangGraph框架自动处理。
"""

# mypy: 禁用错误代码 - "no-untyped-def,misc"
import pathlib
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware

# 定义FastAPI应用实例
# 这是整个Web应用的核心对象，用于注册路由和中间件
app = FastAPI()


def create_images_router(build_dir="images/"):
    """
    创建图像文件的静态文件路由器
    
    该函数创建一个路由器，用于提供图像文件的HTTP访问服务。
    图像文件由fig_inter工具生成，保存在backend/src/images/目录下。
    
    Args:
        build_dir: 相对于此文件的图像目录路径，默认为"images/"
        
    Returns:
        StaticFiles或Route: 
            - 如果图像目录存在，返回StaticFiles对象用于提供静态文件服务
            - 如果图像目录不存在，返回一个虚拟路由，返回503错误提示
    """
    # 构建图像目录的绝对路径（相对于当前文件所在目录）
    build_path = pathlib.Path(__file__).parent / build_dir

    # 检查图像目录是否存在
    if not build_path.is_dir():
        print(
            f"警告: 在 {build_path} 找不到图像目录。图像服务可能无法正常工作。"
        )
        # 如果目录不存在，返回一个虚拟路由器，返回503服务不可用错误
        from starlette.routing import Route

        async def dummy_frontend(request):
            """
            虚拟前端处理函数
            
            当图像目录不存在时，所有请求都会返回503错误。
            """
            return Response(
                "图像目录未找到。请确保images目录存在。",
                media_type="text/plain",
                status_code=503,  # 503 Service Unavailable
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    # 如果目录存在，返回StaticFiles对象用于提供静态文件服务
    # html=True 允许直接访问HTML文件（虽然这里主要用于图像文件）
    return StaticFiles(directory=build_path, html=True)

# ==================== CORS配置（已注释） ====================
# 如果需要跨域资源共享，可以取消注释以下代码
# allowed_origins = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     os.getenv("FRONTEND_URL", "http://localhost:3000")
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=allowed_origins,
#     allow_credentials=True,
#     allow_methods=["GET", "OPTIONS", "HEAD"],
#     allow_headers=["*"],
#     max_age=3600,  # 缓存预检请求结果1小时
# )

# ==================== 路由配置 ====================
# 将图像静态文件服务挂载到 /images 路径下
# 这样前端可以通过 http://host:port/images/filename.png 访问生成的图像
# 注意：此路径不会与LangGraph API路由冲突，因为LangGraph使用不同的路径前缀
app.mount(
    "/images",  # URL路径前缀
    create_images_router(),  # 静态文件路由器
    name="images",  # 路由名称，用于URL反向解析
)
