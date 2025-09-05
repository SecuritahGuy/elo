"""NGS-based situational analysis calculator for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class NGSSituationalCalculator:
    """Calculates NGS-based situational metrics for advanced analytics."""
    
    def __init__(self):
        """Initialize NGS situational calculator."""
        # Situational metrics weights (based on NFL analytics research)
        self.situational_weights = {
            # Red zone efficiency
            'red_zone_efficiency': 1.0,           # Overall red zone performance
            'red_zone_touchdown_rate': 0.9,       # Touchdown rate in red zone
            'red_zone_fg_success_rate': 0.7,      # Field goal success in red zone
            'red_zone_epa': 0.8,                  # EPA in red zone situations
            
            # Third down efficiency
            'third_down_efficiency': 1.0,         # Overall third down conversion
            'third_down_epa': 0.8,                # EPA on third down plays
            'third_down_success_rate': 0.9,       # Success rate on third down
            
            # Fourth down efficiency
            'fourth_down_efficiency': 0.8,        # Fourth down conversion rate
            'fourth_down_epa': 0.7,               # EPA on fourth down plays
            'fourth_down_aggressiveness': 0.6,    # Willingness to go for it
            
            # NGS situational metrics
            'ngs_red_zone_passing': 0.9,          # NGS passing in red zone
            'ngs_red_zone_rushing': 0.8,          # NGS rushing in red zone
            'ngs_third_down_passing': 0.9,        # NGS passing on third down
            'ngs_third_down_rushing': 0.8,        # NGS rushing on third down
            'ngs_clutch_performance': 0.7,        # NGS performance in clutch situations
            'ngs_situational_awareness': 0.6      # NGS situational awareness
        }
    
    def load_ngs_situational_data(self, years: List[int]) -> Dict[str, pd.DataFrame]:
        """
        Load NGS and play-by-play data for situational analysis.
        
        Args:
            years: Years to load data for
            
        Returns:
            Dictionary with NGS and play-by-play data
        """
        import nfl_data_py as nfl
        
        print(f"Loading NGS situational data for years {years}...")
        
        data = {}
        
        # Load NGS data
        ngs_types = ['passing', 'rushing', 'receiving']
        for ngs_type in ngs_types:
            try:
                ngs_data = nfl.import_ngs_data(stat_type=ngs_type, years=years)
                data[f'ngs_{ngs_type}'] = ngs_data
                print(f"  Loaded {len(ngs_data)} {ngs_type} NGS records")
            except Exception as e:
                print(f"  Error loading {ngs_type} NGS data: {e}")
                data[f'ngs_{ngs_type}'] = pd.DataFrame()
        
        # Load play-by-play data
        try:
            pbp = nfl.import_pbp_data(years, downcast=True)
            data['pbp'] = pbp
            print(f"  Loaded {len(pbp)} play-by-play records")
        except Exception as e:
            print(f"  Error loading play-by-play data: {e}")
            data['pbp'] = pd.DataFrame()
        
        return data
    
    def calculate_red_zone_metrics(self, pbp_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate red zone efficiency metrics for each team.
        
        Args:
            pbp_data: Play-by-play data
            
        Returns:
            DataFrame with team red zone metrics
        """
        print("Calculating red zone efficiency metrics...")
        
        # Filter red zone plays (yardline_100 <= 20)
        red_zone_plays = pbp_data[pbp_data['yardline_100'] <= 20]
        
        team_stats = {}
        
        for team in red_zone_plays['posteam'].unique():
            if pd.isna(team):
                continue
                
            team_red_zone = red_zone_plays[red_zone_plays['posteam'] == team]
            
            # Calculate red zone efficiency metrics
            total_plays = len(team_red_zone)
            touchdowns = team_red_zone['touchdown'].sum()
            fg_attempts = team_red_zone['field_goal_attempt'].sum()
            fg_made = (team_red_zone['field_goal_result'] == 'made').sum()
            
            # Calculate rates
            touchdown_rate = touchdowns / total_plays if total_plays > 0 else 0.0
            fg_success_rate = fg_made / fg_attempts if fg_attempts > 0 else 0.0
            
            # Overall efficiency (weighted combination)
            efficiency = (
                touchdown_rate * 0.7 +
                fg_success_rate * 0.3
            )
            
            # EPA in red zone
            red_zone_epa = team_red_zone['epa'].mean() if 'epa' in team_red_zone.columns else 0.0
            
            team_stats[team] = {
                'red_zone_efficiency': efficiency,
                'red_zone_touchdown_rate': touchdown_rate,
                'red_zone_fg_success_rate': fg_success_rate,
                'red_zone_epa': red_zone_epa,
                'red_zone_plays': total_plays,
                'red_zone_touchdowns': touchdowns,
                'red_zone_fg_attempts': fg_attempts,
                'red_zone_fg_made': fg_made
            }
        
        # Convert to DataFrame
        red_zone_df = pd.DataFrame(team_stats).T
        red_zone_df = red_zone_df.fillna(0.0)
        
        print(f"Calculated red zone metrics for {len(red_zone_df)} teams")
        return red_zone_df
    
    def calculate_third_down_metrics(self, pbp_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate third down efficiency metrics for each team.
        
        Args:
            pbp_data: Play-by-play data
            
        Returns:
            DataFrame with team third down metrics
        """
        print("Calculating third down efficiency metrics...")
        
        # Filter third down plays
        third_down_plays = pbp_data[pbp_data['down'] == 3]
        
        team_stats = {}
        
        for team in third_down_plays['posteam'].unique():
            if pd.isna(team):
                continue
                
            team_third_down = third_down_plays[third_down_plays['posteam'] == team]
            
            # Calculate third down efficiency metrics
            total_attempts = len(team_third_down)
            conversions = team_third_down['third_down_converted'].sum()
            
            # Calculate efficiency
            efficiency = conversions / total_attempts if total_attempts > 0 else 0.0
            
            # EPA on third down
            third_down_epa = team_third_down['epa'].mean() if 'epa' in team_third_down.columns else 0.0
            
            # Success rate (EPA > 0)
            success_rate = (team_third_down['epa'] > 0).mean() if 'epa' in team_third_down.columns else 0.0
            
            team_stats[team] = {
                'third_down_efficiency': efficiency,
                'third_down_epa': third_down_epa,
                'third_down_success_rate': success_rate,
                'third_down_attempts': total_attempts,
                'third_down_conversions': conversions
            }
        
        # Convert to DataFrame
        third_down_df = pd.DataFrame(team_stats).T
        third_down_df = third_down_df.fillna(0.0)
        
        print(f"Calculated third down metrics for {len(third_down_df)} teams")
        return third_down_df
    
    def calculate_fourth_down_metrics(self, pbp_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate fourth down efficiency metrics for each team.
        
        Args:
            pbp_data: Play-by-play data
            
        Returns:
            DataFrame with team fourth down metrics
        """
        print("Calculating fourth down efficiency metrics...")
        
        # Filter fourth down plays
        fourth_down_plays = pbp_data[pbp_data['down'] == 4]
        
        team_stats = {}
        
        for team in fourth_down_plays['posteam'].unique():
            if pd.isna(team):
                continue
                
            team_fourth_down = fourth_down_plays[fourth_down_plays['posteam'] == team]
            
            # Calculate fourth down efficiency metrics
            total_attempts = len(team_fourth_down)
            conversions = team_fourth_down['fourth_down_converted'].sum()
            
            # Calculate efficiency
            efficiency = conversions / total_attempts if total_attempts > 0 else 0.0
            
            # EPA on fourth down
            fourth_down_epa = team_fourth_down['epa'].mean() if 'epa' in team_fourth_down.columns else 0.0
            
            # Aggressiveness (attempts per game)
            games = team_fourth_down['game_id'].nunique()
            aggressiveness = total_attempts / games if games > 0 else 0.0
            
            team_stats[team] = {
                'fourth_down_efficiency': efficiency,
                'fourth_down_epa': fourth_down_epa,
                'fourth_down_aggressiveness': aggressiveness,
                'fourth_down_attempts': total_attempts,
                'fourth_down_conversions': conversions,
                'fourth_down_games': games
            }
        
        # Convert to DataFrame
        fourth_down_df = pd.DataFrame(team_stats).T
        fourth_down_df = fourth_down_df.fillna(0.0)
        
        print(f"Calculated fourth down metrics for {len(fourth_down_df)} teams")
        return fourth_down_df
    
    def calculate_ngs_situational_metrics(self, ngs_data: Dict[str, pd.DataFrame], pbp_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate NGS-based situational metrics.
        
        Args:
            ngs_data: Dictionary with NGS data by type
            pbp_data: Play-by-play data
            
        Returns:
            DataFrame with NGS situational metrics
        """
        print("Calculating NGS situational metrics...")
        
        team_stats = {}
        
        # Process each team
        for team in pbp_data['posteam'].unique():
            if pd.isna(team):
                continue
                
            team_stats[team] = {}
            
            # NGS passing metrics
            if 'ngs_passing' in ngs_data and len(ngs_data['ngs_passing']) > 0:
                team_passing = ngs_data['ngs_passing'][ngs_data['ngs_passing']['team_abbr'] == team]
                if len(team_passing) > 0:
                    team_stats[team].update({
                        'ngs_completion_percentage_above_expectation': team_passing['completion_percentage_above_expectation'].mean(),
                        'ngs_avg_time_to_throw': team_passing['avg_time_to_throw'].mean(),
                        'ngs_aggressiveness': team_passing['aggressiveness'].mean(),
                        'ngs_avg_intended_air_yards': team_passing['avg_intended_air_yards'].mean(),
                        'ngs_avg_air_yards_differential': team_passing['avg_air_yards_differential'].mean()
                    })
            
            # NGS rushing metrics
            if 'ngs_rushing' in ngs_data and len(ngs_data['ngs_rushing']) > 0:
                team_rushing = ngs_data['ngs_rushing'][ngs_data['ngs_rushing']['team_abbr'] == team]
                if len(team_rushing) > 0:
                    team_stats[team].update({
                        'ngs_rush_efficiency': team_rushing['efficiency'].mean(),
                        'ngs_rush_yards_over_expected': team_rushing['rush_yards_over_expected'].sum(),
                        'ngs_rush_pct_over_expected': team_rushing['rush_pct_over_expected'].mean(),
                        'ngs_avg_time_to_los': team_rushing['avg_time_to_los'].mean()
                    })
            
            # NGS receiving metrics
            if 'ngs_receiving' in ngs_data and len(ngs_data['ngs_receiving']) > 0:
                team_receiving = ngs_data['ngs_receiving'][ngs_data['ngs_receiving']['team_abbr'] == team]
                if len(team_receiving) > 0:
                    team_stats[team].update({
                        'ngs_avg_yac_above_expectation': team_receiving['avg_yac_above_expectation'].mean(),
                        'ngs_avg_separation': team_receiving['avg_separation'].mean(),
                        'ngs_avg_cushion': team_receiving['avg_cushion'].mean(),
                        'ngs_avg_intended_air_yards_rec': team_receiving['avg_intended_air_yards'].mean()
                    })
        
        # Convert to DataFrame
        ngs_df = pd.DataFrame(team_stats).T
        ngs_df = ngs_df.fillna(0.0)
        
        print(f"Calculated NGS situational metrics for {len(ngs_df)} teams")
        return ngs_df
    
    def calculate_situational_impact(self, red_zone_df: pd.DataFrame, third_down_df: pd.DataFrame, 
                                   fourth_down_df: pd.DataFrame, ngs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate overall situational impact scores for each team.
        
        Args:
            red_zone_df: Red zone metrics
            third_down_df: Third down metrics
            fourth_down_df: Fourth down metrics
            ngs_df: NGS situational metrics
            
        Returns:
            DataFrame with situational impact scores
        """
        print("Calculating situational impact scores...")
        
        # Combine all metrics
        situational_df = pd.DataFrame(index=red_zone_df.index)
        
        # Add red zone metrics
        for col in red_zone_df.columns:
            situational_df[f'red_zone_{col}'] = red_zone_df[col]
        
        # Add third down metrics
        for col in third_down_df.columns:
            situational_df[f'third_down_{col}'] = third_down_df[col]
        
        # Add fourth down metrics
        for col in fourth_down_df.columns:
            situational_df[f'fourth_down_{col}'] = fourth_down_df[col]
        
        # Add NGS metrics
        for col in ngs_df.columns:
            situational_df[f'ngs_{col}'] = ngs_df[col]
        
        # Calculate weighted situational efficiency
        situational_df['situational_efficiency'] = self._calculate_weighted_efficiency(situational_df)
        
        # Calculate situational advantage
        situational_df['situational_advantage'] = situational_df['situational_efficiency']
        
        # Calculate overall situational impact score
        situational_df['situational_impact_score'] = (
            situational_df['situational_efficiency'] * 0.6 +
            situational_df['situational_advantage'] * 0.4
        )
        
        # Normalize impact score to 0-1 scale
        situational_df['situational_impact_normalized'] = (
            (situational_df['situational_impact_score'] - situational_df['situational_impact_score'].min()) /
            (situational_df['situational_impact_score'].max() - situational_df['situational_impact_score'].min())
        )
        
        print(f"Calculated situational impact for {len(situational_df)} teams")
        return situational_df
    
    def _calculate_weighted_efficiency(self, stats: pd.DataFrame) -> pd.Series:
        """Calculate weighted situational efficiency score."""
        efficiency = 0.0
        
        for metric, weight in self.situational_weights.items():
            if metric in stats.columns:
                efficiency += stats[metric] * weight
        
        # Normalize to 0-1 scale
        total_weight = sum(self.situational_weights.values())
        return efficiency / total_weight
    
    def create_ngs_situational_database(self, years: List[int]) -> pd.DataFrame:
        """
        Create comprehensive NGS situational database for specified years.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with NGS situational impact scores
        """
        print(f"Creating NGS situational database for years {years}...")
        
        # Load data
        data = self.load_ngs_situational_data(years)
        
        if data['pbp'].empty:
            print("No play-by-play data loaded, returning empty DataFrame")
            return pd.DataFrame()
        
        # Calculate individual metrics
        red_zone_df = self.calculate_red_zone_metrics(data['pbp'])
        third_down_df = self.calculate_third_down_metrics(data['pbp'])
        fourth_down_df = self.calculate_fourth_down_metrics(data['pbp'])
        ngs_df = self.calculate_ngs_situational_metrics(data, data['pbp'])
        
        # Calculate overall situational impact
        situational_df = self.calculate_situational_impact(red_zone_df, third_down_df, fourth_down_df, ngs_df)
        
        # Add year information
        situational_df['years_analyzed'] = str(years)
        situational_df['last_updated'] = datetime.now().isoformat()
        
        print(f"NGS situational database created with {len(situational_df)} teams")
        return situational_df
    
    def get_team_situational_rating(self, team: str, situational_db: pd.DataFrame) -> Dict[str, float]:
        """
        Get situational rating for a specific team.
        
        Args:
            team: Team abbreviation
            situational_db: Situational database
            
        Returns:
            Dictionary with team situational metrics
        """
        if team not in situational_db.index:
            return {
                'situational_impact_score': 0.0,
                'situational_advantage': 0.0,
                'situational_efficiency': 0.5,  # League average
                'red_zone_efficiency': 0.5,
                'third_down_efficiency': 0.5,
                'fourth_down_efficiency': 0.5
            }
        
        team_stats = situational_db.loc[team]
        
        return {
            'situational_impact_score': team_stats['situational_impact_score'],
            'situational_advantage': team_stats['situational_advantage'],
            'situational_efficiency': team_stats['situational_efficiency'],
            'red_zone_efficiency': team_stats.get('red_zone_red_zone_efficiency', 0.5),
            'third_down_efficiency': team_stats.get('third_down_third_down_efficiency', 0.5),
            'fourth_down_efficiency': team_stats.get('fourth_down_fourth_down_efficiency', 0.5),
            'situational_impact_normalized': team_stats['situational_impact_normalized']
        }


def test_ngs_situational_calculator():
    """Test the NGS situational calculator."""
    print("📊 TESTING NGS SITUATIONAL CALCULATOR")
    print("="*80)
    
    calculator = NGSSituationalCalculator()
    
    # Test with 2024 data
    situational_db = calculator.create_ngs_situational_database([2024])
    
    if situational_db.empty:
        print("No data loaded, cannot test")
        return calculator, situational_db
    
    print(f"\\nNGS situational database created with {len(situational_db)} teams")
    
    # Show top 10 teams by situational efficiency
    print("\\nTop 10 teams by situational efficiency:")
    top_teams = situational_db.sort_values('situational_efficiency', ascending=False).head(10)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['situational_efficiency']:.3f} efficiency")
    
    # Show bottom 10 teams
    print("\\nBottom 10 teams by situational efficiency:")
    bottom_teams = situational_db.sort_values('situational_efficiency', ascending=True).head(10)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['situational_efficiency']:.3f} efficiency")
    
    # Test individual team lookup
    print("\\nTesting team lookup:")
    kc_rating = calculator.get_team_situational_rating('KC', situational_db)
    print(f"KC situational rating: {kc_rating}")
    
    return calculator, situational_db


if __name__ == "__main__":
    calculator, situational_db = test_ngs_situational_calculator()
