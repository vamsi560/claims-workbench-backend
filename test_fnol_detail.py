#!/usr/bin/env python3
"""
Test script to specifically test the FNOL detail endpoint that's failing
"""

import asyncio
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import get_settings
from app.schemas import FNOLDetailSchema, FNOLTraceSchema, FNOLStageExecutionSchema, LLMMetricSchema
import uuid

async def test_fnol_detail_logic():
    """Test the exact logic used in the FNOL detail endpoint"""
    print("🔍 Testing FNOL detail endpoint logic...")
    
    try:
        settings = get_settings()
        db_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://').replace('?sslmode=require', '')
        
        engine = create_async_engine(
            db_url,
            echo=False,
            connect_args={"ssl": "require"}
        )
        
        # Test with EMAIL-1 (which is failing)
        fnol_id = "EMAIL-1"
        email_id_str = fnol_id.replace("EMAIL-", "")
        
        try:
            email_id = int(email_id_str)
        except ValueError:
            print(f"❌ Invalid FNOL ID format: {fnol_id}")
            return False
        
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
                print(f"❌ Record not found for {fnol_id}")
                return False
            
            print(f"✅ Record found: {row}")
            print(f"📊 Data types: {[type(col) for col in row]}")
            
            # Test datetime handling
            received_at = row[5]
            print(f"📅 Original received_at: {received_at} (type: {type(received_at)})")
            
            if received_at is None:
                received_at = datetime.utcnow()
                print("📅 Using current time for None received_at")
            elif isinstance(received_at, str):
                try:
                    received_at = datetime.fromisoformat(received_at.replace('Z', '+00:00'))
                    print(f"📅 Converted string to datetime: {received_at}")
                except Exception as e:
                    print(f"⚠️ Failed to parse datetime string: {e}")
                    received_at = datetime.utcnow()
            
            print(f"📅 Final received_at: {received_at} (type: {type(received_at)})")
            
            # Test creating schemas
            try:
                trace = FNOLTraceSchema(
                    fnol_id=fnol_id,
                    status="SUCCESS",
                    start_time=received_at,
                    end_time=received_at,
                    total_duration_ms=1000,
                    created_at=received_at
                )
                print("✅ FNOLTraceSchema created successfully")
                
                stage_executions = [
                    FNOLStageExecutionSchema(
                        id=uuid.uuid4(),
                        fnol_id=fnol_id,
                        stage_name="EMAIL_PROCESSING",
                        status="SUCCESS",
                        start_time=received_at,
                        end_time=received_at,
                        duration_ms=1000,
                        error_code=None,
                        error_message=None,
                        created_at=received_at
                    )
                ]
                print("✅ FNOLStageExecutionSchema created successfully")
                
                llm_metrics = []
                if row[6]:  # extracted_fields
                    try:
                        extracted_data = json.loads(row[6]) if isinstance(row[6], str) else row[6]
                        llm_metrics = [
                            LLMMetricSchema(
                                id=uuid.uuid4(),
                                fnol_id=fnol_id,
                                stage_name="EMAIL_PROCESSING",
                                model_name="gemini-1.5-pro",
                                prompt_version="v1.0",
                                prompt_hash="test_hash",
                                prompt_tokens=500,
                                completion_tokens=200,
                                total_tokens=700,
                                cost_usd=0.01,
                                latency_ms=2000,
                                temperature=0.7,
                                created_at=received_at
                            )
                        ]
                        print("✅ LLMMetricSchema created successfully")
                    except Exception as json_error:
                        print(f"⚠️ Failed to parse extracted_fields: {json_error}")
                
                # Test final schema
                detail_schema = FNOLDetailSchema(
                    trace=trace,
                    stage_executions=stage_executions,
                    llm_metrics=llm_metrics,
                )
                print("✅ FNOLDetailSchema created successfully")
                print(f"📋 Final schema: trace={trace.fnol_id}, stages={len(stage_executions)}, metrics={len(llm_metrics)}")
                
            except Exception as schema_error:
                print(f"❌ Schema creation failed: {schema_error}")
                return False
        
        await engine.dispose()
        print("✅ All schemas created successfully - endpoint should work!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Run the FNOL detail test"""
    print("🧪 Starting FNOL detail endpoint test...\n")
    
    success = await test_fnol_detail_logic()
    
    print("\n" + "="*50)
    print("🏁 FNOL DETAIL TEST SUMMARY")
    print("="*50)
    
    if success:
        print("🎉 Test passed! The endpoint logic should work.")
        print("🚀 If you still get 500 errors, check your Render logs for the exact error.")
    else:
        print("❌ Test failed! Fix the issues before deploying.")

if __name__ == "__main__":
    asyncio.run(main())