"""Health check router for TurringChat."""

import os

from fastapi import APIRouter

router = APIRouter()

APP_ENV = os.getenv("APP_ENV", "dev")
APP_VERSION = os.getenv("APP_VERSION", "2")


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "env": APP_ENV, "version": APP_VERSION}
