# 🏆 Unified Multi-Sport Database Architecture Plan

## 📊 Current State Analysis

### Current Database Structure
- **Main DB**: `nfl_elo.db` (122KB) - Basic ELO system
  - `games`, `live_games`, `live_game_updates`, `predictions`, `team_ratings`, `projected_elo_ratings`
- **Stats DB**: `artifacts/stats/nfl_elo_stats.db` (1.3MB) - Action Network + NFL stats
  - Action Network: `action_network_experts`, `action_network_picks`, `action_network_games`, `action_network_teams`, `action_network_expert_performance`
  - NFL Stats: `nfl_games_2025`, `nfl_teams_2025`, `nfl_collection_log`
  - Performance: `backtest_results`, `team_performance`, `environmental_impacts`, `backtest_metrics`, `weight_optimization`

### Issues with Current Setup
1. **Data Fragmentation**: Related data split across multiple databases
2. **No Cross-Sport Support**: Hardcoded for NFL only
3. **Inconsistent Schemas**: Different table structures for similar data
4. **Maintenance Overhead**: Multiple database connections and migrations
5. **Scalability Limitations**: Hard to add new sports or features

---

## 🎯 Unified Database Design

### Core Principles
1. **Single Source of Truth**: One database for all sports and data
2. **Sport Agnostic**: Flexible schema that works for any sport
3. **Extensible**: Easy to add new sports, leagues, and features
4. **Performance Optimized**: Proper indexing and query optimization
5. **Data Integrity**: Foreign key relationships and constraints

### Database Name
**`sportsedge_unified.db`** - Single unified database for all sports data

---

## 🏗️ Unified Schema Architecture

### 1. Core Sports Framework

