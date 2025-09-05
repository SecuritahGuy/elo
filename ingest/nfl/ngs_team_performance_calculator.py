"""NGS team performance calculator for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class NGSTeamPerformanceCalculator:
    """Calculates NGS-based team performance metrics for enhanced Elo adjustments."""
    
    def __init__(self):
        """Initialize NGS team performance calculator."""
        # NGS team performance weights (based on NFL analytics research)
        self.ngs_weights = {
            # Passing performance
            'completion_percentage_above_expectation': 1.0,  # CPOE - most important
            'avg_time_to_throw': 0.8,                       # Time to throw
            'aggressiveness': 0.7,                          # Aggressiveness
            'avg_air_yards_differential': 0.6,              # Air yards differential
            'avg_intended_air_yards': 0.5,                  # Intended air yards
            
            # Rushing performance
            'efficiency': 1.0,                              # Rushing efficiency
            'rush_yards_over_expected': 0.9,                # RYOE
            'rush_pct_over_expected': 0.8,                  # Rush percentage over expected
            'avg_time_to_los': 0.6,                         # Time to line of scrimmage
            
            # Receiving performance
            'avg_yac_above_expectation': 1.0,               # YAC above expectation
            'avg_separation': 0.8,                          # Average separation
            'avg_cushion': 0.7,                             # Average cushion
            'avg_intended_air_yards_rec': 0.6,              # Share of intended air yards
        }
    
    def load_ngs_team_data(self, years: List[int]) -> Dict[str, pd.DataFrame]:
        """
        Load NGS data for team performance analysis.
        
        Args:
            years: Years to load data for
            
        Returns:
            Dictionary with NGS data by type
        """
        import nfl_data_py as nfl
        
        print(f"Loading NGS team performance data for years {years}...")
        
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
        
        return data
    
    def calculate_team_ngs_performance(self, ngs_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate NGS team performance metrics.
        
        Args:
            ngs_data: Dictionary with NGS data by type
            
        Returns:
            DataFrame with team NGS performance metrics
        """
        print("Calculating NGS team performance metrics...")
        
        team_stats = {}
        
        # Get all unique teams
        all_teams = set()
        for ngs_type, data in ngs_data.items():
            if not data.empty and 'team_abbr' in data.columns:
                all_teams.update(data['team_abbr'].unique())
        
        # Process each team
        for team in all_teams:
            if pd.isna(team):
                continue
                
            team_stats[team] = {}
            
            # NGS passing metrics
            if 'ngs_passing' in ngs_data and len(ngs_data['ngs_passing']) > 0:
                team_passing = ngs_data['ngs_passing'][ngs_data['ngs_passing']['team_abbr'] == team]
                if len(team_passing) > 0:
                    team_stats[team].update({
                        'completion_percentage_above_expectation': team_passing['completion_percentage_above_expectation'].mean(),
                        'avg_time_to_throw': team_passing['avg_time_to_throw'].mean(),
                        'aggressiveness': team_passing['aggressiveness'].mean(),
                        'avg_intended_air_yards': team_passing['avg_intended_air_yards'].mean(),
                        'avg_air_yards_differential': team_passing['avg_air_yards_differential'].mean(),
                        'passing_yards': team_passing['pass_yards'].sum(),
                        'pass_touchdowns': team_passing['pass_touchdowns'].sum(),
                        'interceptions': team_passing['interceptions'].sum()
                    })
            
            # NGS rushing metrics
            if 'ngs_rushing' in ngs_data and len(ngs_data['ngs_rushing']) > 0:
                team_rushing = ngs_data['ngs_rushing'][ngs_data['ngs_rushing']['team_abbr'] == team]
                if len(team_rushing) > 0:
                    team_stats[team].update({
                        'efficiency': team_rushing['efficiency'].mean(),
                        'rush_yards_over_expected': team_rushing['rush_yards_over_expected'].sum(),
                        'rush_pct_over_expected': team_rushing['rush_pct_over_expected'].mean(),
                        'avg_time_to_los': team_rushing['avg_time_to_los'].mean(),
                        'rush_attempts': team_rushing['rush_attempts'].sum(),
                        'rush_yards': team_rushing['rush_yards'].sum(),
                        'rush_touchdowns': team_rushing['rush_touchdowns'].sum()
                    })
            
            # NGS receiving metrics
            if 'ngs_receiving' in ngs_data and len(ngs_data['ngs_receiving']) > 0:
                team_receiving = ngs_data['ngs_receiving'][ngs_data['ngs_receiving']['team_abbr'] == team]
                if len(team_receiving) > 0:
                    team_stats[team].update({
                        'avg_yac_above_expectation': team_receiving['avg_yac_above_expectation'].mean(),
                        'avg_separation': team_receiving['avg_separation'].mean(),
                        'avg_cushion': team_receiving['avg_cushion'].mean(),
                        'avg_intended_air_yards_rec': team_receiving['avg_intended_air_yards'].mean(),
                        'receptions': team_receiving['receptions'].sum(),
                        'targets': team_receiving['targets'].sum(),
                        'receiving_yards': team_receiving['yards'].sum(),
                        'receiving_touchdowns': team_receiving['rec_touchdowns'].sum()
                    })
        
        # Convert to DataFrame
        ngs_df = pd.DataFrame(team_stats).T
        ngs_df = ngs_df.fillna(0.0)
        
        # Calculate weighted NGS performance score
        ngs_df['ngs_performance_score'] = self._calculate_weighted_performance(ngs_df)
        
        print(f"Calculated NGS team performance for {len(ngs_df)} teams")
        return ngs_df
    
    def _calculate_weighted_performance(self, stats: pd.DataFrame) -> pd.Series:
        """Calculate weighted NGS performance score."""
        performance = 0.0
        
        for metric, weight in self.ngs_weights.items():
            if metric in stats.columns:
                # Normalize each metric to 0-1 scale
                metric_values = stats[metric]
                if metric_values.max() > metric_values.min():
                    normalized = (metric_values - metric_values.min()) / (metric_values.max() - metric_values.min())
                else:
                    normalized = 0.5  # Default to middle if no variation
                performance += normalized * weight
        
        # Normalize to 0-1 scale
        total_weight = sum(self.ngs_weights.values())
        return performance / total_weight
    
    def calculate_ngs_team_impact(self, ngs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate NGS team impact scores.
        
        Args:
            ngs_df: NGS team performance DataFrame
            
        Returns:
            DataFrame with NGS team impact scores
        """
        print("Calculating NGS team impact scores...")
        
        # Calculate NGS advantage
        ngs_df['ngs_advantage'] = ngs_df['ngs_performance_score']
        
        # Calculate overall NGS team impact score
        ngs_df['ngs_team_impact_score'] = (
            ngs_df['ngs_performance_score'] * 0.6 +
            ngs_df['ngs_advantage'] * 0.4
        )
        
        # Normalize impact score to 0-1 scale
        min_score = ngs_df['ngs_team_impact_score'].min()
        max_score = ngs_df['ngs_team_impact_score'].max()
        if max_score > min_score:
            ngs_df['ngs_team_impact_normalized'] = (
                (ngs_df['ngs_team_impact_score'] - min_score) /
                (max_score - min_score)
            )
        else:
            ngs_df['ngs_team_impact_normalized'] = 0.5
        
        print(f"Calculated NGS team impact for {len(ngs_df)} teams")
        return ngs_df
    
    def create_ngs_team_database(self, years: List[int]) -> pd.DataFrame:
        """
        Create comprehensive NGS team database for specified years.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with NGS team impact scores
        """
        print(f"Creating NGS team database for years {years}...")
        
        # Load NGS data
        ngs_data = self.load_ngs_team_data(years)
        
        # Calculate team performance
        ngs_df = self.calculate_team_ngs_performance(ngs_data)
        
        # Calculate impact scores
        ngs_impact = self.calculate_ngs_team_impact(ngs_df)
        
        # Add year information
        ngs_impact['years_analyzed'] = str(years)
        ngs_impact['last_updated'] = datetime.now().isoformat()
        
        print(f"NGS team database created with {len(ngs_impact)} teams")
        return ngs_impact
    
    def get_team_ngs_rating(self, team: str, ngs_db: pd.DataFrame) -> Dict[str, float]:
        """
        Get NGS team rating for a specific team.
        
        Args:
            team: Team abbreviation
            ngs_db: NGS team database
            
        Returns:
            Dictionary with team NGS metrics
        """
        if team not in ngs_db.index:
            return {
                'ngs_team_impact_score': 0.0,
                'ngs_advantage': 0.0,
                'ngs_performance_score': 0.5,  # League average
                'ngs_team_impact_normalized': 0.5
            }
        
        team_stats = ngs_db.loc[team]
        
        return {
            'ngs_team_impact_score': team_stats['ngs_team_impact_score'],
            'ngs_advantage': team_stats['ngs_advantage'],
            'ngs_performance_score': team_stats['ngs_performance_score'],
            'ngs_team_impact_normalized': team_stats['ngs_team_impact_normalized']
        }


def test_ngs_team_performance_calculator():
    """Test the NGS team performance calculator."""
    print("📊 TESTING NGS TEAM PERFORMANCE CALCULATOR")
    print("="*80)
    
    calculator = NGSTeamPerformanceCalculator()
    
    # Test with 2024 data
    ngs_db = calculator.create_ngs_team_database([2024])
    
    if ngs_db.empty:
        print("No data loaded, cannot test")
        return calculator, ngs_db
    
    print(f"\\nNGS team database created with {len(ngs_db)} teams")
    
    # Show top 10 teams by NGS performance
    print("\\nTop 10 teams by NGS performance:")
    top_teams = ngs_db.sort_values('ngs_performance_score', ascending=False).head(10)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['ngs_performance_score']:.3f} performance")
    
    # Show bottom 10 teams
    print("\\nBottom 10 teams by NGS performance:")
    bottom_teams = ngs_db.sort_values('ngs_performance_score', ascending=True).head(10)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['ngs_performance_score']:.3f} performance")
    
    # Test individual team lookup
    print("\\nTesting team lookup:")
    kc_rating = calculator.get_team_ngs_rating('KC', ngs_db)
    print(f"KC NGS team rating: {kc_rating}")
    
    return calculator, ngs_db


if __name__ == "__main__":
    calculator, ngs_db = test_ngs_team_performance_calculator()
