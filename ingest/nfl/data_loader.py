"""Data loader for NFL schedules and team information."""

import pandas as pd
import nfl_data_py as nfl
from typing import List, Optional


def load_games(years: List[int]) -> pd.DataFrame:
    """
    Load NFL game schedules and results for specified years.
    
    Args:
        years: List of years to load data for
        
    Returns:
        DataFrame with game information including scores and rest days
    """
    # Load schedules which include scores and winners
    df = nfl.import_schedules(years)
    
    # Normalize essential columns
    keep_columns = [
        "season", "week", "gameday", "game_id", "home_team", "away_team",
        "home_score", "away_score", "result", "home_rest", "away_rest"
    ]
    
    # Ensure all required columns exist, fill missing ones with None
    for col in ["home_rest", "away_rest"]:
        if col not in df.columns:
            df[col] = None
    
    # Filter to only keep the columns we need
    available_columns = [col for col in keep_columns if col in df.columns]
    df = df[available_columns].copy()
    
    # Ensure numeric columns are properly typed
    numeric_columns = ["home_score", "away_score", "home_rest", "away_rest"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def load_team_reference() -> pd.DataFrame:
    """
    Load team reference information.
    
    Returns:
        DataFrame with team information including abbreviations and names
    """
    # Load team descriptions
    df = nfl.import_team_desc()
    
    # Rename columns for consistency
    if "team_abbr" in df.columns:
        df = df.rename(columns={"team_abbr": "abbr"})
    
    return df


def load_play_by_play(years: List[int]) -> pd.DataFrame:
    """
    Load play-by-play data for specified years (for future EPA features).
    
    Args:
        years: List of years to load data for
        
    Returns:
        DataFrame with play-by-play information
    """
    # This is a placeholder for future EPA-based features
    # nfl_data_py provides play-by-play data via nfl.import_pbp_data()
    return pd.DataFrame()


def save_games_to_csv(games: pd.DataFrame, filepath: str) -> None:
    """
    Save games DataFrame to CSV file.
    
    Args:
        games: DataFrame with game data
        filepath: Path to save the CSV file
    """
    games.to_csv(filepath, index=False)


def load_games_from_csv(filepath: str) -> pd.DataFrame:
    """
    Load games DataFrame from CSV file.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        DataFrame with game data
    """
    return pd.read_csv(filepath)


def validate_game_data(df: pd.DataFrame) -> bool:
    """
    Validate that game data has required columns and reasonable values.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if data is valid, False otherwise
    """
    required_columns = ["season", "week", "home_team", "away_team", "home_score", "away_score"]
    
    # Check required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        return False
    
    # Check for reasonable score values
    if df["home_score"].min() < 0 or df["away_score"].min() < 0:
        print("Found negative scores")
        return False
    
    # Check for reasonable week values
    if df["week"].min() < 1 or df["week"].max() > 22:  # Regular season + playoffs
        print("Found unreasonable week values")
        return False
    
    return True
