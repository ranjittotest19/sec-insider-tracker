from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import form4, filings_13dg, screener, search
from app.database import engine
from app import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="SEC Insider Tracker API",
    description="Real-time SEC Form 4 and 13D/13G filing tracker",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(form4.router, prefix="/api/form4", tags=["Form 4"])
app.include_router(filings_13dg.router, prefix="/api/13dg", tags=["13D/13G"])
app.include_router(screener.router, prefix="/api/screener", tags=["Screener"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])

@app.get("/api/health")
def health():
    return {"status": "ok"}
