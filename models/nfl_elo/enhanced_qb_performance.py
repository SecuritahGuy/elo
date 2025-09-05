"""Enhanced QB performance tracking with environmental adjustments."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from .epa_aggregator import EPAAggregator, TeamEPAMetrics, QBEPAMetrics
from .adjusted_epa_calculator import AdjustedEPACalculator, AdjustedEPAMetrics


@dataclass
class EnhancedQBPerformance:
    """Enhanced QB performance metrics with environmental context."""
    player_name: str
    team: str
    season: int
    week: int
    qbr_total: Optional[float] = None
    epa_total: Optional[float] = None
    adjusted_epa_total: Optional[float] = None
    qb_plays: Optional[int] = None
    win_rate: Optional[float] = None
    games_played: int = 0
    
    # Raw EPA metrics
    avg_epa: Optional[float] = None
    total_qb_epa: Optional[float] = None
    avg_qb_epa: Optional[float] = None
    avg_air_epa: Optional[float] = None
    avg_yac_epa: Optional[float] = None
    
    # Adjusted EPA metrics
    avg_adjusted_epa: Optional[float] = None
    total_adjusted_qb_epa: Optional[float] = None
    avg_adjusted_qb_epa: Optional[float] = None
    avg_adjusted_air_epa: Optional[float] = None
    avg_adjusted_yac_epa: Optional[float] = None
    
    # Environmental context
    avg_weather_factor: Optional[float] = None
    avg_travel_factor: Optional[float] = None
    avg_combined_environmental_factor: Optional[float] = None
    environmental_epa_impact: Optional[float] = None
    
    # Rolling metrics (raw)
    rolling_epa_4wk: Optional[float] = None
    rolling_epa_8wk: Optional[float] = None
    rolling_qbr_4wk: Optional[float] = None
    rolling_qbr_8wk: Optional[float] = None
    rolling_win_rate_4wk: Optional[float] = None
    rolling_win_rate_8wk: Optional[float] = None
    
    # Rolling metrics (adjusted)
    rolling_adjusted_epa_4wk: Optional[float] = None
    rolling_adjusted_epa_8wk: Optional[float] = None
    rolling_adjusted_qb_epa_4wk: Optional[float] = None
    rolling_adjusted_qb_epa_8wk: Optional[float] = None
    
    # Efficiency metrics
    completion_rate: Optional[float] = None
    yards_per_attempt: Optional[float] = None
    td_rate: Optional[float] = None
    int_rate: Optional[float] = None
    sack_rate: Optional[float] = None
    first_down_rate: Optional[float] = None


class EnhancedQBPerformanceTracker:
    """Enhanced QB performance tracker with environmental adjustments."""
    
    def __init__(self, qb_data: pd.DataFrame, games_data: pd.DataFrame, 
                 adjusted_epa_data: Optional[pd.DataFrame] = None):
        """
        Initialize the enhanced QB performance tracker.
        
        Args:
            qb_data: DataFrame with QB performance data
            games_data: DataFrame with game data
            adjusted_epa_data: DataFrame with adjusted EPA data
        """
        self.qb_data = qb_data.copy()
        self.games_data = games_data.copy()
        self.adjusted_epa_data = adjusted_epa_data.copy() if adjusted_epa_data is not None else pd.DataFrame()
        
        # Initialize EPA aggregator for raw metrics
        self.epa_aggregator = None
        if not self.adjusted_epa_data.empty:
            # Use raw EPA data for aggregator
            raw_epa_data = self.adjusted_epa_data[['season', 'week', 'posteam', 'defteam', 'play_type',
                                                 'passer_player_name', 'passer_player_id', 'epa', 'qb_epa',
                                                 'air_epa', 'yac_epa', 'pass_attempt', 'complete_pass',
                                                 'passing_yards', 'pass_touchdown', 'interception', 'sack',
                                                 'first_down']].copy()
            self.epa_aggregator = EPAAggregator(raw_epa_data)
        
        # Initialize adjusted EPA calculator
        self.adjusted_epa_calculator = None
        if not self.adjusted_epa_data.empty:
            self.adjusted_epa_calculator = AdjustedEPACalculator(self.adjusted_epa_data)
        
        # Performance history
        self.performance_history: List[EnhancedQBPerformance] = []
        
    def get_enhanced_qb_performance_at_week(self, player: str, team: str, season: int, week: int) -> Optional[EnhancedQBPerformance]:
        """
        Get enhanced QB performance for a specific week.
        
        Args:
            player: QB name (empty string to find starter)
            team: Team abbreviation
            season: Season year
            week: Week number
            
        Returns:
            EnhancedQBPerformance object or None
        """
        # Find QB if player name is empty
        if not player:
            qb_name = self._find_starting_qb(team, season, week)
            if not qb_name:
                return None
        else:
            qb_name = player
        
        # Get raw QB performance
        raw_performance = self._get_raw_qb_performance(qb_name, team, season, week)
        if raw_performance is None:
            return None
        
        # Get adjusted EPA performance
        adjusted_performance = self._get_adjusted_epa_performance(qb_name, team, season, week)
        
        # Get environmental context
        environmental_context = self._get_environmental_context(qb_name, team, season, week)
        
        # Get rolling metrics
        rolling_metrics = self._get_rolling_metrics(qb_name, team, season, week)
        
        # Combine all metrics
        enhanced_performance = EnhancedQBPerformance(
            player_name=qb_name,
            team=team,
            season=season,
            week=week,
            qbr_total=raw_performance.get('qbr_total'),
            epa_total=raw_performance.get('epa_total'),
            adjusted_epa_total=adjusted_performance.get('adjusted_epa_total'),
            qb_plays=raw_performance.get('qb_plays'),
            win_rate=raw_performance.get('win_rate'),
            games_played=raw_performance.get('games_played', 0),
            
            # Raw EPA metrics
            avg_epa=raw_performance.get('avg_epa'),
            total_qb_epa=raw_performance.get('total_qb_epa'),
            avg_qb_epa=raw_performance.get('avg_qb_epa'),
            avg_air_epa=raw_performance.get('avg_air_epa'),
            avg_yac_epa=raw_performance.get('avg_yac_epa'),
            
            # Adjusted EPA metrics
            avg_adjusted_epa=adjusted_performance.get('avg_adjusted_epa'),
            total_adjusted_qb_epa=adjusted_performance.get('total_adjusted_qb_epa'),
            avg_adjusted_qb_epa=adjusted_performance.get('avg_adjusted_qb_epa'),
            avg_adjusted_air_epa=adjusted_performance.get('avg_adjusted_air_epa'),
            avg_adjusted_yac_epa=adjusted_performance.get('avg_adjusted_yac_epa'),
            
            # Environmental context
            avg_weather_factor=environmental_context.get('avg_weather_factor'),
            avg_travel_factor=environmental_context.get('avg_travel_factor'),
            avg_combined_environmental_factor=environmental_context.get('avg_combined_environmental_factor'),
            environmental_epa_impact=environmental_context.get('environmental_epa_impact'),
            
            # Rolling metrics
            rolling_epa_4wk=rolling_metrics.get('rolling_epa_4wk'),
            rolling_epa_8wk=rolling_metrics.get('rolling_epa_8wk'),
            rolling_qbr_4wk=rolling_metrics.get('rolling_qbr_4wk'),
            rolling_qbr_8wk=rolling_metrics.get('rolling_qbr_8wk'),
            rolling_win_rate_4wk=rolling_metrics.get('rolling_win_rate_4wk'),
            rolling_win_rate_8wk=rolling_metrics.get('rolling_win_rate_8wk'),
            rolling_adjusted_epa_4wk=rolling_metrics.get('rolling_adjusted_epa_4wk'),
            rolling_adjusted_epa_8wk=rolling_metrics.get('rolling_adjusted_epa_8wk'),
            rolling_adjusted_qb_epa_4wk=rolling_metrics.get('rolling_adjusted_qb_epa_4wk'),
            rolling_adjusted_qb_epa_8wk=rolling_metrics.get('rolling_adjusted_qb_epa_8wk'),
            
            # Efficiency metrics
            completion_rate=raw_performance.get('completion_rate'),
            yards_per_attempt=raw_performance.get('yards_per_attempt'),
            td_rate=raw_performance.get('td_rate'),
            int_rate=raw_performance.get('int_rate'),
            sack_rate=raw_performance.get('sack_rate'),
            first_down_rate=raw_performance.get('first_down_rate')
        )
        
        return enhanced_performance
    
    def _get_raw_qb_performance(self, qb_name: str, team: str, season: int, week: int) -> Optional[Dict]:
        """Get raw QB performance metrics."""
        if self.epa_aggregator is None:
            return None
        
        # Get QB metrics from EPA aggregator
        qb_metrics = self.epa_aggregator.calculate_qb_metrics()
        qb_week_data = qb_metrics[
            (qb_metrics['qb_name'] == qb_name) &
            (qb_metrics['team'] == team) &
            (qb_metrics['season'] == season) &
            (qb_metrics['week'] == week)
        ]
        
        if qb_week_data.empty:
            return None
        
        qb_data = qb_week_data.iloc[0]
        
        return {
            'qbr_total': qb_data.get('qbr_total'),
            'epa_total': qb_data.get('total_epa'),
            'avg_epa': qb_data.get('avg_epa'),
            'total_qb_epa': qb_data.get('total_qb_epa'),
            'avg_qb_epa': qb_data.get('avg_qb_epa'),
            'avg_air_epa': qb_data.get('avg_air_epa'),
            'avg_yac_epa': qb_data.get('avg_yac_epa'),
            'qb_plays': qb_data.get('plays'),
            'completion_rate': qb_data.get('completion_rate'),
            'yards_per_attempt': qb_data.get('yards_per_attempt'),
            'td_rate': qb_data.get('td_rate'),
            'int_rate': qb_data.get('int_rate'),
            'sack_rate': qb_data.get('sack_rate'),
            'first_down_rate': qb_data.get('first_down_rate'),
            'games_played': 1,  # This would need to be calculated from history
            'win_rate': None  # This would need to be calculated from game results
        }
    
    def _get_adjusted_epa_performance(self, qb_name: str, team: str, season: int, week: int) -> Dict:
        """Get adjusted EPA performance metrics."""
        if self.adjusted_epa_calculator is None:
            return {}
        
        return self.adjusted_epa_calculator.get_qb_adjusted_epa_summary(qb_name, season, week)
    
    def _get_environmental_context(self, qb_name: str, team: str, season: int, week: int) -> Dict:
        """Get environmental context for QB performance."""
        if self.adjusted_epa_data.empty:
            return {}
        
        # Get QB plays for the week
        qb_plays = self.adjusted_epa_data[
            (self.adjusted_epa_data['passer_player_name'] == qb_name) &
            (self.adjusted_epa_data['posteam'] == team) &
            (self.adjusted_epa_data['season'] == season) &
            (self.adjusted_epa_data['week'] == week)
        ]
        
        if qb_plays.empty:
            return {}
        
        return {
            'avg_weather_factor': qb_plays['weather_epa_factor'].mean(),
            'avg_travel_factor': qb_plays['travel_epa_factor'].mean(),
            'avg_combined_environmental_factor': (qb_plays['weather_epa_factor'] * qb_plays['travel_epa_factor']).mean(),
            'environmental_epa_impact': qb_plays['environmental_epa_impact'].sum()
        }
    
    def _get_rolling_metrics(self, qb_name: str, team: str, season: int, week: int) -> Dict:
        """Get rolling metrics for QB performance."""
        if self.adjusted_epa_data.empty:
            return {}
        
        # Get QB plays up to the current week
        qb_plays = self.adjusted_epa_data[
            (self.adjusted_epa_data['passer_player_name'] == qb_name) &
            (self.adjusted_epa_data['posteam'] == team) &
            (self.adjusted_epa_data['season'] == season) &
            (self.adjusted_epa_data['week'] <= week)
        ].sort_values('week')
        
        if qb_plays.empty:
            return {}
        
        # Calculate rolling metrics
        rolling_metrics = {}
        
        # 4-week rolling averages
        if len(qb_plays) >= 4:
            recent_4wk = qb_plays.tail(4)
            rolling_metrics['rolling_epa_4wk'] = recent_4wk['epa'].mean()
            rolling_metrics['rolling_adjusted_epa_4wk'] = recent_4wk['adjusted_epa'].mean()
            rolling_metrics['rolling_adjusted_qb_epa_4wk'] = recent_4wk['adjusted_qb_epa'].mean()
        
        # 8-week rolling averages
        if len(qb_plays) >= 8:
            recent_8wk = qb_plays.tail(8)
            rolling_metrics['rolling_epa_8wk'] = recent_8wk['epa'].mean()
            rolling_metrics['rolling_adjusted_epa_8wk'] = recent_8wk['adjusted_epa'].mean()
            rolling_metrics['rolling_adjusted_qb_epa_8wk'] = recent_8wk['adjusted_qb_epa'].mean()
        
        return rolling_metrics
    
    def _find_starting_qb(self, team: str, season: int, week: int) -> Optional[str]:
        """Find the starting QB for a team in a specific week."""
        if self.adjusted_epa_data.empty:
            return None
        
        # Look for QB with most plays in the week
        team_plays = self.adjusted_epa_data[
            (self.adjusted_epa_data['posteam'] == team) &
            (self.adjusted_epa_data['season'] == season) &
            (self.adjusted_epa_data['week'] == week) &
            (self.adjusted_epa_data['play_type'] == 'pass') &
            (self.adjusted_epa_data['passer_player_name'].notna())
        ]
        
        if team_plays.empty:
            return None
        
        # Find QB with most passing plays
        qb_counts = team_plays['passer_player_name'].value_counts()
        if qb_counts.empty:
            return None
        
        return qb_counts.index[0]
    
    def calculate_enhanced_qb_rating_delta(self, qb_perf: EnhancedQBPerformance, 
                                         baseline_qb: Optional[EnhancedQBPerformance] = None) -> float:
        """
        Calculate enhanced QB rating delta using adjusted EPA.
        
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
        
        # Use adjusted EPA for performance evaluation
        if qb_perf.avg_adjusted_epa is not None:
            # Adjust based on adjusted EPA per play
            if qb_perf.avg_adjusted_epa > 0.2:
                delta += 2.0  # Excellent adjusted EPA
            elif qb_perf.avg_adjusted_epa > 0.1:
                delta += 1.0  # Good adjusted EPA
            elif qb_perf.avg_adjusted_epa < -0.1:
                delta -= 1.0  # Poor adjusted EPA
            elif qb_perf.avg_adjusted_epa < -0.2:
                delta -= 2.0  # Very poor adjusted EPA
        
        # Rolling adjusted EPA adjustments (more stable)
        if qb_perf.rolling_adjusted_epa_4wk is not None:
            if qb_perf.rolling_adjusted_epa_4wk > 0.15:
                delta += 1.5  # Consistently good
            elif qb_perf.rolling_adjusted_epa_4wk > 0.05:
                delta += 0.5  # Above average
            elif qb_perf.rolling_adjusted_epa_4wk < -0.05:
                delta -= 0.5  # Below average
            elif qb_perf.rolling_adjusted_epa_4wk < -0.15:
                delta -= 1.5  # Consistently poor
        
        # QB-specific adjusted EPA adjustments
        if qb_perf.avg_adjusted_qb_epa is not None:
            if qb_perf.avg_adjusted_qb_epa > 0.3:
                delta += 1.0  # Excellent adjusted QB EPA
            elif qb_perf.avg_adjusted_qb_epa < -0.1:
                delta -= 1.0  # Poor adjusted QB EPA
        
        # Environmental context adjustments
        if qb_perf.avg_combined_environmental_factor is not None:
            # Reward QBs who perform well in adverse conditions
            if qb_perf.avg_combined_environmental_factor < 0.8:  # Adverse conditions
                if qb_perf.avg_adjusted_epa is not None and qb_perf.avg_adjusted_epa > 0.1:
                    delta += 1.0  # Bonus for good performance in bad conditions
            elif qb_perf.avg_combined_environmental_factor > 1.1:  # Favorable conditions
                if qb_perf.avg_adjusted_epa is not None and qb_perf.avg_adjusted_epa < 0.0:
                    delta -= 0.5  # Penalty for poor performance in good conditions
        
        # Efficiency adjustments (unchanged)
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
        
        return delta


