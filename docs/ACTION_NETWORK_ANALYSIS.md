# Action Network Data Analysis & Integration Plan

## Overview
Analysis of Action Network API data for integration into the SportsEdge NFL prediction system. This document outlines the data structure, key tracking fields, and integration strategy.

## Data Sources Analyzed

### 1. Expert Picks API
**URL**: `https://api.actionnetwork.com/web/v1/users/experts/with_picks?includeSocialReactions=true`
**Data Volume**: 123 expert profiles with picks
**Key Structure**: `profiles[]` array containing expert information and their picks

### 2. All Picks API  
**URL**: `https://api.actionnetwork.com/web/v2/scoreboard/picks/all?date=20250904&periods=event`
**Data Volume**: 10 games across 3 leagues (MLB, NFL, WNBA)
**Key Structure**: `all_games[]` array with league-specific game data

## Data Structure Analysis

### Expert Picks Data Structure

#### Profile Level (123 experts)
```json
{
  "id": 335455,
  "name": "Grant Neiffer", 
  "username": "gneiffer07",
  "is_expert": true,
  "is_verified": false,
  "followers": 67280,
  "record": {
    "win": 45,
    "loss": 118, 
    "push": 6,
    "count": 169,
    "units_net": 39.918,
    "roi": 48.3,
    "window": "last_month"
  },
  "win_streak": {
    "type": "cold",
    "value": 1,
    "startDate": "2025-09-03T07:00:00+00:00"
  }
}
```

#### Pick Level (Individual betting picks)
```json
{
  "id": 502511139,
  "league_name": "mlb",
  "play": "Y.Alvarez o0.5 HR",
  "game_id": 259737,
  "user_id": 335455,
  "type": "custom",
  "period": "game", 
  "value": 0.5,
  "odds": 380,
  "units": 0.5,
  "units_net": 1.9,
  "money": 1000,
  "money_net": 3800,
  "result": "pending",
  "created_at": "2025-09-04T15:51:54.921Z",
  "starts_at": "2025-09-04T23:40:00.000Z",
  "ends_at": "2025-09-05T06:59:59.999Z",
  "player_id": 34026,
  "custom_pick_type": "core_bet_type_33_hr",
  "custom_pick_name": "HR",
  "trend": "winning",
  "reactions": {
    "like": [81465, 179334, 229395, ...]
  },
  "number_of_copies": 74
}
```

### All Picks Data Structure

#### Game Level
```json
{
  "id": 259733,
  "league_id": 8,
  "league_name": "mlb", 
  "status": "complete",
  "start_time": "2025-09-04T20:10:00.000Z",
  "away_team_id": 212,
  "home_team_id": 208,
  "winning_team_id": 212,
  "season": 2025,
  "attendance": 26583,
  "teams": [
    {
      "id": 208,
      "full_name": "Milwaukee Brewers",
      "display_name": "Brewers", 
      "abbr": "MIL",
      "standings": {
        "win": 86,
        "loss": 54
      }
    }
  ],
  "boxscore": {
    "stats": {
      "away": {"hits": 9, "runs": 8, "errors": 3},
      "home": {"hits": 9, "runs": 3, "errors": 0}
    },
    "linescore": [...],
    "latest_odds": {
      "game": {
        "over": -105,
        "total": 9,
        "under": -115,
        "ml_away": -143,
        "ml_home": 119
      }
    }
  }
}
```

## Key Tracking Fields for Database Integration

### 1. Expert Performance Tracking
- **Expert ID**: Unique identifier for each expert
- **Expert Name/Username**: For display and identification
- **Performance Metrics**: Win/loss record, ROI, units net
- **Follower Count**: Social validation metric
- **Win Streak**: Current performance trend
- **Verification Status**: Expert credibility indicator

### 2. Pick Tracking
- **Pick ID**: Unique identifier for each pick
- **Expert ID**: Links to expert profile
- **Game ID**: Links to specific game
- **League**: Sport/league classification
- **Pick Type**: Custom, spread, total, etc.
- **Pick Details**: Specific bet description
- **Odds**: Betting odds at time of pick
- **Units**: Bet size/confidence level
- **Result**: Win/loss/pending status
- **Timestamps**: Created, starts, ends, settled
- **Social Metrics**: Likes, copies, reactions

### 3. Game Data Integration
- **Game ID**: Unique game identifier
- **Team Information**: Home/away team details
- **Game Status**: Live, complete, scheduled
- **Scores**: Final and live scoring
- **Odds Data**: Current betting lines
- **Attendance**: Crowd size metrics
- **Weather/Stadium**: Environmental factors

## Integration Strategy

### Database Schema Extensions

#### New Tables Needed:

