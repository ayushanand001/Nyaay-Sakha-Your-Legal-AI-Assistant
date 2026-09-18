from fastapi import FastAPI
from app.routes.auths import router as auth_router

app = FastAPI()

app.include_router(auth_router)


@app.get("/")
def home():
    return {
        "message": "Nyaay Sakha API is running"
    }