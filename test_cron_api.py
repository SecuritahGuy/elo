#!/usr/bin/env python3
"""Test script for cron status API endpoint."""

import requests
import json
import time

def test_cron_status():
    """Test the cron status API endpoint."""
    print("Testing cron status API endpoint...")
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test the cron status endpoint
        response = requests.get('http://localhost:8000/api/system/cron-status', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Cron status API working!")
            print(f"📊 Summary: {data.get('summary', {})}")
            print(f"📅 Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"⏰ Cron Jobs: {len(data.get('cron_jobs', []))}")
            print(f"📋 Recent Logs: {len(data.get('recent_logs', []))}")
        else:
            print(f"❌ API returned status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Is it running?")
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_cron_status()
