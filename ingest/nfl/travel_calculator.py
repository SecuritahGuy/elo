"""Travel distance and fatigue calculations for NFL teams."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from math import radians, cos, sin, asin, sqrt
from .stadium_database import StadiumDatabase


@dataclass
class TravelInfo:
    """Travel information for a team."""
    distance_miles: float
    time_zones_crossed: int
    travel_direction: str  # 'east', 'west', 'same'
    fatigue_factor: float
    recovery_days: int


class TravelCalculator:
    """Calculate travel distances and fatigue factors for NFL teams."""
    
    def __init__(self):
        """Initialize the travel calculator with stadium database."""
        self.stadium_db = StadiumDatabase()
        self._distance_cache: Dict[Tuple[str, str], float] = {}
        self._timezone_cache: Dict[str, int] = {}
        
        # Initialize timezone mapping for NFL cities
        self._init_timezones()
    
    def _init_timezones(self):
        """Initialize timezone mapping for NFL cities."""
        # US Timezones (offset from UTC)
        self._timezone_cache = {
            # Eastern Time (UTC-5/-4)
            'BUF': -5, 'MIA': -5, 'NE': -5, 'NYJ': -5, 'BAL': -5, 'CIN': -5, 
            'CLE': -5, 'PIT': -5, 'HOU': -6, 'IND': -5, 'JAX': -5, 'TEN': -6,
            'ATL': -5, 'CAR': -5, 'NO': -6, 'TB': -5, 'WAS': -5, 'PHI': -5,
            'NYG': -5, 'DAL': -6, 'ARI': -7, 'LAR': -8, 'SF': -8, 'SEA': -8,
            
            # Central Time (UTC-6/-5)
            'CHI': -6, 'DET': -5, 'GB': -6, 'MIN': -6, 'KC': -6, 'LV': -8,
            
            # Mountain Time (UTC-7/-6)
            'DEN': -7, 'LAC': -8,
            
            # Pacific Time (UTC-8/-7)
            'LAR': -8, 'SF': -8, 'SEA': -8, 'LAC': -8
        }
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth.
        
        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point
            
        Returns:
            Distance in miles
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in miles
        r = 3956
        return c * r
    
    def get_travel_distance(self, home_team: str, away_team: str) -> float:
        """
        Get travel distance between two teams' stadiums.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            
        Returns:
            Distance in miles
        """
        # Check cache first
        cache_key = (home_team, away_team)
        if cache_key in self._distance_cache:
            return self._distance_cache[cache_key]
        
        # Get stadium coordinates
        home_stadium = self.stadium_db.get_stadium(home_team)
        away_stadium = self.stadium_db.get_stadium(away_team)
        
        if not home_stadium or not away_stadium:
            return 0.0
        
        # Calculate distance
        distance = self.haversine_distance(
            home_stadium.latitude, home_stadium.longitude,
            away_stadium.latitude, away_stadium.longitude
        )
        
        # Cache the result
        self._distance_cache[cache_key] = distance
        return distance
    
    def get_timezone_difference(self, home_team: str, away_team: str) -> int:
        """
        Get timezone difference between two teams.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            
        Returns:
            Timezone difference in hours
        """
        home_tz = self._timezone_cache.get(home_team, -5)  # Default to Eastern
        away_tz = self._timezone_cache.get(away_team, -5)  # Default to Eastern
        
        return abs(home_tz - away_tz)
    
    def get_travel_direction(self, home_team: str, away_team: str) -> str:
        """
        Determine travel direction for away team.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            
        Returns:
            Travel direction: 'east', 'west', or 'same'
        """
        home_tz = self._timezone_cache.get(home_team, -5)
        away_tz = self._timezone_cache.get(away_team, -5)
        
        if away_tz < home_tz:
            return 'east'  # Traveling east (losing time)
        elif away_tz > home_tz:
            return 'west'  # Traveling west (gaining time)
        else:
            return 'same'  # Same timezone
    
    def calculate_travel_fatigue(self, distance_miles: float, time_zones: int, 
                               travel_direction: str, days_since_travel: int = 1) -> float:
        """
        Calculate travel fatigue factor based on distance and time zones.
        
        Args:
            distance_miles: Distance traveled in miles
            time_zones: Number of time zones crossed
            travel_direction: Direction of travel
            days_since_travel: Days since travel occurred
            
        Returns:
            Fatigue factor (0.0 = no fatigue, 1.0 = maximum fatigue)
        """
        # Base fatigue from distance
        distance_fatigue = min(distance_miles / 2000.0, 1.0)  # Max at 2000 miles
        
        # Time zone fatigue (east travel is worse)
        if travel_direction == 'east':
            tz_fatigue = min(time_zones * 0.15, 0.6)  # Max 0.6 for east travel
        elif travel_direction == 'west':
            tz_fatigue = min(time_zones * 0.10, 0.4)  # Max 0.4 for west travel
        else:
            tz_fatigue = 0.0
        
        # Recovery over time
        recovery_factor = max(0.0, 1.0 - (days_since_travel * 0.2))  # 20% recovery per day
        
        # Combined fatigue factor
        total_fatigue = (distance_fatigue * 0.4 + tz_fatigue * 0.6) * recovery_factor
        
        return min(total_fatigue, 1.0)
    
    def get_travel_info(self, home_team: str, away_team: str, 
                       days_since_travel: int = 1) -> TravelInfo:
        """
        Get comprehensive travel information for a game.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            days_since_travel: Days since travel occurred
            
        Returns:
            TravelInfo object with all travel details
        """
        distance = self.get_travel_distance(home_team, away_team)
        time_zones = self.get_timezone_difference(home_team, away_team)
        direction = self.get_travel_direction(home_team, away_team)
        fatigue = self.calculate_travel_fatigue(distance, time_zones, direction, days_since_travel)
        
        # Recovery days needed (based on distance and time zones)
        recovery_days = max(1, int(distance / 1000) + time_zones)
        
        return TravelInfo(
            distance_miles=distance,
            time_zones_crossed=time_zones,
            travel_direction=direction,
            fatigue_factor=fatigue,
            recovery_days=recovery_days
        )
    
    def add_travel_data_to_games(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add travel data to games DataFrame.
        
        Args:
            games_df: DataFrame with game data
            
        Returns:
            DataFrame with travel data added
        """
        games_with_travel = games_df.copy()
        
        # Initialize travel columns
        travel_columns = [
            'travel_distance', 'time_zones_crossed', 'travel_direction',
            'travel_fatigue', 'recovery_days_needed', 'travel_advantage'
        ]
        
        for col in travel_columns:
            games_with_travel[col] = 0.0
        
        # Calculate travel data for each game
        for idx, game in games_with_travel.iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Get travel info
            travel_info = self.get_travel_info(home_team, away_team)
            
            # Add travel data
            games_with_travel.loc[idx, 'travel_distance'] = travel_info.distance_miles
            games_with_travel.loc[idx, 'time_zones_crossed'] = travel_info.time_zones_crossed
            games_with_travel.loc[idx, 'travel_direction'] = travel_info.travel_direction
            games_with_travel.loc[idx, 'travel_fatigue'] = travel_info.fatigue_factor
            games_with_travel.loc[idx, 'recovery_days_needed'] = travel_info.recovery_days
            
            # Calculate travel advantage (home team gets advantage from away team's fatigue)
            games_with_travel.loc[idx, 'travel_advantage'] = travel_info.fatigue_factor
        
        return games_with_travel
    
    def get_travel_matrix(self) -> pd.DataFrame:
        """
        Get travel distance matrix for all NFL teams.
        
        Returns:
            DataFrame with travel distances between all teams
        """
        teams = list(self._timezone_cache.keys())
        matrix_data = {}
        
        for home_team in teams:
            matrix_data[home_team] = {}
            for away_team in teams:
                if home_team == away_team:
                    matrix_data[home_team][away_team] = 0.0
                else:
                    matrix_data[home_team][away_team] = self.get_travel_distance(home_team, away_team)
        
        return pd.DataFrame(matrix_data, index=teams)
    
    def test_travel_calculations(self):
        """Test travel calculation functions."""
        print("Testing Travel Calculations...")
        
        # Test distance calculation
        distance = self.get_travel_distance('NYJ', 'LAR')
        print(f"NYJ to LAR distance: {distance:.1f} miles")
        
        # Test timezone difference
        tz_diff = self.get_timezone_difference('NYJ', 'LAR')
        print(f"NYJ to LAR timezone difference: {tz_diff} hours")
        
        # Test travel direction
        direction = self.get_travel_direction('NYJ', 'LAR')
        print(f"NYJ to LAR travel direction: {direction}")
        
        # Test travel info
        travel_info = self.get_travel_info('NYJ', 'LAR')
        print(f"Travel info: {travel_info}")
        
        # Test travel matrix
        matrix = self.get_travel_matrix()
        print(f"Travel matrix shape: {matrix.shape}")
        print("Sample distances:")
        print(matrix.loc[['NYJ', 'LAR', 'GB'], ['NYJ', 'LAR', 'GB']].round(1))
        
        print("Travel calculations working!")


def test_travel_calculator():
    """Test the travel calculator."""
    calculator = TravelCalculator()
    calculator.test_travel_calculations()


if __name__ == "__main__":
    test_travel_calculator()
