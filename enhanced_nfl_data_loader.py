#!/usr/bin/env python3
"""
Enhanced NFL Data Loader
Loads comprehensive NFL schedule data and integrates with enhanced database schema
"""

import sqlite3
import pandas as pd
import nfl_data_py as nfl
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import requests
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedNFLDataLoader:
    """Enhanced NFL data loader with comprehensive schedule and odds integration."""
    
    def __init__(self, db_path: str = "nfl_elo.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def load_nfl_schedules(self, years: List[int]) -> pd.DataFrame:
        """Load comprehensive NFL schedule data."""
        logger.info(f"Loading NFL schedules for years: {years}")
        
        try:
            # Load schedules from nfl-data-py
            schedules_df = nfl.import_schedules(years)
            
            # Enhance with additional data
            enhanced_schedules = self._enhance_schedule_data(schedules_df)
            
            logger.info(f"Loaded {len(enhanced_schedules)} games")
            return enhanced_schedules
            
        except Exception as e:
            logger.error(f"Error loading NFL schedules: {e}")
            raise
    
    def _enhance_schedule_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhance schedule data with additional fields."""
        enhanced_df = df.copy()
        
        # Add game type classification
        enhanced_df['game_type'] = enhanced_df['week'].apply(self._classify_game_type)
        
        # Add game status
        enhanced_df['game_status'] = enhanced_df.apply(self._determine_game_status, axis=1)
        
        # Add rest days calculation
        enhanced_df['home_rest_days'] = enhanced_df['home_rest'].fillna(7)
        enhanced_df['away_rest_days'] = enhanced_df['away_rest'].fillna(7)
        
        # Add basic weather data (placeholder - would need real weather API)
        enhanced_df['weather_condition'] = 'Unknown'
        enhanced_df['temperature'] = None
        enhanced_df['wind_speed'] = None
        enhanced_df['precipitation'] = 'Unknown'
        
        # Add stadium information (placeholder - would need stadium database)
        enhanced_df['stadium'] = 'Unknown'
        enhanced_df['surface'] = 'grass'  # Default
        enhanced_df['dome'] = False  # Default
        
        # Add basic odds data (placeholder - would need odds API)
        enhanced_df['spread'] = None
        enhanced_df['total'] = None
        enhanced_df['home_moneyline'] = None
        enhanced_df['away_moneyline'] = None
        
        return enhanced_df
    
    def _classify_game_type(self, week: int) -> str:
        """Classify game type based on week."""
        if week <= 18:
            return 'REG'
        elif week == 19:
            return 'WC'  # Wild Card
        elif week == 20:
            return 'DIV'  # Divisional
        elif week == 21:
            return 'CONF'  # Conference Championship
        elif week == 22:
            return 'SB'  # Super Bowl
        else:
            return 'REG'
    
    def _determine_game_status(self, row: pd.Series) -> str:
        """Determine game status based on available data."""
        if pd.notna(row.get('home_score')) and pd.notna(row.get('away_score')):
            return 'final'
        elif pd.notna(row.get('gameday')):
            game_date = pd.to_datetime(row['gameday'])
            if game_date < datetime.now():
                return 'in_progress'  # Assume in progress if past date but no score
            else:
                return 'scheduled'
        else:
            return 'scheduled'
    
    def load_odds_data(self, game_ids: List[int]) -> pd.DataFrame:
        """Load odds data for specific games (placeholder implementation)."""
        logger.info(f"Loading odds data for {len(game_ids)} games")
        
        # This would integrate with a real odds API
        # For now, return empty DataFrame
        odds_columns = [
            'game_id', 'sportsbook', 'odds_type', 'home_value', 'away_value',
            'total_value', 'home_odds', 'away_odds', 'over_odds', 'under_odds'
        ]
        
        return pd.DataFrame(columns=odds_columns)
    
    def store_enhanced_games(self, games_df: pd.DataFrame) -> None:
        """Store enhanced games data in database."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Prepare data for database insertion
            db_data = []
            for _, game in games_df.iterrows():
                db_data.append({
                    'nfl_game_id': str(game.get('game_id', '')),
                    'season': int(game.get('season', 0)),
                    'week': int(game.get('week', 0)),
                    'game_type': game.get('game_type', 'REG'),
                    'home_team': game.get('home_team', ''),
                    'away_team': game.get('away_team', ''),
                    'home_score': game.get('home_score'),
                    'away_score': game.get('away_score'),
                    'home_win': game.get('result') == 1 if pd.notna(game.get('result')) else None,
                    'game_date': game.get('gameday'),
                    'game_time_et': None,  # Would need to parse from gameday
                    'game_status': game.get('game_status', 'scheduled'),
                    'quarter': None,
                    'time_remaining': None,
                    'possession': None,
                    'down': None,
                    'distance': None,
                    'yard_line': None,
                    'red_zone': False,
                    'weather_condition': game.get('weather_condition'),
                    'temperature': game.get('temperature'),
                    'wind_speed': game.get('wind_speed'),
                    'wind_direction': None,
                    'humidity': None,
                    'precipitation': game.get('precipitation'),
                    'stadium': game.get('stadium'),
                    'surface': game.get('surface'),
                    'dome': game.get('dome'),
                    'attendance': None,
                    'home_rest_days': int(game.get('home_rest_days', 7)),
                    'away_rest_days': int(game.get('away_rest_days', 7)),
                    'home_win_prob': None,
                    'away_win_prob': None,
                    'spread': game.get('spread'),
                    'total': game.get('total'),
                    'home_moneyline': game.get('home_moneyline'),
                    'away_moneyline': game.get('away_moneyline'),
                    'completed': game.get('game_status') == 'final'
                })
            
            # Insert data
            if db_data:
                df_to_insert = pd.DataFrame(db_data)
                df_to_insert.to_sql('enhanced_games', conn, if_exists='append', index=False)
                logger.info(f"Stored {len(db_data)} enhanced games")
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error storing enhanced games: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def load_and_store_nfl_data(self, years: List[int]) -> Dict[str, Any]:
        """Load and store comprehensive NFL data."""
        results = {
            'games_loaded': 0,
            'games_stored': 0,
            'errors': []
        }
        
        try:
            # Load NFL schedules
            games_df = self.load_nfl_schedules(years)
            results['games_loaded'] = len(games_df)
            
            # Store in database
            self.store_enhanced_games(games_df)
            results['games_stored'] = len(games_df)
            
            logger.info(f"Successfully loaded and stored {len(games_df)} games")
            
        except Exception as e:
            error_msg = f"Error in load_and_store_nfl_data: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results

class OddsDataLoader:
    """Loader for betting odds data."""
    
    def __init__(self, db_path: str = "nfl_elo.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def load_odds_for_games(self, game_ids: List[int]) -> pd.DataFrame:
        """Load odds data for specific games."""
        logger.info(f"Loading odds for {len(game_ids)} games")
        
        # This would integrate with real odds APIs like:
        # - The Odds API
        # - SportsData.io
        # - ESPN API
        
        # For now, return mock data
        mock_odds = []
        for game_id in game_ids:
            mock_odds.extend([
                {
                    'game_id': game_id,
                    'sportsbook': 'DraftKings',
                    'odds_type': 'spread',
                    'home_value': -3.5,
                    'away_value': 3.5,
                    'total_value': None,
                    'home_odds': -110,
                    'away_odds': -110,
                    'over_odds': None,
                    'under_odds': None
                },
                {
                    'game_id': game_id,
                    'sportsbook': 'DraftKings',
                    'odds_type': 'total',
                    'home_value': None,
                    'away_value': None,
                    'total_value': 47.5,
                    'home_odds': None,
                    'away_odds': None,
                    'over_odds': -110,
                    'under_odds': -110
                },
                {
                    'game_id': game_id,
                    'sportsbook': 'DraftKings',
                    'odds_type': 'moneyline',
                    'home_value': None,
                    'away_value': None,
                    'total_value': None,
                    'home_odds': -150,
                    'away_odds': 130,
                    'over_odds': None,
                    'under_odds': None
                }
            ])
        
        return pd.DataFrame(mock_odds)
    
    def store_odds_data(self, odds_df: pd.DataFrame) -> None:
        """Store odds data in database."""
        conn = sqlite3.connect(self.db_path)
        
        try:
            odds_df.to_sql('game_odds', conn, if_exists='append', index=False)
            conn.commit()
            logger.info(f"Stored {len(odds_df)} odds records")
            
        except Exception as e:
            logger.error(f"Error storing odds data: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

def main():
    """Main function to test the enhanced data loader."""
    # Test the enhanced data loader
    loader = EnhancedNFLDataLoader()
    
    # Load data for 2024 and 2025
    results = loader.load_and_store_nfl_data([2024, 2025])
    print(f"Results: {results}")
    
    # Test odds loader
    odds_loader = OddsDataLoader()
    
    # Get some game IDs from the database
    conn = sqlite3.connect("nfl_elo.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM enhanced_games LIMIT 5")
    game_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if game_ids:
        odds_df = odds_loader.load_odds_for_games(game_ids)
        odds_loader.store_odds_data(odds_df)
        print(f"Loaded and stored odds for {len(game_ids)} games")

if __name__ == "__main__":
    main()
