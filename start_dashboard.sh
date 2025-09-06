#!/bin/bash

# NFL Elo Dashboard Startup Script
echo "🏈 NFL ELO DASHBOARD STARTUP"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "enhanced_api_server.py" ]; then
    echo "❌ Error: Please run this script from the SportsEdge root directory"
    exit 1
fi

# Check if dashboard directory exists
if [ ! -d "dashboard" ]; then
    echo "❌ Error: Dashboard directory not found"
    exit 1
fi

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

# Start Enhanced Multi-Sport API server
echo "🚀 Starting Enhanced Multi-Sport API server..."
python enhanced_api_server.py &
API_PID=$!
echo "✅ Enhanced API server started (PID: $API_PID)"

# Wait for API to be ready
echo "⏳ Waiting for Enhanced API server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:5001/api/health > /dev/null 2>&1; then
        echo "✅ Enhanced API server is ready!"
        break
    fi
    sleep 1
done

# Start React app
echo "🚀 Starting React app..."
cd dashboard
HOST=0.0.0.0 npm start &
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

# Get local IP address
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

# Display status
echo ""
echo "🎉 MULTI-SPORT DASHBOARD IS READY!"
echo "=================================="
echo "🌐 Dashboard (Local): http://localhost:3000"
echo "🌐 Dashboard (Network): http://${LOCAL_IP}:3000"
echo "🔧 Enhanced API (Local): http://localhost:5001"
echo "🔧 Enhanced API (Network): http://${LOCAL_IP}:5001"
echo "📚 API Health: http://${LOCAL_IP}:5001/api/health"
echo "🏈 NFL Teams: http://${LOCAL_IP}:5001/api/sports/nfl/teams"
echo "🏀 NBA Teams: http://${LOCAL_IP}:5001/api/sports/nba/teams"
echo ""
echo "💡 Other devices on your network can access:"
echo "   Dashboard: http://${LOCAL_IP}:3000"
echo "   Enhanced API: http://${LOCAL_IP}:5001"
echo ""
echo "⌨️ Press Ctrl+C to stop all services"
echo ""

# Keep running and show status periodically
while true; do
    sleep 30
    echo ""
    echo "📊 DASHBOARD STATUS - $(date)"
    echo "================================"
    
    # Check Enhanced API status
    if curl -s http://localhost:5001/api/health > /dev/null 2>&1; then
        echo "✅ Enhanced API Server: Running"
    else
        echo "❌ Enhanced API Server: Not responding"
    fi
    
    # Check React status
    if curl -s http://localhost:3000/ > /dev/null 2>&1; then
        echo "✅ React App: Running"
    else
        echo "❌ React App: Not responding"
    fi
    
    echo "🌐 Dashboard: http://localhost:3000 (Local) | http://${LOCAL_IP}:3000 (Network)"
    echo "🔧 Enhanced API: http://localhost:5001 (Local) | http://${LOCAL_IP}:5001 (Network)"
done
