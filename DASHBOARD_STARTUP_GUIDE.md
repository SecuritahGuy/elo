# 🚀 Multi-Sport Dashboard Startup Guide

## ✅ **Updated Integration Complete**

The `start_dashboard.sh` script has been successfully updated to use the new enhanced multi-sport API server and unified database.

## 🎯 **What's Changed**

### 1. **Enhanced API Server Integration**
- **Old**: Used `api_server.py` on port 8000
- **New**: Uses `enhanced_api_server.py` on port 5001
- **Benefits**: Multi-sport support, unified database, better performance

### 2. **Updated API Endpoints**
- **Health Check**: `http://localhost:5001/api/health`
- **Sports List**: `http://localhost:5001/api/sports`
- **NFL Teams**: `http://localhost:5001/api/sports/nfl/teams`
- **NFL Games**: `http://localhost:5001/api/sports/nfl/games`
- **NFL Dashboard**: `http://localhost:5001/api/sports/nfl/dashboard`

### 3. **Dashboard API Service Updated**
- **Base URL**: Changed from port 8000 to port 5001
- **New Endpoints**: Added multi-sport API methods
- **Backward Compatibility**: Legacy endpoints still supported

## 🚀 **How to Start the Dashboard**

### Option 1: Use the Startup Script (Recommended)
```bash
# Make sure you're in the SportsEdge root directory
cd /Users/tim/Code/Personal/SportsEdge

# Run the startup script
./start_dashboard.sh
```

### Option 2: Manual Startup
```bash
# Terminal 1: Start Enhanced API Server
python enhanced_api_server.py

# Terminal 2: Start React Dashboard
cd dashboard
npm start
```

## 🌐 **Access URLs**

### Local Access
- **Dashboard**: http://localhost:3000
- **Enhanced API**: http://localhost:5001
- **API Health**: http://localhost:5001/api/health

### Network Access (Other Devices)
- **Dashboard**: http://[YOUR_IP]:3000
- **Enhanced API**: http://[YOUR_IP]:5001

## 🧪 **Testing the Integration**

### 1. **Test API Endpoints**
```bash
# Health check
curl http://localhost:5001/api/health

# List all sports
curl http://localhost:5001/api/sports

# Get NFL teams
curl http://localhost:5001/api/sports/nfl/teams

# Get NFL games
curl http://localhost:5001/api/sports/nfl/games
```

### 2. **Test Dashboard**
1. Open http://localhost:3000
2. Navigate to multi-sport dashboard
3. Test sport selection (NFL, NBA, MLB, NHL)
4. Verify data loads correctly

### 3. **Run Integration Tests**
```bash
# Run comprehensive tests
python test_multi_sport_integration.py

# Run dashboard startup tests
python test_dashboard_startup.py
```

## 📊 **What You'll See**

### Dashboard Features
- **Multi-Sport Navigation**: Sport selector with emoji indicators
- **Dynamic Content**: Content changes based on selected sport
- **Live Games**: Real-time game updates
- **Expert Picks**: Action Network expert predictions
- **Team Rankings**: ELO-based team rankings
- **Game Schedules**: Upcoming and past games

### API Features
- **Multi-Sport Support**: NFL, NBA, MLB, NHL, NCAA
- **Unified Database**: Single database for all sports
- **RESTful Endpoints**: Consistent API structure
- **Real-time Data**: Live game updates and scores

## 🔧 **Troubleshooting**

### Common Issues

#### 1. **Port Already in Use**
```bash
# Check what's using port 5001
lsof -i :5001

# Kill the process if needed
kill -9 [PID]
```

#### 2. **API Server Not Starting**
```bash
# Check for errors
python enhanced_api_server.py

# Verify database exists
ls -la sportsedge_unified.db
```

#### 3. **Dashboard Not Loading Data**
- Check browser console for errors
- Verify API server is running on port 5001
- Check network tab for failed requests

#### 4. **Database Issues**
```bash
# Recreate database if needed
python create_unified_database.py
python migrate_to_unified.py
```

## 📱 **Mobile Access**

The dashboard is fully responsive and works on mobile devices:
- **Local Network**: Use your computer's IP address
- **Touch Navigation**: Swipe and tap friendly
- **Responsive Design**: Adapts to screen size

## 🎉 **Success Indicators**

You'll know everything is working when:
- ✅ Dashboard loads at http://localhost:3000
- ✅ Multi-sport navigation appears
- ✅ NFL data loads (teams, games, picks)
- ✅ API responds at http://localhost:5001/api/health
- ✅ No console errors in browser
- ✅ Status shows "Enhanced API Server: Running"

## 🔮 **Next Steps**

1. **Test Multi-Sport Features**: Try switching between sports
2. **Add More Data**: Load NBA, MLB, NHL data
3. **Customize Dashboard**: Modify components as needed
4. **Deploy**: Set up production deployment

---

**The multi-sport dashboard is now ready for use with the enhanced API server and unified database!**
