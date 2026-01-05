from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Dict

fnol_processing_duration = Histogram(
    'fnol_processing_duration_ms',
    'Duration of FNOL processing in milliseconds',
    ['status'],
    buckets=[100, 500, 1000, 2500, 5000, 10000, 30000, 60000, 120000]
)

fnol_failure_total = Counter(
    'fnol_failure_total',
    'Total number of FNOL processing failures',
    ['stage', 'error_code']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total number of LLM tokens consumed',
    ['model_name', 'stage', 'token_type']
)

llm_cost_total = Counter(
    'llm_cost_total',
    'Total cost of LLM usage in USD',
    ['model_name', 'stage']
)

llm_latency = Histogram(
    'llm_latency_ms',
    'LLM API response latency in milliseconds',
    ['model_name', 'stage'],
    buckets=[100, 250, 500, 1000, 2000, 5000, 10000, 20000]
)

fnol_active = Gauge(
    'fnol_active',
    'Number of FNOLs currently being processed'
)

# Email ingestion latency (seconds)
email_ingestion_latency = Histogram(
    'email_ingestion_latency_seconds',
    'Latency for email ingestion step',
    ['source']
)

# Email parsing time (seconds)
email_parsing_time = Histogram(
    'email_parsing_time_seconds',
    'Time taken to parse email',
    ['parser']
)

# Frontend UI latency (ms)
frontend_latency = Gauge(
    'frontend_latency_ms',
    'Frontend UI latency in milliseconds'
)

# System metrics
cpu_usage = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)
memory_usage = Gauge(
    'memory_usage_percent',
    'Memory usage percentage'
)
network_io = Gauge(
    'network_io_kbps',
    'Network IO in KB/s'
)


class MetricsCollector:
    @staticmethod
    def record_fnol_duration(status: str, duration_ms: int):
        fnol_processing_duration.labels(status=status).observe(duration_ms)

    @staticmethod
    def record_fnol_failure(stage: str, error_code: str):
        fnol_failure_total.labels(stage=stage, error_code=error_code or "UNKNOWN").inc()

    @staticmethod
    def record_llm_tokens(model_name: str, stage: str, prompt_tokens: int, completion_tokens: int):
        llm_tokens_total.labels(model_name=model_name, stage=stage, token_type="prompt").inc(prompt_tokens)
        llm_tokens_total.labels(model_name=model_name, stage=stage, token_type="completion").inc(completion_tokens)

    @staticmethod
    def record_llm_cost(model_name: str, stage: str, cost_usd: float):
        llm_cost_total.labels(model_name=model_name, stage=stage).inc(cost_usd)

    @staticmethod
    def record_llm_latency(model_name: str, stage: str, latency_ms: int):
        llm_latency.labels(model_name=model_name, stage=stage).observe(latency_ms)

    @staticmethod
    def set_active_fnols(count: int):
        fnol_active.set(count)


def metrics_endpoint() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
