#!/usr/bin/env python3
"""
NFL Elo Dashboard Launcher
Comprehensive script to start backend, frontend, and display stats
"""

import subprocess
import time
import requests
import sys
import os
import signal
import threading
from datetime import datetime

class DashboardLauncher:
    def __init__(self):
        self.api_process = None
        self.react_process = None
        self.running = True
        
    def print_header(self):
        """Print startup header"""
        print("🏈" + "="*78 + "🏈")
        print("🏈" + " "*20 + "NFL ELO DASHBOARD LAUNCHER" + " "*20 + "🏈")
        print("🏈" + "="*78 + "🏈")
        print()
    
    def check_environment(self):
        """Check if environment is ready"""
        print("🔍 Checking environment...")
        
        # Check if we're in the right directory
        if not os.path.exists("api_server.py"):
            print("❌ Error: api_server.py not found. Run from SportsEdge root directory.")
            return False
        
        if not os.path.exists("dashboard"):
            print("❌ Error: dashboard directory not found.")
            return False
        
        # Check Python dependencies
        try:
            import fastapi
            import uvicorn
            print("✅ Python dependencies: OK")
        except ImportError as e:
            print(f"❌ Missing Python dependency: {e}")
            print("   Run: pip install fastapi uvicorn")
            return False
        
        # Check npm
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm version: {result.stdout.strip()}")
            else:
                print("❌ npm not found")
                return False
        except FileNotFoundError:
            print("❌ npm not found. Please install Node.js")
            return False
        
        return True
    
    def start_api_server(self):
        """Start the API server"""
        print("🚀 Starting API server...")
        try:
            self.api_process = subprocess.Popen(
                [sys.executable, "api_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            print(f"✅ API server started (PID: {self.api_process.pid})")
            return True
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            return False
    
    def start_react_app(self):
        """Start the React application"""
        print("🚀 Starting React application...")
        try:
            dashboard_dir = os.path.join(os.getcwd(), "dashboard")
            
            # Check if node_modules exists
            if not os.path.exists(os.path.join(dashboard_dir, "node_modules")):
                print("📦 Installing React dependencies...")
                install_process = subprocess.run(
                    ["npm", "install"],
                    cwd=dashboard_dir,
                    capture_output=True,
                    text=True
                )
                if install_process.returncode != 0:
                    print(f"❌ Failed to install dependencies: {install_process.stderr}")
                    return False
                print("✅ Dependencies installed")
            
            # Start React app
            self.react_process = subprocess.Popen(
                ["npm", "start"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=dashboard_dir
            )
            print(f"✅ React app started (PID: {self.react_process.pid})")
            return True
        except Exception as e:
            print(f"❌ Failed to start React app: {e}")
            return False
    
    def wait_for_api(self, timeout=30):
        """Wait for API server to be ready"""
        print("⏳ Waiting for API server...")
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
    
    def wait_for_react(self, timeout=120):
        """Wait for React app to be ready"""
        print("⏳ Waiting for React app (this may take a few minutes)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:3000/", timeout=2)
                if response.status_code == 200:
                    print("✅ React app is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(3)
        
        print("❌ React app failed to start within timeout")
        return False
    
    def get_system_stats(self):
        """Get comprehensive system statistics"""
        stats = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_status": "Unknown",
            "react_status": "Unknown",
            "teams_loaded": 0,
            "system_health": "Unknown",
            "performance_metrics": {},
            "errors": []
        }
        
        # Check API status
        try:
            response = requests.get("http://localhost:8000/", timeout=5)
            if response.status_code == 200:
                stats["api_status"] = "Running"
        except Exception as e:
            stats["api_status"] = "Error"
            stats["errors"].append(f"API: {str(e)}")
        
        # Check React status
        try:
            response = requests.get("http://localhost:3000/", timeout=5)
            if response.status_code == 200:
                stats["react_status"] = "Running"
        except Exception as e:
            stats["react_status"] = "Error"
            stats["errors"].append(f"React: {str(e)}")
        
        # Get detailed API stats
        if stats["api_status"] == "Running":
            try:
                # System status
                response = requests.get("http://localhost:8000/api/system/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    stats["teams_loaded"] = data.get("details", {}).get("num_teams", 0)
            except:
                pass
            
            try:
                # System health
                response = requests.get("http://localhost:8000/api/system/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    stats["system_health"] = data.get("status", "Unknown")
            except:
                pass
            
            try:
                # Performance metrics
                response = requests.get("http://localhost:8000/api/metrics/performance", timeout=5)
                if response.status_code == 200:
                    stats["performance_metrics"] = response.json()
            except:
                pass
        
        return stats
    
    def display_stats(self):
        """Display comprehensive statistics"""
        stats = self.get_system_stats()
        
        print("\n" + "="*80)
        print("📊 NFL ELO DASHBOARD STATUS")
        print("="*80)
        print(f"🕐 Timestamp: {stats['timestamp']}")
        print()
        
        # Service Status
        print("🔧 SERVICE STATUS:")
        print("-" * 40)
        api_icon = "✅" if stats["api_status"] == "Running" else "❌"
        react_icon = "✅" if stats["react_status"] == "Running" else "❌"
        print(f"{api_icon} API Server: {stats['api_status']}")
        print(f"{react_icon} React App: {stats['react_status']}")
        
        if stats["errors"]:
            print("\n⚠️ ERRORS:")
            for error in stats["errors"]:
                print(f"   • {error}")
        
        # API Details
        if stats["api_status"] == "Running":
            print(f"\n📊 API DETAILS:")
            print("-" * 40)
            print(f"🌐 URL: http://localhost:8000")
            print(f"📚 Docs: http://localhost:8000/docs")
            print(f"📈 Teams Loaded: {stats['teams_loaded']}")
            print(f"💚 System Health: {stats['system_health']}")
            
            if stats["performance_metrics"]:
                metrics = stats["performance_metrics"]
                print(f"🎯 Accuracy: {metrics.get('system_accuracy', 'N/A')}")
                print(f"📊 Brier Score: {metrics.get('brier_score', 'N/A')}")
                print(f"🎮 Games: {metrics.get('total_games_processed', 'N/A')}")
        
        # React Details
        if stats["react_status"] == "Running":
            print(f"\n⚛️ REACT DETAILS:")
            print("-" * 40)
            print(f"🌐 URL: http://localhost:3000")
            print(f"📱 Dashboard: Available")
            print(f"🎨 Features: Team Rankings, Predictions, Performance")
        
        # Quick Access
        print(f"\n🚀 QUICK ACCESS:")
        print("-" * 40)
        print("🌐 Dashboard: http://localhost:3000")
        print("🔧 API Server: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        
        # Controls
        print(f"\n⌨️ CONTROLS:")
        print("-" * 40)
        print("Press Ctrl+C to stop all services")
        print("Stats update every 30 seconds")
        
        print("="*80)
    
    def monitor_services(self):
        """Monitor services and display stats periodically"""
        while self.running:
            try:
                time.sleep(30)
                if self.running:
                    self.display_stats()
            except KeyboardInterrupt:
                break
    
    def cleanup(self):
        """Clean up all processes"""
        print("\n🛑 Shutting down dashboard...")
        self.running = False
        
        if self.api_process:
            print("🛑 Stopping API server...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
                print("✅ API server stopped")
            except subprocess.TimeoutExpired:
                self.api_process.kill()
                print("⚠️ API server force stopped")
        
        if self.react_process:
            print("🛑 Stopping React app...")
            self.react_process.terminate()
            try:
                self.react_process.wait(timeout=5)
                print("✅ React app stopped")
            except subprocess.TimeoutExpired:
                self.react_process.kill()
                print("⚠️ React app force stopped")
        
        print("✅ Dashboard shutdown complete")
    
    def run(self):
        """Main run method"""
        self.print_header()
        
        # Check environment
        if not self.check_environment():
            print("❌ Environment check failed. Exiting.")
            return False
        
        # Start API server
        if not self.start_api_server():
            print("❌ Failed to start API server. Exiting.")
            return False
        
        # Wait for API
        if not self.wait_for_api():
            print("❌ API server not ready. Exiting.")
            self.cleanup()
            return False
        
        # Start React app
        if not self.start_react_app():
            print("❌ Failed to start React app. Exiting.")
            self.cleanup()
            return False
        
        # Wait for React
        if not self.wait_for_react():
            print("❌ React app not ready. Exiting.")
            self.cleanup()
            return False
        
        # Display initial stats
        self.display_stats()
        
        # Set up signal handler
        def signal_handler(sig, frame):
            print("\n🛑 Received interrupt signal...")
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start monitoring
        monitor_thread = threading.Thread(target=self.monitor_services)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

def main():
    """Main function"""
    launcher = DashboardLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
