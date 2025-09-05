"""Red zone data loader for NFL games."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

from ingest.nfl.redzone_calculator import RedZoneCalculator


def add_redzone_data_to_games(games: pd.DataFrame, years: List[int]) -> pd.DataFrame:
    """
    Add red zone efficiency data to games DataFrame.
    
    Args:
        games: DataFrame with game data
        years: Years to analyze for red zone data
        
    Returns:
        DataFrame with red zone data added
    """
    print(f"Adding red zone data to {len(games)} games...")
    
    # Create red zone calculator
    redzone_calc = RedZoneCalculator()
    
    # Load red zone data
    redzone_db = redzone_calc.create_redzone_database(years)
    print(f"Loaded red zone data for {len(redzone_db)} teams")
    
    # Initialize red zone columns
    games['home_redzone_impact'] = 0.0
    games['away_redzone_impact'] = 0.0
    games['home_redzone_td_rate'] = 0.135  # League average
    games['away_redzone_td_rate'] = 0.135  # League average
    games['home_redzone_defense_td_rate'] = 0.135  # League average
    games['away_redzone_defense_td_rate'] = 0.135  # League average
    
    # Add red zone data for each game
    for idx, game in games.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get red zone ratings for both teams
        home_rating = redzone_calc.get_team_redzone_rating(home_team, redzone_db)
        away_rating = redzone_calc.get_team_redzone_rating(away_team, redzone_db)
        
        # Add red zone impact scores
        games.at[idx, 'home_redzone_impact'] = home_rating['redzone_impact_score']
        games.at[idx, 'away_redzone_impact'] = away_rating['redzone_impact_score']
        
        # Add red zone efficiency rates
        games.at[idx, 'home_redzone_td_rate'] = home_rating['off_redzone_td_rate']
        games.at[idx, 'away_redzone_td_rate'] = away_rating['off_redzone_td_rate']
        games.at[idx, 'home_redzone_defense_td_rate'] = home_rating['def_redzone_td_rate_allowed']
        games.at[idx, 'away_redzone_defense_td_rate'] = away_rating['def_redzone_td_rate_allowed']
    
    print(f"Red zone data added to {len(games)} games")
    return games


def test_redzone_data_loader():
    """Test the red zone data loader."""
    print("🔴 TESTING RED ZONE DATA LOADER")
    print("="*80)
    
    # Load sample games
    from ingest.nfl.data_loader import load_games
    games = load_games([2024])
    print(f"Loaded {len(games)} games")
    
    # Add red zone data
    games_with_redzone = add_redzone_data_to_games(games, [2024])
    
    # Show sample of red zone data
    print("\\nSample red zone data:")
    sample_cols = ['home_team', 'away_team', 'home_redzone_impact', 'away_redzone_impact', 
                   'home_redzone_td_rate', 'away_redzone_td_rate']
    print(games_with_redzone[sample_cols].head(10))
    
    # Show red zone statistics
    print("\\nRed zone statistics:")
    print(f"Home red zone impact range: {games_with_redzone['home_redzone_impact'].min():.3f} to {games_with_redzone['home_redzone_impact'].max():.3f}")
    print(f"Away red zone impact range: {games_with_redzone['away_redzone_impact'].min():.3f} to {games_with_redzone['away_redzone_impact'].max():.3f}")
    print(f"Average home red zone TD rate: {games_with_redzone['home_redzone_td_rate'].mean():.3f}")
    print(f"Average away red zone TD rate: {games_with_redzone['away_redzone_td_rate'].mean():.3f}")
    
    return games_with_redzone


if __name__ == "__main__":
    games_with_redzone = test_redzone_data_loader()
