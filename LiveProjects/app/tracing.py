"""
OpenTelemetry distributed tracing configuration.
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
import structlog

from .config import settings

logger = structlog.get_logger(__name__)


def setup_tracing():
    """Configure OpenTelemetry distributed tracing."""
    if not settings.tracing_enabled:
        logger.info("Tracing disabled")
        return
    
    # Create resource with service information
    resource = Resource.create({
        "service.name": settings.app_name,
        "service.version": settings.app_version,
        "service.environment": settings.environment,
    })
    
    # Set up tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
        collector_endpoint=settings.jaeger_endpoint,
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    logger.info("Tracing configured", 
                service_name=settings.app_name,
                jaeger_endpoint=settings.jaeger_endpoint)


def instrument_app(app):
    """Instrument FastAPI application with automatic tracing."""
    if not settings.tracing_enabled:
        return
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy (will be configured when database is set up)
    SQLAlchemyInstrumentor().instrument()
    
    # Instrument Redis
    RedisInstrumentor().instrument()
    
    logger.info("Application instrumented for tracing")


def get_tracer(name: str):
    """Get a tracer instance."""
    return trace.get_tracer(name)


def trace_function(span_name: str):
    """Decorator to trace function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not settings.tracing_enabled:
                return func(*args, **kwargs)
            
            tracer = get_tracer(__name__)
            with tracer.start_as_current_span(span_name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.result", str(type(result).__name__))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        return wrapper
    return decorator


async def trace_async_function(span_name: str):
    """Decorator to trace async function execution."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not settings.tracing_enabled:
                return await func(*args, **kwargs)
            
            tracer = get_tracer(__name__)
            with tracer.start_as_current_span(span_name) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.result", str(type(result).__name__))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        return wrapper
    return decorator