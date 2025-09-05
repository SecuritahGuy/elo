# 🏈 NFL Elo Dashboard Setup Guide

## 📋 **Overview**

This guide will help you set up the React dashboard for the NFL Elo Rating System. The dashboard provides a modern, interactive interface for viewing team rankings, game predictions, and system performance metrics.

## 🚀 **Quick Start**

### **Prerequisites**
- Node.js 16+ installed
- Python 3.8+ with pip
- NFL Elo system already set up and working

### **1. Install Dependencies**

```bash
# Install Python API dependencies
pip install fastapi uvicorn

# Install React dependencies
cd dashboard
npm install
```

### **2. Start the API Server**

```bash
# From the SportsEdge root directory
python api_server.py
```

The API server will start on `http://localhost:8000`

### **3. Start the React Dashboard**

```bash
# From the dashboard directory
cd dashboard
npm start
```

The dashboard will open at `http://localhost:3000`

## 🏗️ **Architecture**

### **Backend (Python FastAPI)**
- **File**: `api_server.py`
- **Port**: 8000
- **Purpose**: Provides REST API endpoints for the dashboard
- **Endpoints**:
  - `/api/system/status` - System status and health
  - `/api/teams/rankings` - Current team rankings
  - `/api/predictions/game/{home}/{away}` - Game predictions
  - `/api/predictions/week/{week}` - Week predictions
  - `/api/metrics/performance` - Performance metrics
  - `/api/config` - System configuration

### **Frontend (React)**
- **Directory**: `dashboard/`
- **Port**: 3000
- **Purpose**: Interactive dashboard interface
- **Features**:
  - Team rankings with real-time updates
  - Game predictions with confidence scores
  - Performance metrics and charts
  - System health monitoring
  - Custom prediction tool

## 📁 **File Structure**

```
SportsEdge/
├── api_server.py                 # FastAPI backend server
├── dashboard/                    # React frontend
│   ├── package.json             # Node.js dependencies
│   ├── tailwind.config.js       # Tailwind CSS config
│   ├── public/
│   │   └── index.html           # HTML template
│   └── src/
│       ├── App.js               # Main React app
│       ├── App.css              # Custom styles
│       ├── index.js             # React entry point
│       ├── services/
│       │   └── api.js           # API service layer
│       └── components/
│           ├── Header.js        # Navigation header
│           ├── Sidebar.js       # Navigation sidebar
│           ├── Dashboard.js     # Main dashboard view
│           ├── TeamRankings.js  # Team rankings view
│           ├── Predictions.js   # Predictions view
│           ├── Performance.js   # Performance metrics view
│           └── SystemStatus.js  # System status view
└── DASHBOARD_SETUP_GUIDE.md     # This guide
```

## 🎨 **Dashboard Features**

### **1. Main Dashboard**
- **System Overview**: Key metrics and status
- **Top Team Rankings**: Top 10 teams with ratings
- **Recent Predictions**: Latest game predictions
- **System Health**: Real-time status monitoring

### **2. Team Rankings**
- **Complete Rankings**: All 32 NFL teams
- **Search & Filter**: Find specific teams
- **Sort Options**: By rank, rating, or team name
- **Visual Indicators**: Rating bars and team logos
- **Summary Stats**: Highest rated, average rating, total teams

### **3. Game Predictions**
- **Week Predictions**: View predictions for any week
- **Custom Predictions**: Predict any team matchup
- **Confidence Scores**: Visual confidence indicators
- **Prediction Details**: Win probabilities, expected margins
- **Summary Metrics**: Total predictions, confidence levels

### **4. Performance Metrics**
- **Key Metrics**: Accuracy, Brier score, games processed
- **Trend Charts**: 30-day performance trends
- **System Health**: Component status and health
- **Data Quality**: Completeness and validation status
- **Performance Summary**: Detailed metrics breakdown

### **5. System Status**
- **Overall Status**: System operational status
- **Component Health**: Individual component status
- **Configuration**: Current system settings
- **System Messages**: Status updates and alerts
- **Real-time Updates**: Auto-refresh every 30 seconds

## 🔧 **Configuration**

### **Environment Variables**
Create `dashboard/.env`:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_VERSION=1.0.0
```

### **API Configuration**
The API server uses the production configuration from `configs/production.json`:
- **Travel Adjustments**: Enabled
- **QB Adjustments**: Enabled
- **Other Features**: Disabled (based on testing results)

## 🚀 **Deployment**

### **Development**
```bash
# Terminal 1: Start API server
python api_server.py

# Terminal 2: Start React app
cd dashboard
npm start
```

### **Production Build**
```bash
# Build React app
cd dashboard
npm run build

# Serve with a web server (nginx, Apache, etc.)
# Point to dashboard/build directory
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **API Server Not Starting**
   - Check if port 8000 is available
   - Verify Python dependencies are installed
   - Check for import errors in `api_server.py`

2. **React App Not Loading**
   - Verify Node.js is installed (16+)
   - Run `npm install` in dashboard directory
   - Check for JavaScript errors in browser console

3. **API Connection Errors**
   - Verify API server is running on port 8000
   - Check CORS settings in `api_server.py`
   - Verify `REACT_APP_API_URL` in `.env` file

4. **Data Not Loading**
   - Check if NFL Elo system is properly initialized
   - Verify team ratings are loaded
   - Check API endpoint responses

### **Debug Mode**
```bash
# Enable debug logging
export DEBUG=1
python api_server.py

# React debug mode
cd dashboard
REACT_APP_DEBUG=true npm start
```

## 📊 **API Endpoints Reference**

### **System Endpoints**
- `GET /` - Root endpoint
- `GET /api/system/status` - System status
- `GET /api/system/health` - System health

### **Team Endpoints**
- `GET /api/teams/rankings` - All team rankings
- `GET /api/teams/{team_id}` - Specific team details

### **Prediction Endpoints**
- `GET /api/predictions/game/{home}/{away}` - Game prediction
- `GET /api/predictions/week/{week}` - Week predictions

### **Metrics Endpoints**
- `GET /api/metrics/performance` - Performance metrics
- `GET /api/config` - System configuration

## 🎯 **Next Steps**

1. **Customize Styling**: Modify `tailwind.config.js` for custom colors
2. **Add Features**: Extend components with new functionality
3. **Deploy**: Set up production deployment
4. **Monitor**: Use system status page for monitoring
5. **Extend**: Add new API endpoints as needed

## 📝 **Notes**

- The dashboard automatically refreshes data every 5 minutes
- All API calls include proper error handling
- The interface is fully responsive for mobile devices
- Team colors and logos can be customized in CSS
- Performance charts use sample data (replace with real historical data)

## 🆘 **Support**

If you encounter issues:
1. Check the browser console for JavaScript errors
2. Verify the API server is running and accessible
3. Check the system logs for Python errors
4. Ensure all dependencies are properly installed

**The NFL Elo Dashboard is ready for use! 🏈🎯**
