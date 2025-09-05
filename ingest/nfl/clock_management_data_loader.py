"""Clock management data loader for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .clock_management_calculator import ClockManagementCalculator


def load_clock_management_data(years: List[int]) -> pd.DataFrame:
    """
    Load clock management data for specified years.
    
    Args:
        years: Years to load data for
        
    Returns:
        DataFrame with clock management impact scores
    """
    print(f"Loading clock management data for years {years}...")
    
    # Create clock management calculator
    calculator = ClockManagementCalculator()
    
    # Create clock management database
    clock_db = calculator.create_clock_management_database(years)
    
    if clock_db.empty:
        print("No clock management data loaded")
        return pd.DataFrame()
    
    print(f"Loaded clock management data for {len(clock_db)} teams")
    return clock_db


def merge_clock_management_into_games(games: pd.DataFrame, clock_db: pd.DataFrame) -> pd.DataFrame:
    """
    Merge clock management data into games DataFrame.
    
    Args:
        games: Games DataFrame
        clock_db: Clock management database
        
    Returns:
        Games DataFrame with clock management impacts added
    """
    print("Merging clock management data into games...")
    
    if clock_db.empty:
        print("No clock management data to merge")
        # Add empty columns
        games['home_clock_management_impact'] = 0.0
        games['away_clock_management_impact'] = 0.0
        return games
    
    # Create a copy to avoid modifying original
    games_with_clock = games.copy()
    
    # Add clock management impact columns
    games_with_clock['home_clock_management_impact'] = 0.0
    games_with_clock['away_clock_management_impact'] = 0.0
    
    # Map team names to clock management impacts
    for idx, game in games_with_clock.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get clock management impacts
        if home_team in clock_db.index:
            home_impact = clock_db.loc[home_team, 'clock_management_efficiency']
            games_with_clock.at[idx, 'home_clock_management_impact'] = home_impact
        
        if away_team in clock_db.index:
            away_impact = clock_db.loc[away_team, 'clock_management_efficiency']
            games_with_clock.at[idx, 'away_clock_management_impact'] = away_impact
    
    print(f"Merged clock management data into {len(games_with_clock)} games")
    return games_with_clock


def create_clock_management_config() -> Dict[str, Any]:
    """
    Create clock management configuration.
    
    Returns:
        Dictionary with clock management configuration
    """
    return {
        'use_clock_management_adjustment': True,
        'clock_management_adjustment_weight': 1.0,
        'clock_management_max_delta': 4.0,
        'clock_management_impact_threshold': 0.01
    }


def test_clock_management_data_loader():
    """Test clock management data loader."""
    print("📊 TESTING CLOCK MANAGEMENT DATA LOADER")
    print("="*80)
    
    # Test with 2024 data
    years = [2024]
    clock_db = load_clock_management_data(years)
    
    if clock_db.empty:
        print("No data loaded, cannot test")
        return
    
    print(f"\\nClock management database created with {len(clock_db)} teams")
    
    # Show sample data
    print("\\nSample clock management data:")
    print(clock_db.head())
    
    # Test merging with sample games data
    print("\\nTesting merge with sample games data...")
    
    # Create sample games data
    sample_games = pd.DataFrame({
        'home_team': ['KC', 'BUF', 'TB', 'DET'],
        'away_team': ['BUF', 'KC', 'DET', 'TB'],
        'home_score': [24, 21, 28, 31],
        'away_score': [21, 24, 31, 28],
        'season': [2024, 2024, 2024, 2024],
        'week': [1, 1, 1, 1]
    })
    
    # Merge clock management data
    games_with_clock = merge_clock_management_into_games(sample_games, clock_db)
    
    print("\\nSample games with clock management data:")
    print(games_with_clock[['home_team', 'away_team', 'home_clock_management_impact', 'away_clock_management_impact']])
    
    # Test configuration
    config = create_clock_management_config()
    print(f"\\nClock management configuration: {config}")
    
    return clock_db, games_with_clock


if __name__ == "__main__":
    clock_db, games_with_clock = test_clock_management_data_loader()
