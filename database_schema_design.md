# Database Schema Design - Enhanced NFL Data Integration

## Current State
- **Main DB**: `nfl_elo.db` - Basic ELO system tables
- **Stats DB**: `artifacts/stats/nfl_elo_stats.db` - Action Network + NFL stats

## Enhanced Schema Design

### 1. Enhanced Games Table (nfl_elo.db)
```sql
CREATE TABLE enhanced_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nfl_game_id TEXT UNIQUE NOT NULL,           -- NFL.com game ID
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    game_type TEXT,                             -- 'REG', 'WC', 'DIV', 'CONF', 'SB'
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    home_win BOOLEAN,
    game_date TIMESTAMP,
    game_time_et TEXT,                          -- "1:00 PM ET"
    game_status TEXT,                           -- 'scheduled', 'in_progress', 'final'
    quarter INTEGER,
    time_remaining TEXT,
    possession TEXT,
    down INTEGER,
    distance INTEGER,
    yard_line INTEGER,
    red_zone BOOLEAN,
    weather_condition TEXT,
    temperature INTEGER,
    wind_speed INTEGER,
    wind_direction TEXT,
    humidity INTEGER,
    precipitation TEXT,
    stadium TEXT,
    surface TEXT,                               -- 'grass', 'turf', 'hybrid'
    dome BOOLEAN,
    attendance INTEGER,
    home_rest_days INTEGER,
    away_rest_days INTEGER,
    home_win_prob REAL,                         -- Pre-game probability
    away_win_prob REAL,
    spread REAL,                                -- Point spread
    total REAL,                                 -- Over/under total
    home_moneyline INTEGER,
    away_moneyline INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Odds Table (nfl_elo.db)
```sql
CREATE TABLE game_odds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    sportsbook TEXT NOT NULL,                   -- 'DraftKings', 'FanDuel', etc.
    odds_type TEXT NOT NULL,                    -- 'spread', 'total', 'moneyline'
    home_value REAL,
    away_value REAL,
    total_value REAL,
    home_odds INTEGER,
    away_odds INTEGER,
    over_odds INTEGER,
    under_odds INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES enhanced_games(id)
);
```

### 3. Expert Picks Integration (Consolidate into main DB)
```sql
-- Move Action Network data to main database
CREATE TABLE expert_picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pick_id TEXT UNIQUE NOT NULL,               -- Action Network pick ID
    expert_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    league TEXT NOT NULL,                       -- 'nfl', 'mlb', etc.
    pick_type TEXT NOT NULL,                    -- 'spread', 'total', 'moneyline', 'custom'
    play_description TEXT,
    value REAL,
    odds INTEGER,
    units REAL,
    units_net REAL,
    money REAL,
    money_net REAL,
    result TEXT,                                -- 'win', 'loss', 'push', 'pending'
    created_at TIMESTAMP,
    starts_at TIMESTAMP,
    ends_at TIMESTAMP,
    settled_at TIMESTAMP,
    trend TEXT,                                 -- 'winning', 'losing', 'neutral'
    social_likes INTEGER DEFAULT 0,
    social_copies INTEGER DEFAULT 0,
    verified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (game_id) REFERENCES enhanced_games(id),
    FOREIGN KEY (expert_id) REFERENCES experts(id)
);

CREATE TABLE experts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expert_id TEXT UNIQUE NOT NULL,             -- Action Network expert ID
    name TEXT NOT NULL,
    username TEXT,
    is_verified BOOLEAN,
    followers INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expert_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expert_id INTEGER NOT NULL,
    window_period TEXT NOT NULL,                -- 'last_month', 'last_week', etc.
    wins INTEGER,
    losses INTEGER,
    pushes INTEGER,
    total_picks INTEGER,
    units_net REAL,
    roi REAL,
    win_streak_type TEXT,                       -- 'hot', 'cold', 'neutral'
    win_streak_value INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expert_id) REFERENCES experts(id)
);
```

### 4. Team Information Table (nfl_elo.db)
```sql
CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_code TEXT UNIQUE NOT NULL,             -- 'KC', 'BUF', etc.
    team_name TEXT NOT NULL,                    -- 'Kansas City Chiefs'
    city TEXT NOT NULL,
    mascot TEXT NOT NULL,
    conference TEXT,                            -- 'AFC', 'NFC'
    division TEXT,                              -- 'West', 'East', 'North', 'South'
    stadium TEXT,
    surface TEXT,                               -- 'grass', 'turf', 'hybrid'
    dome BOOLEAN,
    timezone TEXT,                              -- 'EST', 'CST', 'MST', 'PST'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Migration Strategy

### Phase 1: Schema Creation
1. Create enhanced_games table
2. Create odds table
3. Create expert_picks, experts, expert_performance tables
4. Create teams table

### Phase 2: Data Migration
1. Migrate existing games data to enhanced_games
2. Migrate Action Network data from stats DB to main DB
3. Load comprehensive NFL schedule data
4. Load historical odds data (if available)

### Phase 3: Data Loading
1. Implement NFL schedule loader
2. Implement odds data loader
3. Implement expert picks loader
4. Create data validation and testing

### Phase 4: API Integration
1. Update API endpoints to use new schema
2. Update dashboard to use new data structure
3. Test end-to-end functionality

## Benefits of Enhanced Schema

1. **Unified Database**: All data in one place
2. **Rich Game Data**: Weather, stadium, rest days, live updates
3. **Odds Integration**: Historical and real-time betting data
4. **Expert Picks**: Complete expert performance tracking
5. **Better Relationships**: Proper foreign key relationships
6. **Scalability**: Designed for future expansion
7. **Performance**: Optimized indexes and queries
