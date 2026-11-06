from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.analysis import router as analysis_router
from app.routes.auths import router as auth_router
from app.routes.library import router as library_router
from app.routes.uploads import router as uploads_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="High-Throughput Legal Decision-Support API featuring LightGBM Outcome Prediction, 36k Precedent Retrieval, and MMR LexRank Summarization."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(uploads_router)
app.include_router(analysis_router)
app.include_router(library_router)


@app.get("/")
def home():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online"
    }
