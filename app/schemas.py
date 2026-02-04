from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Any
from decimal import Decimal
from uuid import UUID


class FNOLStageExecutionSchema(BaseModel):
    id: UUID
    fnol_id: str
    stage_name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LLMMetricSchema(BaseModel):
    id: UUID
    fnol_id: str
    stage_name: str
    model_name: str
    prompt_version: str
    prompt_hash: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Decimal
    latency_ms: int
    temperature: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FNOLTraceSchema(BaseModel):
    fnol_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FNOLListItemSchema(BaseModel):
    fnol_id: str
    status: str
    total_duration_ms: Optional[int] = None
    failure_stage: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FNOLDetailSchema(BaseModel):
    trace: FNOLTraceSchema
    stage_executions: List[FNOLStageExecutionSchema]
    llm_metrics: List[LLMMetricSchema]
    extracted_fields: dict[str, Any] = {}

    class Config:
        from_attributes = True


class FNOLListResponse(BaseModel):
    items: List[FNOLListItemSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class LLMMetricsOverview(BaseModel):
    total_tokens_today: int
    total_cost_today: Decimal
    avg_cost_per_fnol: Decimal
    cost_trend: List[dict]
    model_distribution: List[dict]

    model_config = {"protected_namespaces": ()}


class FailureAnalytics(BaseModel):
    failure_by_stage: List[dict]
    top_error_codes: List[dict]
    failure_trend: List[dict]


class DashboardStats(BaseModel):
    total_fnols_today: int
    success_count: int
    failure_count: int
    partial_count: int
    avg_processing_time_ms: Optional[float] = None
    manual_review_percentage: float


class ParsedEmailSchema(BaseModel):
    subject: str
    body: str
    attachments: list[str] = []  # base64 or URLs, depending on Logic Apps output
    received_at: Optional[datetime] = None
    sender: Optional[str] = None
    to: Optional[list[str]] = None
    cc: Optional[list[str]] = None

    class Config:
        from_attributes = True
