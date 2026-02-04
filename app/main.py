from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api.routes import router
from app.observability.logging import setup_logging, get_logger
from app.observability.tracing import instrument_fastapi
from app.observability.metrics import metrics_endpoint

settings = get_settings()

# Add your deployed frontend origin to allowed CORS origins
settings.cors_origins.append("https://yellow-dune-0859cda0f.4.azurestaticapps.net")

setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FNOL Observability API", extra={"environment": settings.environment})
    yield
    logger.info("Shutting down FNOL Observability API")


app = FastAPI(
    title="FNOL Observability API",
    description="Production-grade observability platform for LLM-driven insurance FNOL claims processing",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yellow-dune-0859cda0f.4.azurestaticapps.net"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrument_fastapi(app)

app.include_router(router)


@app.get("/metrics")
async def metrics():
    return metrics_endpoint()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fnol-observability-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,
    )
