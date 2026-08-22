from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from app.database.core import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield

app = FastAPI(title="Pectora API", version="0.1.0", lifespan=lifespan)

# Allow all origins for hackathon simplicity
app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "Pectora-backend"}

from app.api.websockets import router as websockets_router
from app.api.voice import router as voice_router
from app.api.chat import router as chat_router

app.include_router(websockets_router)
app.include_router(voice_router, prefix="/api/voice")
app.include_router(chat_router, prefix="/api")
