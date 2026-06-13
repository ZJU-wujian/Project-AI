from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from app.config import settings
from app.routers import auth, papers, social, sync
from app.database import engine, Base



app = FastAPI(
    title=settings.APP_NAME,
    description="TurboCholar - 学术社交与论文发现平台",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=PlainTextResponse)
async def root():
    return "TurboCholar API\nDocs: /docs\nAPI Prefix: /api"


@app.get("/health")
async def health_check():
    return {"status": "healthy", "docs": "/docs"}


# 包含所有路由
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(papers.router, prefix=settings.API_PREFIX)
app.include_router(social.router, prefix=settings.API_PREFIX)
app.include_router(sync.router, prefix=settings.API_PREFIX)



@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)