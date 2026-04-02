"""
Utskomia Library — FastAPI Application
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import run_migrations
from routers import (
    artifacts, works, collections, arcs, creators,
    activity, copies, flags, search,
)

COVER_DIR = Path(__file__).parent / "cover_images"


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield


app = FastAPI(
    title="Utskomia Library API",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router_module in (
    artifacts, works, collections, arcs, creators,
    activity, copies, flags, search,
):
    app.include_router(router_module.router, prefix="/api")

if COVER_DIR.is_dir():
    app.mount("/covers", StaticFiles(directory=str(COVER_DIR)), name="covers")
