#!/usr/bin/env python3
"""
Test script for NFL Elo API Server
"""

import sys
import subprocess
import time
import requests
import json

def test_api_server():
    """Test the API server functionality"""
    print("🧪 Testing NFL Elo API Server...")
    
    # Start the API server
    print("🚀 Starting API server...")
    process = subprocess.Popen([sys.executable, "api_server.py"], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(10)
    
    # Test endpoints
    base_url = "http://localhost:8000"
    
    test_cases = [
        ("/", "Root endpoint"),
        ("/api/system/status", "System status"),
        ("/api/teams/rankings", "Team rankings"),
        ("/api/metrics/performance", "Performance metrics"),
        ("/api/system/health", "System health"),
        ("/api/config", "Configuration")
    ]
    
    results = []
    
    for endpoint, description in test_cases:
        try:
            print(f"🔍 Testing {description}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {description}: OK")
                results.append((endpoint, "PASS", response.status_code))
            else:
                print(f"❌ {description}: FAILED (Status: {response.status_code})")
                results.append((endpoint, "FAIL", response.status_code))
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: ERROR - {e}")
            results.append((endpoint, "ERROR", str(e)))
    
    # Stop the server
    print("🛑 Stopping API server...")
    process.terminate()
    process.wait()
    
    # Print results
    print("\n📊 Test Results:")
    print("=" * 50)
    for endpoint, status, details in results:
        print(f"{endpoint:25} {status:8} {details}")
    
    # Summary
    passed = sum(1 for _, status, _ in results if status == "PASS")
    total = len(results)
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API server is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the API server implementation.")
        return False

if __name__ == "__main__":
    success = test_api_server()
    sys.exit(0 if success else 1)
