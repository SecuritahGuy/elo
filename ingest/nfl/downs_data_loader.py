"""Down efficiency data loader for NFL games."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

from ingest.nfl.downs_calculator import DownsCalculator


def add_downs_data_to_games(games: pd.DataFrame, years: List[int]) -> pd.DataFrame:
    """
    Add down efficiency data to games DataFrame.
    
    Args:
        games: DataFrame with game data
        years: Years to analyze for down efficiency data
        
    Returns:
        DataFrame with down efficiency data added
    """
    print(f"Adding down efficiency data to {len(games)} games...")
    
    # Create down efficiency calculator
    downs_calc = DownsCalculator()
    
    # Load down efficiency data
    downs_db = downs_calc.create_downs_database(years)
    print(f"Loaded down efficiency data for {len(downs_db)} teams")
    
    # Initialize down efficiency columns
    games['home_downs_impact'] = 0.0
    games['away_downs_impact'] = 0.0
    games['home_third_down_rate'] = 0.36  # League average
    games['away_third_down_rate'] = 0.36  # League average
    games['home_third_down_defense_rate'] = 0.36  # League average
    games['away_third_down_defense_rate'] = 0.36  # League average
    games['home_fourth_down_rate'] = 0.11  # League average
    games['away_fourth_down_rate'] = 0.11  # League average
    games['home_fourth_down_defense_rate'] = 0.11  # League average
    games['away_fourth_down_defense_rate'] = 0.11  # League average
    
    # Add down efficiency data for each game
    for idx, game in games.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get down efficiency ratings for both teams
        home_rating = downs_calc.get_team_downs_rating(home_team, downs_db)
        away_rating = downs_calc.get_team_downs_rating(away_team, downs_db)
        
        # Add down efficiency impact scores
        games.at[idx, 'home_downs_impact'] = home_rating['downs_impact_score']
        games.at[idx, 'away_downs_impact'] = away_rating['downs_impact_score']
        
        # Add down efficiency rates
        games.at[idx, 'home_third_down_rate'] = home_rating['off_third_down_rate']
        games.at[idx, 'away_third_down_rate'] = away_rating['off_third_down_rate']
        games.at[idx, 'home_third_down_defense_rate'] = home_rating['def_third_down_rate_allowed']
        games.at[idx, 'away_third_down_defense_rate'] = away_rating['def_third_down_rate_allowed']
        games.at[idx, 'home_fourth_down_rate'] = home_rating['off_fourth_down_rate']
        games.at[idx, 'away_fourth_down_rate'] = away_rating['off_fourth_down_rate']
        games.at[idx, 'home_fourth_down_defense_rate'] = home_rating['def_fourth_down_rate_allowed']
        games.at[idx, 'away_fourth_down_defense_rate'] = away_rating['def_fourth_down_rate_allowed']
    
    print(f"Down efficiency data added to {len(games)} games")
    return games


def test_downs_data_loader():
    """Test the down efficiency data loader."""
    print("📊 TESTING DOWN EFFICIENCY DATA LOADER")
    print("="*80)
    
    # Load sample games
    from ingest.nfl.data_loader import load_games
    games = load_games([2024])
    print(f"Loaded {len(games)} games")
    
    # Add down efficiency data
    games_with_downs = add_downs_data_to_games(games, [2024])
    
    # Show sample of down efficiency data
    print("\\nSample down efficiency data:")
    sample_cols = ['home_team', 'away_team', 'home_downs_impact', 'away_downs_impact', 
                   'home_third_down_rate', 'away_third_down_rate']
    print(games_with_downs[sample_cols].head(10))
    
    # Show down efficiency statistics
    print("\\nDown efficiency statistics:")
    print(f"Home down efficiency impact range: {games_with_downs['home_downs_impact'].min():.3f} to {games_with_downs['home_downs_impact'].max():.3f}")
    print(f"Away down efficiency impact range: {games_with_downs['away_downs_impact'].min():.3f} to {games_with_downs['away_downs_impact'].max():.3f}")
    print(f"Average home third down rate: {games_with_downs['home_third_down_rate'].mean():.3f}")
    print(f"Average away third down rate: {games_with_downs['away_third_down_rate'].mean():.3f}")
    print(f"Average home fourth down rate: {games_with_downs['home_fourth_down_rate'].mean():.3f}")
    print(f"Average away fourth down rate: {games_with_downs['away_fourth_down_rate'].mean():.3f}")
    
    return games_with_downs


if __name__ == "__main__":
    games_with_downs = test_downs_data_loader()
