"""Situational efficiency data loader for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .situational_efficiency_calculator import SituationalEfficiencyCalculator


def load_situational_data(years: List[int]) -> pd.DataFrame:
    """
    Load situational efficiency data for specified years.
    
    Args:
        years: Years to load data for
        
    Returns:
        DataFrame with situational efficiency impact scores
    """
    print(f"Loading situational efficiency data for years {years}...")
    
    # Create situational efficiency calculator
    calculator = SituationalEfficiencyCalculator()
    
    # Create situational efficiency database
    situational_db = calculator.create_situational_database(years)
    
    if situational_db.empty:
        print("No situational efficiency data loaded")
        return pd.DataFrame()
    
    print(f"Loaded situational efficiency data for {len(situational_db)} teams")
    return situational_db


def merge_situational_into_games(games: pd.DataFrame, situational_db: pd.DataFrame) -> pd.DataFrame:
    """
    Merge situational efficiency data into games DataFrame.
    
    Args:
        games: Games DataFrame
        situational_db: Situational efficiency database
        
    Returns:
        Games DataFrame with situational efficiency impacts added
    """
    print("Merging situational efficiency data into games...")
    
    if situational_db.empty:
        print("No situational efficiency data to merge")
        # Add empty columns
        games['home_situational_impact'] = 0.0
        games['away_situational_impact'] = 0.0
        return games
    
    # Create a copy to avoid modifying original
    games_with_situational = games.copy()
    
    # Add situational efficiency impact columns
    games_with_situational['home_situational_impact'] = 0.0
    games_with_situational['away_situational_impact'] = 0.0
    
    # Map team names to situational efficiency impacts
    for idx, game in games_with_situational.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get situational efficiency impacts
        if home_team in situational_db.index:
            home_impact = situational_db.loc[home_team, 'situational_efficiency']
            games_with_situational.at[idx, 'home_situational_impact'] = home_impact
        
        if away_team in situational_db.index:
            away_impact = situational_db.loc[away_team, 'situational_efficiency']
            games_with_situational.at[idx, 'away_situational_impact'] = away_impact
    
    print(f"Merged situational efficiency data into {len(games_with_situational)} games")
    return games_with_situational


def create_situational_config() -> Dict[str, Any]:
    """
    Create situational efficiency configuration.
    
    Returns:
        Dictionary with situational efficiency configuration
    """
    return {
        'use_situational_adjustment': True,
        'situational_adjustment_weight': 1.0,
        'situational_max_delta': 5.0,
        'situational_impact_threshold': 0.01
    }


def test_situational_data_loader():
    """Test situational efficiency data loader."""
    print("📊 TESTING SITUATIONAL EFFICIENCY DATA LOADER")
    print("="*80)
    
    # Test with 2024 data
    years = [2024]
    situational_db = load_situational_data(years)
    
    if situational_db.empty:
        print("No data loaded, cannot test")
        return
    
    print(f"\\nSituational efficiency database created with {len(situational_db)} teams")
    
    # Show sample data
    print("\\nSample situational efficiency data:")
    print(situational_db[['situational_efficiency', 'situational_impact_score']].head())
    
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
    
    # Merge situational efficiency data
    games_with_situational = merge_situational_into_games(sample_games, situational_db)
    
    print("\\nSample games with situational efficiency data:")
    print(games_with_situational[['home_team', 'away_team', 'home_situational_impact', 'away_situational_impact']])
    
    # Test configuration
    config = create_situational_config()
    print(f"\\nSituational efficiency configuration: {config}")
    
    return situational_db, games_with_situational


if __name__ == "__main__":
    situational_db, games_with_situational = test_situational_data_loader()
