# 🏈 Expert Picks Dashboard Integration

## Overview

This document describes the integration of Action Network expert picks data into the SportsEdge dashboard, providing comprehensive analysis and visualization of expert performance and picks.

## 🚀 Quick Start

### 1. Start the API Server
```bash
python api_server.py
```

### 2. Start the Dashboard
```bash
cd dashboard
npm start
```

### 3. Or Use the Combined Script
```bash
python start_dashboard_with_api.py
```

### 4. Access the Expert Picks Dashboard
- **Dashboard URL**: http://localhost:3000/expert-picks
- **API Base URL**: http://localhost:8000

## 📊 Features

### Expert Rankings
- **Top 20 experts** ranked by performance
- **Win rates** and **units net** tracking
- **Follower counts** and verification status
- **Click-to-view** detailed expert profiles

### Recent Picks Analysis
- **Latest picks** from all experts
- **Filter by league** (NFL, MLB, WNBA)
- **Filter by result** (Win, Loss, Pending)
- **Social metrics** (likes, copies)
- **Pick details** (odds, units, value)

### Analytics Dashboard
- **League performance summary**
- **Pick accuracy by type**
- **Social engagement metrics**
- **Top performing experts**

### Expert Details Modal
- **Comprehensive expert profiles**
- **Performance history**
- **Recent picks breakdown**
- **Win/loss streaks**

## 🔌 API Endpoints

### System Status
```
GET /api/system/status
```
Returns overall system health and data collection status.

### Expert Data
```
GET /api/action-network/experts?league=nfl&limit=50
GET /api/action-network/experts/{id}
```
Retrieve expert rankings and detailed profiles.

### Picks Data
```
GET /api/action-network/picks?league=nfl&limit=100&expert_id=123&result=win
```
Get expert picks with filtering options.

### Analytics
```
GET /api/action-network/analytics?league=nfl
```
Comprehensive analytics and insights.

### Teams Data
```
GET /api/action-network/teams
```
NFL teams with Action Network mappings.

## 🗄️ Database Schema

### Action Network Tables
- **`action_network_experts`**: Expert profiles and basic info
- **`action_network_expert_performance`**: Performance metrics and records
- **`action_network_picks`**: Individual picks and results
- **`action_network_games`**: Game information and schedules

### Key Fields
- **Expert ID**: Unique identifier for each expert
- **Performance Metrics**: Wins, losses, units net, ROI
- **Pick Details**: Description, odds, units, result
- **Social Metrics**: Likes, copies, trends
- **Game Data**: Teams, start times, status

## 🎨 Dashboard Components

### ExpertPicks.js
Main component with:
- Expert rankings grid
- Recent picks list
- Analytics summary cards
- Expert details modal
- Filtering controls

### API Service Integration
- **`getActionNetworkExperts()`**: Fetch expert rankings
- **`getActionNetworkExpertDetails()`**: Get expert profile
- **`getActionNetworkPicks()`**: Retrieve picks with filters
- **`getActionNetworkAnalytics()`**: Get analytics data

## 🔧 Configuration

### API Server Configuration
- **Port**: 8000
- **CORS**: Enabled for dashboard access
- **Database**: SQLite (`artifacts/stats/nfl_elo_stats.db`)
- **Logging**: Comprehensive request/response logging

### Dashboard Configuration
- **Port**: 3000
- **API URL**: `http://localhost:8000`
- **Routing**: React Router with expert-picks route
- **Styling**: Tailwind CSS with NFL theme

## 📈 Data Flow

1. **Data Collection**: Automated collector gathers Action Network data
2. **Database Storage**: Data stored in SQLite with proper relationships
3. **API Layer**: Flask server provides RESTful endpoints
4. **Dashboard**: React app consumes API and displays data
5. **User Interaction**: Click experts for details, filter picks, view analytics

## 🧪 Testing

### Test API Endpoints
```bash
python test_expert_picks_api.py
```

### Manual Testing
1. Start both servers
2. Navigate to `/expert-picks`
3. Verify expert rankings load
4. Test filtering options
5. Click on experts to view details
6. Check analytics summary

## 🚨 Troubleshooting

### Common Issues

#### API Server Won't Start
- Check if port 8000 is available
- Verify database exists: `artifacts/stats/nfl_elo_stats.db`
- Check Python dependencies

#### Dashboard Won't Load
- Verify API server is running
- Check browser console for errors
- Ensure CORS is enabled

#### No Data Displayed
- Run data collection: `python start_automated_collection.py --mode single`
- Check database has Action Network data
- Verify API endpoints return data

#### Expert Details Modal Issues
- Check expert ID is valid
- Verify database relationships
- Check API response format

### Debug Steps
1. **Check API Status**: `curl http://localhost:8000/api/system/status`
2. **Verify Data**: Check database tables have data
3. **Test Endpoints**: Use test script or browser
4. **Check Logs**: Review API server console output

## 🔄 Data Updates

### Automatic Updates
- **Collection Schedule**: Every 6 hours (configurable)
- **Real-time Data**: Action Network API calls
- **Database Sync**: Automatic storage and updates

### Manual Updates
```bash
# Single collection cycle
python start_automated_collection.py --mode single

# Health check
python start_automated_collection.py --mode health
```

## 📋 Future Enhancements

### Planned Features
- **Real-time Updates**: WebSocket integration
- **Advanced Filtering**: Date ranges, pick types
- **Performance Charts**: Historical performance graphs
- **Export Functionality**: CSV/JSON data export
- **Mobile Responsiveness**: Optimized mobile view

### Analytics Improvements
- **Trend Analysis**: Performance over time
- **Correlation Studies**: Expert vs. market performance
- **Predictive Models**: Success probability scoring
- **Social Impact**: Engagement vs. performance correlation

## 🎯 Usage Examples

### View Top NFL Experts
1. Navigate to Expert Picks dashboard
2. Select "NFL" from league filter
3. View top 20 experts ranked by performance
4. Click any expert for detailed profile

### Analyze Recent Picks
1. Use "Recent Picks" section
2. Filter by result (Win/Loss/Pending)
3. Review pick details and social metrics
4. Track expert performance trends

### Monitor System Health
1. Check system status indicators
2. Review data collection timestamps
3. Verify API endpoint responses
4. Monitor error logs

## 📚 Technical Details

### Dependencies
- **Backend**: Flask, SQLite, pandas
- **Frontend**: React, Tailwind CSS, Lucide React
- **Data**: Action Network API, NFL data sources
- **Analysis**: Custom analytics tools

### Performance
- **API Response Time**: < 500ms average
- **Dashboard Load Time**: < 2 seconds
- **Data Refresh**: Every 6 hours
- **Concurrent Users**: Supports multiple users

### Security
- **CORS**: Configured for localhost
- **Input Validation**: API parameter validation
- **Error Handling**: Graceful error responses
- **Data Privacy**: No sensitive data exposure

---

## 🎉 Success!

The Expert Picks dashboard is now fully integrated and ready for analysis. You can:

✅ **View expert rankings** and performance metrics  
✅ **Analyze recent picks** with filtering options  
✅ **Monitor system health** and data collection  
✅ **Explore detailed expert profiles** and histories  
✅ **Track analytics** and performance trends  

**Next Steps**: Start the servers and begin analyzing your Action Network data! 🚀
