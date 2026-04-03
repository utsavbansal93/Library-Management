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

# --- Serve built frontend (production) ---
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    from fastapi.responses import FileResponse

    # Serve static assets (JS, CSS, images) from Vite build
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA index.html for all non-API routes."""
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