#### `sports` Table
```sql
CREATE TABLE sports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_code TEXT UNIQUE NOT NULL,           -- 'nfl', 'nba', 'mlb', 'nhl', 'ncaaf', 'ncaab'
    sport_name TEXT NOT NULL,                  -- 'National Football League'
    sport_type TEXT NOT NULL,                  -- 'football', 'basketball', 'baseball', 'hockey'
    season_structure TEXT,                     -- 'regular_playoffs', 'tournament', 'series'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `leagues` Table
```sql
CREATE TABLE leagues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id INTEGER NOT NULL,
    league_code TEXT UNIQUE NOT NULL,          -- 'nfl', 'afc', 'nfc', 'nba_east', 'nba_west'
    league_name TEXT NOT NULL,                 -- 'National Football League', 'American Football Conference'
    conference TEXT,                           -- 'AFC', 'NFC', 'Eastern', 'Western'
    division TEXT,                             -- 'East', 'West', 'North', 'South'
    level TEXT,                                -- 'professional', 'college', 'minor'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sport_id) REFERENCES sports(id)
);
```

#### `seasons` Table
```sql
CREATE TABLE seasons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id INTEGER NOT NULL,
    season_year INTEGER NOT NULL,
    season_name TEXT,                          -- '2024-25', '2024', '2025'
    start_date DATE,
    end_date DATE,
    playoff_start_date DATE,
    championship_date DATE,
    status TEXT DEFAULT 'upcoming',            -- 'upcoming', 'active', 'completed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sport_id) REFERENCES sports(id),
    UNIQUE(sport_id, season_year)
);
```

### 2. Teams and Organizations

#### `teams` Table
```sql
CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id INTEGER NOT NULL,
    league_id INTEGER,
    team_code TEXT NOT NULL,                   -- 'KC', 'BUF', 'LAL', 'BOS'
    team_name TEXT NOT NULL,                   -- 'Kansas City Chiefs'
    city TEXT NOT NULL,                        -- 'Kansas City'
    mascot TEXT NOT NULL,                      -- 'Chiefs'
    abbreviation TEXT,                         -- 'KC'
    conference TEXT,                           -- 'AFC', 'Eastern'
    division TEXT,                             -- 'West', 'Atlantic'
    founded_year INTEGER,
    home_venue TEXT,                           -- 'Arrowhead Stadium'
    venue_capacity INTEGER,
    venue_surface TEXT,                        -- 'grass', 'turf', 'hardwood', 'ice'
    venue_dome BOOLEAN,
    timezone TEXT,                             -- 'CST', 'EST', 'PST'
    colors JSON,                               -- {'primary': '#E31837', 'secondary': '#FFB81C'}
    logo_url TEXT,
    website_url TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sport_id) REFERENCES sports(id),
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    UNIQUE(sport_id, team_code)
);
```

### 3. Games and Events

#### `games` Table
```sql
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    league_id INTEGER,
    external_game_id TEXT,                     -- NFL.com game ID, ESPN game ID
    game_type TEXT NOT NULL,                   -- 'regular', 'playoff', 'championship', 'exhibition'
    round TEXT,                                -- 'wild_card', 'divisional', 'conference', 'super_bowl'
    week INTEGER,                              -- Week number (NFL), Game number (NBA)
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    game_date TIMESTAMP,
    game_time_local TEXT,                      -- "1:00 PM CT"
    game_time_utc TIMESTAMP,
    venue TEXT,                                -- Stadium/arena name
    venue_city TEXT,
    venue_state TEXT,
    weather_condition TEXT,                    -- 'sunny', 'rainy', 'snowy', 'indoor'
    temperature INTEGER,                       -- Fahrenheit
    wind_speed INTEGER,                        -- MPH
    wind_direction TEXT,                       -- 'N', 'NE', 'E', etc.
    humidity INTEGER,                          -- Percentage
    precipitation TEXT,                        -- 'none', 'light', 'heavy'
    attendance INTEGER,
    home_score INTEGER,
    away_score INTEGER,
    home_win BOOLEAN,
    game_status TEXT DEFAULT 'scheduled',      -- 'scheduled', 'in_progress', 'final', 'postponed', 'cancelled'
    quarter INTEGER,                           -- Current quarter/period
    time_remaining TEXT,                       -- "8:42", "2:30"
    possession TEXT,                           -- Team with possession
    down INTEGER,                              -- Current down (football)
    distance INTEGER,                          -- Yards to go (football)
    yard_line INTEGER,                         -- Current yard line (football)
    red_zone BOOLEAN,                          -- In red zone (football)
    home_rest_days INTEGER,                    -- Days since last game
    away_rest_days INTEGER,                    -- Days since last game
    home_win_prob REAL,                        -- Pre-game win probability
    away_win_prob REAL,                        -- Pre-game win probability
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sport_id) REFERENCES sports(id),
    FOREIGN KEY (season_id) REFERENCES seasons(id),
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id)
);
```

### 4. Betting and Odds

#### `odds` Table
```sql
CREATE TABLE odds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    sportsbook TEXT NOT NULL,                  -- 'DraftKings', 'FanDuel', 'BetMGM', 'Caesars'
    odds_type TEXT NOT NULL,                   -- 'spread', 'total', 'moneyline', 'prop'
    home_value REAL,                           -- Spread value for home team
    away_value REAL,                           -- Spread value for away team
    total_value REAL,                          -- Over/under total
    home_odds INTEGER,                         -- Moneyline odds for home team
    away_odds INTEGER,                         -- Moneyline odds for away team
    over_odds INTEGER,                         -- Over total odds
    under_odds INTEGER,                        -- Under total odds
    prop_name TEXT,                            -- Prop bet description
    prop_value REAL,                           -- Prop bet value
    prop_odds INTEGER,                         -- Prop bet odds
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id)
);
```

### 5. Expert Picks and Analysis

#### `experts` Table
```sql
CREATE TABLE experts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_expert_id TEXT UNIQUE NOT NULL,   -- Action Network expert ID
    name TEXT NOT NULL,
    username TEXT,
    display_name TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    is_expert BOOLEAN DEFAULT TRUE,
    followers INTEGER DEFAULT 0,
    bio TEXT,
    avatar_url TEXT,
    website_url TEXT,
    social_media JSON,                         -- {'twitter': '@username', 'instagram': '@username'}
    specialties JSON,                          -- ['nfl', 'nba', 'mlb']
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `expert_performance` Table
```sql
CREATE TABLE expert_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expert_id INTEGER NOT NULL,
    sport_id INTEGER NOT NULL,
    window_period TEXT NOT NULL,               -- 'last_week', 'last_month', 'last_season', 'all_time'
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    pushes INTEGER DEFAULT 0,
    total_picks INTEGER DEFAULT 0,
    units_net REAL DEFAULT 0.0,
    roi REAL DEFAULT 0.0,                      -- Return on Investment
    win_percentage REAL DEFAULT 0.0,
    win_streak_type TEXT,                      -- 'hot', 'cold', 'neutral'
    win_streak_value INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    worst_streak INTEGER DEFAULT 0,
    avg_units_per_pick REAL DEFAULT 0.0,
    confidence_score REAL DEFAULT 0.0,         -- Expert confidence rating
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expert_id) REFERENCES experts(id),
    FOREIGN KEY (sport_id) REFERENCES sports(id)
);
```

