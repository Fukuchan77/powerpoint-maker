from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.routes import router
from app.config import settings
from app.core.logging import configure_logging, get_logger
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.security import SecurityHeadersMiddleware

# Initialize structured logging
configure_logging(level=settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info(
        "application_started",
        version="0.1.0",
        log_level=settings.log_level,
        cors_origins=settings.cors_origins,
    )
    yield
    # Shutdown
    logger.info("application_shutdown")


app = FastAPI(
    title="PowerPoint Generator Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


@app.get("/")
async def root():
    return {"message": "Hello from PowerPoint Generator Agent"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
