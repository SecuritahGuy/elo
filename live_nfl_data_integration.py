#!/usr/bin/env python3
"""
Live NFL Data Integration System
Integrates multiple data sources for real-time NFL game data
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
import sqlite3
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LiveGameData:
    """Live game data structure"""
    game_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    quarter: int
    time_remaining: str
    status: str  # 'scheduled', 'in_progress', 'final', 'postponed'
    possession: Optional[str] = None
    down: Optional[int] = None
    distance: Optional[int] = None
    yard_line: Optional[int] = None
    red_zone: bool = False
    weather: Optional[str] = None
    temperature: Optional[int] = None
    wind_speed: Optional[int] = None
    last_update: str = None

class LiveNFLDataService:
    """Service for integrating live NFL data from multiple sources"""
    
    def __init__(self, db_path: str = "nfl_elo.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # API endpoints (these would need actual API keys in production)
        self.data_sources = {
            'espn': {
                'base_url': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl',
                'api_key_required': True,
                'free_tier': False
            },
            'sportsdata': {
                'base_url': 'https://api.sportsdata.io/v3/nfl',
                'api_key_required': True,
                'free_tier': True
            },
            'the_odds_api': {
                'base_url': 'https://api.the-odds-api.com/v4',
                'api_key_required': True,
                'free_tier': True
            },
            'nfl_scraping': {
                'base_url': 'https://www.nfl.com',
                'api_key_required': False,
                'free_tier': True
            }
        }
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize database tables for live data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create live games table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_games (
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
            )
        ''')
        
        # Create live game updates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_game_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT,
                update_type TEXT,
                update_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES live_games (game_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_live_games_espn(self) -> List[LiveGameData]:
        """Get live games from ESPN API (requires API key)"""
        try:
            # This would require an actual ESPN API key
            # For now, return empty list
            logger.info("ESPN API requires authentication - not implemented yet")
            return []
        except Exception as e:
            logger.error(f"Error fetching ESPN data: {e}")
            return []
    
    def get_live_games_sportsdata(self) -> List[LiveGameData]:
        """Get live games from SportsData.io API (requires API key)"""
        try:
            # This would require an actual SportsData API key
            # For now, return empty list
            logger.info("SportsData API requires authentication - not implemented yet")
            return []
        except Exception as e:
            logger.error(f"Error fetching SportsData: {e}")
            return []
    
    def scrape_nfl_live_scores(self) -> List[LiveGameData]:
        """Scrape live scores from NFL.com and ESPN API"""
        try:
            from advanced_nfl_scraper import AdvancedNFLScraper
            
            # Use the advanced scraper
            advanced_scraper = AdvancedNFLScraper()
            games = advanced_scraper.get_live_games()
            
            # Convert to LiveGameData format
            live_games = []
            for game in games:
                live_game = LiveGameData(
                    game_id=game.game_id,
                    home_team=game.home_team,
                    away_team=game.away_team,
                    home_score=game.home_score,
                    away_score=game.away_score,
                    quarter=game.quarter,
                    time_remaining=game.time_remaining,
                    status=game.status,
                    possession=game.possession,
                    down=game.down,
                    distance=game.distance,
                    yard_line=game.yard_line,
                    red_zone=game.red_zone,
                    weather=game.weather,
                    temperature=game.temperature,
                    wind_speed=game.wind_speed,
                    last_update=game.last_update
                )
                live_games.append(live_game)
            
            logger.info(f"Scraped {len(live_games)} games from real sources")
            return live_games
            
        except Exception as e:
            logger.error(f"Error scraping real NFL data: {e}")
            return []
    
    def get_mock_live_games(self) -> List[LiveGameData]:
        """Generate mock live games for testing (simulating Chiefs game)"""
        current_time = datetime.now()
        
        # Simulate Chiefs vs Chargers game that was on Friday
        games = [
            LiveGameData(
                game_id="live_chiefs_chargers_2025_09_05",
                home_team="KC",
                away_team="LAC", 
                home_score=24,
                away_score=21,
                quarter=4,
                time_remaining="0:00",
                status="final",
                possession=None,
                down=None,
                distance=None,
                yard_line=None,
                red_zone=False,
                weather="Clear",
                temperature=72,
                wind_speed=8,
                last_update=current_time.isoformat()
            )
        ]
        
        # Add some simulated live games for testing
        if current_time.hour >= 13:  # After 1 PM, simulate afternoon games
            games.extend([
                LiveGameData(
                    game_id="live_philadelphia_dallas_2025_09_07",
                    home_team="PHI",
                    away_team="DAL",
                    home_score=14,
                    away_score=10,
                    quarter=2,
                    time_remaining="8:42",
                    status="in_progress",
                    possession="PHI",
                    down=2,
                    distance=7,
                    yard_line=45,
                    red_zone=False,
                    weather="Partly Cloudy",
                    temperature=68,
                    wind_speed=12,
                    last_update=current_time.isoformat()
                ),
                LiveGameData(
                    game_id="live_buffalo_nyjets_2025_09_07",
                    home_team="BUF",
                    away_team="NYJ",
                    home_score=21,
                    away_score=17,
                    quarter=3,
                    time_remaining="12:15",
                    status="in_progress",
                    possession="NYJ",
                    down=1,
                    distance=10,
                    yard_line=25,
                    red_zone=True,
                    weather="Clear",
                    temperature=65,
                    wind_speed=6,
                    last_update=current_time.isoformat()
                )
            ])
        
        return games
    
    def get_live_games(self, use_mock: bool = False) -> List[LiveGameData]:
        """Get live games from all available sources"""
        all_games = []
        
        # Try real APIs first
        try:
            espn_games = self.get_live_games_espn()
            all_games.extend(espn_games)
        except:
            pass
        
        try:
            sportsdata_games = self.get_live_games_sportsdata()
            all_games.extend(sportsdata_games)
        except:
            pass
        
        try:
            nfl_games = self.scrape_nfl_live_scores()
            all_games.extend(nfl_games)
        except:
            pass
        
        # If no real data available and mock is enabled, use mock data
        if not all_games and use_mock:
            logger.info("No real data available, using mock data")
            all_games = self.get_mock_live_games()
        
        return all_games
    
    def save_live_games(self, games: List[LiveGameData]):
        """Save live games to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for game in games:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO live_games 
                    (game_id, home_team, away_team, home_score, away_score, quarter, 
                     time_remaining, status, possession, down, distance, yard_line, 
                     red_zone, weather, temperature, wind_speed, last_update)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    game.game_id, game.home_team, game.away_team, game.home_score,
                    game.away_score, game.quarter, game.time_remaining, game.status,
                    game.possession, game.down, game.distance, game.yard_line,
                    game.red_zone, game.weather, game.temperature, game.wind_speed,
                    game.last_update
                ))
            except Exception as e:
                logger.error(f"Error saving game {game.game_id}: {e}")
        
        conn.commit()
        conn.close()
    
    def get_stored_live_games(self) -> List[LiveGameData]:
        """Get live games from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT game_id, home_team, away_team, home_score, away_score, quarter,
                   time_remaining, status, possession, down, distance, yard_line,
                   red_zone, weather, temperature, wind_speed, last_update
            FROM live_games
            ORDER BY last_update DESC
        ''')
        
        games = []
        for row in cursor.fetchall():
            game = LiveGameData(
                game_id=row[0],
                home_team=row[1],
                away_team=row[2],
                home_score=row[3],
                away_score=row[4],
                quarter=row[5],
                time_remaining=row[6],
                status=row[7],
                possession=row[8],
                down=row[9],
                distance=row[10],
                yard_line=row[11],
                red_zone=bool(row[12]),
                weather=row[13],
                temperature=row[14],
                wind_speed=row[15],
                last_update=row[16]
            )
            games.append(game)
        
        conn.close()
        return games
    
    def calculate_live_metrics(self, game: LiveGameData) -> Dict[str, Any]:
        """Calculate live game metrics"""
        score_diff = abs(game.home_score - game.away_score)
        
        # Excitement level (0-100)
        if game.status == "in_progress":
            if score_diff <= 7:
                excitement = 90 + (10 - score_diff)
            elif score_diff <= 14:
                excitement = 70 + (14 - score_diff)
            else:
                excitement = 50 + (20 - score_diff)
        else:
            excitement = 0
        
        # Competitiveness (0-100)
        if game.status == "in_progress":
            if score_diff == 0:
                competitiveness = 100
            elif score_diff <= 3:
                competitiveness = 90
            elif score_diff <= 7:
                competitiveness = 75
            elif score_diff <= 14:
                competitiveness = 50
            else:
                competitiveness = 25
        else:
            competitiveness = 0
        
        # Momentum (home, away, or neutral)
        if game.status == "in_progress" and game.quarter >= 2:
            if score_diff > 7:
                if game.home_score > game.away_score:
                    momentum = "home_momentum"
                else:
                    momentum = "away_momentum"
            else:
                momentum = "neutral"
        else:
            momentum = "neutral"
        
        return {
            "excitement_level": min(100, max(0, excitement)),
            "competitiveness": min(100, max(0, competitiveness)),
            "momentum": momentum,
            "score_difference": score_diff,
            "total_points": game.home_score + game.away_score
        }
    
    def update_live_games(self):
        """Update live games data"""
        logger.info("Updating live games data...")
        
        # Get live games from all sources
        games = self.get_live_games()
        
        # Save to database
        self.save_live_games(games)
        
        # Calculate and log metrics
        for game in games:
            metrics = self.calculate_live_metrics(game)
            logger.info(f"Game {game.home_team} vs {game.away_team}: {metrics}")
        
        logger.info(f"Updated {len(games)} live games")
        return games

def main():
    """Main function for testing live data integration"""
    service = LiveNFLDataService()
    
    print("🏈 Live NFL Data Integration System")
    print("=" * 50)
    
    # Update live games
    games = service.update_live_games()
    
    if games:
        print(f"\n📊 Found {len(games)} live games:")
        for game in games:
            metrics = service.calculate_live_metrics(game)
            print(f"\n🎮 {game.away_team} @ {game.home_team}")
            print(f"   Score: {game.away_team} {game.away_score} - {game.home_team} {game.home_score}")
            print(f"   Quarter: {game.quarter} ({game.time_remaining})")
            print(f"   Status: {game.status}")
            print(f"   Excitement: {metrics['excitement_level']}/100")
            print(f"   Competitiveness: {metrics['competitiveness']}/100")
            print(f"   Momentum: {metrics['momentum']}")
    else:
        print("\n❌ No live games found")
    
    print(f"\n💾 Data saved to database: {service.db_path}")

if __name__ == "__main__":
    main()
