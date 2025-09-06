"""
ELO Projection Service
Projects ELO ratings for future weeks based on current ratings and historical trends
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ELOProjectionService:
    def __init__(self, db_path='nfl_elo.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the projected ELO ratings table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projected_elo_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL,
                season INTEGER NOT NULL,
                week INTEGER NOT NULL,
                projected_rating REAL NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                projection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                projection_method TEXT DEFAULT 'trend_based',
                UNIQUE(team, season, week)
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_projected_elo_team_season_week 
            ON projected_elo_ratings(team, season, week)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Projected ELO ratings table initialized")
    
    def get_current_elo_ratings(self, season: int) -> Dict[str, float]:
        """Get current ELO ratings for all teams in a season"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT team, rating 
            FROM team_ratings 
            WHERE season = ? AND week = (SELECT MAX(week) FROM team_ratings WHERE season = ?)
            ORDER BY rating DESC
        ''', (season, season))
        
        ratings = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        return ratings
    
    def get_team_elo_history(self, team: str, season: int, weeks_back: int = 4) -> List[Dict]:
        """Get recent ELO history for a team to calculate trends"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT week, rating, rating_change
            FROM team_ratings 
            WHERE team = ? AND season = ?
            ORDER BY week DESC
            LIMIT ?
        ''', (team, season, weeks_back))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'week': row[0],
                'rating': row[1],
                'change': row[2]
            })
        
        conn.close()
        return history
    
    def calculate_team_trend(self, team: str, season: int) -> Dict[str, float]:
        """Calculate ELO trend for a team based on recent performance"""
        history = self.get_team_elo_history(team, season, 4)
        
        if len(history) < 2:
            return {'trend': 0.0, 'volatility': 0.0, 'confidence': 0.5}
        
        # Calculate average weekly change
        changes = [h['change'] for h in history if h['change'] is not None]
        if not changes:
            return {'trend': 0.0, 'volatility': 0.0, 'confidence': 0.5}
        
        avg_change = sum(changes) / len(changes)
        
        # Calculate volatility (standard deviation of changes)
        variance = sum((c - avg_change) ** 2 for c in changes) / len(changes)
        volatility = variance ** 0.5
        
        # Calculate confidence based on consistency
        confidence = max(0.1, min(0.9, 1.0 - (volatility / 50.0)))
        
        return {
            'trend': avg_change,
            'volatility': volatility,
            'confidence': confidence
        }
    
    def project_team_elo(self, team: str, current_rating: float, target_week: int, 
                        current_week: int, season: int) -> Dict[str, Any]:
        """Project ELO rating for a team to a future week"""
        
        # Get team trend
        trend_data = self.calculate_team_trend(team, season)
        trend = trend_data['trend']
        volatility = trend_data['volatility']
        confidence = trend_data['confidence']
        
        # Calculate weeks ahead
        weeks_ahead = target_week - current_week
        
        if weeks_ahead <= 0:
            return {
                'team': team,
                'week': target_week,
                'projected_rating': current_rating,
                'confidence_score': 1.0,
                'method': 'current_rating'
            }
        
        # Apply trend-based projection
        # Trend diminishes over time (teams regress toward mean)
        regression_factor = 0.8 ** weeks_ahead  # Exponential decay
        projected_trend = trend * regression_factor
        
        # Add some randomness based on volatility
        import random
        random_factor = random.gauss(0, volatility * 0.1)
        
        # Calculate projected rating
        projected_rating = current_rating + (projected_trend * weeks_ahead) + random_factor
        
        # Apply bounds (teams don't go below 1000 or above 2000 typically)
        projected_rating = max(1000, min(2000, projected_rating))
        
        # Confidence decreases with time and volatility
        time_decay = 0.95 ** weeks_ahead
        volatility_penalty = max(0.1, 1.0 - (volatility / 100.0))
        final_confidence = confidence * time_decay * volatility_penalty
        
        return {
            'team': team,
            'week': target_week,
            'projected_rating': round(projected_rating, 1),
            'confidence_score': round(final_confidence, 3),
            'method': 'trend_based',
            'trend': round(trend, 2),
            'volatility': round(volatility, 2)
        }
    
    def project_week_elos(self, season: int, target_week: int, current_week: int = None) -> List[Dict[str, Any]]:
        """Project ELO ratings for all teams for a specific week"""
        
        if current_week is None:
            # Try to determine current week from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(week) FROM team_ratings 
                WHERE season = ?
            ''', (season,))
            result = cursor.fetchone()
            current_week = result[0] if result[0] else 1
            conn.close()
        
        logger.info(f"Projecting ELOs for season {season}, week {target_week} (current week: {current_week})")
        
        # Get current ratings
        current_ratings = self.get_current_elo_ratings(season)
        
        if not current_ratings:
            logger.warning(f"No current ELO ratings found for season {season}")
            return []
        
        projections = []
        
        for team, current_rating in current_ratings.items():
            projection = self.project_team_elo(
                team, current_rating, target_week, current_week, season
            )
            projections.append(projection)
        
        # Sort by projected rating
        projections.sort(key=lambda x: x['projected_rating'], reverse=True)
        
        # Add ranking
        for i, projection in enumerate(projections):
            projection['rank'] = i + 1
        
        return projections
    
    def store_projections(self, projections: List[Dict[str, Any]], season: int):
        """Store projected ELO ratings in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for projection in projections:
            cursor.execute('''
                INSERT OR REPLACE INTO projected_elo_ratings 
                (team, season, week, projected_rating, confidence_score, projection_method)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                projection['team'],
                season,
                projection['week'],
                projection['projected_rating'],
                projection['confidence_score'],
                projection['method']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Stored {len(projections)} ELO projections for season {season}, week {projections[0]['week'] if projections else 'unknown'}")
    
    def get_projections(self, season: int, week: int) -> List[Dict[str, Any]]:
        """Get stored projections for a specific season and week"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT team, projected_rating, confidence_score, projection_method, projection_date
            FROM projected_elo_ratings 
            WHERE season = ? AND week = ?
            ORDER BY projected_rating DESC
        ''', (season, week))
        
        projections = []
        for i, row in enumerate(cursor.fetchall()):
            projections.append({
                'team': row[0],
                'projected_rating': row[1],
                'confidence_score': row[2],
                'projection_method': row[3],
                'projection_date': row[4],
                'rank': i + 1
            })
        
        conn.close()
        return projections
    
    def project_all_weeks(self, season: int, current_week: int = None):
        """Project ELO ratings for all remaining weeks of the season"""
        if current_week is None:
            # Determine current week
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(week) FROM team_ratings 
                WHERE season = ?
            ''', (season,))
            result = cursor.fetchone()
            current_week = result[0] if result[0] else 1
            conn.close()
        
        logger.info(f"Projecting ELOs for all weeks {current_week + 1} to 18 for season {season}")
        
        for week in range(current_week + 1, 19):  # NFL season is 18 weeks
            try:
                projections = self.project_week_elos(season, week, current_week)
                if projections:
                    self.store_projections(projections, season)
                    logger.info(f"Completed projections for week {week}")
                else:
                    logger.warning(f"No projections generated for week {week}")
            except Exception as e:
                logger.error(f"Error projecting week {week}: {e}")
        
        logger.info("Completed all ELO projections")

def main():
    """Test the ELO projection service"""
    service = ELOProjectionService()
    
    # Test projecting week 2 for 2025 season
    projections = service.project_week_elos(2025, 2, 1)
    
    print(f"\n📊 ELO Projections for Week 2, 2025:")
    print("=" * 50)
    
    for i, proj in enumerate(projections[:10]):  # Show top 10
        print(f"{proj['rank']:2d}. {proj['team']:3s} - {proj['projected_rating']:6.1f} "
              f"(Confidence: {proj['confidence_score']:.2f})")
    
    # Store the projections
    service.store_projections(projections, 2025)
    
    print(f"\n✅ Stored {len(projections)} projections in database")

if __name__ == '__main__':
    main()
