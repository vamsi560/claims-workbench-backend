import asyncio
from datetime import datetime, timedelta
import random
from sqlalchemy import text
from app.database import AsyncSessionLocal

PIPELINE_STAGES = [
    'EMAIL_INGESTION',
    'ATTACHMENT_PARSING',
    'OCR_PROCESSING',
    'LLM_EXTRACTION',
    'VALIDATION',
    'S3_STORAGE',
    'GUIDEWIRE_PUSH',
]

LLM_STAGES = ['OCR_PROCESSING', 'LLM_EXTRACTION', 'VALIDATION']

MODELS = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-1.0-pro']

ERROR_CODES = [
    'TIMEOUT_ERROR',
    'API_RATE_LIMIT',
    'VALIDATION_FAILED',
    'PARSE_ERROR',
    'NETWORK_ERROR',
]

ERROR_MESSAGES = {
    'TIMEOUT_ERROR': 'Request timed out after 30 seconds',
    'API_RATE_LIMIT': 'API rate limit exceeded, retry after 60s',
    'VALIDATION_FAILED': 'Required field "policy_number" missing or invalid',
    'PARSE_ERROR': 'Unable to extract structured data from attachment',
    'NETWORK_ERROR': 'Connection refused to external service',
}


def generate_fnol_trace(fnol_index: int, date_offset_hours: int):
    fnol_id = f"FNOL-{datetime.utcnow().strftime('%Y%m%d')}-{fnol_index:04d}"

    success_rate = 0.75
    partial_rate = 0.15

    rand = random.random()
    if rand < success_rate:
        status = 'SUCCESS'
        failure_stage = None
    elif rand < success_rate + partial_rate:
        status = 'PARTIAL'
        failure_stage = random.choice(PIPELINE_STAGES[3:])
    else:
        status = 'FAILED'
        failure_stage = random.choice(PIPELINE_STAGES)

    start_time = datetime.utcnow() - timedelta(hours=date_offset_hours)
    total_duration_ms = random.randint(5000, 45000)
    end_time = start_time + timedelta(milliseconds=total_duration_ms)

    return {
        'fnol_id': fnol_id,
        'status': status,
        'start_time': start_time,
        'end_time': end_time,
        'total_duration_ms': total_duration_ms,
        'failure_stage': failure_stage,
    }


def generate_stage_executions(trace_data):
    stages = []
    current_time = trace_data['start_time']

    for stage_name in PIPELINE_STAGES:
        if trace_data['failure_stage'] == stage_name:
            status = 'FAILED'
            error_code = random.choice(ERROR_CODES)
            error_message = ERROR_MESSAGES[error_code]
        elif trace_data['status'] == 'PARTIAL' and PIPELINE_STAGES.index(stage_name) > PIPELINE_STAGES.index(trace_data['failure_stage']):
            status = 'SKIPPED'
            error_code = None
            error_message = None
        else:
            status = 'SUCCESS'
            error_code = None
            error_message = None

        duration_ms = random.randint(500, 8000)
        end_time = current_time + timedelta(milliseconds=duration_ms)

        stages.append({
            'fnol_id': trace_data['fnol_id'],
            'stage_name': stage_name,
            'status': status,
            'start_time': current_time,
            'end_time': end_time,
            'duration_ms': duration_ms,
            'error_code': error_code,
            'error_message': error_message,
        })

        current_time = end_time

        if status == 'FAILED':
            break

    return stages


def generate_llm_metrics(trace_data, stage_executions):
    metrics = []

    for stage in stage_executions:
        if stage['stage_name'] in LLM_STAGES and stage['status'] == 'SUCCESS':
            model_name = random.choice(MODELS)
            prompt_version = f"v{random.randint(1, 5)}.{random.randint(0, 9)}"
            prompt_hash = f"hash_{random.randint(100000, 999999)}"

            prompt_tokens = random.randint(500, 3000)
            completion_tokens = random.randint(200, 1500)
            total_tokens = prompt_tokens + completion_tokens

            if 'flash' in model_name:
                cost_per_1k_prompt = 0.00035
                cost_per_1k_completion = 0.00105
            elif '1.5-pro' in model_name:
                cost_per_1k_prompt = 0.00125
                cost_per_1k_completion = 0.00375
            else:
                cost_per_1k_prompt = 0.0005
                cost_per_1k_completion = 0.0015

            cost_usd = (
                (prompt_tokens / 1000) * cost_per_1k_prompt +
                (completion_tokens / 1000) * cost_per_1k_completion
            )

            latency_ms = random.randint(800, 5000)
            temperature = round(random.uniform(0.3, 0.9), 2)

            metrics.append({
                'fnol_id': trace_data['fnol_id'],
                'stage_name': stage['stage_name'],
                'model_name': model_name,
                'prompt_version': prompt_version,
                'prompt_hash': prompt_hash,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'cost_usd': cost_usd,
                'latency_ms': latency_ms,
                'temperature': temperature,
            })

    return metrics


async def seed_database():
    print("Starting database seeding...")

    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM llm_metrics"))
        await session.execute(text("DELETE FROM fnol_stage_executions"))
        await session.execute(text("DELETE FROM fnol_traces"))
        await session.commit()
        print("Cleared existing data")

        total_fnols = 50
        for i in range(total_fnols):
            date_offset_hours = random.randint(0, 48)

            trace_data = generate_fnol_trace(i + 1, date_offset_hours)

            await session.execute(
                text("""
                    INSERT INTO fnol_traces (fnol_id, status, start_time, end_time, total_duration_ms)
                    VALUES (:fnol_id, :status, :start_time, :end_time, :total_duration_ms)
                """),
                {
                    'fnol_id': trace_data['fnol_id'],
                    'status': trace_data['status'],
                    'start_time': trace_data['start_time'],
                    'end_time': trace_data['end_time'],
                    'total_duration_ms': trace_data['total_duration_ms'],
                }
            )

            stage_executions = generate_stage_executions(trace_data)
            for stage in stage_executions:
                await session.execute(
                    text("""
                        INSERT INTO fnol_stage_executions
                        (fnol_id, stage_name, status, start_time, end_time, duration_ms, error_code, error_message)
                        VALUES (:fnol_id, :stage_name, :status, :start_time, :end_time, :duration_ms, :error_code, :error_message)
                    """),
                    stage
                )

            llm_metrics = generate_llm_metrics(trace_data, stage_executions)
            for metric in llm_metrics:
                await session.execute(
                    text("""
                        INSERT INTO llm_metrics
                        (fnol_id, stage_name, model_name, prompt_version, prompt_hash,
                         prompt_tokens, completion_tokens, total_tokens, cost_usd, latency_ms, temperature)
                        VALUES (:fnol_id, :stage_name, :model_name, :prompt_version, :prompt_hash,
                                :prompt_tokens, :completion_tokens, :total_tokens, :cost_usd, :latency_ms, :temperature)
                    """),
                    metric
                )

            await session.commit()

            if (i + 1) % 10 == 0:
                print(f"Seeded {i + 1}/{total_fnols} FNOLs...")

    print(f"Database seeding completed! Created {total_fnols} FNOLs with complete traces.")


if __name__ == "__main__":
    asyncio.run(seed_database())
