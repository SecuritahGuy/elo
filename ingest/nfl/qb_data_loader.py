"""QB data loader for NFL Elo system."""

import pandas as pd
import nfl_data_py as nfl
from typing import List, Dict, Optional, Tuple
import numpy as np


def load_qb_depth_charts(years: List[int]) -> pd.DataFrame:
    """
    Load QB depth chart data to track starting QBs.
    
    Args:
        years: List of years to load data for
        
    Returns:
        DataFrame with QB depth chart information
    """
    try:
        depth_charts = nfl.import_depth_charts(years)
        
        # Filter for QBs only
        qb_depth = depth_charts[depth_charts['position'] == 'QB'].copy()
        
        # Clean and standardize columns
        qb_depth = qb_depth.rename(columns={
            'club_code': 'team',
            'full_name': 'player_name',
            'depth_position': 'qb_position'
        })
        
        # Select relevant columns
        columns = ['season', 'week', 'team', 'player_name', 'gsis_id', 'qb_position', 'jersey_number']
        qb_depth = qb_depth[columns].copy()
        
        # Add QB rank (1 = starter, 2 = backup, etc.)
        qb_depth['qb_rank'] = qb_depth['qb_position'].map({
            'QB': 1,
            'QB2': 2, 
            'QB3': 3,
            'QB4': 4
        }).fillna(5)  # Unknown position = rank 5
        
        return qb_depth
        
    except Exception as e:
        print(f"Error loading QB depth charts: {e}")
        return pd.DataFrame()


def load_qb_weekly_rosters(years: List[int]) -> pd.DataFrame:
    """
    Load weekly roster data to track QB availability.
    
    Args:
        years: List of years to load data for
        
    Returns:
        DataFrame with QB roster information
    """
    try:
        rosters = nfl.import_weekly_rosters(years)
        
        # Filter for QBs only
        qb_rosters = rosters[rosters['position'] == 'QB'].copy()
        
        # Select relevant columns
        columns = ['season', 'week', 'team', 'player_name', 'player_id', 'status', 'years_exp']
        qb_rosters = qb_rosters[columns].copy()
        
        # Map status to availability
        status_map = {
            'ACT': 'active',
            'RES': 'reserve',
            'PUP': 'pup',
            'IR': 'injured_reserve',
            'SUS': 'suspended',
            'EXE': 'exempt'
        }
        qb_rosters['availability'] = qb_rosters['status'].map(status_map).fillna('unknown')
        
        return qb_rosters
        
    except Exception as e:
        print(f"Error loading QB weekly rosters: {e}")
        return pd.DataFrame()


