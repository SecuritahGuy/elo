#!/usr/bin/env python3
"""
NFL Elo Dashboard Startup Script
Starts both backend API server and React frontend, then displays stats
"""

import subprocess
import time
import requests
import json
import sys
import os
import signal
import threading
from datetime import datetime

class DashboardManager:
    def __init__(self):
        self.api_process = None
        self.react_process = None
        self.running = True
        
    def start_api_server(self):
        """Start the FastAPI backend server"""
        print("🚀 Starting API server...")
        try:
            self.api_process = subprocess.Popen(
                [sys.executable, "api_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            print("✅ API server started (PID: {})".format(self.api_process.pid))
            return True
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            return False
    
    def start_react_app(self):
        """Start the React frontend"""
        print("🚀 Starting React frontend...")
        try:
            # Change to dashboard directory
            dashboard_dir = os.path.join(os.getcwd(), "dashboard")
            if not os.path.exists(dashboard_dir):
                print("❌ Dashboard directory not found!")
                return False
                
            self.react_process = subprocess.Popen(
                ["npm", "start"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=dashboard_dir
            )
            print("✅ React app started (PID: {})".format(self.react_process.pid))
            return True
        except Exception as e:
            print(f"❌ Failed to start React app: {e}")
            return False
    
    def wait_for_api(self, timeout=30):
        """Wait for API server to be ready"""
        print("⏳ Waiting for API server to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:8000/", timeout=2)
                if response.status_code == 200:
                    print("✅ API server is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        print("❌ API server failed to start within timeout")
        return False
    
    def wait_for_react(self, timeout=60):
        """Wait for React app to be ready"""
        print("⏳ Waiting for React app to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:3000/", timeout=2)
                if response.status_code == 200:
                    print("✅ React app is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        
        print("❌ React app failed to start within timeout")
        return False
    
    def get_api_stats(self):
        """Get stats from the API server"""
        stats = {
            "api_status": "Unknown",
            "teams_loaded": 0,
            "system_health": "Unknown",
            "performance_metrics": {},
            "error": None
        }
        
        try:
            # Test API endpoints
            base_url = "http://localhost:8000"
            
            # Test root endpoint
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                stats["api_status"] = "Running"
            
            # Test system status
            try:
                response = requests.get(f"{base_url}/api/system/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    stats["teams_loaded"] = data.get("details", {}).get("num_teams", 0)
            except:
                pass
            
            # Test system health
            try:
                response = requests.get(f"{base_url}/api/system/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    stats["system_health"] = data.get("status", "Unknown")
            except:
                pass
            
            # Test performance metrics
            try:
                response = requests.get(f"{base_url}/api/metrics/performance", timeout=5)
                if response.status_code == 200:
                    stats["performance_metrics"] = response.json()
            except:
                pass
                
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    def display_stats(self):
        """Display dashboard statistics"""
        print("\n" + "="*80)
        print("🏈 NFL ELO DASHBOARD STATISTICS")
        print("="*80)
        print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # API Stats
        print("🔧 BACKEND API SERVER:")
        print("-" * 40)
        api_stats = self.get_api_stats()
        
        if api_stats["api_status"] == "Running":
            print("✅ Status: Running")
            print(f"🌐 URL: http://localhost:8000")
            print(f"📊 Teams Loaded: {api_stats['teams_loaded']}")
            print(f"💚 System Health: {api_stats['system_health']}")
            
            if api_stats["performance_metrics"]:
                metrics = api_stats["performance_metrics"]
                print(f"🎯 Accuracy: {metrics.get('system_accuracy', 'N/A')}")
                print(f"📈 Brier Score: {metrics.get('brier_score', 'N/A')}")
                print(f"🎮 Games Processed: {metrics.get('total_games_processed', 'N/A')}")
        else:
            print("❌ Status: Not Running")
            if api_stats["error"]:
                print(f"⚠️ Error: {api_stats['error']}")
        
        print()
        
        # React Stats
        print("⚛️ REACT FRONTEND:")
        print("-" * 40)
        try:
            response = requests.get("http://localhost:3000/", timeout=5)
            if response.status_code == 200:
                print("✅ Status: Running")
                print("🌐 URL: http://localhost:3000")
                print("📱 Dashboard: Available")
            else:
                print("❌ Status: Not Responding")
        except:
            print("❌ Status: Not Running")
        
        print()
        
        # Dashboard Features
        print("🎨 DASHBOARD FEATURES:")
        print("-" * 40)
        print("✅ Team Rankings - View all 32 NFL teams")
        print("✅ Game Predictions - Week predictions & custom matchups")
        print("✅ Performance Metrics - System performance & trends")
        print("✅ System Status - Real-time health monitoring")
        print("✅ Interactive Charts - Visual data representation")
        print("✅ Real-time Updates - Auto-refresh every 5 minutes")
        
        print()
        print("🚀 QUICK ACCESS:")
        print("-" * 40)
        print("🌐 Dashboard: http://localhost:3000")
        print("🔧 API Docs: http://localhost:8000/docs")
        print("📊 API Status: http://localhost:8000/api/system/status")
        
        print()
        print("⌨️ CONTROLS:")
        print("-" * 40)
        print("Press Ctrl+C to stop both servers")
        print("The dashboard will auto-refresh every 30 seconds")
        
        print("\n" + "="*80)
    
    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            try:
                # Check API process
                if self.api_process and self.api_process.poll() is not None:
                    print("⚠️ API server stopped unexpectedly")
                    break
                
                # Check React process
                if self.react_process and self.react_process.poll() is not None:
                    print("⚠️ React app stopped unexpectedly")
                    break
                
                time.sleep(5)
            except KeyboardInterrupt:
                break
    
    def cleanup(self):
        """Clean up running processes"""
        print("\n🛑 Shutting down dashboard...")
        self.running = False
        
        if self.api_process:
            print("🛑 Stopping API server...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
        
        if self.react_process:
            print("🛑 Stopping React app...")
            self.react_process.terminate()
            try:
                self.react_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.react_process.kill()
        
        print("✅ Dashboard stopped successfully")
    
    def run(self):
        """Main run method"""
        print("🏈 NFL ELO DASHBOARD STARTUP")
        print("="*50)
        
        # Start API server
        if not self.start_api_server():
            print("❌ Failed to start API server. Exiting.")
            return False
        
        # Wait for API to be ready
        if not self.wait_for_api():
            print("❌ API server not ready. Exiting.")
            self.cleanup()
            return False
        
        # Start React app
        if not self.start_react_app():
            print("❌ Failed to start React app. Exiting.")
            self.cleanup()
            return False
        
        # Wait for React to be ready
        if not self.wait_for_react():
            print("❌ React app not ready. Exiting.")
            self.cleanup()
            return False
        
        # Display initial stats
        self.display_stats()
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n🛑 Received interrupt signal...")
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Keep running and display stats periodically
        try:
            while self.running:
                time.sleep(30)  # Update stats every 30 seconds
                if self.running:
                    self.display_stats()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

def main():
    """Main function"""
    # Check if we're in the right directory
    if not os.path.exists("api_server.py"):
        print("❌ Error: Please run this script from the SportsEdge root directory")
        sys.exit(1)
    
    # Check if dashboard directory exists
    if not os.path.exists("dashboard"):
        print("❌ Error: Dashboard directory not found")
        sys.exit(1)
    
    # Check if npm is available
    try:
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: npm not found. Please install Node.js and npm")
        sys.exit(1)
    
    # Start the dashboard
    manager = DashboardManager()
    manager.run()

if __name__ == "__main__":
    main()
