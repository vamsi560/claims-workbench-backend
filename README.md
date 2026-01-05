# Claims Workbench - Backend

FastAPI-based backend service for the Claims Workbench platform.

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
- `DATABASE_URL` - Your PostgreSQL connection string (Supabase no longer required; use Retool or your new DB connection)

### 3. Seed Sample Data

```bash
python seed_data.py
```

This will create 50 sample FNOL traces with complete stage executions and LLM metrics.

### 4. Run Server

```bash
# Development mode
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API endpoints
│   └── observability/
│       ├── __init__.py
│       ├── logging.py       # Structured JSON logging
│       ├── tracing.py       # OpenTelemetry tracing
│       └── metrics.py       # Prometheus metrics
├── requirements.txt         # Python dependencies
├── seed_data.py            # Sample data generator
└── .env.example            # Environment template
```

## API Endpoints

### FNOL Endpoints
- `GET /api/fnols` - List FNOLs with pagination and filters
- `GET /api/fnols/{fnol_id}` - Get FNOL detail with complete trace

### Metrics Endpoints
- `GET /api/metrics/llm` - LLM usage metrics and costs
- `GET /api/analytics/failures` - Failure analytics by stage
- `GET /api/dashboard/stats` - Dashboard statistics

### Observability Endpoints
- `GET /metrics` - Prometheus metrics
- `GET /health` - Health check

## Key Features

### Structured Logging
- JSON format with automatic PII masking
- Contextual fields: fnol_id, stage, model_name, prompt_version
- Configured via LOG_LEVEL environment variable

### Distributed Tracing
- OpenTelemetry instrumentation
- Automatic FastAPI and SQLAlchemy tracing
- Each FNOL = one trace, each stage = one span

### Prometheus Metrics
- Processing duration histograms
- Failure counters by stage
- LLM token and cost tracking
- Latency monitoring

## Database Models

### FNOLTrace
Main trace record for each FNOL processing attempt.

### FNOLStageExecution
Individual stage execution within a trace. Includes timing, status, and error information.

### LLMMetric
LLM-specific metrics including token usage, costs, model version, and prompt tracking.

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (required)
- `ENVIRONMENT` - Environment name (default: production)
- `LOG_LEVEL` - Logging level (default: INFO)
- `OTEL_SERVICE_NAME` - Service name for tracing (default: fnol-observability-api)
- `OTEL_EXPORTER_ENDPOINT` - OpenTelemetry collector endpoint (optional)

## Development

### Adding New Endpoints

1. Define route in `app/api/routes.py`
2. Add corresponding schema in `app/schemas.py`
3. Implement business logic with proper error handling
4. Add logging and tracing spans

### Adding Custom Metrics

In `app/observability/metrics.py`:

```python
from prometheus_client import Counter

custom_metric = Counter(
    'custom_metric_name',
    'Description',
    ['label1', 'label2']
)
```

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Monitoring

Access Prometheus metrics at `/metrics` endpoint for integration with monitoring systems.

Key metrics to monitor:
- `fnol_processing_duration_ms` - Processing latency
- `fnol_failure_total` - Failure rates
- `llm_cost_total` - Cost tracking
- `llm_tokens_total` - Token consumption
