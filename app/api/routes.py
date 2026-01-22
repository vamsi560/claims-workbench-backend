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
from app.config import get_settings
import requests

logger = get_logger(__name__)
router = APIRouter(prefix="/api")


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
        try:
            # Query database for actual email intake data
            db_url = get_settings().database_url.replace('postgresql://', 'postgresql+asyncpg://').replace('?sslmode=require', '')
            engine = create_async_engine(
                db_url,
                echo=False,
                connect_args={"ssl": "require"}
            )
            
            async with engine.begin() as conn:
                # Get total count
                total_result = await conn.execute(text("SELECT COUNT(*) FROM email_intake"))
                total = total_result.scalar()
                logger.info(f"Total records in email_intake: {total}")
                
                # Get paginated data
                offset = (page - 1) * page_size
                result = await conn.execute(
                    text("""
                        SELECT id, subject, sender, received_at, extracted_fields 
                        FROM email_intake 
                        ORDER BY received_at DESC NULLS LAST
                        LIMIT :limit OFFSET :offset
                    """),
                    {"limit": page_size, "offset": offset}
                )
                
                items = []
                for row in result:
                    logger.info(f"Processing row: {row}")
                    items.append(FNOLListItemSchema(
                        fnol_id=f"EMAIL-{row[0]}",  # Use email_intake.id as fnol_id
                        status="SUCCESS",  # Default status for email intake
                        total_duration_ms=None,
                        failure_stage=None,
                        created_at=row[3] if row[3] else datetime.utcnow()  # received_at
                    ))
            
            await engine.dispose()
            total_pages = (total + page_size - 1) // page_size
            
            logger.info(f"Returning {len(items)} items, total: {total}")

        except Exception as e:
            logger.error(f"Error querying email_intake: {e}")
            # Return empty response on error
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
        try:
            # Extract email ID from fnol_id (format: EMAIL-123)
            if not fnol_id.startswith("EMAIL-"):
                raise HTTPException(status_code=404, detail=f"Invalid FNOL ID format: {fnol_id}")
            
            email_id = fnol_id.replace("EMAIL-", "")
            
            # Query database for email details
            db_url = get_settings().database_url.replace('postgresql://', 'postgresql+asyncpg://').replace('?sslmode=require', '')
            engine = create_async_engine(
                db_url,
                echo=False,
                connect_args={"ssl": "require"}
            )
            
            async with engine.begin() as conn:
                result = await conn.execute(
                    text("""
                        SELECT id, subject, body, attachments, sender, received_at, extracted_fields 
                        FROM email_intake 
                        WHERE id = :email_id
                    """),
                    {"email_id": email_id}
                )
                
                row = result.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail=f"FNOL {fnol_id} not found")
                
                # Create trace from email data
                trace = FNOLTraceSchema(
                    fnol_id=fnol_id,
                    status="SUCCESS",
                    start_time=row[5] if row[5] else datetime.utcnow(),  # received_at
                    end_time=row[5] if row[5] else datetime.utcnow(),    # received_at
                    total_duration_ms=1000,  # Placeholder
                    created_at=row[5] if row[5] else datetime.utcnow()   # received_at
                )
                
                # Create a stage execution for email processing
                stage_executions = [
                    FNOLStageExecutionSchema(
                        id="00000000-0000-0000-0000-000000000001",  # Placeholder UUID
                        fnol_id=fnol_id,
                        stage_name="EMAIL_PROCESSING",
                        status="SUCCESS",
                        start_time=row[5] if row[5] else datetime.utcnow(),
                        end_time=row[5] if row[5] else datetime.utcnow(),
                        duration_ms=1000,
                        error_code=None,
                        error_message=None,
                        created_at=row[5] if row[5] else datetime.utcnow()
                    )
                ]
                
                # Create LLM metrics if extracted_fields exist
                llm_metrics = []
                if row[6]:  # extracted_fields
                    try:
                        extracted_data = json.loads(row[6]) if isinstance(row[6], str) else row[6]
                        llm_metrics = [
                            LLMMetricSchema(
                                id="00000000-0000-0000-0000-000000000002",  # Placeholder UUID
                                fnol_id=fnol_id,
                                stage_name="EMAIL_PROCESSING",
                                model_name="gemini-2.5-flash",
                                prompt_version="v1.0",
                                prompt_hash="test_hash",
                                prompt_tokens=500,
                                completion_tokens=200,
                                total_tokens=700,
                                cost_usd=0.01,
                                latency_ms=2000,
                                temperature=0.7,
                                created_at=row[5] if row[5] else datetime.utcnow()
                            )
                        ]
                    except:
                        pass  # Skip if JSON parsing fails
            
            await engine.dispose()

            logger.info(
                f"Retrieved FNOL detail: {fnol_id}",
                extra={"fnol_id": fnol_id, "stage_count": len(stage_executions)}
            )

            return FNOLDetailSchema(
                trace=trace,
                stage_executions=stage_executions,
                llm_metrics=llm_metrics,
            )
            
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            logger.error(f"Error retrieving FNOL detail {fnol_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


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


from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import json

@router.post("/fnol-ingest")
async def ingest_fnol_email(payload: ParsedEmailSchema):
    """
    Receives parsed email data from Logic Apps, extracts FNOL fields using LangChain + Gemini,
    and stores the result in PostgreSQL.
    """
    with tracer.start_as_current_span("ingest_fnol_email"):
        extracted_fields = extract_fnol_fields_with_gemini(payload.body)
        # Store in PostgreSQL
        db_url = get_settings().database_url.replace('postgresql://', 'postgresql+asyncpg://').replace('?sslmode=require', '')
        engine = create_async_engine(
            db_url,
            echo=False,
            connect_args={"ssl": "require"}
        )
        async with engine.begin() as conn:
            await conn.execute(
                text("""
                    INSERT INTO email_intake (subject, body, attachments, sender, received_at, extracted_fields)
                    VALUES (:subject, :body, :attachments, :sender, :received_at, :extracted_fields)
                """),
                {
                    "subject": payload.subject,
                    "body": payload.body,
                    "attachments": json.dumps(payload.attachments),
                    "sender": payload.sender,
                    "received_at": payload.received_at.isoformat() if payload.received_at else None,
                    "extracted_fields": json.dumps(extracted_fields),
                }
            )
        await engine.dispose()
        return {"status": "success", "extracted_fields": extracted_fields}
