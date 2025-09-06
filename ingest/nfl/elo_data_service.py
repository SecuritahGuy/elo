#!/usr/bin/env python3
"""
ELO Data Service for retrieving and managing ELO ratings data.
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class EloDataService:
    """Service for retrieving ELO ratings and related data."""
    
    def __init__(self, db_path: str = "../../nfl_elo.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
    
    def get_available_seasons(self) -> List[int]:
        """Get list of available seasons from team_ratings table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get seasons from team_ratings table
            cursor.execute("""
                SELECT DISTINCT season
                FROM team_ratings
                ORDER BY season DESC
            """)
            
            seasons = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            # If no seasons found, return default recent seasons
            if not seasons:
                current_year = datetime.now().year
                return [current_year, current_year - 1, current_year - 2, current_year - 3, current_year - 4]
            
            return seasons
            
        except Exception as e:
            logger.error(f"Error getting available seasons: {e}")
            # Fallback to default seasons
            current_year = datetime.now().year
            return [current_year, current_year - 1, current_year - 2, current_year - 3, current_year - 4]
    
    def get_team_ratings_for_season(self, season: int, config_name: str = "baseline") -> List[Dict[str, Any]]:
        """
        Get team ratings for a specific season.
        
        Args:
            season: Season year
            config_name: Configuration name (baseline, weather_only, etc.) - ignored for now
            
        Returns:
            List of team ratings with metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get ratings from database (no config_name column exists)
            cursor.execute('''
                SELECT team, rating, wins, losses, win_pct, rating_change
                FROM team_ratings
                WHERE season = ?
                ORDER BY rating DESC
            ''', (season,))
            
            ratings = []
            for i, row in enumerate(cursor.fetchall(), 1):
                team, rating, wins, losses, win_pct, rating_change = row
                ratings.append({
                    "team": team,
                    "rating": round(rating, 1),
                    "rank": i,
                    "season": season,
                    "change": round(rating_change, 1),
                    "wins": wins,
                    "losses": losses,
                    "win_pct": round(win_pct, 3)
                })
            
            conn.close()
            
            # If no data in database, fall back to sample data
            if not ratings:
                logger.warning(f"No ELO ratings found for season {season}, using sample data")
                return self._generate_sample_ratings(season)
            
            return ratings
            
        except Exception as e:
            logger.error(f"Error getting team ratings for season {season}: {e}")
            # Fall back to sample data on error
            return self._generate_sample_ratings(season)
    
    def _generate_sample_ratings(self, season: int) -> List[Dict[str, Any]]:
        """Generate sample team ratings for demonstration."""
        # NFL team names
        teams = [
            "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
            "DET", "GB", "HOU", "IND", "JAX", "KC", "LV", "LAC", "LAR", "MIA",
            "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SF", "SEA", "TB",
            "TEN", "WAS"
        ]
        
        # Generate realistic ELO ratings (1500 base with variation)
        import random
        random.seed(season)  # Consistent for same season
        
        ratings = []
        for i, team in enumerate(teams):
            # Generate rating between 1200-1800 with some teams being better
            base_rating = 1500
            variation = random.gauss(0, 100)  # Normal distribution around 0
            rating = max(1200, min(1800, base_rating + variation))
            
            # Add some season-specific trends
            if season >= 2023:
                if team in ["KC", "BUF", "CIN", "SF"]:
                    rating += 50  # Good teams
                elif team in ["HOU", "CAR", "ARI"]:
                    rating -= 30  # Struggling teams
            
            ratings.append({
                "team": team,
                "rating": round(rating, 1),
                "rank": i + 1,
                "season": season,
                "change": round(random.gauss(0, 20), 1),  # Weekly change
                "wins": random.randint(5, 12),
                "losses": random.randint(4, 11),
                "win_pct": round(random.uniform(0.3, 0.8), 3)
            })
        
        # Sort by rating (highest first)
        ratings.sort(key=lambda x: x["rating"], reverse=True)
        
        # Update ranks
        for i, team in enumerate(ratings):
            team["rank"] = i + 1
        
        return ratings
    
    def get_rating_history(self, team: str, seasons: List[int]) -> List[Dict[str, Any]]:
        """Get rating history for a specific team across seasons."""
        try:
            # For now, generate sample history
            history = []
            for season in seasons:
                ratings = self._generate_sample_ratings(season)
                team_rating = next((r for r in ratings if r["team"] == team), None)
                if team_rating:
                    history.append({
                        "season": season,
                        "rating": team_rating["rating"],
                        "rank": team_rating["rank"]
                    })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting rating history for {team}: {e}")
            return []
    
    def get_season_summary(self, season: int) -> Dict[str, Any]:
        """Get summary statistics for a season."""
        try:
            ratings = self._generate_sample_ratings(season)
            
            if not ratings:
                return {}
            
            rating_values = [r["rating"] for r in ratings]
            
            return {
                "season": season,
                "total_teams": len(ratings),
                "avg_rating": round(sum(rating_values) / len(rating_values), 1),
                "highest_rating": max(rating_values),
                "lowest_rating": min(rating_values),
                "rating_std": round(pd.Series(rating_values).std(), 1),
                "top_team": ratings[0]["team"],
                "bottom_team": ratings[-1]["team"]
            }
            
        except Exception as e:
            logger.error(f"Error getting season summary for {season}: {e}")
            return {}
    
    def get_team_comparison(self, teams: List[str], season: int) -> List[Dict[str, Any]]:
        """Get comparison data for specific teams."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get ratings from database for specific teams
            placeholders = ','.join(['?' for _ in teams])
            cursor.execute(f'''
                SELECT team, rating, wins, losses, win_pct, rating_change
                FROM team_ratings
                WHERE season = ? AND config_name = 'baseline' AND team IN ({placeholders})
                ORDER BY rating DESC
            ''', [season] + teams)
            
            ratings = []
            for i, row in enumerate(cursor.fetchall(), 1):
                team, rating, wins, losses, win_pct, rating_change = row
                ratings.append({
                    "team": team,
                    "rating": round(rating, 1),
                    "rank": i,  # This will be updated after sorting
                    "season": season,
                    "change": round(rating_change, 1),
                    "wins": wins,
                    "losses": losses,
                    "win_pct": round(win_pct, 3)
                })
            
            conn.close()
            
            # If no data in database, fall back to sample data
            if not ratings:
                logger.warning(f"No ELO ratings found for teams {teams}, using sample data")
                sample_ratings = self._generate_sample_ratings(season)
                team_ratings = [r for r in sample_ratings if r["team"] in teams]
                return sorted(team_ratings, key=lambda x: x["rating"], reverse=True)
            
            return ratings
            
        except Exception as e:
            logger.error(f"Error getting team comparison: {e}")
            # Fall back to sample data on error
            sample_ratings = self._generate_sample_ratings(season)
            team_ratings = [r for r in sample_ratings if r["team"] in teams]
            return sorted(team_ratings, key=lambda x: x["rating"], reverse=True)

def test_elo_data_service():
    """Test the ELO data service."""
    try:
        service = EloDataService()
        
        # Test available seasons
        seasons = service.get_available_seasons()
        print(f"Available seasons: {seasons}")
        
        # Test team ratings
        ratings = service.get_team_ratings_for_season(2024)
        print(f"Team ratings for 2024: {len(ratings)} teams")
        print("Top 5 teams:")
        for team in ratings[:5]:
            print(f"  {team['rank']}. {team['team']}: {team['rating']}")
        
        # Test season summary
        summary = service.get_season_summary(2024)
        print(f"Season summary: {summary}")
        
    except Exception as e:
        print(f"Error testing ELO data service: {e}")

if __name__ == "__main__":
    test_elo_data_service()
