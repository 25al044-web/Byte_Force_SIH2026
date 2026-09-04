from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file if present
load_dotenv()

from app.database import init_db
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database on startup
    init_db()
    yield


app = FastAPI(
    title="AI-Based Fake Identity & Document Screening System API",
    description="Backend API for SIH26188 Fake Identity & Document Screening System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration to enable communication with the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes under /api
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "AI-Based Fake Identity & Document Screening System API is running",
        "docs": "/docs",
        "health": "/api/health",
    }