#### `expert_picks` Table
```sql
CREATE TABLE expert_picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_pick_id TEXT UNIQUE NOT NULL,     -- Action Network pick ID
    expert_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    sport_id INTEGER NOT NULL,
    pick_type TEXT NOT NULL,                   -- 'spread', 'total', 'moneyline', 'prop', 'custom'
    play_description TEXT NOT NULL,            -- "KC -3.5", "Over 47.5", "KC ML"
    value REAL,                                -- Spread value, total value, etc.
    odds INTEGER,                              -- Betting odds
    units REAL,                                -- Units wagered
    units_net REAL,                            -- Net units won/lost
    money REAL,                                -- Dollar amount wagered
    money_net REAL,                            -- Net money won/lost
    result TEXT,                               -- 'win', 'loss', 'push', 'pending', 'cancelled'
    confidence_level INTEGER,                  -- 1-5 confidence rating
    reasoning TEXT,                            -- Expert's reasoning
    created_at TIMESTAMP,
    starts_at TIMESTAMP,
    ends_at TIMESTAMP,
    settled_at TIMESTAMP,
    trend TEXT,                                -- 'winning', 'losing', 'neutral'
    social_likes INTEGER DEFAULT 0,
    social_copies INTEGER DEFAULT 0,
    social_comments INTEGER DEFAULT 0,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expert_id) REFERENCES experts(id),
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (sport_id) REFERENCES sports(id)
);
```

### 6. ELO Ratings and Predictions

#### `team_ratings` Table
```sql
CREATE TABLE team_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    sport_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    week INTEGER,
    rating REAL NOT NULL,
    rating_change REAL DEFAULT 0.0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0,
    win_percentage REAL DEFAULT 0.0,
    points_for INTEGER DEFAULT 0,
    points_against INTEGER DEFAULT 0,
    point_differential INTEGER DEFAULT 0,
    home_record TEXT,                          -- "5-3"
    away_record TEXT,                          -- "4-4"
    division_record TEXT,                      -- "3-1"
    conference_record TEXT,                    -- "7-5"
    strength_of_schedule REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (sport_id) REFERENCES sports(id),
    FOREIGN KEY (season_id) REFERENCES seasons(id)
);
```

#### `predictions` Table
```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    sport_id INTEGER NOT NULL,
    prediction_type TEXT NOT NULL,             -- 'elo', 'ml', 'ensemble', 'expert_consensus'
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_rating REAL,
    away_rating REAL,
    home_win_prob REAL NOT NULL,
    away_win_prob REAL NOT NULL,
    predicted_winner_id INTEGER,
    confidence REAL NOT NULL,
    predicted_home_score INTEGER,
    predicted_away_score INTEGER,
    predicted_spread REAL,
    predicted_total REAL,
    model_version TEXT,
    features_used JSON,                        -- List of features used in prediction
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (sport_id) REFERENCES sports(id),
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id),
    FOREIGN KEY (predicted_winner_id) REFERENCES teams(id)
);
```

