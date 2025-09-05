"""Travel and rest day adjustments for NFL Elo system."""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from ingest.nfl.travel_calculator import TravelCalculator


@dataclass
class RestDayInfo:
    """Rest day information for a team."""
    days_off: int
    travel_fatigue: float
    recovery_factor: float
    rest_advantage: float
    travel_penalty: float


class TravelAdjustmentCalculator:
    """Calculate travel and rest day adjustments for NFL games."""
    
    def __init__(self):
        """Initialize the travel adjustment calculator."""
        self.travel_calc = TravelCalculator()
    
    def calculate_rest_advantage(self, home_rest: int, away_rest: int, 
                               home_travel_fatigue: float = 0.0, 
                               away_travel_fatigue: float = 0.0) -> Tuple[float, float]:
        """
        Calculate rest day advantage considering travel fatigue.
        
        Args:
            home_rest: Home team's rest days
            away_rest: Away team's rest days
            home_travel_fatigue: Home team's travel fatigue (0-1)
            away_travel_fatigue: Away team's travel fatigue (0-1)
            
        Returns:
            Tuple of (home_advantage, away_advantage) in Elo points
        """
        # Base rest advantage (existing logic)
        rest_difference = home_rest - away_rest
        
        # Rest advantage per day (diminishing returns)
        if rest_difference > 0:
            # Home team has more rest
            if rest_difference == 1:
                home_advantage = 1.0
            elif rest_difference == 2:
                home_advantage = 1.5
            elif rest_difference == 3:
                home_advantage = 2.0
            elif rest_difference >= 4:
                home_advantage = 2.5
            else:
                home_advantage = 0.0
            away_advantage = 0.0
        elif rest_difference < 0:
            # Away team has more rest
            if rest_difference == -1:
                away_advantage = 1.0
            elif rest_difference == -2:
                away_advantage = 1.5
            elif rest_difference == -3:
                away_advantage = 2.0
            elif rest_difference <= -4:
                away_advantage = 2.5
            else:
                away_advantage = 0.0
            home_advantage = 0.0
        else:
            home_advantage = 0.0
            away_advantage = 0.0
        
        # Adjust for travel fatigue
        # Travel fatigue reduces rest advantage
        home_advantage *= (1.0 - home_travel_fatigue * 0.5)  # 50% reduction max
        away_advantage *= (1.0 - away_travel_fatigue * 0.5)  # 50% reduction max
        
        return home_advantage, away_advantage
    
    def calculate_travel_penalty(self, travel_fatigue: float, days_since_travel: int) -> float:
        """
        Calculate travel penalty based on fatigue and recovery time.
        
        Args:
            travel_fatigue: Travel fatigue factor (0-1)
            days_since_travel: Days since travel occurred
            
        Returns:
            Travel penalty in Elo points
        """
        # Base penalty from fatigue
        base_penalty = travel_fatigue * 3.0  # Max 3 Elo points
        
        # Recovery over time (exponential decay)
        recovery_factor = np.exp(-days_since_travel * 0.3)  # 30% recovery per day
        
        # Final penalty
        penalty = base_penalty * recovery_factor
        
        return min(penalty, 3.0)  # Cap at 3 Elo points
    
    def calculate_short_week_penalty(self, rest_days: int) -> float:
        """
        Calculate penalty for short rest weeks.
        
        Args:
            rest_days: Number of rest days
            
        Returns:
            Short week penalty in Elo points
        """
        if rest_days < 7:
            # Short week penalty
            if rest_days == 6:
                return 0.5  # Thursday night games
            elif rest_days == 5:
                return 1.0  # Wednesday games
            elif rest_days == 4:
                return 1.5  # Tuesday games
            elif rest_days <= 3:
                return 2.0  # Very short rest
        elif rest_days > 10:
            # Long rest penalty (rust factor)
            return -0.5  # Slight disadvantage for too much rest
        
        return 0.0
    
    def get_rest_day_info(self, home_team: str, away_team: str, 
                         home_rest: int, away_rest: int,
                         home_previous_opponent: Optional[str] = None,
                         away_previous_opponent: Optional[str] = None) -> Tuple[RestDayInfo, RestDayInfo]:
        """
        Get comprehensive rest day information for both teams.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            home_rest: Home team's rest days
            away_rest: Away team's rest days
            home_previous_opponent: Home team's previous opponent (for travel calculation)
            away_previous_opponent: Away team's previous opponent (for travel calculation)
            
        Returns:
            Tuple of (home_rest_info, away_rest_info)
        """
        # Calculate travel fatigue for each team
        home_travel_fatigue = 0.0
        away_travel_fatigue = 0.0
        
        if home_previous_opponent:
            home_travel_info = self.travel_calc.get_travel_info(home_previous_opponent, home_team, home_rest)
            home_travel_fatigue = home_travel_info.fatigue_factor
        
        if away_previous_opponent:
            away_travel_info = self.travel_calc.get_travel_info(away_previous_opponent, away_team, away_rest)
            away_travel_fatigue = away_travel_info.fatigue_factor
        
        # Calculate rest advantages
        home_rest_adv, away_rest_adv = self.calculate_rest_advantage(
            home_rest, away_rest, home_travel_fatigue, away_travel_fatigue
        )
        
        # Calculate travel penalties
        home_travel_penalty = self.calculate_travel_penalty(home_travel_fatigue, home_rest)
        away_travel_penalty = self.calculate_travel_penalty(away_travel_fatigue, away_rest)
        
        # Calculate short week penalties
        home_short_week_penalty = self.calculate_short_week_penalty(home_rest)
        away_short_week_penalty = self.calculate_short_week_penalty(away_rest)
        
        # Calculate recovery factors
        home_recovery = max(0.0, 1.0 - home_travel_fatigue * 0.5)
        away_recovery = max(0.0, 1.0 - away_travel_fatigue * 0.5)
        
        # Create rest day info objects
        home_info = RestDayInfo(
            days_off=home_rest,
            travel_fatigue=home_travel_fatigue,
            recovery_factor=home_recovery,
            rest_advantage=home_rest_adv,
            travel_penalty=home_travel_penalty + home_short_week_penalty
        )
        
        away_info = RestDayInfo(
            days_off=away_rest,
            travel_fatigue=away_travel_fatigue,
            recovery_factor=away_recovery,
            rest_advantage=away_rest_adv,
            travel_penalty=away_travel_penalty + away_short_week_penalty
        )
        
        return home_info, away_info
    
    def calculate_travel_adjustments(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate travel adjustments for all games.
        
        Args:
            games_df: DataFrame with game data
            
        Returns:
            DataFrame with travel adjustments added
        """
        games_with_travel = games_df.copy()
        
        # Add travel adjustment columns
        travel_columns = [
            'home_travel_fatigue', 'away_travel_fatigue',
            'home_travel_penalty', 'away_travel_penalty',
            'home_rest_advantage', 'away_rest_advantage',
            'travel_advantage', 'rest_advantage'
        ]
        
        for col in travel_columns:
            games_with_travel[col] = 0.0
        
        # Calculate travel data for each game
        for idx, game in games_with_travel.iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            home_rest = game.get('home_rest', 7)
            away_rest = game.get('away_rest', 7)
            
            # Get previous opponents (simplified - would need game history in real implementation)
            home_previous_opponent = None
            away_previous_opponent = None
            
            # Calculate rest day info
            home_rest_info, away_rest_info = self.get_rest_day_info(
                home_team, away_team, home_rest, away_rest,
                home_previous_opponent, away_previous_opponent
            )
            
            # Add travel data
            games_with_travel.loc[idx, 'home_travel_fatigue'] = home_rest_info.travel_fatigue
            games_with_travel.loc[idx, 'away_travel_fatigue'] = away_rest_info.travel_fatigue
            games_with_travel.loc[idx, 'home_travel_penalty'] = home_rest_info.travel_penalty
            games_with_travel.loc[idx, 'away_travel_penalty'] = away_rest_info.travel_penalty
            games_with_travel.loc[idx, 'home_rest_advantage'] = home_rest_info.rest_advantage
            games_with_travel.loc[idx, 'away_rest_advantage'] = away_rest_info.rest_advantage
            
            # Calculate net advantages
            travel_advantage = away_rest_info.travel_penalty - home_rest_info.travel_penalty
            rest_advantage = home_rest_info.rest_advantage - away_rest_info.rest_advantage
            
            games_with_travel.loc[idx, 'travel_advantage'] = travel_advantage
            games_with_travel.loc[idx, 'rest_advantage'] = rest_advantage
        
        return games_with_travel
    
    def test_travel_adjustments(self):
        """Test travel adjustment calculations."""
        print("Testing Travel Adjustments...")
        
        # Test rest advantage calculation
        home_adv, away_adv = self.calculate_rest_advantage(7, 6, 0.0, 0.0)
        print(f"Rest advantage (7 vs 6 days): Home={home_adv:.1f}, Away={away_adv:.1f}")
        
        # Test travel penalty
        penalty = self.calculate_travel_penalty(0.5, 1)
        print(f"Travel penalty (0.5 fatigue, 1 day): {penalty:.1f}")
        
        # Test short week penalty
        short_week = self.calculate_short_week_penalty(6)
        print(f"Short week penalty (6 days): {short_week:.1f}")
        
        # Test comprehensive rest day info
        home_info, away_info = self.get_rest_day_info('NYJ', 'LAR', 7, 6)
        print(f"Rest day info: Home={home_info}, Away={away_info}")
        
        print("Travel adjustments working!")


def test_travel_adjustments():
    """Test the travel adjustment calculator."""
    calculator = TravelAdjustmentCalculator()
    calculator.test_travel_adjustments()


if __name__ == "__main__":
    test_travel_adjustments()
