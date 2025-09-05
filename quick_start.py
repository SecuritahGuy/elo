#!/usr/bin/env python3
"""
Quick Start Script for NFL Elo Dashboard
Simple script to start services and show status
"""

import subprocess
import time
import requests
import sys
import os
import signal

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python packages
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI and Uvicorn available")
    except ImportError:
        print("❌ FastAPI not installed. Run: pip install fastapi uvicorn")
        return False
    
    # Check npm
    try:
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        print("✅ npm available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ npm not found. Please install Node.js")
        return False
    
    return True

def start_api_server():
    """Start the API server in background"""
    print("🚀 Starting API server...")
    try:
        process = subprocess.Popen(
            [sys.executable, "api_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"✅ API server started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def start_react_app():
    """Start the React app in background"""
    print("🚀 Starting React app...")
    try:
        dashboard_dir = os.path.join(os.getcwd(), "dashboard")
        process = subprocess.Popen(
            ["npm", "start"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=dashboard_dir
        )
        print(f"✅ React app started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start React app: {e}")
        return None

def wait_for_services():
    """Wait for services to be ready"""
    print("⏳ Waiting for services to start...")
    
    # Wait for API
    api_ready = False
    for i in range(30):  # 30 seconds timeout
        try:
            response = requests.get("http://localhost:8000/", timeout=2)
            if response.status_code == 200:
                api_ready = True
                break
        except:
            pass
        time.sleep(1)
    
    if api_ready:
        print("✅ API server ready")
    else:
        print("❌ API server not ready")
        return False
    
    # Wait for React
    react_ready = False
    for i in range(60):  # 60 seconds timeout
        try:
            response = requests.get("http://localhost:3000/", timeout=2)
            if response.status_code == 200:
                react_ready = True
                break
        except:
            pass
        time.sleep(2)
    
    if react_ready:
        print("✅ React app ready")
    else:
        print("❌ React app not ready")
        return False
    
    return True

def get_quick_stats():
    """Get quick stats from the API"""
    stats = {
        "api_status": "Unknown",
        "teams_loaded": 0,
        "system_health": "Unknown"
    }
    
    try:
        # Test API
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            stats["api_status"] = "Running"
        
        # Get system status
        try:
            response = requests.get("http://localhost:8000/api/system/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                stats["teams_loaded"] = data.get("details", {}).get("num_teams", 0)
        except:
            pass
        
        # Get system health
        try:
            response = requests.get("http://localhost:8000/api/system/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                stats["system_health"] = data.get("status", "Unknown")
        except:
            pass
            
    except Exception as e:
        stats["error"] = str(e)
    
    return stats

def display_quick_stats():
    """Display quick statistics"""
    print("\n" + "="*60)
    print("🏈 NFL ELO DASHBOARD - QUICK STATUS")
    print("="*60)
    
    stats = get_quick_stats()
    
    print(f"🔧 API Server: {stats['api_status']}")
    print(f"📊 Teams Loaded: {stats['teams_loaded']}")
    print(f"💚 System Health: {stats['system_health']}")
    
    print("\n🌐 URLs:")
    print("   Dashboard: http://localhost:3000")
    print("   API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    
    print("\n⌨️ Press Ctrl+C to stop all services")
    print("="*60)

def cleanup_processes(api_process, react_process):
    """Clean up running processes"""
    print("\n🛑 Shutting down services...")
    
    if api_process:
        api_process.terminate()
        try:
            api_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_process.kill()
    
    if react_process:
        react_process.terminate()
        try:
            react_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            react_process.kill()
    
    print("✅ Services stopped")

def main():
    """Main function"""
    print("🏈 NFL ELO DASHBOARD - QUICK START")
    print("="*50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check directory
    if not os.path.exists("api_server.py"):
        print("❌ Error: Please run from SportsEdge root directory")
        sys.exit(1)
    
    # Start services
    api_process = start_api_server()
    if not api_process:
        sys.exit(1)
    
    react_process = start_react_app()
    if not react_process:
        api_process.terminate()
        sys.exit(1)
    
    # Wait for services
    if not wait_for_services():
        cleanup_processes(api_process, react_process)
        sys.exit(1)
    
    # Display stats
    display_quick_stats()
    
    # Set up signal handler
    def signal_handler(sig, frame):
        cleanup_processes(api_process, react_process)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Keep running
    try:
        while True:
            time.sleep(30)
            display_quick_stats()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_processes(api_process, react_process)

if __name__ == "__main__":
    main()
