#!/usr/bin/env python3
"""
Test script to verify database connectivity and FNOL listing functionality
Run this to test the database before deploying to production.
"""

import asyncio
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import get_settings

async def test_database_connection():
    """Test basic database connectivity"""
    print("🔌 Testing database connection...")
    
    try:
        settings = get_settings()
        db_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://').replace('?sslmode=require', '')
        
        engine = create_async_engine(
            db_url,
            echo=False,
            connect_args={"ssl": "require"}
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            print(f"✅ Database connection successful! Test query returned: {value}")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_table_exists():
    """Test if email_intake table exists and check its structure"""
    print("\n📋 Testing email_intake table...")
    
    try:
        settings = get_settings()
        db_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://').replace('?sslmode=require', '')
        
        engine = create_async_engine(
            db_url,
            echo=False,
            connect_args={"ssl": "require"}
        )
        
        async with engine.begin() as conn:
            # Check if table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'email_intake'
                );
            """))
            
            table_exists = result.scalar()
            if table_exists:
                print("✅ email_intake table exists")
                
                # Check table structure
                result = await conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'email_intake' 
                    ORDER BY ordinal_position;
                """))
                
                columns = result.fetchall()
                print("📊 Table structure:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
                    
            else:
                print("❌ email_intake table does not exist")
                return False
                
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False

async def test_insert_sample_data():
    """Insert a sample email record for testing"""
    print("\n📝 Inserting sample test data...")
    
    try:
        settings = get_settings()
        db_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://').replace('?sslmode=require', '')
        
        engine = create_async_engine(
            db_url,
            echo=False,
            connect_args={"ssl": "require"}
        )
        
        sample_data = {
            "subject": "Test FNOL - Auto Accident",
            "body": "This is a test email for FNOL processing. Policy holder: John Doe. Incident: Car accident on Main St.",
            "attachments": json.dumps([]),
            "sender": "test@example.com",
            "received_at": datetime.utcnow().isoformat(),
            "extracted_fields": json.dumps({
                "policy_holder": "John Doe",
                "incident_type": "Auto Accident",
                "location": "Main St"
            })
        }
        
        async with engine.begin() as conn:
            await conn.execute(
                text("""
                    INSERT INTO email_intake (subject, body, attachments, sender, received_at, extracted_fields)
                    VALUES (:subject, :body, :attachments, :sender, :received_at, :extracted_fields)
                """),
                sample_data
            )
            
        await engine.dispose()
        print("✅ Sample data inserted successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to insert sample data: {e}")
        return False

async def test_fnol_query():
    """Test the FNOL listing query (same as API endpoint)"""
    print("\n🔍 Testing FNOL query...")
    
    try:
        settings = get_settings()
        db_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://').replace('?sslmode=require', '')
        
        engine = create_async_engine(
            db_url,
            echo=False,
            connect_args={"ssl": "require"}
        )
        
        async with engine.begin() as conn:
            # Get total count
            total_result = await conn.execute(text("SELECT COUNT(*) FROM email_intake"))
            total = total_result.scalar()
            print(f"📊 Total records in email_intake: {total}")
            
            if total > 0:
                # Get sample data
                result = await conn.execute(
                    text("""
                        SELECT id, subject, sender, received_at, extracted_fields 
                        FROM email_intake 
                        ORDER BY received_at DESC NULLS LAST
                        LIMIT 5
                    """)
                )
                
                records = result.fetchall()
                print(f"📋 Sample records ({len(records)}):")
                for i, row in enumerate(records, 1):
                    print(f"  {i}. ID: {row[0]}, Subject: {row[1][:50]}...")
                    print(f"     Sender: {row[2]}, Received: {row[3]}")
                    print(f"     FNOL ID would be: EMAIL-{row[0]}")
                    
            else:
                print("⚠️  No records found in email_intake table")
                
        await engine.dispose()
        return total > 0
        
    except Exception as e:
        print(f"❌ FNOL query failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Starting database and FNOL functionality tests...\n")
    
    # Run tests in sequence
    tests = [
        ("Database Connection", test_database_connection),
        ("Table Structure", test_table_exists),
        ("Sample Data Insert", test_insert_sample_data),
        ("FNOL Query", test_fnol_query),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("🏁 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your setup should work in production.")
    else:
        print("⚠️  Some tests failed. Fix the issues before deploying.")

if __name__ == "__main__":
    asyncio.run(main())