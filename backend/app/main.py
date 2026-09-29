"""FastAPI application entrypoint (Phase 6).

Wires together the layers: CORS, global exception handlers that produce the
consistent response envelope (NFR-6), the routers, and Swagger/OpenAPI docs at
/docs. Run with:  uvicorn app.main:app --reload
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .database import Base, engine
from . import models  # noqa: F401 — ensures all tables are registered on Base
from .routers import auth, devices, providers, listings, quotations, bookings, collections, dashboard, notifications, pricing, price_reviews, valuation, assistant
from .utils.responses import APIError, failure, success

app = FastAPI(
    title="Circular Electronics Marketplace API",
    description="REST API for the circular electronics lifecycle platform "
                "(repair · reuse · resale · refurbish · recycle).",
    version="0.6.0",
)

# --- CORS (Phase 1 §1.6): allow only the known frontend origin ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Create tables on startup so the app runs even before seeding ---
# (Idempotent. Run `python seed.py` to populate demo data.)
Base.metadata.create_all(bind=engine)


# --- Global exception handlers: always return the { success, message } envelope ---
@app.exception_handler(APIError)
async def handle_api_error(request: Request, exc: APIError):
    return JSONResponse(status_code=exc.status_code, content=failure(exc.message))


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content=failure(str(exc.detail)))


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", [])[1:]) or "input"
    return JSONResponse(status_code=422, content=failure(f"Invalid {field}: {first.get('msg', 'validation error')}"))


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    # Never leak stack traces to the client (NFR-6).
    return JSONResponse(status_code=500, content=failure("Internal server error"))


# --- Routers ---
app.include_router(auth.router, prefix="/api")
app.include_router(devices.router, prefix="/api")
app.include_router(providers.router, prefix="/api")
app.include_router(listings.router, prefix="/api")
app.include_router(quotations.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")
app.include_router(collections.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(pricing.router, prefix="/api")
app.include_router(price_reviews.router, prefix="/api")
app.include_router(valuation.router, prefix="/api")
app.include_router(assistant.router, prefix="/api")


@app.get("/api/health", tags=["System"], summary="Health check")
def health():
    return success({"status": "ok"}, "API is running")
