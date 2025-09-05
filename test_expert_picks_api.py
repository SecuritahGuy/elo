#!/usr/bin/env python3
"""
Test script to verify Action Network expert picks API endpoints.
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

def test_api_endpoint(url, description):
    """Test a single API endpoint."""
    try:
        print(f"Testing {description}...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {description}: SUCCESS")
            print(f"   Response keys: {list(data.keys())}")
            if 'experts' in data:
                print(f"   Experts count: {len(data['experts'])}")
            if 'picks' in data:
                print(f"   Picks count: {len(data['picks'])}")
            return True
        else:
            print(f"❌ {description}: FAILED (Status: {response.status_code})")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ {description}: ERROR - {e}")
        return False

def main():
    """Test all Action Network API endpoints."""
    print("🧪 Testing Action Network Expert Picks API")
    print("=" * 50)
    
    # Check if API server is running
    try:
        response = requests.get("http://localhost:8000/api/system/status", timeout=5)
        if response.status_code != 200:
            print("❌ API server is not running. Please start it first:")
            print("   python api_server.py")
            return
    except:
        print("❌ API server is not running. Please start it first:")
        print("   python api_server.py")
        return
    
    print("✅ API server is running")
    print()
    
    # Test endpoints
    base_url = "http://localhost:8000"
    endpoints = [
        (f"{base_url}/api/system/status", "System Status"),
        (f"{base_url}/api/action-network/experts?league=nfl&limit=5", "Expert Rankings"),
        (f"{base_url}/api/action-network/picks?league=nfl&limit=10", "Recent Picks"),
        (f"{base_url}/api/action-network/analytics?league=nfl", "Analytics"),
        (f"{base_url}/api/action-network/teams", "Teams Data"),
    ]
    
    results = []
    for url, description in endpoints:
        success = test_api_endpoint(url, description)
        results.append(success)
        print()
    
    # Summary
    print("=" * 50)
    print("📊 Test Results Summary:")
    print(f"✅ Successful: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 All tests passed! The API is ready for the dashboard.")
        print()
        print("Next steps:")
        print("1. Start the dashboard: cd dashboard && npm start")
        print("2. Or use the combined script: python start_dashboard_with_api.py")
        print("3. Visit: http://localhost:3000/expert-picks")
    else:
        print("⚠️  Some tests failed. Check the API server logs for details.")

if __name__ == "__main__":
    main()
