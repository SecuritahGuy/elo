#!/bin/bash

# NFL Elo Dashboard Setup Script
echo "🏈 Setting up NFL Elo Dashboard..."

# Check if we're in the right directory
if [ ! -f "api_server.py" ]; then
    echo "❌ Error: Please run this script from the SportsEdge root directory"
    exit 1
fi

# Install Python dependencies for API server
echo "📦 Installing Python dependencies..."
pip install fastapi uvicorn

# Install React dependencies
echo "📦 Installing React dependencies..."
cd dashboard
npm install

# Create environment file
echo "⚙️ Creating environment configuration..."
cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_VERSION=1.0.0
EOF

echo "✅ Dashboard setup complete!"
echo ""
echo "🚀 To start the dashboard:"
echo "1. Start the API server: python api_server.py"
echo "2. Start the React app: cd dashboard && npm start"
echo ""
echo "📱 The dashboard will be available at http://localhost:3000"
echo "🔗 API server will run on http://localhost:8000"
