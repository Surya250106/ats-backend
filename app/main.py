from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.exceptions import setup_exception_handlers
from app.middleware.jwt_middleware import JWTMiddleware

app = FastAPI(
    title="Job Application Tracking System (ATS) API",
    description="Production-quality Job Application Tracking System (ATS) backend built with FastAPI.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Custom JWT Middleware
app.add_middleware(JWTMiddleware)

# 3. Custom Global Exception Handlers
setup_exception_handlers(app)

# 4. Include API routers
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Root"])
def root_endpoint() -> dict:
    """
    Root API health check and index.
    """
    return {
        "status": "healthy",
        "service": "ATS Backend API",
        "documentation": "/docs"
    }
