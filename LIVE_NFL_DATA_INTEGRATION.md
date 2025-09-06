# 🏈 Live NFL Data Integration System

## Overview

This system provides real-time NFL game data integration with multiple data sources, live metrics calculation, and comprehensive API endpoints for the SportsEdge dashboard.

## 🚀 Features

### Real-Time Data Sources
- **ESPN API** (requires API key)
- **SportsData.io API** (requires API key, has free tier)
- **The Odds API** (requires API key, has free tier)
- **NFL.com Scraping** (free, rate limited)
- **Mock Data Generation** (for testing and development)

### Live Game Metrics
- **Excitement Level** (0-100): Based on score difference and game state
- **Competitiveness** (0-100): Measures how close the game is
- **Momentum** (home/away/neutral): Indicates which team has momentum
- **Score Difference**: Current point differential
- **Total Points**: Combined scoring

### Database Integration
- **SQLite Storage**: Live games and updates stored in `nfl_elo.db`
- **Real-time Updates**: Continuous data refresh
- **Historical Tracking**: Game state changes over time

## 📊 API Endpoints

### Get All Live Games
```http
GET /api/live/games
```

**Response:**
```json
{
  "games": [
    {
      "id": "live_philadelphia_dallas_2025_09_07",
      "home_team": "PHI",
      "away_team": "DAL",
      "home_score": 14,
      "away_score": 10,
      "quarter": 2,
      "time_remaining": "8:42",
      "status": "in_progress",
      "possession": "PHI",
      "down": 2,
      "distance": 7,
      "yard_line": 45,
      "red_zone": false,
      "weather": "Partly Cloudy",
      "temperature": 68,
      "wind_speed": 12,
      "metrics": {
        "excitement_level": 96,
        "competitiveness": 75,
        "momentum": "neutral",
        "score_difference": 4,
        "total_points": 24
      }
    }
  ],
  "total_games": 3,
  "live_games": 2,
  "timestamp": "2025-09-05T21:03:00.185100"
}
```

### Get Specific Game
```http
GET /api/live/games/{game_id}
```

### Get Game Statistics
```http
GET /api/live/games/{game_id}/stats
```

### Get Live Game Predictions
```http
GET /api/live/games/{game_id}/predictions
```

**Response:**
```json
{
  "game_id": "live_philadelphia_dallas_2025_09_07",
  "home_team": "PHI",
  "away_team": "DAL",
  "current_score": {
    "home": 14,
    "away": 10
  },
  "game_state": {
    "quarter": 2,
    "time_remaining": "8:42",
    "status": "in_progress"
  },
  "prediction": {
    "home_win_probability": 0.852,
    "away_win_probability": 0.148,
    "predicted_winner": "PHI",
    "confidence": 0.852,
    "expected_margin": 76.0,
    "home_rating": 1765.2,
    "away_rating": 1461.1
  },
  "live_metrics": {
    "excitement_level": 96,
    "competitiveness": 75,
    "momentum": "neutral"
  }
}
```

## 🔧 Implementation

### Live Data Service
```python
from live_nfl_data_integration import LiveNFLDataService

# Initialize service
service = LiveNFLDataService()

# Get live games
games = service.get_live_games(use_mock=True)

# Calculate metrics
for game in games:
    metrics = service.calculate_live_metrics(game)
    print(f"Game: {game.home_team} vs {game.away_team}")
    print(f"Excitement: {metrics['excitement_level']}/100")
    print(f"Competitiveness: {metrics['competitiveness']}/100")
```

### Database Schema
```sql
-- Live games table
CREATE TABLE live_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT UNIQUE,
    home_team TEXT,
    away_team TEXT,
    home_score INTEGER,
    away_score INTEGER,
    quarter INTEGER,
    time_remaining TEXT,
    status TEXT,
    possession TEXT,
    down INTEGER,
    distance INTEGER,
    yard_line INTEGER,
    red_zone BOOLEAN,
    weather TEXT,
    temperature INTEGER,
    wind_speed INTEGER,
    last_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Live game updates table
CREATE TABLE live_game_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT,
    update_type TEXT,
    update_data TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES live_games (game_id)
);
```

## 🎯 Live Metrics Calculation

### Excitement Level (0-100)
- **Close games** (≤7 points): 90-100
- **Moderate games** (8-14 points): 70-89
- **Blowouts** (>14 points): 50-69
- **Final games**: 0

### Competitiveness (0-100)
- **Tied games**: 100
- **≤3 points**: 90
- **4-7 points**: 75
- **8-14 points**: 50
- **>14 points**: 25

### Momentum
- **Home momentum**: Home team leading by >7 points
- **Away momentum**: Away team leading by >7 points
- **Neutral**: Close games or early quarters

## 🔌 Data Source Integration

### ESPN API
```python
def get_live_games_espn(self):
    # Requires API key
    # Returns real-time game data
    pass
```

### SportsData.io API
```python
def get_live_games_sportsdata(self):
    # Requires API key
    # Has free tier available
    # Returns comprehensive game stats
    pass
```

### NFL.com Scraping
```python
def scrape_nfl_live_scores(self):
    # Free but rate limited
    # Requires HTML parsing
    # Returns basic score data
    pass
```

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install requests sqlite3
```

### 2. Run Live Data Service
```bash
python live_nfl_data_integration.py
```

### 3. Test API Endpoints
```bash
# Get all live games
curl "http://localhost:8000/api/live/games"

# Get specific game
curl "http://localhost:8000/api/live/games/live_philadelphia_dallas_2025_09_07"

# Get game predictions
curl "http://localhost:8000/api/live/games/live_philadelphia_dallas_2025_09_07/predictions"
```

## 📈 Current Status

### ✅ Implemented
- Mock data generation for testing
- Live metrics calculation
- Database integration
- API endpoints
- Real-time updates

### 🔄 In Progress
- ESPN API integration (requires API key)
- SportsData.io integration (requires API key)
- NFL.com scraping implementation

### 📋 Future Enhancements
- Real-time WebSocket updates
- Push notifications for score changes
- Historical game analysis
- Advanced metrics (pace, efficiency, etc.)
- Mobile app integration

## 🎮 Example Live Games

### Chiefs vs Chargers (Final)
- **Score**: KC 24 - LAC 21
- **Status**: Final
- **Excitement**: 0/100 (game over)
- **Competitiveness**: 0/100 (game over)

### Eagles vs Cowboys (Live)
- **Score**: PHI 14 - DAL 10
- **Quarter**: 2nd (8:42 remaining)
- **Status**: In Progress
- **Excitement**: 96/100 (close game)
- **Competitiveness**: 75/100 (4-point game)
- **Momentum**: Neutral

### Bills vs Jets (Live)
- **Score**: BUF 21 - NYJ 17
- **Quarter**: 3rd (12:15 remaining)
- **Status**: In Progress
- **Excitement**: 96/100 (close game)
- **Competitiveness**: 75/100 (4-point game)
- **Momentum**: Neutral

## 🔑 API Keys Required

To use real data sources, you'll need API keys for:

1. **ESPN API**: Contact ESPN for developer access
2. **SportsData.io**: Sign up at https://sportsdata.io
3. **The Odds API**: Sign up at https://the-odds-api.com

## 📞 Support

For questions or issues with the live data integration system, please check the logs or contact the development team.

---

**Last Updated**: September 5, 2025
**Version**: 1.0.0
**Status**: Active Development
