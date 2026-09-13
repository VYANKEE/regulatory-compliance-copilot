"""
OpenTelemetry tracing setup.

Important concept: tracing aur logging alag problems solve karte hain.
Logging batata hai "is request me kya hua" (discrete events); tracing
batata hai "is request ka time kahan gaya" -- ek request jo 3 services
(ya is monolith ke andar 3 modules: retrieval -> LLM call -> DB write) se
guzarti hai, uska trace ek waterfall/flamegraph banata hai jisme har span
ka apna start/end/duration hota hai, parent-child relationship ke saath.
Yahi cheez batati hai "80% latency LLM call me gaya, sirf 5% DB me" --
sirf logs se ye nikaalna mushkil hota.

Config se `otlp_endpoint` set na ho (default local dev me) to koi bhi
external collector chahiye hi nahi -- traces generate hote hain par kahin
export nahi hote (span processor hi nahi lagta), is liye ye function
kabhi crash nahi karta chahe Jaeger/Tempo/whatever chal raha ho ya na ho."""

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .config import get_settings


def configure_tracing(app: FastAPI) -> None:
    settings = get_settings()

    resource = Resource(attributes={SERVICE_NAME: "compliance-copilot-api"})
    provider = TracerProvider(resource=resource)

    if settings.otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