### 7. Performance Tracking

#### `backtest_results` Table
```sql
CREATE TABLE backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT,
    config_name TEXT,
    test_period_start DATE,
    test_period_end DATE,
    total_games INTEGER,
    correct_predictions INTEGER,
    accuracy REAL,
    brier_score REAL,
    log_loss REAL,
    calibration_error REAL,
    sharpness REAL,
    roi REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    win_rate REAL,
    avg_confidence REAL,
    features_used JSON,
    hyperparameters JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sport_id) REFERENCES sports(id)
);
```

### 8. Live Data and Updates

#### `live_updates` Table
```sql
CREATE TABLE live_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    update_type TEXT NOT NULL,                 -- 'score', 'possession', 'weather', 'odds'
    update_data JSON NOT NULL,                 -- Flexible JSON for different update types
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id)
);
```

---

## 🔄 Migration Strategy

### Phase 1: Schema Creation (Week 1)
1. **Create Unified Database**: `sportsedge_unified.db`
2. **Implement Core Tables**: sports, leagues, seasons, teams
3. **Create Games Schema**: Enhanced games table with sport flexibility
4. **Set Up Indexes**: Performance optimization

### Phase 2: Data Migration (Week 2)
1. **Migrate NFL Data**: From both existing databases
2. **Migrate Action Network Data**: Expert picks and performance
3. **Migrate ELO Data**: Team ratings and predictions
4. **Data Validation**: Ensure data integrity

### Phase 3: API Integration (Week 3)
1. **Update Data Access Layer**: Single database connection
2. **Modify API Endpoints**: Support multi-sport queries
3. **Update Dashboard**: Multi-sport support
4. **Testing**: Comprehensive testing suite

### Phase 4: Multi-Sport Expansion (Week 4+)
1. **Add NBA Support**: Basketball data integration
2. **Add MLB Support**: Baseball data integration
3. **Add NHL Support**: Hockey data integration
4. **Add College Sports**: NCAA football and basketball

---

## 🚀 Implementation Plan

### Step 1: Create Unified Database Schema
```bash
# Create migration script
python create_unified_database.py
```

### Step 2: Data Migration Scripts
```bash
# Migrate from existing databases
python migrate_to_unified.py --source-db nfl_elo.db --target-db sportsedge_unified.db
python migrate_to_unified.py --source-db artifacts/stats/nfl_elo_stats.db --target-db sportsedge_unified.db
```

### Step 3: Update Application Code
```bash
# Update database connections
# Update data access layer
# Update API endpoints
# Update dashboard components
```

### Step 4: Testing and Validation
```bash
# Run comprehensive tests
python test_unified_database.py
python test_multi_sport_support.py
```

---

## 📈 Benefits of Unified Architecture

### 1. **Scalability**
- Easy to add new sports
- Consistent data structure across sports
- Flexible schema for different sport requirements

### 2. **Performance**
- Single database connection
- Optimized queries across all data
- Better caching and indexing

### 3. **Maintainability**
- Single source of truth
- Consistent API patterns
- Easier debugging and monitoring

### 4. **Feature Development**
- Cross-sport analytics
- Multi-sport expert tracking
- Unified prediction system

### 5. **Data Integrity**
- Foreign key relationships
- Consistent data validation
- Better error handling

---

## 🎯 Next Steps

1. **Review and Approve**: This unified database design
2. **Create Migration Scripts**: Automated data migration
3. **Implement Schema**: Create the unified database
4. **Test Migration**: Validate data integrity
5. **Update Application**: Modify code to use unified database
6. **Add Multi-Sport Support**: Expand beyond NFL

This unified architecture will provide a solid foundation for expanding SportsEdge to support multiple sports while maintaining performance and data integrity.
