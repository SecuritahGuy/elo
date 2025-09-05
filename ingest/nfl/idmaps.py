"""Team ID mapping utilities for NFL data."""

from typing import Dict, Optional
import pandas as pd


def create_team_id_map(df: pd.DataFrame) -> Dict[str, str]:
    """
    Create a mapping from team abbreviations to standardized team names.
    
    Args:
        df: DataFrame with team information
        
    Returns:
        Dictionary mapping team abbreviations to standardized names
    """
    if "team_abbr" in df.columns and "team_name" in df.columns:
        return dict(zip(df["team_abbr"], df["team_name"]))
    elif "abbr" in df.columns and "team_name" in df.columns:
        return dict(zip(df["abbr"], df["team_name"]))
    else:
        # Fallback to a basic mapping if columns don't exist
        return {}


def normalize_team_name(team_name: str, team_map: Optional[Dict[str, str]] = None) -> str:
    """
    Normalize team name to a standard format.
    
    Args:
        team_name: Raw team name or abbreviation
        team_map: Optional mapping dictionary
        
    Returns:
        Normalized team name
    """
    if team_map and team_name in team_map:
        return team_map[team_name]
    
    # Basic normalization - remove common suffixes and standardize
    normalized = team_name.strip().upper()
    
    # Handle common variations
    variations = {
        "LAR": "LA RAMS",
        "LAC": "LA CHARGERS", 
        "LV": "LAS VEGAS RAIDERS",
        "GB": "GREEN BAY PACKERS",
        "KC": "KANSAS CITY CHIEFS",
        "TB": "TAMPA BAY BUCCANEERS",
        "NE": "NEW ENGLAND PATRIOTS",
        "SF": "SAN FRANCISCO 49ERS",
        "NO": "NEW ORLEANS SAINTS"
    }
    
    return variations.get(normalized, normalized)


def get_unique_teams(df: pd.DataFrame) -> set:
    """
    Extract unique team names from game data.
    
    Args:
        df: DataFrame with game information
        
    Returns:
        Set of unique team names
    """
    teams = set()
    
    if "home_team" in df.columns:
        teams.update(df["home_team"].dropna().unique())
    if "away_team" in df.columns:
        teams.update(df["away_team"].dropna().unique())
    
    return teams
