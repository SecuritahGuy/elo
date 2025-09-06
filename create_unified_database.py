#!/usr/bin/env python3
"""
Create Unified Multi-Sport Database
Creates the unified database schema for SportsEdge supporting multiple sports
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedDatabaseCreator:
    """Creates the unified multi-sport database schema."""
    
    def __init__(self, db_path: str = "sportsedge_unified.db"):
        self.db_path = db_path
        self.backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_database(self) -> None:
        """Create the unified database with all tables."""
        logger.info(f"Creating unified database: {self.db_path}")
        
        # Create backup if database exists
        if Path(self.db_path).exists():
            backup_path = f"{self.db_path}.backup_{self.backup_suffix}"
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create all tables
            self._create_sports_tables(cursor)
            self._create_teams_tables(cursor)
            self._create_games_tables(cursor)
            self._create_odds_tables(cursor)
            self._create_expert_tables(cursor)
            self._create_rating_tables(cursor)
            self._create_performance_tables(cursor)
            self._create_live_tables(cursor)
            
            # Create indexes for performance
            self._create_indexes(cursor)
            
            # Insert initial data
            self._insert_initial_data(cursor)
            
            conn.commit()
            logger.info("Unified database created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _create_sports_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create sports, leagues, and seasons tables."""
        
        # Sports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_code TEXT UNIQUE NOT NULL,
                sport_name TEXT NOT NULL,
                sport_type TEXT NOT NULL,
                season_structure TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Leagues table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leagues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_id INTEGER NOT NULL,
                league_code TEXT UNIQUE NOT NULL,
                league_name TEXT NOT NULL,
                conference TEXT,
                division TEXT,
                level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sport_id) REFERENCES sports(id)
            )
        ''')
        
        # Seasons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_id INTEGER NOT NULL,
                season_year INTEGER NOT NULL,
                season_name TEXT,
                start_date DATE,
                end_date DATE,
                playoff_start_date DATE,
                championship_date DATE,
                status TEXT DEFAULT 'upcoming',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sport_id) REFERENCES sports(id),
                UNIQUE(sport_id, season_year)
            )
        ''')
    
    def _create_teams_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create teams table."""
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_id INTEGER NOT NULL,
                league_id INTEGER,
                team_code TEXT NOT NULL,
                team_name TEXT NOT NULL,
                city TEXT NOT NULL,
                mascot TEXT NOT NULL,
                abbreviation TEXT,
                conference TEXT,
                division TEXT,
                founded_year INTEGER,
                home_venue TEXT,
                venue_capacity INTEGER,
                venue_surface TEXT,
                venue_dome BOOLEAN,
                timezone TEXT,
                colors JSON,
                logo_url TEXT,
                website_url TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sport_id) REFERENCES sports(id),
                FOREIGN KEY (league_id) REFERENCES leagues(id),
                UNIQUE(sport_id, team_code)
            )
        ''')
    
    def _create_games_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create games table."""
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_id INTEGER NOT NULL,
                season_id INTEGER NOT NULL,
                league_id INTEGER,
                external_game_id TEXT,
                game_type TEXT NOT NULL,
                round TEXT,
                week INTEGER,
                home_team_id INTEGER NOT NULL,
                away_team_id INTEGER NOT NULL,
                game_date TIMESTAMP,
                game_time_local TEXT,
                game_time_utc TIMESTAMP,
                venue TEXT,
                venue_city TEXT,
                venue_state TEXT,
                weather_condition TEXT,
                temperature INTEGER,
                wind_speed INTEGER,
                wind_direction TEXT,
                humidity INTEGER,
                precipitation TEXT,
                attendance INTEGER,
                home_score INTEGER,
                away_score INTEGER,
                home_win BOOLEAN,
                game_status TEXT DEFAULT 'scheduled',
                quarter INTEGER,
                time_remaining TEXT,
                possession TEXT,
                down INTEGER,
                distance INTEGER,
                yard_line INTEGER,
                red_zone BOOLEAN,
                home_rest_days INTEGER,
                away_rest_days INTEGER,
                home_win_prob REAL,
                away_win_prob REAL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sport_id) REFERENCES sports(id),
                FOREIGN KEY (season_id) REFERENCES seasons(id),
                FOREIGN KEY (league_id) REFERENCES leagues(id),
                FOREIGN KEY (home_team_id) REFERENCES teams(id),
                FOREIGN KEY (away_team_id) REFERENCES teams(id)
            )
        ''')
    
    def _create_odds_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create odds table."""
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds (
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
                prop_name TEXT,
                prop_value REAL,
                prop_odds INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')
    
    def _create_expert_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create expert-related tables."""
        
        # Experts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_expert_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                username TEXT,
                display_name TEXT,
                is_verified BOOLEAN DEFAULT FALSE,
                is_expert BOOLEAN DEFAULT TRUE,
                followers INTEGER DEFAULT 0,
                bio TEXT,
                avatar_url TEXT,
                website_url TEXT,
                social_media JSON,
                specialties JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Expert performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expert_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expert_id INTEGER NOT NULL,
                sport_id INTEGER NOT NULL,
                window_period TEXT NOT NULL,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                pushes INTEGER DEFAULT 0,
                total_picks INTEGER DEFAULT 0,
                units_net REAL DEFAULT 0.0,
                roi REAL DEFAULT 0.0,
                win_percentage REAL DEFAULT 0.0,
                win_streak_type TEXT,
                win_streak_value INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                worst_streak INTEGER DEFAULT 0,
                avg_units_per_pick REAL DEFAULT 0.0,
                confidence_score REAL DEFAULT 0.0,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (expert_id) REFERENCES experts(id),
                FOREIGN KEY (sport_id) REFERENCES sports(id)
            )
        ''')
        
        # Expert picks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expert_picks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_pick_id TEXT UNIQUE NOT NULL,
                expert_id INTEGER NOT NULL,
                game_id INTEGER NOT NULL,
                sport_id INTEGER NOT NULL,
                pick_type TEXT NOT NULL,
                play_description TEXT NOT NULL,
                value REAL,
                odds INTEGER,
                units REAL,
                units_net REAL,
                money REAL,
                money_net REAL,
                result TEXT,
                confidence_level INTEGER,
                reasoning TEXT,
                pick_created_at TIMESTAMP,
                starts_at TIMESTAMP,
                ends_at TIMESTAMP,
                settled_at TIMESTAMP,
                trend TEXT,
                social_likes INTEGER DEFAULT 0,
                social_copies INTEGER DEFAULT 0,
                social_comments INTEGER DEFAULT 0,
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (expert_id) REFERENCES experts(id),
                FOREIGN KEY (game_id) REFERENCES games(id),
                FOREIGN KEY (sport_id) REFERENCES sports(id)
            )
        ''')
    
    def _create_rating_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create rating and prediction tables."""
        
        # Team ratings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_ratings (
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
                home_record TEXT,
                away_record TEXT,
                division_record TEXT,
                conference_record TEXT,
                strength_of_schedule REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id),
                FOREIGN KEY (sport_id) REFERENCES sports(id),
                FOREIGN KEY (season_id) REFERENCES seasons(id)
            )
        ''')
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                sport_id INTEGER NOT NULL,
                prediction_type TEXT NOT NULL,
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
                features_used JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id),
                FOREIGN KEY (sport_id) REFERENCES sports(id),
                FOREIGN KEY (home_team_id) REFERENCES teams(id),
                FOREIGN KEY (away_team_id) REFERENCES teams(id),
                FOREIGN KEY (predicted_winner_id) REFERENCES teams(id)
            )
        ''')
    
    def _create_performance_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create performance tracking tables."""
        
        # Backtest results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
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
            )
        ''')
    
    def _create_live_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create live data tables."""
        
        # Live updates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                update_type TEXT NOT NULL,
                update_data JSON NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')
    
    def _create_indexes(self, cursor: sqlite3.Cursor) -> None:
        """Create performance indexes."""
        
        indexes = [
            # Sports and leagues
            "CREATE INDEX IF NOT EXISTS idx_sports_code ON sports(sport_code)",
            "CREATE INDEX IF NOT EXISTS idx_leagues_sport_id ON leagues(sport_id)",
            "CREATE INDEX IF NOT EXISTS idx_seasons_sport_year ON seasons(sport_id, season_year)",
            
            # Teams
            "CREATE INDEX IF NOT EXISTS idx_teams_sport_code ON teams(sport_id, team_code)",
            "CREATE INDEX IF NOT EXISTS idx_teams_league ON teams(league_id)",
            "CREATE INDEX IF NOT EXISTS idx_teams_active ON teams(active)",
            
            # Games
            "CREATE INDEX IF NOT EXISTS idx_games_sport_season ON games(sport_id, season_id)",
            "CREATE INDEX IF NOT EXISTS idx_games_teams ON games(home_team_id, away_team_id)",
            "CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date)",
            "CREATE INDEX IF NOT EXISTS idx_games_status ON games(game_status)",
            "CREATE INDEX IF NOT EXISTS idx_games_external_id ON games(external_game_id)",
            
            # Odds
            "CREATE INDEX IF NOT EXISTS idx_odds_game_id ON odds(game_id)",
            "CREATE INDEX IF NOT EXISTS idx_odds_sportsbook ON odds(sportsbook)",
            "CREATE INDEX IF NOT EXISTS idx_odds_type ON odds(odds_type)",
            
            # Experts
            "CREATE INDEX IF NOT EXISTS idx_experts_external_id ON experts(external_expert_id)",
            "CREATE INDEX IF NOT EXISTS idx_expert_performance_expert_sport ON expert_performance(expert_id, sport_id)",
            "CREATE INDEX IF NOT EXISTS idx_expert_picks_expert_game ON expert_picks(expert_id, game_id)",
            "CREATE INDEX IF NOT EXISTS idx_expert_picks_sport ON expert_picks(sport_id)",
            "CREATE INDEX IF NOT EXISTS idx_expert_picks_result ON expert_picks(result)",
            
            # Ratings and predictions
            "CREATE INDEX IF NOT EXISTS idx_team_ratings_team_season ON team_ratings(team_id, season_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_ratings_sport_season ON team_ratings(sport_id, season_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_game ON predictions(game_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_sport ON predictions(sport_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type)",
            
            # Performance
            "CREATE INDEX IF NOT EXISTS idx_backtest_sport ON backtest_results(sport_id)",
            "CREATE INDEX IF NOT EXISTS idx_backtest_model ON backtest_results(model_name)",
            
            # Live updates
            "CREATE INDEX IF NOT EXISTS idx_live_updates_game ON live_updates(game_id)",
            "CREATE INDEX IF NOT EXISTS idx_live_updates_type ON live_updates(update_type)",
            "CREATE INDEX IF NOT EXISTS idx_live_updates_timestamp ON live_updates(timestamp)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def _insert_initial_data(self, cursor: sqlite3.Cursor) -> None:
        """Insert initial sports and league data."""
        
        # Insert sports
        sports_data = [
            ('nfl', 'National Football League', 'football', 'regular_playoffs'),
            ('nba', 'National Basketball Association', 'basketball', 'regular_playoffs'),
            ('mlb', 'Major League Baseball', 'baseball', 'regular_playoffs'),
            ('nhl', 'National Hockey League', 'hockey', 'regular_playoffs'),
            ('ncaaf', 'NCAA Football', 'football', 'regular_playoffs'),
            ('ncaab', 'NCAA Basketball', 'basketball', 'tournament')
        ]
        
        cursor.executemany('''
            INSERT INTO sports (sport_code, sport_name, sport_type, season_structure)
            VALUES (?, ?, ?, ?)
        ''', sports_data)
        
        # Insert NFL leagues
        cursor.execute("SELECT id FROM sports WHERE sport_code = 'nfl'")
        nfl_id = cursor.fetchone()[0]
        
        nfl_leagues = [
            (nfl_id, 'nfl', 'National Football League', None, None, 'professional'),
            (nfl_id, 'afc', 'American Football Conference', 'AFC', None, 'professional'),
            (nfl_id, 'nfc', 'National Football Conference', 'NFC', None, 'professional'),
            (nfl_id, 'afc_east', 'AFC East', 'AFC', 'East', 'professional'),
            (nfl_id, 'afc_west', 'AFC West', 'AFC', 'West', 'professional'),
            (nfl_id, 'afc_north', 'AFC North', 'AFC', 'North', 'professional'),
            (nfl_id, 'afc_south', 'AFC South', 'AFC', 'South', 'professional'),
            (nfl_id, 'nfc_east', 'NFC East', 'NFC', 'East', 'professional'),
            (nfl_id, 'nfc_west', 'NFC West', 'NFC', 'West', 'professional'),
            (nfl_id, 'nfc_north', 'NFC North', 'NFC', 'North', 'professional'),
            (nfl_id, 'nfc_south', 'NFC South', 'NFC', 'South', 'professional')
        ]
        
        cursor.executemany('''
            INSERT INTO leagues (sport_id, league_code, league_name, conference, division, level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', nfl_leagues)
        
        # Insert recent NFL seasons
        current_year = datetime.now().year
        nfl_seasons = []
        for year in range(2020, current_year + 2):
            nfl_seasons.append((
                nfl_id, year, str(year), 
                f"{year}-09-01", f"{year+1}-02-01",
                f"{year+1}-01-01", f"{year+1}-02-01",
                'completed' if year < current_year else 'active' if year == current_year else 'upcoming'
            ))
        
        cursor.executemany('''
            INSERT INTO seasons (sport_id, season_year, season_name, start_date, end_date, 
                               playoff_start_date, championship_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', nfl_seasons)
        
        logger.info("Initial data inserted successfully")

def main():
    """Main function to create unified database."""
    creator = UnifiedDatabaseCreator()
    creator.create_database()
    print("✅ Unified database created successfully!")
    print(f"Database location: {creator.db_path}")

if __name__ == "__main__":
    main()
