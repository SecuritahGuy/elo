#!/usr/bin/env python3
"""Test the cron status API endpoint without interfering with the server."""

import requests
import json
import time

def test_cron_status():
    """Test the cron status API endpoint."""
    print("Testing cron status API endpoint...")
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        # Test the cron status endpoint
        response = requests.get('http://localhost:8000/api/system/cron-status', timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Cron status API working!")
            print(f"📊 Summary: {json.dumps(data.get('summary', {}), indent=2)}")
            print(f"📅 Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"⏰ Cron Jobs: {len(data.get('cron_jobs', []))}")
            print(f"📋 Recent Logs: {len(data.get('recent_logs', []))}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Is it running?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_cron_status()
    exit(0 if success else 1)
