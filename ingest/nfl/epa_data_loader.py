"""EPA data loader for NFL Elo system."""

import pandas as pd
import nfl_data_py as nfl
from typing import List, Dict, Optional, Tuple
import numpy as np
from pathlib import Path


def load_epa_data(years: List[int], sample_size: Optional[int] = None) -> pd.DataFrame:
    """
    Load play-by-play EPA data from nfl-data-py.
    
    Args:
        years: List of years to load data for
        sample_size: Optional limit on number of plays to load (for testing)
        
    Returns:
        DataFrame with EPA data
    """
    try:
        # Load play-by-play data
        pbp = nfl.import_pbp_data(years, downcast=True)
        
        if sample_size:
            pbp = pbp.head(sample_size)
        
        # Select relevant EPA columns
        epa_columns = [
            'season', 'week', 'home_team', 'away_team', 'posteam', 'defteam',
            'play_type', 'passer_player_name', 'passer_player_id', 'rusher_player_name', 'rusher_player_id',
            'epa', 'qb_epa', 'air_epa', 'yac_epa', 'comp_air_epa', 'comp_yac_epa',
            'total_home_epa', 'total_away_epa', 'total_home_pass_epa', 'total_away_pass_epa',
            'total_home_rush_epa', 'total_away_rush_epa', 'pass_attempt', 'rush_attempt',
            'complete_pass', 'passing_yards', 'rushing_yards', 'pass_touchdown', 'rush_touchdown',
            'interception', 'sack', 'fumble_lost', 'first_down'
        ]
        
        # Only include columns that exist
        available_columns = [col for col in epa_columns if col in pbp.columns]
        epa_data = pbp[available_columns].copy()
        
        # Filter for relevant plays (exclude special teams, etc.)
        epa_data = epa_data[
            (epa_data['play_type'].isin(['pass', 'run', 'qb_kneel', 'qb_spike'])) |
            (epa_data['play_type'].isna())
        ].copy()
        
        # Clean up missing values
        epa_data = epa_data.fillna({
            'epa': 0.0,
            'qb_epa': 0.0,
            'air_epa': 0.0,
            'yac_epa': 0.0,
            'pass_attempt': 0,
            'rush_attempt': 0,
            'complete_pass': 0,
            'passing_yards': 0,
            'rushing_yards': 0,
            'pass_touchdown': 0,
            'rush_touchdown': 0,
            'interception': 0,
            'sack': 0,
            'fumble_lost': 0,
            'first_down': 0
        })
        
        return epa_data
        
    except Exception as e:
        print(f"Error loading EPA data: {e}")
        return pd.DataFrame()


def aggregate_team_epa(epa_data: pd.DataFrame, window: int = 4) -> pd.DataFrame:
    """
    Aggregate EPA data by team and week with rolling averages.
    
    Args:
        epa_data: Play-by-play EPA data
        window: Rolling window size for averages
        
    Returns:
        DataFrame with team-level EPA metrics
    """
    if epa_data.empty:
        return pd.DataFrame()
    
    # Group by team, season, week
    team_epa = epa_data.groupby(['season', 'week', 'posteam']).agg({
        'epa': ['sum', 'mean', 'count'],
        'qb_epa': ['sum', 'mean'],
        'air_epa': ['sum', 'mean'],
        'yac_epa': ['sum', 'mean'],
        'pass_attempt': 'sum',
        'rush_attempt': 'sum',
        'complete_pass': 'sum',
        'passing_yards': 'sum',
        'rushing_yards': 'sum',
        'pass_touchdown': 'sum',
        'rush_touchdown': 'sum',
        'interception': 'sum',
        'sack': 'sum',
        'fumble_lost': 'sum',
        'first_down': 'sum'
    }).reset_index()
    
    # Flatten column names
    team_epa.columns = ['season', 'week', 'team', 'total_epa', 'avg_epa', 'plays',
                       'total_qb_epa', 'avg_qb_epa', 'total_air_epa', 'avg_air_epa',
                       'total_yac_epa', 'avg_yac_epa', 'pass_attempts', 'rush_attempts',
                       'completions', 'passing_yards', 'rushing_yards', 'pass_tds',
                       'rush_tds', 'interceptions', 'sacks', 'fumbles', 'first_downs']
    
    # Calculate efficiency metrics
    team_epa['completion_rate'] = team_epa['completions'] / team_epa['pass_attempts'].replace(0, 1)
    team_epa['yards_per_attempt'] = team_epa['passing_yards'] / team_epa['pass_attempts'].replace(0, 1)
    team_epa['yards_per_carry'] = team_epa['rushing_yards'] / team_epa['rush_attempts'].replace(0, 1)
    team_epa['first_down_rate'] = team_epa['first_downs'] / team_epa['plays'].replace(0, 1)
    
    # Calculate rolling averages
    team_epa = team_epa.sort_values(['team', 'season', 'week']).reset_index(drop=True)
    
    rolling_cols = ['total_epa', 'avg_epa', 'total_qb_epa', 'avg_qb_epa', 
                   'total_air_epa', 'avg_air_epa', 'total_yac_epa', 'avg_yac_epa',
                   'completion_rate', 'yards_per_attempt', 'yards_per_carry', 'first_down_rate']
    
    for col in rolling_cols:
        if col in team_epa.columns:
            rolling_series = (
                team_epa.groupby('team')[col]
                .rolling(window=window, min_periods=1)
                .mean()
                .reset_index(0, drop=True)
            )
            team_epa[f'rolling_{col}_{window}wk'] = rolling_series.values
    
    return team_epa


