"""QB performance tracking system for NFL Elo."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from .epa_aggregator import EPAAggregator, TeamEPAMetrics, QBEPAMetrics


@dataclass
class QBPerformance:
    """QB performance metrics for a specific period."""
    player_name: str
    team: str
    season: int
    week: int
    qbr_total: Optional[float] = None
    epa_total: Optional[float] = None
    qb_plays: Optional[int] = None
    win_rate: Optional[float] = None
    games_played: int = 0
    rolling_epa_4wk: Optional[float] = None
    rolling_epa_8wk: Optional[float] = None
    rolling_qbr_4wk: Optional[float] = None
    rolling_qbr_8wk: Optional[float] = None
    rolling_win_rate_4wk: Optional[float] = None
    rolling_win_rate_8wk: Optional[float] = None
    # EPA-specific metrics
    avg_epa: Optional[float] = None
    total_qb_epa: Optional[float] = None
    avg_qb_epa: Optional[float] = None
    avg_air_epa: Optional[float] = None
    avg_yac_epa: Optional[float] = None
    completion_rate: Optional[float] = None
    yards_per_attempt: Optional[float] = None
    td_rate: Optional[float] = None
    int_rate: Optional[float] = None
    sack_rate: Optional[float] = None
    first_down_rate: Optional[float] = None
    rolling_avg_epa_4wk: Optional[float] = None
    rolling_avg_epa_8wk: Optional[float] = None
    rolling_avg_qb_epa_4wk: Optional[float] = None
    rolling_avg_qb_epa_8wk: Optional[float] = None


class QBPerformanceTracker:
    """Tracks QB performance over time with rolling averages."""
    
    def __init__(self, qb_data: pd.DataFrame, games_data: pd.DataFrame, epa_data: Optional[pd.DataFrame] = None):
        """
        Initialize QB performance tracker.
        
        Args:
            qb_data: QB weekly data from qb_data_loader
            games_data: Game results data
            epa_data: Optional play-by-play EPA data
        """
        self.qb_data = qb_data.copy()
        self.games_data = games_data.copy()
        self.qb_performance_history: List[QBPerformance] = []
        
        # Initialize EPA aggregator if EPA data is provided
        self.epa_aggregator = None
        if epa_data is not None and not epa_data.empty:
            self.epa_aggregator = EPAAggregator(epa_data)
        
    def calculate_rolling_metrics(self, window: int = 4) -> pd.DataFrame:
        """
        Calculate rolling QB performance metrics.
        
        Args:
            window: Rolling window size in weeks
            
        Returns:
            DataFrame with rolling metrics
        """
        # Sort by player, season, week
        qb_sorted = self.qb_data.sort_values(['player_name', 'season', 'week']).copy()
        
        # Calculate rolling metrics for each QB
        rolling_metrics = []
        
        for player in qb_sorted['player_name'].unique():
            player_data = qb_sorted[qb_sorted['player_name'] == player].copy()
            
            # Calculate rolling EPA (if available)
            if 'epa_total' in player_data.columns:
                player_data[f'rolling_epa_{window}wk'] = (
                    player_data['epa_total']
                    .rolling(window=window, min_periods=1)
                    .mean()
                )
            
            # Calculate rolling QBR (if available)
            if 'qbr_total' in player_data.columns:
                player_data[f'rolling_qbr_{window}wk'] = (
                    player_data['qbr_total']
                    .rolling(window=window, min_periods=1)
                    .mean()
                )
            
            # Calculate rolling win rate
            player_data[f'rolling_win_rate_{window}wk'] = self._calculate_rolling_win_rate(
                player, player_data, window
            )
            
            rolling_metrics.append(player_data)
        
        if rolling_metrics:
            return pd.concat(rolling_metrics, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def _calculate_rolling_win_rate(self, player: str, player_data: pd.DataFrame, window: int) -> pd.Series:
        """
        Calculate rolling win rate for a QB.
        
        Args:
            player: QB name
            player_data: QB weekly data
            window: Rolling window size
            
        Returns:
            Series with rolling win rates
        """
        win_rates = []
        
        for idx, row in player_data.iterrows():
            # Get games for this QB in the rolling window
            start_week = max(1, row['week'] - window + 1)
            end_week = row['week']
            
            # Find games where this QB was the starter
            qb_games = self._get_qb_games(player, row['team'], row['season'], start_week, end_week)
            
            if len(qb_games) > 0:
                wins = qb_games['home_win'].sum() if 'home_win' in qb_games.columns else 0
                win_rate = wins / len(qb_games)
            else:
                win_rate = np.nan
            
            win_rates.append(win_rate)
        
        return pd.Series(win_rates, index=player_data.index)
    
    def _get_qb_games(self, player: str, team: str, season: int, start_week: int, end_week: int) -> pd.DataFrame:
        """
        Get games where a specific QB was the starter.
        
        Args:
            player: QB name
            team: Team abbreviation
            season: Season year
            start_week: Starting week
            end_week: Ending week
            
        Returns:
            DataFrame with QB games
        """
        # Filter games for this team and season
        team_games = self.games_data[
            (self.games_data['season'] == season) &
            ((self.games_data['home_team'] == team) | (self.games_data['away_team'] == team)) &
            (self.games_data['week'] >= start_week) &
            (self.games_data['week'] <= end_week)
        ].copy()
        
        # For now, assume the QB started all games for their team
        # In a more sophisticated system, we'd check actual QB starts
        if not team_games.empty:
            # Add home_win column
            team_games['home_win'] = (
                (team_games['home_team'] == team) & 
                (team_games['home_score'] > team_games['away_score'])
            ) | (
                (team_games['away_team'] == team) & 
                (team_games['away_score'] > team_games['home_score'])
            )
        
        return team_games
    
    def get_qb_performance_at_week(self, player: str, team: str, season: int, week: int) -> Optional[QBPerformance]:
        """
        Get QB performance metrics at a specific week.
        
        Args:
            player: QB name
            team: Team abbreviation
            season: Season year
            week: Week number
            
        Returns:
            QBPerformance object or None if not found
        """
        # Get QB data for this week (handle both int and float week types)
        if player:  # If player name is provided, use it
            qb_week_data = self.qb_data[
                (self.qb_data['player_name'] == player) &
                (self.qb_data['team'] == team) &
                (self.qb_data['season'] == season) &
                (self.qb_data['week'] == float(week))
            ]
        else:  # If no player name, find the starting QB for this team/week
            qb_week_data = self.qb_data[
                (self.qb_data['team'] == team) &
                (self.qb_data['season'] == season) &
                (self.qb_data['week'] == float(week)) &
                (self.qb_data['is_starter'] == True)
            ]
        
        if qb_week_data.empty:
            return None
        
        qb_row = qb_week_data.iloc[0]
        
        # Calculate rolling metrics
        rolling_data = self.calculate_rolling_metrics()
        qb_rolling = rolling_data[
            (rolling_data['player_name'] == player) &
            (rolling_data['team'] == team) &
            (rolling_data['season'] == season) &
            (rolling_data['week'] == week)
        ]
        
        # Get rolling metrics if available
        rolling_epa_4wk = qb_rolling['rolling_epa_4wk'].iloc[0] if not qb_rolling.empty and 'rolling_epa_4wk' in qb_rolling.columns else None
        rolling_epa_8wk = qb_rolling['rolling_epa_8wk'].iloc[0] if not qb_rolling.empty and 'rolling_epa_8wk' in qb_rolling.columns else None
        rolling_qbr_4wk = qb_rolling['rolling_qbr_4wk'].iloc[0] if not qb_rolling.empty and 'rolling_qbr_4wk' in qb_rolling.columns else None
        rolling_qbr_8wk = qb_rolling['rolling_qbr_8wk'].iloc[0] if not qb_rolling.empty and 'rolling_qbr_8wk' in qb_rolling.columns else None
        rolling_win_rate_4wk = qb_rolling['rolling_win_rate_4wk'].iloc[0] if not qb_rolling.empty and 'rolling_win_rate_4wk' in qb_rolling.columns else None
        rolling_win_rate_8wk = qb_rolling['rolling_win_rate_8wk'].iloc[0] if not qb_rolling.empty and 'rolling_win_rate_8wk' in qb_rolling.columns else None
        
        # Get EPA metrics if available
        epa_metrics = None
        if self.epa_aggregator is not None:
            # Try to find QB in EPA data with name matching
            epa_qb_name = self._find_epa_qb_name(player, team, season, week)
            if epa_qb_name:
                epa_metrics = self.epa_aggregator.get_qb_epa_at_week(epa_qb_name, team, season, week)
        
        # Count games played
        games_played = len(self._get_qb_games(player, team, season, 1, week))
        
        return QBPerformance(
            player_name=player,
            team=team,
            season=season,
            week=week,
            qbr_total=qb_row.get('qbr_total'),
            epa_total=qb_row.get('epa_total'),
            qb_plays=qb_row.get('qb_plays'),
            rolling_epa_4wk=rolling_epa_4wk,
            rolling_epa_8wk=rolling_epa_8wk,
            rolling_qbr_4wk=rolling_qbr_4wk,
            rolling_qbr_8wk=rolling_qbr_8wk,
            rolling_win_rate_4wk=rolling_win_rate_4wk,
            rolling_win_rate_8wk=rolling_win_rate_8wk,
            games_played=games_played,
            # EPA-specific metrics
            avg_epa=epa_metrics.avg_epa if epa_metrics else None,
            total_qb_epa=epa_metrics.total_qb_epa if epa_metrics else None,
            avg_qb_epa=epa_metrics.avg_qb_epa if epa_metrics else None,
            avg_air_epa=epa_metrics.avg_air_epa if epa_metrics else None,
            avg_yac_epa=epa_metrics.avg_yac_epa if epa_metrics else None,
            completion_rate=epa_metrics.completion_rate if epa_metrics else None,
            yards_per_attempt=epa_metrics.yards_per_attempt if epa_metrics else None,
            td_rate=epa_metrics.td_rate if epa_metrics else None,
            int_rate=epa_metrics.int_rate if epa_metrics else None,
            sack_rate=epa_metrics.sack_rate if epa_metrics else None,
            first_down_rate=epa_metrics.first_down_rate if epa_metrics else None,
            rolling_avg_epa_4wk=epa_metrics.rolling_avg_epa_4wk if epa_metrics else None,
            rolling_avg_epa_8wk=epa_metrics.rolling_avg_epa_8wk if epa_metrics else None,
            rolling_avg_qb_epa_4wk=epa_metrics.rolling_avg_qb_epa_4wk if epa_metrics else None,
            rolling_avg_qb_epa_8wk=epa_metrics.rolling_avg_qb_epa_8wk if epa_metrics else None
        )
    
    def calculate_qb_rating_delta(self, qb_perf: QBPerformance, baseline_qb: Optional[QBPerformance] = None) -> float:
        """
        Calculate QB rating delta based on performance metrics.
        
        Args:
            qb_perf: Current QB performance
            baseline_qb: Baseline QB performance for comparison
            
        Returns:
            Rating delta in Elo points
        """
        delta = 0.0
        
        # Experience adjustment
        if qb_perf.games_played < 5:  # Rookie or very inexperienced
            delta -= 3.0
        elif qb_perf.games_played > 50:  # Veteran
            delta += 1.0
        
        # Rolling QBR adjustment
        if qb_perf.rolling_qbr_4wk is not None:
            if qb_perf.rolling_qbr_4wk > 70:  # Excellent
                delta += 4.0
            elif qb_perf.rolling_qbr_4wk > 60:  # Good
                delta += 2.0
            elif qb_perf.rolling_qbr_4wk < 40:  # Poor
                delta -= 3.0
            elif qb_perf.rolling_qbr_4wk < 30:  # Very poor
                delta -= 5.0
        
        # Rolling EPA adjustment (legacy)
        if qb_perf.rolling_epa_4wk is not None:
            if qb_perf.rolling_epa_4wk > 0.2:  # Excellent EPA
                delta += 2.0
            elif qb_perf.rolling_epa_4wk > 0.1:  # Good EPA
                delta += 1.0
            elif qb_perf.rolling_epa_4wk < -0.1:  # Poor EPA
                delta -= 2.0
            elif qb_perf.rolling_epa_4wk < -0.2:  # Very poor EPA
                delta -= 4.0
        
        # New EPA-based adjustments (more sophisticated)
        if qb_perf.avg_epa is not None:
            # Adjust based on average EPA per play
            if qb_perf.avg_epa > 0.2:
                delta += 2.0  # Excellent EPA
            elif qb_perf.avg_epa > 0.1:
                delta += 1.0  # Good EPA
            elif qb_perf.avg_epa < -0.1:
                delta -= 1.0  # Poor EPA
            elif qb_perf.avg_epa < -0.2:
                delta -= 2.0  # Very poor EPA
        
        # Rolling EPA adjustments (more stable)
        if qb_perf.rolling_avg_epa_4wk is not None:
            if qb_perf.rolling_avg_epa_4wk > 0.15:
                delta += 1.5  # Consistently good
            elif qb_perf.rolling_avg_epa_4wk > 0.05:
                delta += 0.5  # Above average
            elif qb_perf.rolling_avg_epa_4wk < -0.05:
                delta -= 0.5  # Below average
            elif qb_perf.rolling_avg_epa_4wk < -0.15:
                delta -= 1.5  # Consistently poor
        
        # QB-specific EPA adjustments
        if qb_perf.avg_qb_epa is not None:
            if qb_perf.avg_qb_epa > 0.3:
                delta += 1.0  # Excellent QB EPA
            elif qb_perf.avg_qb_epa < -0.1:
                delta -= 1.0  # Poor QB EPA
        
        # Efficiency adjustments
        if qb_perf.completion_rate is not None:
            if qb_perf.completion_rate > 0.7:
                delta += 0.5  # High completion rate
            elif qb_perf.completion_rate < 0.55:
                delta -= 0.5  # Low completion rate
        
        if qb_perf.yards_per_attempt is not None:
            if qb_perf.yards_per_attempt > 8.0:
                delta += 0.5  # High YPA
            elif qb_perf.yards_per_attempt < 6.0:
                delta -= 0.5  # Low YPA
        
        if qb_perf.td_rate is not None:
            if qb_perf.td_rate > 0.06:
                delta += 0.5  # High TD rate
            elif qb_perf.td_rate < 0.03:
                delta -= 0.5  # Low TD rate
        
        if qb_perf.int_rate is not None:
            if qb_perf.int_rate > 0.03:
                delta -= 0.5  # High INT rate
            elif qb_perf.int_rate < 0.01:
                delta += 0.5  # Low INT rate
        
        # Rolling win rate adjustment
        if qb_perf.rolling_win_rate_4wk is not None:
            if qb_perf.rolling_win_rate_4wk > 0.7:  # Excellent win rate
                delta += 2.0
            elif qb_perf.rolling_win_rate_4wk > 0.6:  # Good win rate
                delta += 1.0
            elif qb_perf.rolling_win_rate_4wk < 0.3:  # Poor win rate
                delta -= 2.0
            elif qb_perf.rolling_win_rate_4wk < 0.2:  # Very poor win rate
                delta -= 4.0
        
        # Cap the delta to reasonable bounds
        delta = max(min(delta, 10.0), -10.0)
        
        return delta
    
    def _find_epa_qb_name(self, qb_name: str, team: str, season: int, week: int) -> Optional[str]:
        """
        Find the EPA data QB name that matches the QB data name.
        
        Args:
            qb_name: QB name from QB data
            team: Team abbreviation
            season: Season year
            week: Week number
            
        Returns:
            EPA data QB name or None if not found
        """
        if not self.epa_aggregator:
            return None
        
        # Get all QBs for this team/week from EPA data
        qb_metrics_df = self.epa_aggregator.calculate_qb_metrics()
        team_week_qbs = qb_metrics_df[
            (qb_metrics_df['team'] == team) &
            (qb_metrics_df['season'] == season) &
            (qb_metrics_df['week'] == week)
        ]
        
        if team_week_qbs.empty:
            return None
        
        # Try exact match first
        exact_match = team_week_qbs[team_week_qbs['qb_name'] == qb_name]
        if not exact_match.empty:
            return qb_name
        
        # Try partial matching (last name)
        qb_last_name = qb_name.split()[-1] if ' ' in qb_name else qb_name
        for epa_qb_name in team_week_qbs['qb_name']:
            if qb_last_name in epa_qb_name or epa_qb_name.split()[-1] == qb_last_name:
                return epa_qb_name
        
        # Return the first QB found for this team/week (likely the starter)
        return team_week_qbs.iloc[0]['qb_name']
    
    def save_performance_history(self, filepath: str) -> None:
        """
        Save QB performance history to CSV.
        
        Args:
            filepath: Path to save the file
        """
        if self.qb_performance_history:
            history_df = pd.DataFrame([
                {
                    'player_name': perf.player_name,
                    'team': perf.team,
                    'season': perf.season,
                    'week': perf.week,
                    'qbr_total': perf.qbr_total,
                    'epa_total': perf.epa_total,
                    'qb_plays': perf.qb_plays,
                    'games_played': perf.games_played,
                    'rolling_epa_4wk': perf.rolling_epa_4wk,
                    'rolling_epa_8wk': perf.rolling_epa_8wk,
                    'rolling_qbr_4wk': perf.rolling_qbr_4wk,
                    'rolling_qbr_8wk': perf.rolling_qbr_8wk,
                    'rolling_win_rate_4wk': perf.rolling_win_rate_4wk,
                    'rolling_win_rate_8wk': perf.rolling_win_rate_8wk
                }
                for perf in self.qb_performance_history
            ])
            history_df.to_csv(filepath, index=False)
            print(f"QB performance history saved to {filepath}")
    
    def load_performance_history(self, filepath: str) -> None:
        """
        Load QB performance history from CSV.
        
        Args:
            filepath: Path to load the file from
        """
        if Path(filepath).exists():
            history_df = pd.read_csv(filepath)
            self.qb_performance_history = [
                QBPerformance(
                    player_name=row['player_name'],
                    team=row['team'],
                    season=row['season'],
                    week=row['week'],
                    qbr_total=row.get('qbr_total'),
                    epa_total=row.get('epa_total'),
                    qb_plays=row.get('qb_plays'),
                    games_played=row.get('games_played', 0),
                    rolling_epa_4wk=row.get('rolling_epa_4wk'),
                    rolling_epa_8wk=row.get('rolling_epa_8wk'),
                    rolling_qbr_4wk=row.get('rolling_qbr_4wk'),
                    rolling_qbr_8wk=row.get('rolling_qbr_8wk'),
                    rolling_win_rate_4wk=row.get('rolling_win_rate_4wk'),
                    rolling_win_rate_8wk=row.get('rolling_win_rate_8wk')
                )
                for _, row in history_df.iterrows()
            ]
            print(f"QB performance history loaded from {filepath}")
        else:
            print(f"File {filepath} not found")
