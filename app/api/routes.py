from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal

# from app.models import FNOLTrace, FNOLStageExecution, LLMMetric  # Removed for Retool migration
from app.schemas import (
    FNOLListResponse,
    FNOLListItemSchema,
    FNOLDetailSchema,
    FNOLTraceSchema,
    FNOLStageExecutionSchema,
    LLMMetricSchema,
    LLMMetricsOverview,
    FailureAnalytics,
    DashboardStats,
    ParsedEmailSchema,
)
from app.observability.logging import get_logger
from app.observability.tracing import tracer
from app.llm_extract import extract_fnol_fields_with_gemini
import requests

logger = get_logger(__name__)
router = APIRouter(prefix="/api")

RETOOL_API_URL = "https://retool.yourdomain.com/api/data"  # Replace with actual Retool API endpoint
RETOOL_API_KEY = "YOUR_RETOOL_API_KEY"  # Replace with actual Retool API key

@router.get("/fnols", response_model=FNOLListResponse)
async def list_fnols(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    with tracer.start_as_current_span("list_fnols"):
        # Stubbed response for Retool migration
        items = []
        total = 0
        total_pages = 0

        logger.info(
            f"Listed FNOLs: page={page}, total={total}",
            extra={"page": page, "total": total, "filters": {"status": status, "search": search}}
        )

        return FNOLListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


@router.get("/fnols/{fnol_id}", response_model=FNOLDetailSchema)
async def get_fnol_detail(fnol_id: str):
    with tracer.start_as_current_span("get_fnol_detail", attributes={"fnol_id": fnol_id}):
        # Stubbed response for Retool migration
        trace = None

        if not trace:
            logger.warning(f"FNOL not found: {fnol_id}", extra={"fnol_id": fnol_id})
            raise HTTPException(status_code=404, detail=f"FNOL {fnol_id} not found")

        stage_executions = []
        llm_metrics = []

        logger.info(
            f"Retrieved FNOL detail: {fnol_id}",
            extra={"fnol_id": fnol_id, "stage_count": len(stage_executions)}
        )

        return FNOLDetailSchema(
            trace=FNOLTraceSchema.model_validate(trace),
            stage_executions=[FNOLStageExecutionSchema.model_validate(s) for s in stage_executions],
            llm_metrics=[LLMMetricSchema.model_validate(m) for m in llm_metrics],
        )


@router.get("/metrics/llm", response_model=LLMMetricsOverview)
async def get_llm_metrics():
    with tracer.start_as_current_span("get_llm_metrics"):
        # Stubbed response for Retool migration
        total_tokens_today = 0
        total_cost_today = Decimal("0.0")
        avg_cost_per_fnol = Decimal("0.0")
        cost_trend = []
        model_distribution = []

        logger.info(
            f"Retrieved LLM metrics: tokens={total_tokens_today}, cost={total_cost_today}",
            extra={"total_tokens": total_tokens_today, "total_cost": str(total_cost_today)}
        )

        return LLMMetricsOverview(
            total_tokens_today=total_tokens_today,
            total_cost_today=total_cost_today,
            avg_cost_per_fnol=avg_cost_per_fnol,
            cost_trend=cost_trend,
            model_distribution=model_distribution,
        )


@router.get("/analytics/failures", response_model=FailureAnalytics)
async def get_failure_analytics():
    with tracer.start_as_current_span("get_failure_analytics"):
        # Stubbed response for Retool migration
        failure_by_stage = []
        top_error_codes = []
        failure_trend = []

        logger.info(
            f"Retrieved failure analytics: stages={len(failure_by_stage)}",
            extra={"failure_stages": len(failure_by_stage)}
        )

        return FailureAnalytics(
            failure_by_stage=failure_by_stage,
            top_error_codes=top_error_codes,
            failure_trend=failure_trend,
        )


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    with tracer.start_as_current_span("get_dashboard_stats"):
        # Stubbed response for Retool migration
        total_fnols_today = 0
        success_count = 0
        failure_count = 0
        partial_count = 0
        avg_processing_time_ms = None
        manual_review_percentage = 0.0

        logger.info(
            f"Retrieved dashboard stats: total={total_fnols_today}",
            extra={"total_fnols": total_fnols_today, "success": success_count, "failed": failure_count}
        )

        return DashboardStats(
            total_fnols_today=total_fnols_today,
            success_count=success_count,
            failure_count=failure_count,
            partial_count=partial_count,
            avg_processing_time_ms=avg_processing_time_ms,
            manual_review_percentage=manual_review_percentage,
        )


@router.post("/fnol-ingest")
async def ingest_fnol_email(payload: ParsedEmailSchema):
    """
    Receives parsed email data from Logic Apps, extracts FNOL fields using LangChain + Gemini,
    and stores the result in Retool.
    """
    with tracer.start_as_current_span("ingest_fnol_email"):
        extracted_fields = extract_fnol_fields_with_gemini(payload.body)
        # Prepare data for Retool
        retool_payload = {
            "subject": payload.subject,
            "body": payload.body,
            "attachments": payload.attachments,
            "sender": payload.sender,
            "received_at": payload.received_at.isoformat(),
            "extracted_fields": extracted_fields,
        }
        # Send to Retool (stub)
        headers = {"Authorization": f"Bearer {RETOOL_API_KEY}", "Content-Type": "application/json"}
        try:
            response = requests.post(RETOOL_API_URL, json=retool_payload, headers=headers)
            response.raise_for_status()
            retool_result = response.json()
        except Exception as e:
            logger.error(f"Retool API error: {e}")
            raise HTTPException(status_code=500, detail="Failed to store FNOL in Retool")
        return {"status": "success", "extracted_fields": extracted_fields, "retool_result": retool_result}