def aggregate_qb_epa(epa_data: pd.DataFrame, window: int = 4) -> pd.DataFrame:
    """
    Aggregate EPA data by QB and week with rolling averages.
    
    Args:
        epa_data: Play-by-play EPA data
        window: Rolling window size for averages
        
    Returns:
        DataFrame with QB-level EPA metrics
    """
    if epa_data.empty:
        return pd.DataFrame()
    
    # Filter for passing plays with QB data
    qb_epa = epa_data[
        (epa_data['play_type'] == 'pass') &
        (epa_data['passer_player_name'].notna()) &
        (epa_data['qb_epa'].notna())
    ].copy()
    
    if qb_epa.empty:
        return pd.DataFrame()
    
    # Group by QB, season, week
    qb_metrics = qb_epa.groupby(['season', 'week', 'posteam', 'passer_player_name', 'passer_player_id']).agg({
        'epa': ['sum', 'mean', 'count'],
        'qb_epa': ['sum', 'mean'],
        'air_epa': ['sum', 'mean'],
        'yac_epa': ['sum', 'mean'],
        'pass_attempt': 'sum',
        'complete_pass': 'sum',
        'passing_yards': 'sum',
        'pass_touchdown': 'sum',
        'interception': 'sum',
        'sack': 'sum',
        'first_down': 'sum'
    }).reset_index()
    
    # Flatten column names
    qb_metrics.columns = ['season', 'week', 'team', 'qb_name', 'qb_id',
                         'total_epa', 'avg_epa', 'plays', 'total_qb_epa', 'avg_qb_epa',
                         'total_air_epa', 'avg_air_epa', 'total_yac_epa', 'avg_yac_epa',
                         'pass_attempts', 'completions', 'passing_yards', 'pass_tds',
                         'interceptions', 'sacks', 'first_downs']
    
    # Calculate QB efficiency metrics
    qb_metrics['completion_rate'] = qb_metrics['completions'] / qb_metrics['pass_attempts'].replace(0, 1)
    qb_metrics['yards_per_attempt'] = qb_metrics['passing_yards'] / qb_metrics['pass_attempts'].replace(0, 1)
    qb_metrics['td_rate'] = qb_metrics['pass_tds'] / qb_metrics['pass_attempts'].replace(0, 1)
    qb_metrics['int_rate'] = qb_metrics['interceptions'] / qb_metrics['pass_attempts'].replace(0, 1)
    qb_metrics['sack_rate'] = qb_metrics['sacks'] / qb_metrics['pass_attempts'].replace(0, 1)
    qb_metrics['first_down_rate'] = qb_metrics['first_downs'] / qb_metrics['pass_attempts'].replace(0, 1)
    
    # Calculate rolling averages
    qb_metrics = qb_metrics.sort_values(['qb_name', 'team', 'season', 'week']).reset_index(drop=True)
    
    rolling_cols = ['total_epa', 'avg_epa', 'total_qb_epa', 'avg_qb_epa',
                   'total_air_epa', 'avg_air_epa', 'total_yac_epa', 'avg_yac_epa',
                   'completion_rate', 'yards_per_attempt', 'td_rate', 'int_rate', 'sack_rate', 'first_down_rate']
    
    for col in rolling_cols:
        if col in qb_metrics.columns:
            rolling_series = (
                qb_metrics.groupby(['qb_name', 'team'])[col]
                .rolling(window=window, min_periods=1)
                .mean()
                .reset_index(0, drop=True)
            )
            qb_metrics[f'rolling_{col}_{window}wk'] = rolling_series.values
    
    return qb_metrics


