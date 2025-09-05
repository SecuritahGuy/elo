"""NFL Clock Management efficiency calculator for advanced analytics."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class ClockManagementCalculator:
    """Calculates NFL Clock Management efficiency metrics for advanced analytics."""
    
    def __init__(self):
        """Initialize Clock Management calculator."""
        # Clock management metrics weights (based on NFL analytics research)
        self.clock_weights = {
            # Close game performance (within 7 points)
            'close_game_efficiency': 1.0,           # Overall close game performance
            'close_game_first_down_rate': 0.8,      # First down conversion in close games
            'close_game_touchdown_rate': 0.9,       # Touchdown rate in close games
            'close_game_fg_success_rate': 0.7,      # Field goal success in close games
            
            # Late game performance (4th quarter)
            'late_game_efficiency': 1.0,            # 4th quarter performance
            'late_game_first_down_rate': 0.8,       # First down conversion in 4th quarter
            'late_game_touchdown_rate': 0.9,        # Touchdown rate in 4th quarter
            'late_game_fg_success_rate': 0.7,       # Field goal success in 4th quarter
            
            # Two-minute drill performance
            'two_minute_efficiency': 1.0,           # Two-minute drill performance
            'two_minute_first_down_rate': 0.8,      # First down conversion in two-minute drill
            'two_minute_touchdown_rate': 0.9,       # Touchdown rate in two-minute drill
            'two_minute_fg_success_rate': 0.7,      # Field goal success in two-minute drill
            
            # Timeout management
            'timeout_efficiency': 0.6,              # Timeout usage efficiency
            'timeout_remaining_avg': 0.4,           # Average timeouts remaining
            'timeout_usage_rate': 0.3,              # Timeout usage rate
            
            # Situational awareness
            'situational_awareness': 0.8,           # Performance in different game situations
            'score_differential_management': 0.7,   # Performance based on score differential
            'field_position_efficiency': 0.6,       # Performance based on field position
            'down_distance_efficiency': 0.5         # Performance based on down and distance
        }
    
    def load_clock_management_data(self, years: List[int]) -> pd.DataFrame:
        """
        Load NFL play-by-play data for clock management analysis.
        
        Args:
            years: Years to load data for
            
        Returns:
            DataFrame with play-by-play data
        """
        import nfl_data_py as nfl
        
        print(f"Loading clock management data for years {years}...")
        
        try:
            pbp = nfl.import_pbp_data(years, downcast=True)
            print(f"  Loaded {len(pbp)} play-by-play records")
            return pbp
        except Exception as e:
            print(f"  Error loading play-by-play data: {e}")
            return pd.DataFrame()
    
    def calculate_team_clock_management(self, pbp_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate clock management efficiency for each team.
        
        Args:
            pbp_data: Play-by-play data
            
        Returns:
            DataFrame with team clock management stats
        """
        print("Calculating clock management efficiency...")
        
        team_stats = {}
        
        # Process each team
        for team in pbp_data['posteam'].unique():
            if pd.isna(team):
                continue
                
            team_plays = pbp_data[pbp_data['posteam'] == team]
            
            # Calculate close game performance (within 7 points)
            close_game_stats = self._calculate_close_game_stats(team_plays)
            
            # Calculate late game performance (4th quarter)
            late_game_stats = self._calculate_late_game_stats(team_plays)
            
            # Calculate two-minute drill performance
            two_minute_stats = self._calculate_two_minute_stats(team_plays)
            
            # Calculate timeout management
            timeout_stats = self._calculate_timeout_stats(team_plays)
            
            # Calculate situational awareness
            situational_stats = self._calculate_situational_stats(team_plays)
            
            # Combine all stats
            team_stats[team] = {
                **close_game_stats,
                **late_game_stats,
                **two_minute_stats,
                **timeout_stats,
                **situational_stats
            }
        
        # Convert to DataFrame
        clock_df = pd.DataFrame(team_stats).T
        clock_df = clock_df.fillna(0.0)
        
        # Calculate weighted clock management efficiency
        clock_df['clock_management_efficiency'] = self._calculate_weighted_efficiency(clock_df)
        
        print(f"Calculated clock management for {len(clock_df)} teams")
        return clock_df
    
    def _calculate_close_game_stats(self, team_plays: pd.DataFrame) -> Dict[str, float]:
        """Calculate close game performance stats."""
        # Close games are within 7 points
        close_plays = team_plays[team_plays['score_differential'].abs() <= 7]
        
        if len(close_plays) == 0:
            return {
                'close_game_efficiency': 0.0,
                'close_game_first_down_rate': 0.0,
                'close_game_touchdown_rate': 0.0,
                'close_game_fg_success_rate': 0.0,
                'close_game_plays': 0
            }
        
        # Calculate efficiency metrics
        first_downs = close_plays['first_down'].sum()
        touchdowns = close_plays['touchdown'].sum()
        fg_attempts = close_plays['field_goal_attempt'].sum()
        fg_made = (close_plays['field_goal_result'] == 'made').sum()
        
        total_plays = len(close_plays)
        
        # Calculate rates
        first_down_rate = first_downs / total_plays if total_plays > 0 else 0.0
        touchdown_rate = touchdowns / total_plays if total_plays > 0 else 0.0
        fg_success_rate = fg_made / fg_attempts if fg_attempts > 0 else 0.0
        
        # Overall efficiency (weighted combination)
        efficiency = (
            first_down_rate * 0.4 +
            touchdown_rate * 0.4 +
            fg_success_rate * 0.2
        )
        
        return {
            'close_game_efficiency': efficiency,
            'close_game_first_down_rate': first_down_rate,
            'close_game_touchdown_rate': touchdown_rate,
            'close_game_fg_success_rate': fg_success_rate,
            'close_game_plays': total_plays
        }
    
    def _calculate_late_game_stats(self, team_plays: pd.DataFrame) -> Dict[str, float]:
        """Calculate late game performance stats (4th quarter)."""
        late_plays = team_plays[team_plays['qtr'] == 4]
        
        if len(late_plays) == 0:
            return {
                'late_game_efficiency': 0.0,
                'late_game_first_down_rate': 0.0,
                'late_game_touchdown_rate': 0.0,
                'late_game_fg_success_rate': 0.0,
                'late_game_plays': 0
            }
        
        # Calculate efficiency metrics
        first_downs = late_plays['first_down'].sum()
        touchdowns = late_plays['touchdown'].sum()
        fg_attempts = late_plays['field_goal_attempt'].sum()
        fg_made = (late_plays['field_goal_result'] == 'made').sum()
        
        total_plays = len(late_plays)
        
        # Calculate rates
        first_down_rate = first_downs / total_plays if total_plays > 0 else 0.0
        touchdown_rate = touchdowns / total_plays if total_plays > 0 else 0.0
        fg_success_rate = fg_made / fg_attempts if fg_attempts > 0 else 0.0
        
        # Overall efficiency (weighted combination)
        efficiency = (
            first_down_rate * 0.4 +
            touchdown_rate * 0.4 +
            fg_success_rate * 0.2
        )
        
        return {
            'late_game_efficiency': efficiency,
            'late_game_first_down_rate': first_down_rate,
            'late_game_touchdown_rate': touchdown_rate,
            'late_game_fg_success_rate': fg_success_rate,
            'late_game_plays': total_plays
        }
    
    def _calculate_two_minute_stats(self, team_plays: pd.DataFrame) -> Dict[str, float]:
        """Calculate two-minute drill performance stats."""
        # Two-minute drill: 4th quarter with <= 120 seconds remaining
        two_minute_plays = team_plays[
            (team_plays['qtr'] == 4) & 
            (team_plays['quarter_seconds_remaining'] <= 120)
        ]
        
        if len(two_minute_plays) == 0:
            return {
                'two_minute_efficiency': 0.0,
                'two_minute_first_down_rate': 0.0,
                'two_minute_touchdown_rate': 0.0,
                'two_minute_fg_success_rate': 0.0,
                'two_minute_plays': 0
            }
        
        # Calculate efficiency metrics
        first_downs = two_minute_plays['first_down'].sum()
        touchdowns = two_minute_plays['touchdown'].sum()
        fg_attempts = two_minute_plays['field_goal_attempt'].sum()
        fg_made = (two_minute_plays['field_goal_result'] == 'made').sum()
        
        total_plays = len(two_minute_plays)
        
        # Calculate rates
        first_down_rate = first_downs / total_plays if total_plays > 0 else 0.0
        touchdown_rate = touchdowns / total_plays if total_plays > 0 else 0.0
        fg_success_rate = fg_made / fg_attempts if fg_attempts > 0 else 0.0
        
        # Overall efficiency (weighted combination)
        efficiency = (
            first_down_rate * 0.4 +
            touchdown_rate * 0.4 +
            fg_success_rate * 0.2
        )
        
        return {
            'two_minute_efficiency': efficiency,
            'two_minute_first_down_rate': first_down_rate,
            'two_minute_touchdown_rate': touchdown_rate,
            'two_minute_fg_success_rate': fg_success_rate,
            'two_minute_plays': total_plays
        }
    
    def _calculate_timeout_stats(self, team_plays: pd.DataFrame) -> Dict[str, float]:
        """Calculate timeout management stats."""
        # Get timeout calls by this team
        team_timeouts = team_plays[team_plays['timeout_team'] == team_plays['posteam'].iloc[0]]
        
        # Calculate timeout efficiency metrics
        timeout_calls = len(team_timeouts)
        total_plays = len(team_plays)
        timeout_usage_rate = timeout_calls / total_plays if total_plays > 0 else 0.0
        
        # Average timeouts remaining (from posteam_timeouts_remaining)
        avg_timeouts_remaining = team_plays['posteam_timeouts_remaining'].mean()
        
        # Timeout efficiency (higher is better - more strategic use)
        timeout_efficiency = min(timeout_usage_rate * 2, 1.0)  # Cap at 1.0
        
        return {
            'timeout_efficiency': timeout_efficiency,
            'timeout_remaining_avg': avg_timeouts_remaining,
            'timeout_usage_rate': timeout_usage_rate,
            'timeout_calls': timeout_calls
        }
    
    def _calculate_situational_stats(self, team_plays: pd.DataFrame) -> Dict[str, float]:
        """Calculate situational awareness stats."""
        # Score differential management
        score_diff_stats = self._calculate_score_differential_stats(team_plays)
        
        # Field position efficiency
        field_pos_stats = self._calculate_field_position_stats(team_plays)
        
        # Down and distance efficiency
        down_distance_stats = self._calculate_down_distance_stats(team_plays)
        
        # Overall situational awareness
        situational_awareness = (
            score_diff_stats['score_differential_efficiency'] * 0.4 +
            field_pos_stats['field_position_efficiency'] * 0.3 +
            down_distance_stats['down_distance_efficiency'] * 0.3
        )
        
        return {
            'situational_awareness': situational_awareness,
            **score_diff_stats,
            **field_pos_stats,
            **down_distance_stats
        }
    
    def _calculate_score_differential_stats(self, team_plays: pd.DataFrame) -> Dict[str, float]:
        """Calculate score differential management stats."""
        # Performance when leading vs trailing
        leading_plays = team_plays[team_plays['score_differential'] > 0]
        trailing_plays = team_plays[team_plays['score_differential'] < 0]
        
        leading_efficiency = self._calculate_play_efficiency(leading_plays)
        trailing_efficiency = self._calculate_play_efficiency(trailing_plays)
        
        # Overall score differential efficiency
        score_diff_efficiency = (leading_efficiency + trailing_efficiency) / 2
        
        return {
            'score_differential_efficiency': score_diff_efficiency,
            'leading_efficiency': leading_efficiency,
            'trailing_efficiency': trailing_efficiency
        }
    
    def _calculate_field_position_stats(self, team_plays: pd.DataFrame) -> Dict[str, float]:
        """Calculate field position efficiency stats."""
        # Performance in different field positions
        own_territory = team_plays[team_plays['yardline_100'] > 50]
        opponent_territory = team_plays[team_plays['yardline_100'] <= 50]
        
        own_territory_efficiency = self._calculate_play_efficiency(own_territory)
        opponent_territory_efficiency = self._calculate_play_efficiency(opponent_territory)
        
        # Overall field position efficiency
        field_pos_efficiency = (own_territory_efficiency + opponent_territory_efficiency) / 2
        
        return {
            'field_position_efficiency': field_pos_efficiency,
            'own_territory_efficiency': own_territory_efficiency,
            'opponent_territory_efficiency': opponent_territory_efficiency
        }
    
    def _calculate_down_distance_stats(self, team_plays: pd.DataFrame) -> Dict[str, float]:
        """Calculate down and distance efficiency stats."""
        # Performance on different downs
        first_down_plays = team_plays[team_plays['down'] == 1]
        second_down_plays = team_plays[team_plays['down'] == 2]
        third_down_plays = team_plays[team_plays['down'] == 3]
        fourth_down_plays = team_plays[team_plays['down'] == 4]
        
        first_down_efficiency = self._calculate_play_efficiency(first_down_plays)
        second_down_efficiency = self._calculate_play_efficiency(second_down_plays)
        third_down_efficiency = self._calculate_play_efficiency(third_down_plays)
        fourth_down_efficiency = self._calculate_play_efficiency(fourth_down_plays)
        
        # Overall down and distance efficiency
        down_distance_efficiency = (
            first_down_efficiency * 0.3 +
            second_down_efficiency * 0.3 +
            third_down_efficiency * 0.3 +
            fourth_down_efficiency * 0.1
        )
        
        return {
            'down_distance_efficiency': down_distance_efficiency,
            'first_down_efficiency': first_down_efficiency,
            'second_down_efficiency': second_down_efficiency,
            'third_down_efficiency': third_down_efficiency,
            'fourth_down_efficiency': fourth_down_efficiency
        }
    
    def _calculate_play_efficiency(self, plays: pd.DataFrame) -> float:
        """Calculate basic play efficiency."""
        if len(plays) == 0:
            return 0.0
        
        # Simple efficiency metric: first downs + touchdowns + field goals made
        first_downs = plays['first_down'].sum()
        touchdowns = plays['touchdown'].sum()
        fg_made = (plays['field_goal_result'] == 'made').sum()
        
        total_plays = len(plays)
        efficiency = (first_downs + touchdowns + fg_made) / total_plays
        
        return efficiency
    
    def _calculate_weighted_efficiency(self, stats: pd.DataFrame) -> pd.Series:
        """Calculate weighted clock management efficiency score."""
        efficiency = 0.0
        
        for metric, weight in self.clock_weights.items():
            if metric in stats.columns:
                efficiency += stats[metric] * weight
        
        # Normalize to 0-1 scale
        total_weight = sum(self.clock_weights.values())
        return efficiency / total_weight
    
    def calculate_clock_management_impact(self, clock_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate clock management impact scores for each team.
        
        Args:
            clock_stats: Team clock management stats
            
        Returns:
            DataFrame with clock management impact scores
        """
        print("Calculating clock management impact scores...")
        
        # Calculate clock management advantage
        clock_stats['clock_advantage'] = clock_stats['clock_management_efficiency']
        
        # Calculate overall clock management impact score
        clock_stats['clock_impact_score'] = (
            clock_stats['clock_management_efficiency'] * 0.6 +
            clock_stats['clock_advantage'] * 0.4
        )
        
        # Normalize impact score to 0-1 scale
        clock_stats['clock_impact_normalized'] = (
            (clock_stats['clock_impact_score'] - clock_stats['clock_impact_score'].min()) /
            (clock_stats['clock_impact_score'].max() - clock_stats['clock_impact_score'].min())
        )
        
        print(f"Calculated clock management impact for {len(clock_stats)} teams")
        return clock_stats
    
    def create_clock_management_database(self, years: List[int]) -> pd.DataFrame:
        """
        Create comprehensive clock management database for specified years.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with clock management impact scores
        """
        print(f"Creating clock management database for years {years}...")
        
        # Load play-by-play data
        pbp_data = self.load_clock_management_data(years)
        
        if pbp_data.empty:
            print("No data loaded, returning empty DataFrame")
            return pd.DataFrame()
        
        # Calculate team clock management stats
        clock_stats = self.calculate_team_clock_management(pbp_data)
        
        # Calculate impact scores
        clock_impact = self.calculate_clock_management_impact(clock_stats)
        
        # Add year information
        clock_impact['years_analyzed'] = str(years)
        clock_impact['last_updated'] = datetime.now().isoformat()
        
        print(f"Clock management database created with {len(clock_impact)} teams")
        return clock_impact
    
    def get_team_clock_management_rating(self, team: str, clock_db: pd.DataFrame) -> Dict[str, float]:
        """
        Get clock management rating for a specific team.
        
        Args:
            team: Team abbreviation
            clock_db: Clock management database
            
        Returns:
            Dictionary with team clock management metrics
        """
        if team not in clock_db.index:
            return {
                'clock_impact_score': 0.0,
                'clock_advantage': 0.0,
                'clock_management_efficiency': 0.5,  # League average
                'close_game_efficiency': 0.5,
                'late_game_efficiency': 0.5,
                'two_minute_efficiency': 0.5
            }
        
        team_stats = clock_db.loc[team]
        
        return {
            'clock_impact_score': team_stats['clock_impact_score'],
            'clock_advantage': team_stats['clock_advantage'],
            'clock_management_efficiency': team_stats['clock_management_efficiency'],
            'close_game_efficiency': team_stats['close_game_efficiency'],
            'late_game_efficiency': team_stats['late_game_efficiency'],
            'two_minute_efficiency': team_stats['two_minute_efficiency'],
            'clock_impact_normalized': team_stats['clock_impact_normalized']
        }


def test_clock_management_calculator():
    """Test the clock management calculator."""
    print("📊 TESTING CLOCK MANAGEMENT CALCULATOR")
    print("="*80)
    
    calculator = ClockManagementCalculator()
    
    # Test with 2024 data
    clock_db = calculator.create_clock_management_database([2024])
    
    if clock_db.empty:
        print("No data loaded, cannot test")
        return calculator, clock_db
    
    print(f"\\nClock management database created with {len(clock_db)} teams")
    
    # Show top 10 teams by clock management
    print("\\nTop 10 teams by clock management efficiency:")
    top_teams = clock_db.sort_values('clock_management_efficiency', ascending=False).head(10)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['clock_management_efficiency']:.3f} efficiency, "
              f"{stats['close_game_efficiency']:.3f} close game, "
              f"{stats['late_game_efficiency']:.3f} late game")
    
    # Show bottom 10 teams
    print("\\nBottom 10 teams by clock management efficiency:")
    bottom_teams = clock_db.sort_values('clock_management_efficiency', ascending=True).head(10)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['clock_management_efficiency']:.3f} efficiency, "
              f"{stats['close_game_efficiency']:.3f} close game, "
              f"{stats['late_game_efficiency']:.3f} late game")
    
    # Test individual team lookup
    print("\\nTesting team lookup:")
    kc_rating = calculator.get_team_clock_management_rating('KC', clock_db)
    print(f"KC clock management rating: {kc_rating}")
    
    return calculator, clock_db


if __name__ == "__main__":
    calculator, clock_db = test_clock_management_calculator()