def test_enhanced_qb_performance_tracker():
    """Test the enhanced QB performance tracker."""
    print("Testing Enhanced QB Performance Tracker...")
    
    # Load data with environmental context
    from ingest.nfl.enhanced_epa_loader import load_epa_with_weather_and_travel_context
    from ingest.nfl.data_loader import load_games
    
    # Load EPA data with environmental context
    epa_data = load_epa_with_weather_and_travel_context([2023], sample_size=1000)
    print(f"Loaded {len(epa_data)} plays with environmental context")
    
    # Load games data
    games_data = load_games([2023])
    print(f"Loaded {len(games_data)} games")
    
    # Initialize enhanced tracker
    tracker = EnhancedQBPerformanceTracker(
        qb_data=pd.DataFrame(),  # Empty for now
        games_data=games_data,
        adjusted_epa_data=epa_data
    )
    
    # Test QB performance lookup
    print("\nTesting QB performance lookup...")
    qb_perf = tracker.get_enhanced_qb_performance_at_week("", "WAS", 2023, 1)
    
    if qb_perf:
        print(f"Found QB: {qb_perf.player_name}")
        print(f"Raw EPA: {qb_perf.avg_epa:.4f}")
        print(f"Adjusted EPA: {qb_perf.avg_adjusted_epa:.4f}")
        print(f"Weather Factor: {qb_perf.avg_weather_factor:.4f}")
        print(f"Travel Factor: {qb_perf.avg_travel_factor:.4f}")
        print(f"Environmental Impact: {qb_perf.environmental_epa_impact:.4f}")
        
        # Test rating delta calculation
        rating_delta = tracker.calculate_enhanced_qb_rating_delta(qb_perf)
        print(f"Enhanced Rating Delta: {rating_delta:.2f}")
    else:
        print("No QB performance found")
    
    print("\nEnhanced QB Performance Tracker test complete!")


if __name__ == "__main__":
    test_enhanced_qb_performance_tracker()
