#!/usr/bin/env python3
"""
Advanced NFL Scraper
Handles multiple data sources including NFL.com, ESPN, and other sources
"""

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
import random
import urllib.parse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AdvancedGameData:
    """Advanced game data structure"""
    game_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    quarter: int
    time_remaining: str
    status: str
    possession: Optional[str] = None
    down: Optional[int] = None
    distance: Optional[int] = None
    yard_line: Optional[int] = None
    red_zone: bool = False
    weather: Optional[str] = None
    temperature: Optional[int] = None
    wind_speed: Optional[int] = None
    last_update: str = None
    source: str = "unknown"

class AdvancedNFLScraper:
    """Advanced NFL scraper with multiple data sources"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # Data sources
        self.sources = {
            'espn': {
                'base_url': 'https://www.espn.com',
                'scores_url': 'https://www.espn.com/nfl/scoreboard',
                'api_url': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard'
            },
            'yahoo': {
                'base_url': 'https://sports.yahoo.com',
                'scores_url': 'https://sports.yahoo.com/nfl/scoreboard/',
                'api_url': 'https://sports.yahoo.com/nfl/scoreboard/'
            }
        }
        
        # Team abbreviations
        self.team_abbreviations = {
            'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL', 'Baltimore Ravens': 'BAL',
            'Buffalo Bills': 'BUF', 'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI',
            'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE', 'Dallas Cowboys': 'DAL',
            'Denver Broncos': 'DEN', 'Detroit Lions': 'DET', 'Green Bay Packers': 'GB',
            'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX',
            'Kansas City Chiefs': 'KC', 'Las Vegas Raiders': 'LV', 'Los Angeles Chargers': 'LAC',
            'Los Angeles Rams': 'LAR', 'Miami Dolphins': 'MIA', 'Minnesota Vikings': 'MIN',
            'New England Patriots': 'NE', 'New Orleans Saints': 'NO', 'New York Giants': 'NYG',
            'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI', 'Pittsburgh Steelers': 'PIT',
            'San Francisco 49ers': 'SF', 'Seattle Seahawks': 'SEA', 'Tampa Bay Buccaneers': 'TB',
            'Tennessee Titans': 'TEN', 'Washington Commanders': 'WAS'
        }
        
        # Status mapping
        self.status_mapping = {
            'FINAL': 'final', 'FINAL/OT': 'final', 'LIVE': 'in_progress',
            'IN PROGRESS': 'in_progress', 'HALFTIME': 'in_progress',
            'PREGAME': 'scheduled', 'POSTPONED': 'postponed', 'CANCELLED': 'cancelled'
        }
    
    def get_random_headers(self) -> Dict[str, str]:
        """Get random headers with fake user agent"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }
    
    def make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make a request with random headers and retry logic"""
        for attempt in range(max_retries):
            try:
                headers = self.get_random_headers()
                response = self.session.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    logger.info(f"Successfully scraped {url} (attempt {attempt + 1})")
                    return response
                elif response.status_code == 429:
                    wait_time = (2 ** attempt) + random.uniform(1, 3)
                    logger.warning(f"Rate limited, waiting {wait_time:.1f}s before retry {attempt + 1}")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"HTTP {response.status_code} on attempt {attempt + 1}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        logger.error(f"Failed to scrape {url} after {max_retries} attempts")
        return None
    
    
    def scrape_espn_api(self) -> List[AdvancedGameData]:
        """Try to scrape ESPN's API"""
        logger.info("Trying ESPN API...")
        
        api_url = self.sources['espn']['api_url']
        response = self.make_request(api_url)
        
        if not response:
            return []
        
        try:
            data = response.json()
            games = []
            
            if 'events' in data:
                for event in data['events']:
                    game_data = self._parse_espn_event(event)
                    if game_data:
                        games.append(game_data)
            
            logger.info(f"Found {len(games)} games from ESPN API")
            return games
            
        except Exception as e:
            logger.warning(f"Error parsing ESPN API response: {e}")
            return []
    
    def _parse_espn_event(self, event) -> Optional[AdvancedGameData]:
        """Parse ESPN event data"""
        try:
            # Extract basic info
            home_team = event['competitions'][0]['competitors'][0]['team']['abbreviation']
            away_team = event['competitions'][0]['competitors'][1]['team']['abbreviation']
            
            # Extract scores
            home_score = int(event['competitions'][0]['competitors'][0]['score'])
            away_score = int(event['competitions'][0]['competitors'][1]['score'])
            
            # Extract status
            status = event['status']['type']['name']
            quarter = event['status']['period']
            time_remaining = event['status']['displayClock'] or '0:00'
            
            # Map status
            mapped_status = self.status_mapping.get(status.upper(), 'scheduled')
            
            # Generate game ID
            game_id = f"espn_{home_team}_{away_team}_{datetime.now().strftime('%Y%m%d')}"
            
            return AdvancedGameData(
                game_id=game_id,
                home_team=home_team,
                away_team=away_team,
                home_score=home_score,
                away_score=away_score,
                quarter=quarter,
                time_remaining=time_remaining,
                status=mapped_status,
                last_update=datetime.now().isoformat(),
                source='espn_api'
            )
            
        except Exception as e:
            logger.warning(f"Error parsing ESPN event: {e}")
            return None
    
    def scrape_nfl_html(self) -> List[AdvancedGameData]:
        """Scrape ESPN HTML page as fallback"""
        logger.info("Trying ESPN HTML scraping...")
        
        response = self.make_request(self.sources['espn']['scores_url'])
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        games = []
        
        # Look for various selectors
        selectors = [
            '.nfl-c-game-card',
            '.game-card',
            '.score-card',
            '[data-testid*="game"]',
            '.nfl-s-scoreboard-game',
            '.game',
            '.scoreboard-game'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Found {len(elements)} games using selector: {selector}")
                for element in elements:
                    game_data = self._parse_html_game_element(element)
                    if game_data:
                        games.append(game_data)
                break
        
        logger.info(f"Found {len(games)} games from NFL HTML")
        return games
    
    def _parse_html_game_element(self, element) -> Optional[AdvancedGameData]:
        """Parse HTML game element"""
        try:
            # This is a simplified parser - would need to be updated based on actual HTML structure
            text = element.get_text()
            
            # Look for team patterns
            team_pattern = r'([A-Z]{2,4})\s*(\d+)\s*-\s*([A-Z]{2,4})\s*(\d+)'
            match = re.search(team_pattern, text)
            
            if match:
                away_team, away_score, home_team, home_score = match.groups()
                
                game_id = f"nfl_html_{home_team}_{away_team}_{datetime.now().strftime('%Y%m%d')}"
                
                return AdvancedGameData(
                    game_id=game_id,
                    home_team=home_team,
                    away_team=away_team,
                    home_score=int(home_score),
                    away_score=int(away_score),
                    quarter=1,
                    time_remaining='0:00',
                    status='scheduled',
                    last_update=datetime.now().isoformat(),
                    source='nfl_html'
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing HTML game element: {e}")
            return None
    
    def get_live_games(self) -> List[AdvancedGameData]:
        """Get live games from all available sources"""
        all_games = []
        
        # Try different sources in order of preference
        sources_to_try = [
            ('ESPN API', self.scrape_espn_api),
            ('ESPN HTML', self.scrape_nfl_html)
        ]
        
        for source_name, scrape_func in sources_to_try:
            try:
                logger.info(f"Trying {source_name}...")
                games = scrape_func()
                if games:
                    all_games.extend(games)
                    logger.info(f"Successfully got {len(games)} games from {source_name}")
                    break  # Stop after first successful source
                else:
                    logger.info(f"No games found from {source_name}")
            except Exception as e:
                logger.warning(f"Error with {source_name}: {e}")
        
        # Remove duplicates based on game_id
        unique_games = {}
        for game in all_games:
            unique_games[game.game_id] = game
        
        final_games = list(unique_games.values())
        logger.info(f"Total unique games found: {len(final_games)}")
        
        return final_games

def test_advanced_scraper():
    """Test the advanced scraper"""
    print("🏈 Advanced NFL Scraper Test")
    print("=" * 50)
    
    scraper = AdvancedNFLScraper()
    
    # Test user agents
    print("\n🤖 Testing User Agents:")
    for i in range(3):
        headers = scraper.get_random_headers()
        print(f"  {i+1}. {headers['User-Agent']}")
    
    # Test live games
    print("\n📊 Testing Live Games Scraping:")
    games = scraper.get_live_games()
    
    if games:
        print(f"\n✅ Found {len(games)} games:")
        for game in games:
            print(f"\n🎮 {game.away_team} @ {game.home_team}")
            print(f"   Score: {game.away_team} {game.away_score} - {game.home_team} {game.home_score}")
            print(f"   Status: {game.status} (Q{game.quarter}, {game.time_remaining})")
            print(f"   Source: {game.source}")
            print(f"   Last Update: {game.last_update}")
    else:
        print("\n❌ No games found")
        print("\nThis could mean:")
        print("  - No games are currently live")
        print("  - All data sources are unavailable")
        print("  - Rate limiting is in effect")
        print("  - Website structures have changed")

if __name__ == "__main__":
    test_advanced_scraper()
