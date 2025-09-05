#!/bin/bash

# NFL Elo Dashboard Network Access Startup Script
echo "🏈 NFL ELO DASHBOARD - NETWORK ACCESS"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "api_server.py" ]; then
    echo "❌ Error: Please run this script from the SportsEdge root directory"
    exit 1
fi

# Get local IP address
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

if [ -z "$LOCAL_IP" ]; then
    echo "❌ Error: Could not determine local IP address"
    echo "Please check your network connection"
    exit 1
fi

echo "📍 Your local IP address: $LOCAL_IP"
echo ""

# Function to cleanup processes
cleanup() {
    echo ""
    echo "🛑 Shutting down dashboard..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null
        echo "✅ API server stopped"
    fi
    if [ ! -z "$REACT_PID" ]; then
        kill $REACT_PID 2>/dev/null
        echo "✅ React app stopped"
    fi
    echo "✅ Dashboard stopped successfully"
    exit 0
}

# Set up signal handler
trap cleanup SIGINT SIGTERM

# Start API server
echo "🚀 Starting API server..."
python api_server.py &
API_PID=$!
echo "✅ API server started (PID: $API_PID)"

# Wait for API to be ready
echo "⏳ Waiting for API server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ API server is ready!"
        break
    fi
    sleep 1
done

# Start React app with network access
echo "🚀 Starting React app with network access..."
cd dashboard
HOST=0.0.0.0 PORT=3000 npm start &
REACT_PID=$!
echo "✅ React app started (PID: $REACT_PID)"
cd ..

# Wait for React to be ready
echo "⏳ Waiting for React app to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:3000/ > /dev/null 2>&1; then
        echo "✅ React app is ready!"
        break
    fi
    sleep 2
done

# Display network access information
echo ""
echo "🎉 DASHBOARD IS READY FOR NETWORK ACCESS!"
echo "=========================================="
echo ""
echo "🌐 ACCESS URLS:"
echo "   Dashboard: http://${LOCAL_IP}:3000"
echo "   API Server: http://${LOCAL_IP}:8000"
echo "   API Docs: http://${LOCAL_IP}:8000/docs"
echo ""
echo "📱 SHARE WITH OTHER DEVICES:"
echo "   Any device on your local network can access:"
echo "   http://${LOCAL_IP}:3000"
echo ""
echo "🔧 TROUBLESHOOTING:"
echo "   • Make sure all devices are on the same WiFi network"
echo "   • Check firewall settings if connection is refused"
echo "   • Try accessing from another device's browser"
echo ""
echo "⌨️ Press Ctrl+C to stop all services"
echo ""

# Keep running and show status periodically
while true; do
    sleep 30
    echo ""
    echo "📊 DASHBOARD STATUS - $(date)"
    echo "================================"
    
    # Check API status
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ API Server: Running on http://${LOCAL_IP}:8000"
    else
        echo "❌ API Server: Not responding"
    fi
    
    # Check React status
    if curl -s http://localhost:3000/ > /dev/null 2>&1; then
        echo "✅ React App: Running on http://${LOCAL_IP}:3000"
    else
        echo "❌ React App: Not responding"
    fi
    
    echo "🌐 Network Access: http://${LOCAL_IP}:3000"
done
