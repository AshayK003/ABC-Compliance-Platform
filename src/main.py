from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.routes import router as auth_router
from src.centres.routes import router as centres_router
from src.config import settings
from src.dogs.routes import router as dogs_router
from src.inspections.routes import router as inspections_router
from src.surgeries.routes import router as surgeries_router

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(centres_router)
app.include_router(dogs_router)
app.include_router(inspections_router)
app.include_router(surgeries_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