1. **action_network_experts**
```sql
CREATE TABLE action_network_experts (
    id INTEGER PRIMARY KEY,
    an_expert_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    username TEXT,
    is_verified BOOLEAN,
    followers INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

2. **action_network_expert_performance**
```sql
CREATE TABLE action_network_expert_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expert_id INTEGER,
    window_period TEXT, -- 'last_month', 'last_week', etc.
    wins INTEGER,
    losses INTEGER,
    pushes INTEGER,
    total_picks INTEGER,
    units_net REAL,
    roi REAL,
    win_streak_type TEXT, -- 'hot', 'cold', 'neutral'
    win_streak_value INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expert_id) REFERENCES action_network_experts(id)
);
```

3. **action_network_picks**
```sql
CREATE TABLE action_network_picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    an_pick_id INTEGER UNIQUE NOT NULL,
    expert_id INTEGER,
    game_id INTEGER,
    league_name TEXT,
    pick_type TEXT,
    play_description TEXT,
    value REAL,
    odds INTEGER,
    units REAL,
    units_net REAL,
    money REAL,
    money_net REAL,
    result TEXT, -- 'win', 'loss', 'push', 'pending'
    created_at TIMESTAMP,
    starts_at TIMESTAMP,
    ends_at TIMESTAMP,
    settled_at TIMESTAMP,
    player_id INTEGER,
    trend TEXT, -- 'winning', 'losing', 'neutral'
    social_likes INTEGER,
    social_copies INTEGER,
    FOREIGN KEY (expert_id) REFERENCES action_network_experts(id)
);
```

4. **action_network_games**
```sql
CREATE TABLE action_network_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    an_game_id INTEGER UNIQUE NOT NULL,
    league_name TEXT,
    season INTEGER,
    home_team_id INTEGER,
    away_team_id INTEGER,
    winning_team_id INTEGER,
    game_status TEXT,
    start_time TIMESTAMP,
    attendance INTEGER,
    home_score INTEGER,
    away_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Integration Points with Existing System

1. **Game Matching**: Link Action Network game IDs to existing NFL game data
2. **Team Mapping**: Map Action Network team IDs to existing team references
3. **Performance Comparison**: Compare Action Network expert picks against SportsEdge predictions
4. **Market Validation**: Use Action Network odds as market validation for predictions
5. **Social Sentiment**: Incorporate social metrics (likes, copies) as additional signals

### Data Collection Strategy

1. **Scheduled Updates**: 
   - Expert picks: Every 15 minutes during active periods
   - Game data: Every 5 minutes during live games
   - Expert performance: Daily updates

2. **Historical Data**:
   - Backfill expert performance data
   - Archive completed picks for analysis
   - Maintain historical odds data

3. **Error Handling**:
   - Rate limiting compliance
   - API failure fallbacks
   - Data validation and cleaning

## Benefits for SportsEdge System

### 1. Market Validation
- Compare SportsEdge predictions against market consensus
- Identify when SportsEdge has edge over market
- Validate prediction accuracy against expert picks

### 2. Expert Performance Analysis
- Track which experts consistently outperform
- Identify expert specializations (NFL vs other sports)
- Build expert credibility scoring system

### 3. Social Sentiment Integration
- Use social metrics as additional prediction signals
- Track which picks generate most interest
- Identify trending predictions and market sentiment

### 4. Enhanced Prediction System
- Incorporate expert consensus into predictions
- Use market odds as additional features
- Build ensemble models combining SportsEdge + expert picks

## Implementation Priority

### Phase 1: Basic Integration
1. Set up database tables
2. Create data collection scripts
3. Basic expert and pick tracking

### Phase 2: Analysis & Comparison
1. Expert performance analysis
2. Pick accuracy tracking
3. SportsEdge vs expert comparison

### Phase 3: Advanced Features
1. Social sentiment integration
2. Market validation features
3. Ensemble prediction models

## Technical Considerations

### API Rate Limits
- Implement proper rate limiting
- Use exponential backoff for retries
- Cache data to minimize API calls

### Data Quality
- Validate all incoming data
- Handle missing or malformed data
- Implement data cleaning pipelines

### Performance
- Index database tables properly
- Implement data archiving strategy
- Optimize queries for large datasets

## Next Steps

1. **Database Setup**: Create the new tables in the existing SQLite database
2. **Data Collection Scripts**: Build Python scripts to fetch and store data
3. **Integration Testing**: Test data collection and storage
4. **Analysis Tools**: Build tools to analyze expert performance
5. **Dashboard Integration**: Add Action Network data to existing dashboard

This integration will significantly enhance the SportsEdge system by providing market validation, expert consensus, and social sentiment data to improve prediction accuracy and provide additional insights for users.
