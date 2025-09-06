#!/usr/bin/env python3
"""
Database Migration Script
Expands games table and consolidates Action Network data into main database
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Handles database schema migration and data consolidation."""
    
    def __init__(self, main_db_path: str = "nfl_elo.db", stats_db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        self.main_db_path = main_db_path
        self.stats_db_path = stats_db_path
        self.backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_backup(self) -> None:
        """Create backup of main database before migration."""
        import shutil
        backup_path = f"{self.main_db_path}.backup_{self.backup_suffix}"
        shutil.copy2(self.main_db_path, backup_path)
        logger.info(f"Database backup created: {backup_path}")
    
    def create_enhanced_schema(self) -> None:
        """Create enhanced database schema."""
        conn = sqlite3.connect(self.main_db_path)
        cursor = conn.cursor()
        
        try:
            # 1. Create enhanced_games table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enhanced_games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nfl_game_id TEXT UNIQUE NOT NULL,
                    season INTEGER NOT NULL,
                    week INTEGER NOT NULL,
                    game_type TEXT DEFAULT 'REG',
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    home_score INTEGER,
                    away_score INTEGER,
                    home_win BOOLEAN,
                    game_date TIMESTAMP,
                    game_time_et TEXT,
                    game_status TEXT DEFAULT 'scheduled',
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
                    surface TEXT,
                    dome BOOLEAN,
                    attendance INTEGER,
                    home_rest_days INTEGER,
                    away_rest_days INTEGER,
                    home_win_prob REAL,
                    away_win_prob REAL,
                    spread REAL,
                    total REAL,
                    home_moneyline INTEGER,
                    away_moneyline INTEGER,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. Create game_odds table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_odds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    sportsbook TEXT NOT NULL,
                    odds_type TEXT NOT NULL,
                    home_value REAL,
                    away_value REAL,
                    total_value REAL,
                    home_odds INTEGER,
                    away_odds INTEGER,
                    over_odds INTEGER,
                    under_odds INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES enhanced_games(id)
                )
            ''')
            
            # 3. Create experts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expert_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    username TEXT,
                    is_verified BOOLEAN,
                    followers INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 4. Create expert_performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expert_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expert_id INTEGER NOT NULL,
                    window_period TEXT NOT NULL,
                    wins INTEGER,
                    losses INTEGER,
                    pushes INTEGER,
                    total_picks INTEGER,
                    units_net REAL,
                    roi REAL,
                    win_streak_type TEXT,
                    win_streak_value INTEGER,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (expert_id) REFERENCES experts(id)
                )
            ''')
            
            # 5. Create expert_picks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expert_picks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pick_id TEXT UNIQUE NOT NULL,
                    expert_id INTEGER NOT NULL,
                    game_id INTEGER NOT NULL,
                    league TEXT NOT NULL,
                    pick_type TEXT NOT NULL,
                    play_description TEXT,
                    value REAL,
                    odds INTEGER,
                    units REAL,
                    units_net REAL,
                    money REAL,
                    money_net REAL,
                    result TEXT,
                    created_at TIMESTAMP,
                    starts_at TIMESTAMP,
                    ends_at TIMESTAMP,
                    settled_at TIMESTAMP,
                    trend TEXT,
                    social_likes INTEGER DEFAULT 0,
                    social_copies INTEGER DEFAULT 0,
                    verified BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (game_id) REFERENCES enhanced_games(id),
                    FOREIGN KEY (expert_id) REFERENCES experts(id)
                )
            ''')
            
            # 6. Create teams table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_code TEXT UNIQUE NOT NULL,
                    team_name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    mascot TEXT NOT NULL,
                    conference TEXT,
                    division TEXT,
                    stadium TEXT,
                    surface TEXT,
                    dome BOOLEAN,
                    timezone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_enhanced_games_season_week ON enhanced_games(season, week)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_enhanced_games_teams ON enhanced_games(home_team, away_team)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_enhanced_games_date ON enhanced_games(game_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_game_odds_game_id ON game_odds(game_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_expert_picks_expert_id ON expert_picks(expert_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_expert_picks_game_id ON expert_picks(game_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_expert_picks_league ON expert_picks(league)')
            
            conn.commit()
            logger.info("Enhanced schema created successfully")
            
        except Exception as e:
            logger.error(f"Error creating enhanced schema: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def migrate_existing_games(self) -> None:
        """Migrate existing games data to enhanced_games table."""
        conn = sqlite3.connect(self.main_db_path)
        cursor = conn.cursor()
        
        try:
            # Check if enhanced_games table has data
            cursor.execute("SELECT COUNT(*) FROM enhanced_games")
            count = cursor.fetchone()[0]
            
            if count > 0:
                logger.info("Enhanced games table already has data, skipping migration")
                return
            
            # Migrate from existing games table
            cursor.execute('''
                INSERT INTO enhanced_games (
                    nfl_game_id, season, week, home_team, away_team, 
                    home_score, away_score, home_win, game_date, completed
                )
                SELECT 
                    'legacy_' || id as nfl_game_id,
                    season, week, home_team, away_team,
                    home_score, away_score, home_win, 
                    CASE 
                        WHEN game_date IS NOT NULL THEN datetime(game_date)
                        ELSE NULL 
                    END as game_date,
                    completed
                FROM games
            ''')
            
            conn.commit()
            logger.info(f"Migrated {cursor.rowcount} games to enhanced_games table")
            
        except Exception as e:
            logger.error(f"Error migrating existing games: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def migrate_action_network_data(self) -> None:
        """Migrate Action Network data from stats database to main database."""
        try:
            # Connect to both databases
            main_conn = sqlite3.connect(self.main_db_path)
            stats_conn = sqlite3.connect(self.stats_db_path)
            
            # 1. Migrate experts
            experts_df = pd.read_sql_query("SELECT * FROM action_network_experts", stats_conn)
            if not experts_df.empty:
                experts_df = experts_df.rename(columns={'an_expert_id': 'expert_id'})
                experts_df.to_sql('experts', main_conn, if_exists='append', index=False)
                logger.info(f"Migrated {len(experts_df)} experts")
            
            # 2. Migrate expert performance
            perf_df = pd.read_sql_query("SELECT * FROM action_network_expert_performance", stats_conn)
            if not perf_df.empty:
                perf_df.to_sql('expert_performance', main_conn, if_exists='append', index=False)
                logger.info(f"Migrated {len(perf_df)} expert performance records")
            
            # 3. Migrate expert picks
            picks_df = pd.read_sql_query("SELECT * FROM action_network_picks", stats_conn)
            if not picks_df.empty:
                picks_df = picks_df.rename(columns={'an_pick_id': 'pick_id'})
                picks_df.to_sql('expert_picks', main_conn, if_exists='append', index=False)
                logger.info(f"Migrated {len(picks_df)} expert picks")
            
            main_conn.commit()
            logger.info("Action Network data migration completed")
            
        except Exception as e:
            logger.error(f"Error migrating Action Network data: {e}")
            raise
        finally:
            main_conn.close()
            stats_conn.close()
    
    def load_nfl_teams_data(self) -> None:
        """Load comprehensive NFL teams data."""
        conn = sqlite3.connect(self.main_db_path)
        cursor = conn.cursor()
        
        try:
            # Check if teams table has data
            cursor.execute("SELECT COUNT(*) FROM teams")
            count = cursor.fetchone()[0]
            
            if count > 0:
                logger.info("Teams table already has data, skipping load")
                return
            
            # NFL teams data
            teams_data = [
                ('KC', 'Kansas City Chiefs', 'Kansas City', 'Chiefs', 'AFC', 'West', 'Arrowhead Stadium', 'grass', False, 'CST'),
                ('BUF', 'Buffalo Bills', 'Buffalo', 'Bills', 'AFC', 'East', 'Highmark Stadium', 'grass', False, 'EST'),
                ('MIA', 'Miami Dolphins', 'Miami', 'Dolphins', 'AFC', 'East', 'Hard Rock Stadium', 'grass', False, 'EST'),
                ('NE', 'New England Patriots', 'New England', 'Patriots', 'AFC', 'East', 'Gillette Stadium', 'grass', False, 'EST'),
                ('NYJ', 'New York Jets', 'New York', 'Jets', 'AFC', 'East', 'MetLife Stadium', 'grass', False, 'EST'),
                ('BAL', 'Baltimore Ravens', 'Baltimore', 'Ravens', 'AFC', 'North', 'M&T Bank Stadium', 'grass', False, 'EST'),
                ('CIN', 'Cincinnati Bengals', 'Cincinnati', 'Bengals', 'AFC', 'North', 'Paycor Stadium', 'grass', False, 'EST'),
                ('CLE', 'Cleveland Browns', 'Cleveland', 'Browns', 'AFC', 'North', 'FirstEnergy Stadium', 'grass', False, 'EST'),
                ('PIT', 'Pittsburgh Steelers', 'Pittsburgh', 'Steelers', 'AFC', 'North', 'Heinz Field', 'grass', False, 'EST'),
                ('HOU', 'Houston Texans', 'Houston', 'Texans', 'AFC', 'South', 'NRG Stadium', 'grass', True, 'CST'),
                ('IND', 'Indianapolis Colts', 'Indianapolis', 'Colts', 'AFC', 'South', 'Lucas Oil Stadium', 'grass', True, 'EST'),
                ('JAX', 'Jacksonville Jaguars', 'Jacksonville', 'Jaguars', 'AFC', 'South', 'TIAA Bank Field', 'grass', False, 'EST'),
                ('TEN', 'Tennessee Titans', 'Tennessee', 'Titans', 'AFC', 'South', 'Nissan Stadium', 'grass', False, 'CST'),
                ('DEN', 'Denver Broncos', 'Denver', 'Broncos', 'AFC', 'West', 'Empower Field at Mile High', 'grass', False, 'MST'),
                ('LAC', 'Los Angeles Chargers', 'Los Angeles', 'Chargers', 'AFC', 'West', 'SoFi Stadium', 'grass', False, 'PST'),
                ('LV', 'Las Vegas Raiders', 'Las Vegas', 'Raiders', 'AFC', 'West', 'Allegiant Stadium', 'grass', True, 'PST'),
                ('DAL', 'Dallas Cowboys', 'Dallas', 'Cowboys', 'NFC', 'East', 'AT&T Stadium', 'grass', True, 'CST'),
                ('NYG', 'New York Giants', 'New York', 'Giants', 'NFC', 'East', 'MetLife Stadium', 'grass', False, 'EST'),
                ('PHI', 'Philadelphia Eagles', 'Philadelphia', 'Eagles', 'NFC', 'East', 'Lincoln Financial Field', 'grass', False, 'EST'),
                ('WAS', 'Washington Commanders', 'Washington', 'Commanders', 'NFC', 'East', 'FedExField', 'grass', False, 'EST'),
                ('CHI', 'Chicago Bears', 'Chicago', 'Bears', 'NFC', 'North', 'Soldier Field', 'grass', False, 'CST'),
                ('DET', 'Detroit Lions', 'Detroit', 'Lions', 'NFC', 'North', 'Ford Field', 'grass', True, 'EST'),
                ('GB', 'Green Bay Packers', 'Green Bay', 'Packers', 'NFC', 'North', 'Lambeau Field', 'grass', False, 'CST'),
                ('MIN', 'Minnesota Vikings', 'Minneapolis', 'Vikings', 'NFC', 'North', 'U.S. Bank Stadium', 'grass', True, 'CST'),
                ('ATL', 'Atlanta Falcons', 'Atlanta', 'Falcons', 'NFC', 'South', 'Mercedes-Benz Stadium', 'grass', True, 'EST'),
                ('CAR', 'Carolina Panthers', 'Carolina', 'Panthers', 'NFC', 'South', 'Bank of America Stadium', 'grass', False, 'EST'),
                ('NO', 'New Orleans Saints', 'New Orleans', 'Saints', 'NFC', 'South', 'Caesars Superdome', 'grass', True, 'CST'),
                ('TB', 'Tampa Bay Buccaneers', 'Tampa Bay', 'Buccaneers', 'NFC', 'South', 'Raymond James Stadium', 'grass', False, 'EST'),
                ('ARI', 'Arizona Cardinals', 'Arizona', 'Cardinals', 'NFC', 'West', 'State Farm Stadium', 'grass', True, 'MST'),
                ('LAR', 'Los Angeles Rams', 'Los Angeles', 'Rams', 'NFC', 'West', 'SoFi Stadium', 'grass', False, 'PST'),
                ('SF', 'San Francisco 49ers', 'San Francisco', '49ers', 'NFC', 'West', 'Levi\'s Stadium', 'grass', False, 'PST'),
                ('SEA', 'Seattle Seahawks', 'Seattle', 'Seahawks', 'NFC', 'West', 'Lumen Field', 'grass', False, 'PST')
            ]
            
            cursor.executemany('''
                INSERT INTO teams (team_code, team_name, city, mascot, conference, division, stadium, surface, dome, timezone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', teams_data)
            
            conn.commit()
            logger.info(f"Loaded {len(teams_data)} NFL teams")
            
        except Exception as e:
            logger.error(f"Error loading NFL teams data: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def run_migration(self) -> None:
        """Run the complete migration process."""
        logger.info("Starting database migration...")
        
        try:
            # Create backup
            self.create_backup()
            
            # Create enhanced schema
            self.create_enhanced_schema()
            
            # Migrate existing data
            self.migrate_existing_games()
            self.migrate_action_network_data()
            self.load_nfl_teams_data()
            
            logger.info("Database migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

def main():
    """Main function to run migration."""
    migration = DatabaseMigration()
    migration.run_migration()

if __name__ == "__main__":
    main()
