"""
main.py — FastAPI application entry point.

This is where the app is created, middleware is added, and all route modules are registered.
Think of this file as the "hub" — it pulls everything together but does no business logic itself.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import health, domains, events, insights, users

# --- Create the FastAPI app ---
app = FastAPI(
    title="The Eye of GodAI",
    description="AI progress and risk intelligence API",
    version="0.1.0",
)

# --- CORS Middleware ---
# CORS (Cross-Origin Resource Sharing) controls which origins can call this API.
# Without this, the browser will block the frontend from calling the backend
# because they run on different ports (5173 vs 8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register Routers ---
# Each router is a separate module that handles a group of related endpoints.
# This keeps the codebase organised — domains logic stays in routes/domains.py, etc.
app.include_router(health.router)
app.include_router(domains.router)
app.include_router(events.router)
app.include_router(insights.router)
app.include_router(users.router)
