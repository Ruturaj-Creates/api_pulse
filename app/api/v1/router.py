"""Combines all v1 routers — mounted once in main.py."""

from fastapi import APIRouter

from app.api.v1 import auth

api_router = APIRouter()
api_router.include_router(auth.router)
