from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from app.config import get_settings

settings = get_settings()


def setup_tracing():
    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.namespace": "fnol",
        "deployment.environment": settings.environment,
    })

    provider = TracerProvider(resource=resource)

    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    return trace.get_tracer(__name__)


def instrument_fastapi(app):
    FastAPIInstrumentor.instrument_app(app)


def instrument_sqlalchemy(engine):
    SQLAlchemyInstrumentor().instrument(
        engine=engine.sync_engine,
    )


tracer = setup_tracing()