def load_qb_performance(years: List[int]) -> pd.DataFrame:
    """
    Load QB performance data from weekly stats including EPA.
    
    Args:
        years: List of years to load data for
        
    Returns:
        DataFrame with QB performance metrics
    """
    try:
        # Use weekly data instead of QBR data for more comprehensive stats
        weekly_data = nfl.import_weekly_data(years)
        
        # Filter for QBs only
        qb_data = weekly_data[weekly_data['position'] == 'QB'].copy()
        
        # Clean and standardize columns
        qb_data = qb_data.rename(columns={
            'recent_team': 'team',
            'player_display_name': 'player_name'
        })
        
        # Filter for regular season only
        qb_data = qb_data[qb_data['season_type'] == 'REG'].copy()
        
        # Select relevant columns for QB performance
        columns = [
            'season', 'week', 'team', 'player_name', 'player_id',
            'completions', 'attempts', 'passing_yards', 'passing_tds', 
            'interceptions', 'sacks', 'passing_epa', 'rushing_epa',
            'fantasy_points', 'opponent_team'
        ]
        
        # Only include columns that exist
        available_columns = [col for col in columns if col in qb_data.columns]
        qb_data = qb_data[available_columns].copy()
        
        # Add calculated metrics
        if 'completions' in qb_data.columns and 'attempts' in qb_data.columns:
            qb_data['completion_pct'] = (qb_data['completions'] / qb_data['attempts'] * 100).round(2)
        
        if 'passing_epa' in qb_data.columns and 'rushing_epa' in qb_data.columns:
            qb_data['total_epa'] = qb_data['passing_epa'] + qb_data['rushing_epa']
        
        # Add QB performance rating (simplified)
        if 'passing_epa' in qb_data.columns:
            qb_data['qb_rating'] = (qb_data['passing_epa'] * 100).round(2)
        
        print(f"Loaded {len(qb_data)} QB performance records")
        return qb_data
        
    except Exception as e:
        print(f"Error loading QB performance data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def load_qb_play_by_play_epa(years: List[int], sample_size: Optional[int] = None) -> pd.DataFrame:
    """
    Load QB EPA data from play-by-play for more detailed analysis.
    
    Args:
        years: List of years to load data for
        sample_size: Optional limit on number of plays to load (for testing)
        
    Returns:
        DataFrame with QB EPA data
    """
    try:
        # Load play-by-play data
        pbp = nfl.import_pbp_data(years, downcast=True)
        
        # Filter for passing plays with QB data
        qb_plays = pbp[
            (pbp['play_type'] == 'pass') & 
            (pbp['passer_player_name'].notna()) &
            (pbp['qb_epa'].notna())
        ].copy()
        
        if sample_size:
            qb_plays = qb_plays.head(sample_size)
        
        # Select relevant columns
        columns = [
            'season', 'week', 'home_team', 'away_team', 'posteam',
            'passer_player_name', 'passer_player_id', 'qb_epa', 'epa',
            'air_epa', 'yac_epa', 'pass_attempt', 'complete_pass',
            'passing_yards', 'pass_touchdown', 'interception', 'sack'
        ]
        qb_plays = qb_plays[columns].copy()
        
        # Add team context
        qb_plays['team'] = qb_plays['posteam']
        
        return qb_plays
        
    except Exception as e:
        print(f"Error loading QB play-by-play data: {e}")
        return pd.DataFrame()


def create_qb_weekly_summary(years: List[int]) -> pd.DataFrame:
    """
    Create a comprehensive weekly QB summary combining all data sources.
    
    Args:
        years: List of years to load data for
        
    Returns:
        DataFrame with comprehensive QB weekly data
    """
    # Load all data sources
    depth_charts = load_qb_depth_charts(years)
    rosters = load_qb_weekly_rosters(years)
    performance = load_qb_performance(years)
    
    if depth_charts.empty and rosters.empty and performance.empty:
        return pd.DataFrame()
    
    # Start with depth charts as base (most reliable for starters)
    if not depth_charts.empty:
        qb_summary = depth_charts.copy()
        
        # Merge with roster data
        if not rosters.empty:
            qb_summary = qb_summary.merge(
                rosters[['season', 'week', 'team', 'player_name', 'availability', 'years_exp']],
                on=['season', 'week', 'team', 'player_name'],
                how='left'
            )
        
        # Merge with performance data
        if not performance.empty:
            # Only merge columns that exist in performance data
            perf_cols = ['season', 'week', 'team', 'player_name']
            available_perf_cols = [col for col in ['qbr_total', 'epa_total', 'qb_plays'] if col in performance.columns]
            merge_cols = perf_cols + available_perf_cols
            
            qb_summary = qb_summary.merge(
                performance[merge_cols],
                on=['season', 'week', 'team', 'player_name'],
                how='left'
            )
    else:
        # Fallback to rosters if depth charts not available
        qb_summary = rosters.copy()
        
        # Merge with performance data
        if not performance.empty:
            # Only merge columns that exist in performance data
            perf_cols = ['season', 'week', 'team', 'player_name']
            available_perf_cols = [col for col in ['qbr_total', 'epa_total', 'qb_plays'] if col in performance.columns]
            merge_cols = perf_cols + available_perf_cols
            
            qb_summary = qb_summary.merge(
                performance[merge_cols],
                on=['season', 'week', 'team', 'player_name'],
                how='left'
            )
    
    # Add derived fields
    qb_summary['is_starter'] = qb_summary.get('qb_rank', 0) == 1
    qb_summary['is_active'] = qb_summary.get('availability', 'unknown') == 'active'
    
    # Fill missing values
    qb_summary['qb_rank'] = qb_summary.get('qb_rank', 0).fillna(5)
    qb_summary['is_starter'] = qb_summary['is_starter'].fillna(False)
    qb_summary['is_active'] = qb_summary['is_active'].fillna(True)
    
    return qb_summary


def get_team_starting_qb(team: str, season: int, week: int, qb_data: pd.DataFrame) -> Optional[Dict]:
    """
    Get the starting QB for a specific team, season, and week.
    
    Args:
        team: Team abbreviation
        season: Season year
        week: Week number
        qb_data: QB summary data
        
    Returns:
        Dictionary with QB information or None if not found
    """
    qb_info = qb_data[
        (qb_data['team'] == team) &
        (qb_data['season'] == season) &
        (qb_data['week'] == week) &
        (qb_data['is_starter'] == True)
    ]
    
    if qb_info.empty:
        return None
    
    # Return the first (should be only) starting QB
    qb = qb_info.iloc[0]
    return {
        'player_name': qb['player_name'],
        'player_id': qb.get('player_id'),
        'gsis_id': qb.get('gsis_id'),
        'qb_rank': qb.get('qb_rank', 1),
        'is_active': qb.get('is_active', True),
        'availability': qb.get('availability', 'active'),
        'years_exp': qb.get('years_exp'),
        'qbr_total': qb.get('qbr_total'),
        'epa_total': qb.get('epa_total'),
        'qb_plays': qb.get('qb_plays')
    }


def calculate_qb_change_impact(
    home_qb: Optional[Dict], 
    away_qb: Optional[Dict],
    qb_performance_history: pd.DataFrame
) -> Tuple[float, float]:
    """
    Calculate the impact of QB changes on expected performance.
    
    Args:
        home_qb: Home team QB info
        away_qb: Away team QB info  
        qb_performance_history: Historical QB performance data
        
    Returns:
        Tuple of (home_qb_delta, away_qb_delta) in rating points
    """
    # For now, return simple adjustments based on QB experience and performance
    # This is a placeholder - will be enhanced with more sophisticated logic
    
    home_delta = 0.0
    away_delta = 0.0
    
    if home_qb:
        # Simple adjustment based on years of experience
        years_exp = home_qb.get('years_exp', 0)
        if years_exp < 2:  # Rookie or 2nd year
            home_delta = -2.0  # Slight disadvantage
        elif years_exp > 8:  # Veteran
            home_delta = 1.0   # Slight advantage
        
        # Adjustment based on recent QBR
        qbr = home_qb.get('qbr_total')
        if qbr is not None:
            if qbr > 70:  # Excellent QBR
                home_delta += 3.0
            elif qbr < 30:  # Poor QBR
                home_delta -= 3.0
    
    if away_qb:
        # Same logic for away QB
        years_exp = away_qb.get('years_exp', 0)
        if years_exp < 2:
            away_delta = -2.0
        elif years_exp > 8:
            away_delta = 1.0
        
        qbr = away_qb.get('qbr_total')
        if qbr is not None:
            if qbr > 70:
                away_delta += 3.0
            elif qbr < 30:
                away_delta -= 3.0
    
    return home_delta, away_delta


def validate_qb_data(df: pd.DataFrame) -> bool:
    """
    Validate QB data quality.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if data is valid, False otherwise
    """
    if df.empty:
        return False
    
    required_columns = ['season', 'week', 'team', 'player_name']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Missing required QB data columns: {missing_columns}")
        return False
    
    # Check for reasonable values
    if 'season' in df.columns:
        if df['season'].min() < 2000 or df['season'].max() > 2030:
            print("Invalid season values in QB data")
            return False
    
    if 'week' in df.columns:
        if df['week'].min() < 1 or df['week'].max() > 22:
            print("Invalid week values in QB data")
            return False
    
    return True
