"""EPA aggregation system for NFL Elo ratings."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TeamEPAMetrics:
    """Team EPA metrics for a specific period."""
    team: str
    season: int
    week: int
    total_epa: float
    avg_epa: float
    plays: int
    total_qb_epa: float
    avg_qb_epa: float
    total_air_epa: float
    avg_air_epa: float
    total_yac_epa: float
    avg_yac_epa: float
    completion_rate: float
    yards_per_attempt: float
    yards_per_carry: float
    first_down_rate: float
    rolling_avg_epa_4wk: float
    rolling_avg_epa_8wk: float
    rolling_avg_qb_epa_4wk: float
    rolling_avg_qb_epa_8wk: float


@dataclass
class QBEPAMetrics:
    """QB EPA metrics for a specific period."""
    qb_name: str
    team: str
    season: int
    week: int
    total_epa: float
    avg_epa: float
    plays: int
    total_qb_epa: float
    avg_qb_epa: float
    total_air_epa: float
    avg_air_epa: float
    total_yac_epa: float
    avg_yac_epa: float
    completion_rate: float
    yards_per_attempt: float
    td_rate: float
    int_rate: float
    sack_rate: float
    first_down_rate: float
    rolling_avg_epa_4wk: float
    rolling_avg_epa_8wk: float
    rolling_avg_qb_epa_4wk: float
    rolling_avg_qb_epa_8wk: float


class EPAAggregator:
    """Aggregates and tracks EPA metrics for teams and QBs."""
    
    def __init__(self, epa_data: pd.DataFrame):
        """
        Initialize EPA aggregator.
        
        Args:
            epa_data: Play-by-play EPA data
        """
        self.epa_data = epa_data.copy()
        self.team_metrics: List[TeamEPAMetrics] = []
        self.qb_metrics: List[QBEPAMetrics] = []
        
    def calculate_team_metrics(self, window_4: int = 4, window_8: int = 8) -> pd.DataFrame:
        """
        Calculate comprehensive team EPA metrics.
        
        Args:
            window_4: Rolling window for 4-week metrics
            window_8: Rolling window for 8-week metrics
            
        Returns:
            DataFrame with team EPA metrics
        """
        if self.epa_data.empty:
            return pd.DataFrame()
        
        # Group by team, season, week
        team_agg = self.epa_data.groupby(['season', 'week', 'posteam']).agg({
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
        team_agg.columns = ['season', 'week', 'team', 'total_epa', 'avg_epa', 'plays',
                           'total_qb_epa', 'avg_qb_epa', 'total_air_epa', 'avg_air_epa',
                           'total_yac_epa', 'avg_yac_epa', 'pass_attempts', 'rush_attempts',
                           'completions', 'passing_yards', 'rushing_yards', 'pass_tds',
                           'rush_tds', 'interceptions', 'sacks', 'fumbles', 'first_downs']
        
        # Calculate efficiency metrics
        team_agg['completion_rate'] = team_agg['completions'] / team_agg['pass_attempts'].replace(0, 1)
        team_agg['yards_per_attempt'] = team_agg['passing_yards'] / team_agg['pass_attempts'].replace(0, 1)
        team_agg['yards_per_carry'] = team_agg['rushing_yards'] / team_agg['rush_attempts'].replace(0, 1)
        team_agg['first_down_rate'] = team_agg['first_downs'] / team_agg['plays'].replace(0, 1)
        
        # Calculate rolling averages
        team_agg = team_agg.sort_values(['team', 'season', 'week']).reset_index(drop=True)
        
        rolling_cols = ['avg_epa', 'avg_qb_epa', 'completion_rate', 'yards_per_attempt', 
                       'yards_per_carry', 'first_down_rate']
        
        for col in rolling_cols:
            if col in team_agg.columns:
                # 4-week rolling average
                rolling_4wk = (
                    team_agg.groupby('team')[col]
                    .rolling(window=window_4, min_periods=1)
                    .mean()
                    .reset_index(0, drop=True)
                )
                team_agg[f'rolling_{col}_{window_4}wk'] = rolling_4wk.values
                
                # 8-week rolling average
                rolling_8wk = (
                    team_agg.groupby('team')[col]
                    .rolling(window=window_8, min_periods=1)
                    .mean()
                    .reset_index(0, drop=True)
                )
                team_agg[f'rolling_{col}_{window_8}wk'] = rolling_8wk.values
        
        return team_agg
    
    def calculate_qb_metrics(self, window_4: int = 4, window_8: int = 8) -> pd.DataFrame:
        """
        Calculate comprehensive QB EPA metrics.
        
        Args:
            window_4: Rolling window for 4-week metrics
            window_8: Rolling window for 8-week metrics
            
        Returns:
            DataFrame with QB EPA metrics
        """
        if self.epa_data.empty:
            return pd.DataFrame()
        
        # Filter for passing plays with QB data
        qb_data = self.epa_data[
            (self.epa_data['play_type'] == 'pass') &
            (self.epa_data['passer_player_name'].notna()) &
            (self.epa_data['qb_epa'].notna())
        ].copy()
        
        if qb_data.empty:
            return pd.DataFrame()
        
        # Group by QB, season, week
        qb_agg = qb_data.groupby(['season', 'week', 'posteam', 'passer_player_name', 'passer_player_id']).agg({
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
        qb_agg.columns = ['season', 'week', 'team', 'qb_name', 'qb_id',
                         'total_epa', 'avg_epa', 'plays', 'total_qb_epa', 'avg_qb_epa',
                         'total_air_epa', 'avg_air_epa', 'total_yac_epa', 'avg_yac_epa',
                         'pass_attempts', 'completions', 'passing_yards', 'pass_tds',
                         'interceptions', 'sacks', 'first_downs']
        
        # Calculate QB efficiency metrics
        qb_agg['completion_rate'] = qb_agg['completions'] / qb_agg['pass_attempts'].replace(0, 1)
        qb_agg['yards_per_attempt'] = qb_agg['passing_yards'] / qb_agg['pass_attempts'].replace(0, 1)
        qb_agg['td_rate'] = qb_agg['pass_tds'] / qb_agg['pass_attempts'].replace(0, 1)
        qb_agg['int_rate'] = qb_agg['interceptions'] / qb_agg['pass_attempts'].replace(0, 1)
        qb_agg['sack_rate'] = qb_agg['sacks'] / qb_agg['pass_attempts'].replace(0, 1)
        qb_agg['first_down_rate'] = qb_agg['first_downs'] / qb_agg['pass_attempts'].replace(0, 1)
        
        # Calculate rolling averages
        qb_agg = qb_agg.sort_values(['qb_name', 'team', 'season', 'week']).reset_index(drop=True)
        
        rolling_cols = ['avg_epa', 'avg_qb_epa', 'completion_rate', 'yards_per_attempt',
                       'td_rate', 'int_rate', 'sack_rate', 'first_down_rate']
        
        for col in rolling_cols:
            if col in qb_agg.columns:
                # 4-week rolling average
                rolling_4wk = (
                    qb_agg.groupby(['qb_name', 'team'])[col]
                    .rolling(window=window_4, min_periods=1)
                    .mean()
                    .reset_index(0, drop=True)
                )
                qb_agg[f'rolling_{col}_{window_4}wk'] = rolling_4wk.values
                
                # 8-week rolling average
                rolling_8wk = (
                    qb_agg.groupby(['qb_name', 'team'])[col]
                    .rolling(window=window_8, min_periods=1)
                    .mean()
                    .reset_index(0, drop=True)
                )
                qb_agg[f'rolling_{col}_{window_8}wk'] = rolling_8wk.values
        
        return qb_agg
    
    def get_team_epa_at_week(self, team: str, season: int, week: int) -> Optional[TeamEPAMetrics]:
        """
        Get team EPA metrics for a specific week.
        
        Args:
            team: Team abbreviation
            season: Season year
            week: Week number
            
        Returns:
            TeamEPAMetrics object or None if not found
        """
        team_metrics_df = self.calculate_team_metrics()
        
        team_week_data = team_metrics_df[
            (team_metrics_df['team'] == team) &
            (team_metrics_df['season'] == season) &
            (team_metrics_df['week'] == week)
        ]
        
        if team_week_data.empty:
            return None
        
        row = team_week_data.iloc[0]
        return TeamEPAMetrics(
            team=team,
            season=season,
            week=week,
            total_epa=row.get('total_epa', 0.0),
            avg_epa=row.get('avg_epa', 0.0),
            plays=row.get('plays', 0),
            total_qb_epa=row.get('total_qb_epa', 0.0),
            avg_qb_epa=row.get('avg_qb_epa', 0.0),
            total_air_epa=row.get('total_air_epa', 0.0),
            avg_air_epa=row.get('avg_air_epa', 0.0),
            total_yac_epa=row.get('total_yac_epa', 0.0),
            avg_yac_epa=row.get('avg_yac_epa', 0.0),
            completion_rate=row.get('completion_rate', 0.0),
            yards_per_attempt=row.get('yards_per_attempt', 0.0),
            yards_per_carry=row.get('yards_per_carry', 0.0),
            first_down_rate=row.get('first_down_rate', 0.0),
            rolling_avg_epa_4wk=row.get('rolling_avg_epa_4wk', 0.0),
            rolling_avg_epa_8wk=row.get('rolling_avg_epa_8wk', 0.0),
            rolling_avg_qb_epa_4wk=row.get('rolling_avg_qb_epa_4wk', 0.0),
            rolling_avg_qb_epa_8wk=row.get('rolling_avg_qb_epa_8wk', 0.0)
        )
    
    def get_qb_epa_at_week(self, qb_name: str, team: str, season: int, week: int) -> Optional[QBEPAMetrics]:
        """
        Get QB EPA metrics for a specific week.
        
        Args:
            qb_name: QB name
            team: Team abbreviation
            season: Season year
            week: Week number
            
        Returns:
            QBEPAMetrics object or None if not found
        """
        qb_metrics_df = self.calculate_qb_metrics()
        
        qb_week_data = qb_metrics_df[
            (qb_metrics_df['qb_name'] == qb_name) &
            (qb_metrics_df['team'] == team) &
            (qb_metrics_df['season'] == season) &
            (qb_metrics_df['week'] == week)
        ]
        
        if qb_week_data.empty:
            return None
        
        row = qb_week_data.iloc[0]
        return QBEPAMetrics(
            qb_name=qb_name,
            team=team,
            season=season,
            week=week,
            total_epa=row.get('total_epa', 0.0),
            avg_epa=row.get('avg_epa', 0.0),
            plays=row.get('plays', 0),
            total_qb_epa=row.get('total_qb_epa', 0.0),
            avg_qb_epa=row.get('avg_qb_epa', 0.0),
            total_air_epa=row.get('total_air_epa', 0.0),
            avg_air_epa=row.get('avg_air_epa', 0.0),
            total_yac_epa=row.get('total_yac_epa', 0.0),
            avg_yac_epa=row.get('avg_yac_epa', 0.0),
            completion_rate=row.get('completion_rate', 0.0),
            yards_per_attempt=row.get('yards_per_attempt', 0.0),
            td_rate=row.get('td_rate', 0.0),
            int_rate=row.get('int_rate', 0.0),
            sack_rate=row.get('sack_rate', 0.0),
            first_down_rate=row.get('first_down_rate', 0.0),
            rolling_avg_epa_4wk=row.get('rolling_avg_epa_4wk', 0.0),
            rolling_avg_epa_8wk=row.get('rolling_avg_epa_8wk', 0.0),
            rolling_avg_qb_epa_4wk=row.get('rolling_avg_qb_epa_4wk', 0.0),
            rolling_avg_qb_epa_8wk=row.get('rolling_avg_qb_epa_8wk', 0.0)
        )
    
    def save_metrics(self, output_dir: str) -> None:
        """
        Save EPA metrics to CSV files.
        
        Args:
            output_dir: Directory to save files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save team metrics
        team_metrics_df = self.calculate_team_metrics()
        if not team_metrics_df.empty:
            team_file = output_path / "team_epa_metrics.csv"
            team_metrics_df.to_csv(team_file, index=False)
            print(f"Team EPA metrics saved to {team_file}")
        
        # Save QB metrics
        qb_metrics_df = self.calculate_qb_metrics()
        if not qb_metrics_df.empty:
            qb_file = output_path / "qb_epa_metrics.csv"
            qb_metrics_df.to_csv(qb_file, index=False)
            print(f"QB EPA metrics saved to {qb_file}")
    
    def load_metrics(self, team_file: str, qb_file: str) -> None:
        """
        Load EPA metrics from CSV files.
        
        Args:
            team_file: Path to team EPA CSV file
            qb_file: Path to QB EPA CSV file
        """
        # This would load pre-calculated metrics
        # For now, we'll calculate on-demand
        pass
