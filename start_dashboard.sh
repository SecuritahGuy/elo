#!/bin/bash

# NFL Elo Dashboard Startup Script
echo "🏈 NFL ELO DASHBOARD STARTUP"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "api_server.py" ]; then
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

# Start React app
echo "🚀 Starting React app..."
cd dashboard
npm start &
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

# Display status
echo ""
echo "🎉 DASHBOARD IS READY!"
echo "======================"
echo "🌐 Dashboard: http://localhost:3000"
echo "🔧 API Server: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
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
        echo "✅ API Server: Running"
    else
        echo "❌ API Server: Not responding"
    fi
    
    # Check React status
    if curl -s http://localhost:3000/ > /dev/null 2>&1; then
        echo "✅ React App: Running"
    else
        echo "❌ React App: Not responding"
    fi
    
    echo "🌐 Dashboard: http://localhost:3000"
    echo "🔧 API: http://localhost:8000"
done
