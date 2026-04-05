from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_router

# 创建FastAPI应用
app = FastAPI(
    title="对外服务API",
    description="提供任务管理和实时状态更新的API服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "对外服务API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
