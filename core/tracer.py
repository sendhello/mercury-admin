from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from core.settings import settings


def configure_tracer() -> None:
    resource = Resource(attributes={"service.name": settings.project_name})
    trace.set_tracer_provider(TracerProvider(resource=resource))

    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.jaeger_agent_host,
        agent_port=settings.jaeger_agent_port,
    )
    jaeger_span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(jaeger_span_processor)

    if settings.debug:
        # To see traces in console
        console_exporter = ConsoleSpanExporter()
        console_span_processor = BatchSpanProcessor(console_exporter)
        trace.get_tracer_provider().add_span_processor(console_span_processor)
