from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.analysis import router as analysis_router
from app.routes.auths import router as auth_router
from app.routes.library import router as library_router
from app.routes.uploads import router as uploads_router

app = FastAPI(title="Nyaay Sakha API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
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
    return {"message": "Nyaay Sakha API is running"}