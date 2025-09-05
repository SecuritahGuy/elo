#!/usr/bin/env python3
"""
Start both the API server and React dashboard for Action Network expert picks analysis.
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

def start_api_server():
    """Start the Flask API server."""
    print("🚀 Starting Action Network API server...")
    try:
        # Start the API server
        api_process = subprocess.Popen([
            sys.executable, "api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Check if the server started successfully
        if api_process.poll() is None:
            print("✅ API server started successfully on http://localhost:8000")
            return api_process
        else:
            stdout, stderr = api_process.communicate()
            print(f"❌ Failed to start API server:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        return None

def start_dashboard():
    """Start the React dashboard."""
    print("🚀 Starting React dashboard...")
    try:
        # Change to dashboard directory
        dashboard_dir = Path("dashboard")
        if not dashboard_dir.exists():
            print("❌ Dashboard directory not found!")
            return None
            
        # Start the React development server
        dashboard_process = subprocess.Popen([
            "npm", "start"
        ], cwd=dashboard_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for the server to start
        time.sleep(5)
        
        # Check if the server started successfully
        if dashboard_process.poll() is None:
            print("✅ Dashboard started successfully on http://localhost:3000")
            return dashboard_process
        else:
            stdout, stderr = dashboard_process.communicate()
            print(f"❌ Failed to start dashboard:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Shutting down servers...")
    sys.exit(0)

def main():
    """Main function to start both servers."""
    print("=" * 60)
    print("🏈 SportsEdge Action Network Expert Picks Dashboard")
    print("=" * 60)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check if we're in the right directory
    if not Path("api_server.py").exists():
        print("❌ Please run this script from the SportsEdge root directory")
        sys.exit(1)
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Failed to start API server. Exiting.")
        sys.exit(1)
    
    # Start dashboard
    dashboard_process = start_dashboard()
    if not dashboard_process:
        print("❌ Failed to start dashboard. Stopping API server.")
        api_process.terminate()
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Both servers are running!")
    print("📊 Dashboard: http://localhost:3000")
    print("🔌 API Server: http://localhost:8000")
    print("📋 Expert Picks: http://localhost:3000/expert-picks")
    print("=" * 60)
    print("Press Ctrl+C to stop both servers")
    print("=" * 60)
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if api_process.poll() is not None:
                print("❌ API server stopped unexpectedly")
                break
                
            if dashboard_process.poll() is not None:
                print("❌ Dashboard stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
    finally:
        # Clean up processes
        if api_process and api_process.poll() is None:
            api_process.terminate()
            print("✅ API server stopped")
            
        if dashboard_process and dashboard_process.poll() is None:
            dashboard_process.terminate()
            print("✅ Dashboard stopped")
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
