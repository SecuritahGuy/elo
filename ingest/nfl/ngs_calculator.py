"""NFL Next Gen Stats metrics calculator for advanced analytics."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class NGSCalculator:
    """Calculates NFL Next Gen Stats metrics for advanced analytics."""
    
    def __init__(self):
        """Initialize NGS calculator."""
        # NGS metrics weights (based on NFL analytics research)
        self.ngs_weights = {
            # Passing metrics
            'completion_percentage_above_expectation': 1.0,  # CPOE
            'avg_time_to_throw': 0.8,                       # Time to throw
            'aggressiveness': 0.7,                          # Aggressiveness
            'avg_air_yards_differential': 0.6,              # Air yards differential
            'avg_intended_air_yards': 0.5,                  # Intended air yards
            
            # Rushing metrics
            'efficiency': 1.0,                              # Rushing efficiency
            'rush_yards_over_expected': 0.9,                # RYOE
            'rush_pct_over_expected': 0.8,                  # Rush percentage over expected
            'avg_time_to_los': 0.6,                         # Time to line of scrimmage
            
            # Receiving metrics
            'avg_yac_above_expectation': 1.0,               # YAC above expectation
            'avg_separation': 0.8,                          # Average separation
            'avg_cushion': 0.7,                             # Average cushion
            'percent_share_of_intended_air_yards': 0.6,     # Share of intended air yards
            
            # Advanced play-by-play metrics
            'cpoe': 1.0,                                    # Completion percentage over expected
            'yac_epa': 0.9,                                 # YAC EPA
            'xyac_epa': 0.8,                                # Expected YAC EPA
            'xyac_success': 0.7,                            # Expected YAC success
            'xyac_fd': 0.6,                                 # Expected YAC first down
            'time_to_throw': 0.5,                           # Time to throw
            'was_pressure': 0.4,                            # Pressure indicator
            'air_yards': 0.3,                               # Air yards
            'xyac_mean_yardage': 0.2,                       # Expected YAC mean yardage
            'xyac_median_yardage': 0.1                      # Expected YAC median yardage
        }
    
    def load_ngs_data(self, years: List[int]) -> Dict[str, pd.DataFrame]:
        """
        Load NFL Next Gen Stats data for specified years.
        
        Args:
            years: Years to load data for
            
        Returns:
            Dictionary with NGS data by type
        """
        import nfl_data_py as nfl
        
        print(f"Loading NGS data for years {years}...")
        
        ngs_data = {}
        
        # Load different types of NGS data
        ngs_types = ['passing', 'rushing', 'receiving']
        
        for ngs_type in ngs_types:
            try:
                data = nfl.import_ngs_data(stat_type=ngs_type, years=years)
                ngs_data[ngs_type] = data
                print(f"  Loaded {len(data)} {ngs_type} records")
            except Exception as e:
                print(f"  Error loading {ngs_type} data: {e}")
                ngs_data[ngs_type] = pd.DataFrame()
        
        # Load play-by-play data for advanced metrics
        try:
            pbp = nfl.import_pbp_data(years, downcast=True)
            ngs_data['pbp'] = pbp
            print(f"  Loaded {len(pbp)} play-by-play records")
        except Exception as e:
            print(f"  Error loading play-by-play data: {e}")
            ngs_data['pbp'] = pd.DataFrame()
        
        return ngs_data
    
    def calculate_team_ngs_offense(self, ngs_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate NGS offensive metrics for each team.
        
        Args:
            ngs_data: Dictionary with NGS data by type
            
        Returns:
            DataFrame with team NGS offensive stats
        """
        print("Calculating NGS offensive metrics...")
        
        team_stats = {}
        
        # Process passing data
        if 'passing' in ngs_data and len(ngs_data['passing']) > 0:
            passing_stats = self._calculate_passing_metrics(ngs_data['passing'])
            team_stats.update(passing_stats)
        
        # Process rushing data
        if 'rushing' in ngs_data and len(ngs_data['rushing']) > 0:
            rushing_stats = self._calculate_rushing_metrics(ngs_data['rushing'])
            team_stats.update(rushing_stats)
        
        # Process receiving data
        if 'receiving' in ngs_data and len(ngs_data['receiving']) > 0:
            receiving_stats = self._calculate_receiving_metrics(ngs_data['receiving'])
            team_stats.update(receiving_stats)
        
        # Process play-by-play data
        if 'pbp' in ngs_data and len(ngs_data['pbp']) > 0:
            pbp_stats = self._calculate_pbp_metrics(ngs_data['pbp'])
            team_stats.update(pbp_stats)
        
        # Convert to DataFrame
        offense_df = pd.DataFrame(team_stats).T
        offense_df = offense_df.fillna(0.0)
        
        # Calculate weighted NGS efficiency score
        offense_df['ngs_efficiency'] = self._calculate_weighted_efficiency(offense_df)
        
        print(f"Calculated NGS offense for {len(offense_df)} teams")
        return offense_df
    
    def calculate_team_ngs_defense(self, ngs_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate NGS defensive metrics for each team.
        
        Args:
            ngs_data: Dictionary with NGS data by type
            
        Returns:
            DataFrame with team NGS defensive stats
        """
        print("Calculating NGS defensive metrics...")
        
        team_stats = {}
        
        # Process play-by-play data for defensive metrics
        if 'pbp' in ngs_data and len(ngs_data['pbp']) > 0:
            pbp_def_stats = self._calculate_pbp_defensive_metrics(ngs_data['pbp'])
            team_stats.update(pbp_def_stats)
        
        # Convert to DataFrame
        defense_df = pd.DataFrame(team_stats).T
        defense_df = defense_df.fillna(0.0)
        
        # Calculate weighted NGS defensive efficiency score (lower is better)
        defense_df['ngs_defense_efficiency'] = self._calculate_weighted_defense_efficiency(defense_df)
        
        print(f"Calculated NGS defense for {len(defense_df)} teams")
        return defense_df
    
    def _calculate_passing_metrics(self, passing_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate passing metrics from NGS data."""
        team_stats = {}
        
        for team in passing_data['team_abbr'].unique():
            team_passing = passing_data[passing_data['team_abbr'] == team]
            
            team_stats[team] = {
                'completion_percentage_above_expectation': team_passing['completion_percentage_above_expectation'].mean(),
                'avg_time_to_throw': team_passing['avg_time_to_throw'].mean(),
                'aggressiveness': team_passing['aggressiveness'].mean(),
                'avg_air_yards_differential': team_passing['avg_air_yards_differential'].mean(),
                'avg_intended_air_yards': team_passing['avg_intended_air_yards'].mean(),
                'passing_yards': team_passing['pass_yards'].sum(),
                'pass_touchdowns': team_passing['pass_touchdowns'].sum(),
                'interceptions': team_passing['interceptions'].sum(),
                'sacks': team_passing['attempts'].sum() - team_passing['completions'].sum()  # Approximate sacks
            }
        
        return team_stats
    
    def _calculate_rushing_metrics(self, rushing_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate rushing metrics from NGS data."""
        team_stats = {}
        
        for team in rushing_data['team_abbr'].unique():
            team_rushing = rushing_data[rushing_data['team_abbr'] == team]
            
            team_stats[team] = {
                'efficiency': team_rushing['efficiency'].mean(),
                'rush_yards_over_expected': team_rushing['rush_yards_over_expected'].sum(),
                'rush_pct_over_expected': team_rushing['rush_pct_over_expected'].mean(),
                'avg_time_to_los': team_rushing['avg_time_to_los'].mean(),
                'rush_attempts': team_rushing['rush_attempts'].sum(),
                'rush_yards': team_rushing['rush_yards'].sum(),
                'rush_touchdowns': team_rushing['rush_touchdowns'].sum()
            }
        
        return team_stats
    
    def _calculate_receiving_metrics(self, receiving_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate receiving metrics from NGS data."""
        team_stats = {}
        
        for team in receiving_data['team_abbr'].unique():
            team_receiving = receiving_data[receiving_data['team_abbr'] == team]
            
            team_stats[team] = {
                'avg_yac_above_expectation': team_receiving['avg_yac_above_expectation'].mean(),
                'avg_separation': team_receiving['avg_separation'].mean(),
                'avg_cushion': team_receiving['avg_cushion'].mean(),
                'percent_share_of_intended_air_yards': team_receiving['percent_share_of_intended_air_yards'].mean(),
                'receptions': team_receiving['receptions'].sum(),
                'targets': team_receiving['targets'].sum(),
                'receiving_yards': team_receiving['yards'].sum(),
                'receiving_touchdowns': team_receiving['rec_touchdowns'].sum()
            }
        
        return team_stats
    
    def _calculate_pbp_metrics(self, pbp_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate play-by-play metrics for offense."""
        team_stats = {}
        
        for team in pbp_data['posteam'].unique():
            team_plays = pbp_data[pbp_data['posteam'] == team]
            
            team_stats[team] = {
                'cpoe': team_plays['cpoe'].mean(),
                'yac_epa': team_plays['yac_epa'].mean(),
                'xyac_epa': team_plays['xyac_epa'].mean(),
                'xyac_success': team_plays['xyac_success'].mean(),
                'xyac_fd': team_plays['xyac_fd'].mean(),
                'time_to_throw': team_plays['time_to_throw'].mean(),
                'was_pressure': team_plays['was_pressure'].mean(),
                'air_yards': team_plays['air_yards'].mean(),
                'xyac_mean_yardage': team_plays['xyac_mean_yardage'].mean(),
                'xyac_median_yardage': team_plays['xyac_median_yardage'].mean()
            }
        
        return team_stats
    
    def _calculate_pbp_defensive_metrics(self, pbp_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate play-by-play metrics for defense."""
        team_stats = {}
        
        for team in pbp_data['defteam'].unique():
            team_plays = pbp_data[pbp_data['defteam'] == team]
            
            team_stats[team] = {
                'def_cpoe_allowed': -team_plays['cpoe'].mean(),  # Negative because we want to minimize
                'def_yac_epa_allowed': -team_plays['yac_epa'].mean(),
                'def_xyac_epa_allowed': -team_plays['xyac_epa'].mean(),
                'def_xyac_success_allowed': -team_plays['xyac_success'].mean(),
                'def_xyac_fd_allowed': -team_plays['xyac_fd'].mean(),
                'def_time_to_throw_allowed': team_plays['time_to_throw'].mean(),  # Higher is better for defense
                'def_pressure_rate': team_plays['was_pressure'].mean(),
                'def_air_yards_allowed': -team_plays['air_yards'].mean(),
                'def_xyac_mean_yardage_allowed': -team_plays['xyac_mean_yardage'].mean(),
                'def_xyac_median_yardage_allowed': -team_plays['xyac_median_yardage'].mean()
            }
        
        return team_stats
    
    def _calculate_weighted_efficiency(self, stats: pd.DataFrame) -> pd.Series:
        """Calculate weighted NGS efficiency score."""
        efficiency = 0.0
        
        for metric, weight in self.ngs_weights.items():
            if metric in stats.columns:
                efficiency += stats[metric] * weight
        
        # Normalize to 0-1 scale
        total_weight = sum(self.ngs_weights.values())
        return efficiency / total_weight
    
    def _calculate_weighted_defense_efficiency(self, stats: pd.DataFrame) -> pd.Series:
        """Calculate weighted NGS defensive efficiency score (lower is better)."""
        efficiency = 0.0
        
        for metric, weight in self.ngs_weights.items():
            if metric in stats.columns:
                efficiency += stats[metric] * weight
        
        # Normalize to 0-1 scale (lower is better for defense)
        total_weight = sum(self.ngs_weights.values())
        return efficiency / total_weight
    
    def calculate_ngs_impact(self, offense_stats: pd.DataFrame, defense_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate NGS impact scores for each team.
        
        Args:
            offense_stats: Team NGS offensive stats
            defense_stats: Team NGS defensive stats
            
        Returns:
            DataFrame with NGS impact scores
        """
        print("Calculating NGS impact scores...")
        
        # Combine offense and defense stats
        ngs_impact = pd.DataFrame(index=offense_stats.index)
        
        # Copy offensive stats
        for col in offense_stats.columns:
            ngs_impact[f'off_{col}'] = offense_stats[col]
        
        # Copy defensive stats
        for col in defense_stats.columns:
            ngs_impact[f'def_{col}'] = defense_stats[col]
        
        # Calculate net NGS efficiency (offense - defense)
        ngs_impact['net_ngs_efficiency'] = (
            ngs_impact['off_ngs_efficiency'] - 
            ngs_impact['def_ngs_defense_efficiency']
        )
        
        # Calculate NGS advantage (positive = good, negative = bad)
        ngs_impact['ngs_advantage'] = (
            ngs_impact['off_ngs_efficiency'] - 
            ngs_impact['def_ngs_defense_efficiency']
        )
        
        # Calculate overall NGS impact score
        ngs_impact['ngs_impact_score'] = (
            ngs_impact['net_ngs_efficiency'] * 0.6 +
            ngs_impact['ngs_advantage'] * 0.4
        )
        
        # Normalize impact score to 0-1 scale
        ngs_impact['ngs_impact_normalized'] = (
            (ngs_impact['ngs_impact_score'] - ngs_impact['ngs_impact_score'].min()) /
            (ngs_impact['ngs_impact_score'].max() - ngs_impact['ngs_impact_score'].min())
        )
        
        print(f"Calculated NGS impact for {len(ngs_impact)} teams")
        return ngs_impact
    
    def create_ngs_database(self, years: List[int]) -> pd.DataFrame:
        """
        Create comprehensive NGS database for specified years.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with NGS impact scores
        """
        print(f"Creating NGS database for years {years}...")
        
        # Load NGS data
        ngs_data = self.load_ngs_data(years)
        
        # Calculate offensive and defensive stats
        offense_stats = self.calculate_team_ngs_offense(ngs_data)
        defense_stats = self.calculate_team_ngs_defense(ngs_data)
        
        # Calculate impact scores
        ngs_impact = self.calculate_ngs_impact(offense_stats, defense_stats)
        
        # Add year information
        ngs_impact['years_analyzed'] = str(years)
        ngs_impact['last_updated'] = datetime.now().isoformat()
        
        print(f"NGS database created with {len(ngs_impact)} teams")
        return ngs_impact
    
    def get_team_ngs_rating(self, team: str, ngs_db: pd.DataFrame) -> Dict[str, float]:
        """
        Get NGS rating for a specific team.
        
        Args:
            team: Team abbreviation
            ngs_db: NGS database
            
        Returns:
            Dictionary with team NGS metrics
        """
        if team not in ngs_db.index:
            return {
                'ngs_impact_score': 0.0,
                'ngs_advantage': 0.0,
                'off_ngs_efficiency': 0.5,  # League average
                'def_ngs_defense_efficiency': 0.5,  # League average
                'net_ngs_efficiency': 0.0
            }
        
        team_stats = ngs_db.loc[team]
        
        return {
            'ngs_impact_score': team_stats['ngs_impact_score'],
            'ngs_advantage': team_stats['ngs_advantage'],
            'off_ngs_efficiency': team_stats['off_ngs_efficiency'],
            'def_ngs_defense_efficiency': team_stats['def_ngs_defense_efficiency'],
            'net_ngs_efficiency': team_stats['net_ngs_efficiency'],
            'ngs_impact_normalized': team_stats['ngs_impact_normalized']
        }


def test_ngs_calculator():
    """Test the NGS calculator."""
    print("📊 TESTING NGS CALCULATOR")
    print("="*80)
    
    calculator = NGSCalculator()
    
    # Test with 2024 data
    ngs_db = calculator.create_ngs_database([2024])
    
    print(f"\\nNGS database created with {len(ngs_db)} teams")
    
    # Show top 10 teams by NGS impact
    print("\\nTop 10 teams by NGS impact:")
    top_teams = ngs_db.sort_values('ngs_impact_score', ascending=False).head(10)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['ngs_impact_score']:.3f} impact, "
              f"{stats['off_ngs_efficiency']:.3f} offense, "
              f"{stats['def_ngs_defense_efficiency']:.3f} defense")
    
    # Show bottom 10 teams
    print("\\nBottom 10 teams by NGS impact:")
    bottom_teams = ngs_db.sort_values('ngs_impact_score', ascending=True).head(10)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['ngs_impact_score']:.3f} impact, "
              f"{stats['off_ngs_efficiency']:.3f} offense, "
              f"{stats['def_ngs_defense_efficiency']:.3f} defense")
    
    # Test individual team lookup
    print("\\nTesting team lookup:")
    kc_rating = calculator.get_team_ngs_rating('KC', ngs_db)
    print(f"KC NGS rating: {kc_rating}")
    
    return calculator, ngs_db


if __name__ == "__main__":
    calculator, ngs_db = test_ngs_calculator()
