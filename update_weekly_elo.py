#!/usr/bin/env python3
"""
Weekly ELO Update System - Updates team ratings based on new games played.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.nfl_elo.prediction_interface import NFLPredictionInterface
from models.nfl_elo.config import EloConfig
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class WeeklyEloUpdater:
    """Updates ELO ratings weekly based on new games played."""
    
    def __init__(self, db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        self.db_path = Path(db_path)
        self.config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75
        )
    
    def get_current_ratings(self, season: int) -> Dict[str, float]:
        """Get current ELO ratings for a season from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT team, rating FROM team_ratings 
                WHERE season = ? AND config_name = 'baseline'
                ORDER BY rating DESC
            ''', (season,))
            
            ratings = {team: rating for team, rating in cursor.fetchall()}
            conn.close()
            
            return ratings
            
        except Exception as e:
            logger.error(f"Error getting current ratings: {e}")
            return {}
    
    def get_games_for_week(self, season: int, week: int) -> pd.DataFrame:
        """Get games for a specific week."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT season, week, gameday, home_team, away_team, home_score, away_score, result
                FROM nfl_games_2025
                WHERE season = ? AND week = ?
                AND home_score IS NOT NULL AND away_score IS NOT NULL
                ORDER BY gameday
            '''
            
            games_df = pd.read_sql_query(query, conn, params=(season, week))
            conn.close()
            
            return games_df
            
        except Exception as e:
            logger.error(f"Error getting games for week {week}: {e}")
            return pd.DataFrame()
    
    def calculate_win_loss_records(self, season: int, through_week: int) -> Dict[str, Dict[str, int]]:
        """Calculate win/loss records for all teams through a specific week."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get all completed games through the specified week
            query = '''
                SELECT home_team, away_team, home_score, away_score
                FROM nfl_games_2025
                WHERE season = ? AND week <= ?
                AND home_score IS NOT NULL AND away_score IS NOT NULL
            '''
            
            games_df = pd.read_sql_query(query, conn, params=(season, through_week))
            conn.close()
            
            # Initialize records for all teams
            records = {}
            all_teams = set(games_df['home_team'].unique()) | set(games_df['away_team'].unique())
            
            for team in all_teams:
                records[team] = {'wins': 0, 'losses': 0, 'ties': 0}
            
            # Calculate records
            for _, game in games_df.iterrows():
                home_team = game['home_team']
                away_team = game['away_team']
                home_score = game['home_score']
                away_score = game['away_score']
                
                if home_score > away_score:
                    records[home_team]['wins'] += 1
                    records[away_team]['losses'] += 1
                elif away_score > home_score:
                    records[away_team]['wins'] += 1
                    records[home_team]['losses'] += 1
                else:
                    records[home_team]['ties'] += 1
                    records[away_team]['ties'] += 1
            
            return records
            
        except Exception as e:
            logger.error(f"Error calculating win/loss records: {e}")
            return {}
    
    def update_ratings_for_week(self, season: int, week: int) -> Dict[str, Dict[str, any]]:
        """Update ELO ratings for a specific week's games."""
        try:
            print(f"🔄 Updating ELO ratings for {season} Week {week}...")
            
            # Get current ratings
            current_ratings = self.get_current_ratings(season)
            if not current_ratings:
                print("❌ No current ratings found!")
                return {}
            
            # Get games for this week
            games_df = self.get_games_for_week(season, week)
            if games_df.empty:
                print(f"❌ No games found for {season} Week {week}")
                return {}
            
            print(f"📊 Found {len(games_df)} games for Week {week}")
            
            # Initialize new ratings
            new_ratings = current_ratings.copy()
            rating_changes = {}
            
            # Process each game
            for _, game in games_df.iterrows():
                home_team = game['home_team']
                away_team = game['away_team']
                home_score = game['home_score']
                away_score = game['away_score']
                
                # Get current ratings
                home_rating = new_ratings.get(home_team, 1500.0)
                away_rating = new_ratings.get(away_team, 1500.0)
                
                # Calculate ELO update
                home_change, away_change = self._calculate_elo_update(
                    home_rating, away_rating, home_score, away_score
                )
                
                # Update ratings
                new_ratings[home_team] = home_rating + home_change
                new_ratings[away_team] = away_rating + away_change
                
                # Track changes
                rating_changes[home_team] = home_change
                rating_changes[away_team] = away_change
                
                print(f"  {home_team} {home_score}-{away_score} {away_team}")
                print(f"    {home_team}: {home_rating:.1f} → {new_ratings[home_team]:.1f} ({home_change:+.1f})")
                print(f"    {away_team}: {away_rating:.1f} → {new_ratings[away_team]:.1f} ({away_change:+.1f})")
            
            # Calculate win/loss records
            records = self.calculate_win_loss_records(season, week)
            
            # Store updated ratings
            self._store_updated_ratings(season, new_ratings, rating_changes, records)
            
            return {
                'new_ratings': new_ratings,
                'rating_changes': rating_changes,
                'records': records,
                'games_processed': len(games_df)
            }
            
        except Exception as e:
            logger.error(f"Error updating ratings for week {week}: {e}")
            return {}
    
    def _calculate_elo_update(self, home_rating: float, away_rating: float, 
                            home_score: int, away_score: int) -> Tuple[float, float]:
        """Calculate ELO rating changes for a game."""
        # Calculate expected scores
        elo_diff = home_rating - away_rating + self.config.hfa_points
        expected_home = 1 / (1 + 10 ** (-elo_diff / 400))
        expected_away = 1 - expected_home
        
        # Determine actual results
        if home_score > away_score:
            actual_home = 1.0
            actual_away = 0.0
        elif away_score > home_score:
            actual_home = 0.0
            actual_away = 1.0
        else:
            actual_home = 0.5
            actual_away = 0.5
        
        # Calculate margin of victory multiplier
        margin = abs(home_score - away_score)
        mov_multiplier = 1.0
        if self.config.mov_enabled and margin > 0:
            mov_multiplier = (margin + 1) ** 0.8 / (0.001 * abs(elo_diff) + 2.2)
        
        # Calculate rating changes
        home_change = self.config.k * mov_multiplier * (actual_home - expected_home)
        away_change = self.config.k * mov_multiplier * (actual_away - expected_away)
        
        return home_change, away_change
    
    def _store_updated_ratings(self, season: int, new_ratings: Dict[str, float], 
                             rating_changes: Dict[str, float], records: Dict[str, Dict[str, int]]):
        """Store updated ratings in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update ratings for each team
            for team, rating in new_ratings.items():
                wins = records.get(team, {}).get('wins', 0)
                losses = records.get(team, {}).get('losses', 0)
                ties = records.get(team, {}).get('ties', 0)
                total_games = wins + losses + ties
                win_pct = wins / total_games if total_games > 0 else 0.0
                rating_change = rating_changes.get(team, 0.0)
                
                cursor.execute('''
                    UPDATE team_ratings 
                    SET rating = ?, wins = ?, losses = ?, win_pct = ?, rating_change = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE team = ? AND season = ? AND config_name = 'baseline'
                ''', (rating, wins, losses, win_pct, rating_change, team, season))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Updated ratings stored in database")
            
        except Exception as e:
            logger.error(f"Error storing updated ratings: {e}")

def main():
    """Main function to update ELO ratings for a specific week."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update ELO ratings for a specific week')
    parser.add_argument('--season', type=int, default=2025, help='Season year')
    parser.add_argument('--week', type=int, required=True, help='Week number')
    
    args = parser.parse_args()
    
    updater = WeeklyEloUpdater()
    result = updater.update_ratings_for_week(args.season, args.week)
    
    if result:
        print(f"\n🎉 Successfully updated ELO ratings for {args.season} Week {args.week}")
        print(f"📊 Processed {result['games_processed']} games")
        
        # Show top 5 teams
        sorted_teams = sorted(result['new_ratings'].items(), key=lambda x: x[1], reverse=True)
        print(f"\n🏆 Top 5 Teams After Week {args.week}:")
        for i, (team, rating) in enumerate(sorted_teams[:5], 1):
            change = result['rating_changes'].get(team, 0.0)
            print(f"{i:2d}. {team}: {rating:.1f} ({change:+.1f})")
    else:
        print("❌ Failed to update ELO ratings")
        sys.exit(1)

if __name__ == "__main__":
    main()
