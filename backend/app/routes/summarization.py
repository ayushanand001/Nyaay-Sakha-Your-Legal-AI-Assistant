from fastapi import FastAPI
from pydantic import BaseModel
from services.lexRank import lexrank_summarize
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


class SummarizeRequest(BaseModel):
    text: str
    num_sentences: int = 3
    clean_citations: bool = False
    strip_headers: bool = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Create React App / Vite default (CRA)
        "http://localhost:5173",   # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],   # allows OPTIONS, POST, GET, etc.
    allow_headers=["*"],
)

@app.get("/")
def greet():
    return {"hello": "world"}

@app.post("/summarize")
def summarize(req: SummarizeRequest):
    summary = lexrank_summarize(
        req.text,
        num_sentences=req.num_sentences,
        clean_citations=req.clean_citations,
        strip_headers=req.strip_headers,
    )
    return JSONResponse(status_code=201, content={"summary": summary})