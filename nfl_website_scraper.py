#!/usr/bin/env python3
"""
NFL Website Scraper
Real-time scraping of NFL.com for live game data
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScrapedGameData:
    """Scraped game data structure"""
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

class NFLWebsiteScraper:
    """Scraper for NFL.com live game data"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.base_url = "https://www.nfl.com"
        self.live_scores_url = "https://www.nfl.com/scores"
        self.game_detail_url = "https://www.nfl.com/games"
        
        # Team abbreviations mapping
        self.team_abbreviations = {
            'Arizona Cardinals': 'ARI',
            'Atlanta Falcons': 'ATL',
            'Baltimore Ravens': 'BAL',
            'Buffalo Bills': 'BUF',
            'Carolina Panthers': 'CAR',
            'Chicago Bears': 'CHI',
            'Cincinnati Bengals': 'CIN',
            'Cleveland Browns': 'CLE',
            'Dallas Cowboys': 'DAL',
            'Denver Broncos': 'DEN',
            'Detroit Lions': 'DET',
            'Green Bay Packers': 'GB',
            'Houston Texans': 'HOU',
            'Indianapolis Colts': 'IND',
            'Jacksonville Jaguars': 'JAX',
            'Kansas City Chiefs': 'KC',
            'Las Vegas Raiders': 'LV',
            'Los Angeles Chargers': 'LAC',
            'Los Angeles Rams': 'LAR',
            'Miami Dolphins': 'MIA',
            'Minnesota Vikings': 'MIN',
            'New England Patriots': 'NE',
            'New Orleans Saints': 'NO',
            'New York Giants': 'NYG',
            'New York Jets': 'NYJ',
            'Philadelphia Eagles': 'PHI',
            'Pittsburgh Steelers': 'PIT',
            'San Francisco 49ers': 'SF',
            'Seattle Seahawks': 'SEA',
            'Tampa Bay Buccaneers': 'TB',
            'Tennessee Titans': 'TEN',
            'Washington Commanders': 'WAS'
        }
        
        # Status mapping
        self.status_mapping = {
            'FINAL': 'final',
            'FINAL/OT': 'final',
            'LIVE': 'in_progress',
            'IN PROGRESS': 'in_progress',
            'HALFTIME': 'in_progress',
            'PREGAME': 'scheduled',
            'POSTPONED': 'postponed',
            'CANCELLED': 'cancelled'
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
            'Cache-Control': 'max-age=0'
        }
    
    def make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make a request with random headers and retry logic"""
        for attempt in range(max_retries):
            try:
                headers = self.get_random_headers()
                response = self.session.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"Successfully scraped {url} (attempt {attempt + 1})")
                    return response
                elif response.status_code == 429:
                    # Rate limited, wait longer
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
    
    def scrape_live_scores_page(self) -> List[ScrapedGameData]:
        """Scrape the NFL live scores page"""
        logger.info("Scraping NFL live scores page...")
        
        response = self.make_request(self.live_scores_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        games = []
        
        try:
            # Look for game cards or score elements
            # NFL.com structure may vary, so we'll try multiple selectors
            game_selectors = [
                '.nfl-c-game-card',
                '.game-card',
                '.score-card',
                '[data-testid*="game"]',
                '.nfl-s-scoreboard-game'
            ]
            
            game_elements = []
            for selector in game_selectors:
                elements = soup.select(selector)
                if elements:
                    game_elements = elements
                    logger.info(f"Found {len(elements)} games using selector: {selector}")
                    break
            
            if not game_elements:
                # Fallback: look for any elements with team names or scores
                logger.info("No game cards found, trying fallback method...")
                return self._scrape_fallback_method(soup)
            
            for game_element in game_elements:
                game_data = self._parse_game_element(game_element)
                if game_data:
                    games.append(game_data)
            
        except Exception as e:
            logger.error(f"Error parsing live scores page: {e}")
        
        logger.info(f"Scraped {len(games)} games from live scores page")
        return games
    
    def _parse_game_element(self, element) -> Optional[ScrapedGameData]:
        """Parse a single game element"""
        try:
            # Extract team names
            team_elements = element.find_all(['span', 'div'], class_=re.compile(r'.*team.*|.*name.*', re.I))
            if len(team_elements) < 2:
                return None
            
            home_team = self._extract_team_name(team_elements[1])
            away_team = self._extract_team_name(team_elements[0])
            
            if not home_team or not away_team:
                return None
            
            # Extract scores
            score_elements = element.find_all(['span', 'div'], class_=re.compile(r'.*score.*|.*points.*', re.I))
            home_score = self._extract_score(score_elements[1] if len(score_elements) > 1 else None)
            away_score = self._extract_score(score_elements[0] if len(score_elements) > 0 else None)
            
            # Extract game status and time
            status_element = element.find(['span', 'div'], class_=re.compile(r'.*status.*|.*time.*|.*quarter.*', re.I))
            status, quarter, time_remaining = self._extract_game_status(status_element)
            
            # Generate game ID
            game_id = f"scraped_{home_team}_{away_team}_{datetime.now().strftime('%Y%m%d')}"
            
            return ScrapedGameData(
                game_id=game_id,
                home_team=home_team,
                away_team=away_team,
                home_score=home_score,
                away_score=away_score,
                quarter=quarter,
                time_remaining=time_remaining,
                status=status,
                last_update=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.warning(f"Error parsing game element: {e}")
            return None
    
    def _extract_team_name(self, element) -> Optional[str]:
        """Extract team name from element"""
        if not element:
            return None
        
        text = element.get_text(strip=True)
        
        # Try to find team abbreviation
        for full_name, abbrev in self.team_abbreviations.items():
            if full_name.lower() in text.lower() or abbrev in text:
                return abbrev
        
        # Try to extract from text
        words = text.split()
        if len(words) >= 2:
            # Look for city + team pattern
            potential_team = ' '.join(words[-2:])
            if potential_team in self.team_abbreviations:
                return self.team_abbreviations[potential_team]
        
        return None
    
    def _extract_score(self, element) -> int:
        """Extract score from element"""
        if not element:
            return 0
        
        text = element.get_text(strip=True)
        try:
            return int(text)
        except ValueError:
            return 0
    
    def _extract_game_status(self, element) -> tuple:
        """Extract game status, quarter, and time remaining"""
        if not element:
            return 'scheduled', 1, '0:00'
        
        text = element.get_text(strip=True).upper()
        
        # Determine status
        status = 'scheduled'
        for key, value in self.status_mapping.items():
            if key in text:
                status = value
                break
        
        # Extract quarter
        quarter = 1
        quarter_match = re.search(r'(\d+)(?:ST|ND|RD|TH)?', text)
        if quarter_match:
            quarter = int(quarter_match.group(1))
        
        # Extract time remaining
        time_remaining = '0:00'
        time_match = re.search(r'(\d+):(\d+)', text)
        if time_match:
            time_remaining = f"{time_match.group(1)}:{time_match.group(2)}"
        
        return status, quarter, time_remaining
    
    def _scrape_fallback_method(self, soup) -> List[ScrapedGameData]:
        """Fallback scraping method when main selectors fail"""
        logger.info("Using fallback scraping method...")
        
        games = []
        
        # Look for any text that might contain team names and scores
        text_content = soup.get_text()
        
        # Simple pattern matching for team names and scores
        team_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+|[A-Z]{2,4})'
        score_pattern = r'(\d+)\s*-\s*(\d+)'
        
        # This is a very basic fallback - in practice, you'd need more sophisticated parsing
        logger.warning("Fallback method is very basic - consider updating selectors")
        
        return games
    
    def scrape_game_details(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Scrape detailed game information"""
        logger.info(f"Scraping details for game {game_id}")
        
        # This would scrape individual game pages for more details
        # For now, return basic structure
        return {
            'game_id': game_id,
            'possession': None,
            'down': None,
            'distance': None,
            'yard_line': None,
            'red_zone': False,
            'weather': 'Unknown',
            'temperature': None,
            'wind_speed': None
        }
    
    def get_live_games(self) -> List[ScrapedGameData]:
        """Get all live games from NFL.com"""
        logger.info("Starting NFL.com live games scrape...")
        
        # Scrape live scores page
        games = self.scrape_live_scores_page()
        
        # If no games found, try alternative methods
        if not games:
            logger.info("No games found on live scores page, trying alternative...")
            games = self._try_alternative_scraping()
        
        # Add details for each game
        for game in games:
            details = self.scrape_game_details(game.game_id)
            if details:
                game.possession = details.get('possession')
                game.down = details.get('down')
                game.distance = details.get('distance')
                game.yard_line = details.get('yard_line')
                game.red_zone = details.get('red_zone', False)
                game.weather = details.get('weather')
                game.temperature = details.get('temperature')
                game.wind_speed = details.get('wind_speed')
        
        logger.info(f"Successfully scraped {len(games)} live games")
        return games
    
    def _try_alternative_scraping(self) -> List[ScrapedGameData]:
        """Try alternative scraping methods"""
        # This could include:
        # - Scraping different NFL.com pages
        # - Using different selectors
        # - Parsing JSON data from API calls
        logger.info("Alternative scraping methods not implemented yet")
        return []

