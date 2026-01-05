# All SQLAlchemy model code is now disabled for Retool migration
# from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, CheckConstraint, Index
# from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from app.database import Base
# import uuid

# class FNOLTrace(Base):
#     __tablename__ = "fnol_traces"

#     fnol_id = Column(String, primary_key=True, index=True)
#     status = Column(String, nullable=False)
#     start_time = Column(TIMESTAMP(timezone=True), nullable=False)
#     end_time = Column(TIMESTAMP(timezone=True))
#     total_duration_ms = Column(Integer)
#     created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

#     stage_executions = relationship("FNOLStageExecution", back_populates="trace", cascade="all, delete-orphan")
#     llm_metrics = relationship("LLMMetric", back_populates="trace", cascade="all, delete-orphan")

#     __table_args__ = (
#         CheckConstraint(status.in_(['SUCCESS', 'FAILED', 'PARTIAL']), name='check_trace_status'),
#         Index('idx_fnol_traces_status', 'status'),
#         Index('idx_fnol_traces_created_at', 'created_at'),
#         Index('idx_fnol_traces_status_created', 'status', 'created_at'),
#     )

# class FNOLStageExecution(Base):
#     __tablename__ = "fnol_stage_executions"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     fnol_id = Column(String, ForeignKey("fnol_traces.fnol_id", ondelete="CASCADE"), nullable=False)
#     stage_name = Column(String, nullable=False)
#     status = Column(String, nullable=False)
#     start_time = Column(TIMESTAMP(timezone=True), nullable=False)
#     end_time = Column(TIMESTAMP(timezone=True))
#     duration_ms = Column(Integer)
#     error_code = Column(String)
#     error_message = Column(String)
#     created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

#     trace = relationship("FNOLTrace", back_populates="stage_executions")

#     __table_args__ = (
#         CheckConstraint(
#             stage_name.in_([
#                 'EMAIL_INGESTION', 'ATTACHMENT_PARSING', 'OCR_PROCESSING',
#                 'LLM_EXTRACTION', 'VALIDATION', 'S3_STORAGE', 'GUIDEWIRE_PUSH'
#             ]),
#             name='check_stage_name'
#         ),
#         CheckConstraint(status.in_(['SUCCESS', 'FAILED', 'SKIPPED']), name='check_stage_status'),
#         Index('idx_stage_executions_fnol_id', 'fnol_id'),
#         Index('idx_stage_executions_status', 'status'),
#         Index('idx_stage_executions_stage_name', 'stage_name'),
#         Index('idx_stage_executions_created_at', 'created_at'),
#     )

# class LLMMetric(Base):
#     __tablename__ = "llm_metrics"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     fnol_id = Column(String, ForeignKey("fnol_traces.fnol_id", ondelete="CASCADE"), nullable=False)
#     stage_name = Column(String, nullable=False)
#     model_name = Column(String, nullable=False)
#     prompt_version = Column(String, nullable=False)
#     prompt_hash = Column(String, nullable=False)
#     prompt_tokens = Column(Integer, nullable=False, default=0)
#     completion_tokens = Column(Integer, nullable=False, default=0)
#     total_tokens = Column(Integer, nullable=False, default=0)
#     cost_usd = Column(Numeric(10, 6), nullable=False, default=0)
#     latency_ms = Column(Integer, nullable=False, default=0)
#     temperature = Column(Numeric(3, 2), default=0.7)
#     created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

#     trace = relationship("FNOLTrace", back_populates="llm_metrics")

#     __table_args__ = (
#         Index('idx_llm_metrics_fnol_id', 'fnol_id'),
#         Index('idx_llm_metrics_model_name', 'model_name'),
#         Index('idx_llm_metrics_created_at', 'created_at'),
#         Index('idx_llm_metrics_stage_name', 'stage_name'),
#     )
