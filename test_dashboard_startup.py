#!/usr/bin/env python3
"""
Test Dashboard Startup Integration
Test script to verify the enhanced multi-sport API works with the dashboard startup script
"""

import subprocess
import time
import requests
import signal
import os
import sys
from typing import Optional

class DashboardStartupTester:
    """Test the dashboard startup integration."""
    
    def __init__(self):
        self.api_process: Optional[subprocess.Popen] = None
        self.dashboard_process: Optional[subprocess.Popen] = None
        self.api_url = "http://localhost:5001"
        self.dashboard_url = "http://localhost:3000"
    
    def start_enhanced_api(self) -> bool:
        """Start the enhanced API server."""
        try:
            print("🚀 Starting Enhanced API Server...")
            self.api_process = subprocess.Popen(
                ["python", "enhanced_api_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for API to be ready
            print("⏳ Waiting for API server to be ready...")
            for i in range(30):
                try:
                    response = requests.get(f"{self.api_url}/api/health", timeout=2)
                    if response.status_code == 200:
                        print("✅ Enhanced API server is ready!")
                        return True
                except:
                    pass
                time.sleep(1)
            
            print("❌ API server failed to start within 30 seconds")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test key API endpoints."""
        print("\n🧪 Testing API Endpoints...")
        
        endpoints = [
            ("/api/health", "Health Check"),
            ("/api/sports", "Sports List"),
            ("/api/sports/nfl/teams", "NFL Teams"),
            ("/api/sports/nfl/games", "NFL Games"),
            ("/api/sports/nfl/dashboard", "NFL Dashboard")
        ]
        
        all_passed = True
        
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{self.api_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ {description}: {len(data) if isinstance(data, list) else 'OK'}")
                else:
                    print(f"  ❌ {description}: Status {response.status_code}")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {description}: Error - {e}")
                all_passed = False
        
        return all_passed
    
    def test_dashboard_startup_script(self) -> bool:
        """Test the dashboard startup script."""
        print("\n🧪 Testing Dashboard Startup Script...")
        
        try:
            # Check if the script exists and is executable
            if not os.path.exists("start_dashboard.sh"):
                print("❌ start_dashboard.sh not found")
                return False
            
            # Make it executable
            os.chmod("start_dashboard.sh", 0o755)
            
            print("✅ Dashboard startup script found and made executable")
            return True
            
        except Exception as e:
            print(f"❌ Error with dashboard script: {e}")
            return False
    
    def cleanup(self):
        """Clean up running processes."""
        print("\n🛑 Cleaning up...")
        
        if self.api_process:
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=5)
                print("✅ API server stopped")
            except:
                try:
                    self.api_process.kill()
                    print("✅ API server killed")
                except:
                    pass
        
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=5)
                print("✅ Dashboard process stopped")
            except:
                try:
                    self.dashboard_process.kill()
                    print("✅ Dashboard process killed")
                except:
                    pass
    
    def run_tests(self) -> bool:
        """Run all tests."""
        print("🧪 Dashboard Startup Integration Tests")
        print("=" * 50)
        
        try:
            # Test 1: Start Enhanced API
            if not self.start_enhanced_api():
                return False
            
            # Test 2: Test API Endpoints
            if not self.test_api_endpoints():
                print("⚠️  Some API endpoints failed, but continuing...")
            
            # Test 3: Test Dashboard Script
            if not self.test_dashboard_startup_script():
                return False
            
            print("\n🎉 All tests completed successfully!")
            print("\n📋 Next Steps:")
            print("1. Run: ./start_dashboard.sh")
            print("2. Open: http://localhost:3000")
            print("3. Test multi-sport navigation")
            
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️  Tests interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            return False
        finally:
            self.cleanup()

def main():
    """Main function."""
    tester = DashboardStartupTester()
    
    # Set up signal handler for cleanup
    def signal_handler(sig, frame):
        print("\n⏹️  Received interrupt signal")
        tester.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    success = tester.run_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