def test_nfl_scraper():
    """Test function for the NFL scraper"""
    print("🏈 NFL Website Scraper Test")
    print("=" * 50)
    
    scraper = NFLWebsiteScraper()
    
    # Test random headers
    print("\n🔧 Testing random headers...")
    for i in range(3):
        headers = scraper.get_random_headers()
        print(f"  User-Agent {i+1}: {headers['User-Agent']}")
    
    # Test live games scraping
    print("\n📊 Scraping live games...")
    games = scraper.get_live_games()
    
    if games:
        print(f"\n✅ Found {len(games)} games:")
        for game in games:
            print(f"\n🎮 {game.away_team} @ {game.home_team}")
            print(f"   Score: {game.away_team} {game.away_score} - {game.home_team} {game.home_score}")
            print(f"   Status: {game.status}")
            print(f"   Quarter: {game.quarter} ({game.time_remaining})")
            print(f"   Last Update: {game.last_update}")
    else:
        print("\n❌ No games found")
        print("\n🔍 This could mean:")
        print("   - No games are currently live")
        print("   - NFL.com structure has changed")
        print("   - Rate limiting is in effect")
        print("   - Network connectivity issues")
    
    # Test individual game details
    if games:
        print(f"\n🔍 Testing game details for first game...")
        details = scraper.scrape_game_details(games[0].game_id)
        print(f"   Details: {details}")

if __name__ == "__main__":
    test_nfl_scraper()