def get_team_epa_at_week(team: str, season: int, week: int, 
                        team_epa_data: pd.DataFrame) -> Optional[Dict]:
    """
    Get team EPA metrics for a specific week.
    
    Args:
        team: Team abbreviation
        season: Season year
        week: Week number
        team_epa_data: Team EPA aggregated data
        
    Returns:
        Dictionary with team EPA metrics or None if not found
    """
    team_week_data = team_epa_data[
        (team_epa_data['team'] == team) &
        (team_epa_data['season'] == season) &
        (team_epa_data['week'] == week)
    ]
    
    if team_week_data.empty:
        return None
    
    row = team_week_data.iloc[0]
    return {
        'total_epa': row.get('total_epa', 0.0),
        'avg_epa': row.get('avg_epa', 0.0),
        'plays': row.get('plays', 0),
        'total_qb_epa': row.get('total_qb_epa', 0.0),
        'avg_qb_epa': row.get('avg_qb_epa', 0.0),
        'rolling_avg_epa_4wk': row.get('rolling_avg_epa_4wk', 0.0),
        'rolling_avg_qb_epa_4wk': row.get('rolling_avg_qb_epa_4wk', 0.0),
        'completion_rate': row.get('completion_rate', 0.0),
        'yards_per_attempt': row.get('yards_per_attempt', 0.0),
        'first_down_rate': row.get('first_down_rate', 0.0)
    }


def get_qb_epa_at_week(qb_name: str, team: str, season: int, week: int,
                      qb_epa_data: pd.DataFrame) -> Optional[Dict]:
    """
    Get QB EPA metrics for a specific week.
    
    Args:
        qb_name: QB name
        team: Team abbreviation
        season: Season year
        week: Week number
        qb_epa_data: QB EPA aggregated data
        
    Returns:
        Dictionary with QB EPA metrics or None if not found
    """
    qb_week_data = qb_epa_data[
        (qb_epa_data['qb_name'] == qb_name) &
        (qb_epa_data['team'] == team) &
        (qb_epa_data['season'] == season) &
        (qb_epa_data['week'] == week)
    ]
    
    if qb_week_data.empty:
        return None
    
    row = qb_week_data.iloc[0]
    return {
        'total_epa': row.get('total_epa', 0.0),
        'avg_epa': row.get('avg_epa', 0.0),
        'plays': row.get('plays', 0),
        'total_qb_epa': row.get('total_qb_epa', 0.0),
        'avg_qb_epa': row.get('avg_qb_epa', 0.0),
        'rolling_avg_epa_4wk': row.get('rolling_avg_epa_4wk', 0.0),
        'rolling_avg_qb_epa_4wk': row.get('rolling_avg_qb_epa_4wk', 0.0),
        'completion_rate': row.get('completion_rate', 0.0),
        'yards_per_attempt': row.get('yards_per_attempt', 0.0),
        'td_rate': row.get('td_rate', 0.0),
        'int_rate': row.get('int_rate', 0.0),
        'sack_rate': row.get('sack_rate', 0.0),
        'first_down_rate': row.get('first_down_rate', 0.0)
    }


def save_epa_data(team_epa_data: pd.DataFrame, qb_epa_data: pd.DataFrame, 
                 output_dir: str) -> None:
    """
    Save EPA data to CSV files.
    
    Args:
        team_epa_data: Team EPA aggregated data
        qb_epa_data: QB EPA aggregated data
        output_dir: Directory to save files
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    if not team_epa_data.empty:
        team_file = output_path / "team_epa_data.csv"
        team_epa_data.to_csv(team_file, index=False)
        print(f"Team EPA data saved to {team_file}")
    
    if not qb_epa_data.empty:
        qb_file = output_path / "qb_epa_data.csv"
        qb_epa_data.to_csv(qb_file, index=False)
        print(f"QB EPA data saved to {qb_file}")


def load_epa_data_from_csv(team_file: str, qb_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load EPA data from CSV files.
    
    Args:
        team_file: Path to team EPA CSV file
        qb_file: Path to QB EPA CSV file
        
    Returns:
        Tuple of (team_epa_data, qb_epa_data)
    """
    team_epa_data = pd.DataFrame()
    qb_epa_data = pd.DataFrame()
    
    if Path(team_file).exists():
        team_epa_data = pd.read_csv(team_file)
        print(f"Team EPA data loaded from {team_file}")
    
    if Path(qb_file).exists():
        qb_epa_data = pd.read_csv(qb_file)
        print(f"QB EPA data loaded from {qb_file}")
    
    return team_epa_data, qb_epa_data


def validate_epa_data(epa_data: pd.DataFrame) -> bool:
    """
    Validate EPA data quality.
    
    Args:
        epa_data: EPA data to validate
        
    Returns:
        True if data is valid, False otherwise
    """
    if epa_data.empty:
        return False
    
    required_columns = ['season', 'week', 'posteam', 'epa']
    missing_columns = [col for col in required_columns if col not in epa_data.columns]
    
    if missing_columns:
        print(f"Missing required EPA data columns: {missing_columns}")
        return False
    
    # Check for reasonable values
    if 'season' in epa_data.columns:
        if epa_data['season'].min() < 2000 or epa_data['season'].max() > 2030:
            print("Invalid season values in EPA data")
            return False
    
    if 'week' in epa_data.columns:
        if epa_data['week'].min() < 1 or epa_data['week'].max() > 22:
            print("Invalid week values in EPA data")
            return False
    
    return True
