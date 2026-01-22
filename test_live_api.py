#!/usr/bin/env python3
"""
Test the live API endpoint to verify the FNOL detail fix works
"""

import requests
import time

def test_live_api():
    """Test the live API endpoints"""
    base_url = "https://claims-workbench-backend.onrender.com"
    
    print("🔍 Testing live API endpoints...")
    print(f"Base URL: {base_url}")
    
    # Test health check first
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        print(f"Health: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test FNOL list
    print("\n2. Testing FNOL list...")
    try:
        response = requests.get(f"{base_url}/api/fnols", timeout=30)
        print(f"FNOL List: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Found {data.get('total', 0)} FNOLs")
            if data.get('items'):
                first_fnol_id = data['items'][0]['fnol_id']
                print(f"📄 First FNOL ID: {first_fnol_id}")
                
                # Test FNOL detail
                print("\n3. Testing FNOL detail...")
                detail_response = requests.get(f"{base_url}/api/fnols/{first_fnol_id}", timeout=30)
                print(f"FNOL Detail: {detail_response.status_code}")
                
                if detail_response.status_code == 200:
                    print("✅ FNOL Detail endpoint working!")
                    detail_data = detail_response.json()
                    print(f"📊 Trace ID: {detail_data['trace']['fnol_id']}")
                    print(f"📊 Stages: {len(detail_data['stage_executions'])}")
                    print(f"📊 Metrics: {len(detail_data['llm_metrics'])}")
                    return True
                else:
                    print(f"❌ FNOL Detail failed: {detail_response.text}")
                    return False
            else:
                print("⚠️ No FNOLs found in list")
                return False
        else:
            print(f"❌ FNOL list failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing live API after deployment...")
    print("⏳ Waiting 30 seconds for deployment to complete...")
    time.sleep(30)
    
    success = test_live_api()
    
    print("\n" + "="*50)
    print("🏁 LIVE API TEST SUMMARY")
    print("="*50)
    
    if success:
        print("🎉 All tests passed! The FNOL detail endpoint is working.")
    else:
        print("❌ Tests failed. Check the deployment logs on Render.")
        print("💡 The fix may still be deploying - try again in a few minutes.")