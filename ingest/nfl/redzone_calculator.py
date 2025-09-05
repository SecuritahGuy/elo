"""Red zone efficiency calculator for NFL Elo ratings."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class RedZoneCalculator:
    """Calculates red zone efficiency metrics for NFL teams."""
    
    def __init__(self):
        """Initialize red zone calculator."""
        # Red zone efficiency weights (based on NFL analytics research)
        self.redzone_weights = {
            'td_rate': 1.0,           # Touchdown rate (most important)
            'score_rate': 0.8,        # Overall scoring rate (TD + FG)
            'pass_td_rate': 0.9,      # Passing touchdown rate
            'rush_td_rate': 0.7,      # Rushing touchdown rate
            'fg_rate': 0.6,           # Field goal rate
            'efficiency': 0.5         # Overall efficiency metric
        }
        
        # Red zone distance weights (closer to goal = more important)
        self.distance_weights = {
            '1-5': 1.0,      # Goal line area
            '6-10': 0.9,     # Close red zone
            '11-15': 0.8,    # Mid red zone
            '16-20': 0.7     # Far red zone
        }
    
    def load_redzone_data(self, years: List[int]) -> pd.DataFrame:
        """
        Load red zone data from play-by-play data.
        
        Args:
            years: Years to load data for
            
        Returns:
            DataFrame with red zone plays
        """
        import nfl_data_py as nfl
        
        print(f"Loading red zone data for years {years}...")
        
        # Load play-by-play data
        pbp = nfl.import_pbp_data(years, downcast=True)
        print(f"Loaded {len(pbp)} total plays")
        
        # Filter for red zone plays (yardline_100 <= 20)
        redzone_plays = pbp[pbp['yardline_100'] <= 20].copy()
        print(f"Found {len(redzone_plays)} red zone plays")
        
        # Add red zone distance categories
        redzone_plays['redzone_distance'] = redzone_plays['yardline_100'].apply(self._categorize_redzone_distance)
        
        return redzone_plays
    
    def _categorize_redzone_distance(self, yardline: float) -> str:
        """Categorize red zone distance."""
        if yardline <= 5:
            return '1-5'
        elif yardline <= 10:
            return '6-10'
        elif yardline <= 15:
            return '11-15'
        else:
            return '16-20'
    
    def calculate_team_redzone_offense(self, redzone_plays: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate red zone offensive efficiency for each team.
        
        Args:
            redzone_plays: DataFrame with red zone plays
            
        Returns:
            DataFrame with team red zone offensive stats
        """
        print("Calculating red zone offensive efficiency...")
        
        # Group by team and calculate offensive stats
        offense_stats = redzone_plays.groupby('posteam').agg({
            'play_id': 'count',                    # Total red zone plays
            'touchdown': 'sum',                    # Total touchdowns
            'pass_touchdown': 'sum',               # Passing touchdowns
            'rush_touchdown': 'sum',               # Rushing touchdowns
            'field_goal_attempt': 'sum',           # Field goal attempts
            'field_goal_result': lambda x: (x == 'made').sum(),  # Made field goals
            'redzone_distance': lambda x: x.value_counts().to_dict()  # Distance distribution
        }).rename(columns={
            'play_id': 'redzone_plays',
            'touchdown': 'redzone_tds',
            'pass_touchdown': 'redzone_pass_tds',
            'rush_touchdown': 'redzone_rush_tds',
            'field_goal_attempt': 'redzone_fg_attempts',
            'field_goal_result': 'redzone_fg_made'
        })
        
        # Calculate efficiency rates
        offense_stats['redzone_td_rate'] = offense_stats['redzone_tds'] / offense_stats['redzone_plays']
        offense_stats['redzone_pass_td_rate'] = offense_stats['redzone_pass_tds'] / offense_stats['redzone_plays']
        offense_stats['redzone_rush_td_rate'] = offense_stats['redzone_rush_tds'] / offense_stats['redzone_plays']
        offense_stats['redzone_fg_rate'] = offense_stats['redzone_fg_made'] / offense_stats['redzone_fg_attempts'].replace(0, np.nan)
        offense_stats['redzone_score_rate'] = (offense_stats['redzone_tds'] + offense_stats['redzone_fg_made']) / offense_stats['redzone_plays']
        
        # Calculate weighted efficiency score
        offense_stats['redzone_efficiency'] = self._calculate_weighted_efficiency(offense_stats)
        
        # Fill NaN values
        offense_stats = offense_stats.fillna(0.0)
        
        print(f"Calculated red zone offense for {len(offense_stats)} teams")
        return offense_stats
    
    def calculate_team_redzone_defense(self, redzone_plays: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate red zone defensive efficiency for each team.
        
        Args:
            redzone_plays: DataFrame with red zone plays
            
        Returns:
            DataFrame with team red zone defensive stats
        """
        print("Calculating red zone defensive efficiency...")
        
        # Group by defensive team and calculate defensive stats
        defense_stats = redzone_plays.groupby('defteam').agg({
            'play_id': 'count',                    # Total red zone plays against
            'touchdown': 'sum',                    # Touchdowns allowed
            'pass_touchdown': 'sum',               # Passing touchdowns allowed
            'rush_touchdown': 'sum',               # Rushing touchdowns allowed
            'field_goal_attempt': 'sum',           # Field goal attempts against
            'field_goal_result': lambda x: (x == 'made').sum(),  # Field goals allowed
            'redzone_distance': lambda x: x.value_counts().to_dict()  # Distance distribution
        }).rename(columns={
            'play_id': 'redzone_plays_against',
            'touchdown': 'redzone_tds_allowed',
            'pass_touchdown': 'redzone_pass_tds_allowed',
            'rush_touchdown': 'redzone_rush_tds_allowed',
            'field_goal_attempt': 'redzone_fg_attempts_against',
            'field_goal_result': 'redzone_fg_allowed'
        })
        
        # Calculate defensive efficiency rates
        defense_stats['redzone_td_rate_allowed'] = defense_stats['redzone_tds_allowed'] / defense_stats['redzone_plays_against']
        defense_stats['redzone_pass_td_rate_allowed'] = defense_stats['redzone_pass_tds_allowed'] / defense_stats['redzone_plays_against']
        defense_stats['redzone_rush_td_rate_allowed'] = defense_stats['redzone_rush_tds_allowed'] / defense_stats['redzone_plays_against']
        defense_stats['redzone_fg_rate_allowed'] = defense_stats['redzone_fg_allowed'] / defense_stats['redzone_fg_attempts_against'].replace(0, np.nan)
        defense_stats['redzone_score_rate_allowed'] = (defense_stats['redzone_tds_allowed'] + defense_stats['redzone_fg_allowed']) / defense_stats['redzone_plays_against']
        
        # Calculate weighted defensive efficiency (lower is better)
        defense_stats['redzone_defense_efficiency'] = self._calculate_weighted_defense_efficiency(defense_stats)
        
        # Fill NaN values
        defense_stats = defense_stats.fillna(0.0)
        
        print(f"Calculated red zone defense for {len(defense_stats)} teams")
        return defense_stats
    
    def _calculate_weighted_efficiency(self, stats: pd.DataFrame) -> pd.Series:
        """Calculate weighted red zone efficiency score."""
        efficiency = (
            stats['redzone_td_rate'] * self.redzone_weights['td_rate'] +
            stats['redzone_score_rate'] * self.redzone_weights['score_rate'] +
            stats['redzone_pass_td_rate'] * self.redzone_weights['pass_td_rate'] +
            stats['redzone_rush_td_rate'] * self.redzone_weights['rush_td_rate'] +
            stats['redzone_fg_rate'] * self.redzone_weights['fg_rate']
        )
        
        # Normalize to 0-1 scale
        return efficiency / sum(self.redzone_weights.values())
    
    def _calculate_weighted_defense_efficiency(self, stats: pd.DataFrame) -> pd.Series:
        """Calculate weighted red zone defensive efficiency score (lower is better)."""
        # For defense, we want to minimize these rates
        efficiency = (
            stats['redzone_td_rate_allowed'] * self.redzone_weights['td_rate'] +
            stats['redzone_score_rate_allowed'] * self.redzone_weights['score_rate'] +
            stats['redzone_pass_td_rate_allowed'] * self.redzone_weights['pass_td_rate'] +
            stats['redzone_rush_td_rate_allowed'] * self.redzone_weights['rush_td_rate'] +
            stats['redzone_fg_rate_allowed'] * self.redzone_weights['fg_rate']
        )
        
        # Normalize to 0-1 scale (lower is better for defense)
        return efficiency / sum(self.redzone_weights.values())
    
    def calculate_redzone_impact(self, offense_stats: pd.DataFrame, defense_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate red zone impact scores for each team.
        
        Args:
            offense_stats: Team red zone offensive stats
            defense_stats: Team red zone defensive stats
            
        Returns:
            DataFrame with red zone impact scores
        """
        print("Calculating red zone impact scores...")
        
        # Combine offense and defense stats
        redzone_impact = pd.DataFrame(index=offense_stats.index)
        
        # Copy offensive stats
        for col in offense_stats.columns:
            redzone_impact[f'off_{col}'] = offense_stats[col]
        
        # Copy defensive stats
        for col in defense_stats.columns:
            redzone_impact[f'def_{col}'] = defense_stats[col]
        
        # Calculate net red zone efficiency (offense - defense)
        redzone_impact['net_redzone_efficiency'] = (
            redzone_impact['off_redzone_efficiency'] - 
            redzone_impact['def_redzone_defense_efficiency']
        )
        
        # Calculate red zone advantage (positive = good, negative = bad)
        redzone_impact['redzone_advantage'] = (
            redzone_impact['off_redzone_td_rate'] - 
            redzone_impact['def_redzone_td_rate_allowed']
        )
        
        # Calculate overall red zone impact score
        redzone_impact['redzone_impact_score'] = (
            redzone_impact['net_redzone_efficiency'] * 0.6 +
            redzone_impact['redzone_advantage'] * 0.4
        )
        
        # Normalize impact score to 0-1 scale
        redzone_impact['redzone_impact_normalized'] = (
            (redzone_impact['redzone_impact_score'] - redzone_impact['redzone_impact_score'].min()) /
            (redzone_impact['redzone_impact_score'].max() - redzone_impact['redzone_impact_score'].min())
        )
        
        print(f"Calculated red zone impact for {len(redzone_impact)} teams")
        return redzone_impact
    
    def create_redzone_database(self, years: List[int]) -> pd.DataFrame:
        """
        Create comprehensive red zone database for specified years.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with red zone impact scores
        """
        print(f"Creating red zone database for years {years}...")
        
        # Load red zone data
        redzone_plays = self.load_redzone_data(years)
        
        # Calculate offensive and defensive stats
        offense_stats = self.calculate_team_redzone_offense(redzone_plays)
        defense_stats = self.calculate_team_redzone_defense(redzone_plays)
        
        # Calculate impact scores
        redzone_impact = self.calculate_redzone_impact(offense_stats, defense_stats)
        
        # Add year information
        redzone_impact['years_analyzed'] = str(years)
        redzone_impact['last_updated'] = datetime.now().isoformat()
        
        print(f"Red zone database created with {len(redzone_impact)} teams")
        return redzone_impact
    
    def get_team_redzone_rating(self, team: str, redzone_db: pd.DataFrame) -> Dict[str, float]:
        """
        Get red zone rating for a specific team.
        
        Args:
            team: Team abbreviation
            redzone_db: Red zone database
            
        Returns:
            Dictionary with team red zone metrics
        """
        if team not in redzone_db.index:
            return {
                'redzone_impact_score': 0.0,
                'redzone_advantage': 0.0,
                'off_redzone_td_rate': 0.135,  # League average
                'def_redzone_td_rate_allowed': 0.135,  # League average
                'net_redzone_efficiency': 0.0
            }
        
        team_stats = redzone_db.loc[team]
        
        return {
            'redzone_impact_score': team_stats['redzone_impact_score'],
            'redzone_advantage': team_stats['redzone_advantage'],
            'off_redzone_td_rate': team_stats['off_redzone_td_rate'],
            'def_redzone_td_rate_allowed': team_stats['def_redzone_td_rate_allowed'],
            'net_redzone_efficiency': team_stats['net_redzone_efficiency'],
            'redzone_impact_normalized': team_stats['redzone_impact_normalized']
        }


def test_redzone_calculator():
    """Test the red zone calculator."""
    print("🔴 TESTING RED ZONE CALCULATOR")
    print("="*80)
    
    calculator = RedZoneCalculator()
    
    # Test with 2024 data
    redzone_db = calculator.create_redzone_database([2024])
    
    print(f"\\nRed zone database created with {len(redzone_db)} teams")
    
    # Show top 10 teams by red zone impact
    print("\\nTop 10 teams by red zone impact:")
    top_teams = redzone_db.sort_values('redzone_impact_score', ascending=False).head(10)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['redzone_impact_score']:.3f} impact, "
              f"{stats['off_redzone_td_rate']:.3f} TD rate, "
              f"{stats['def_redzone_td_rate_allowed']:.3f} TD allowed")
    
    # Show bottom 10 teams
    print("\\nBottom 10 teams by red zone impact:")
    bottom_teams = redzone_db.sort_values('redzone_impact_score', ascending=True).head(10)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['redzone_impact_score']:.3f} impact, "
              f"{stats['off_redzone_td_rate']:.3f} TD rate, "
              f"{stats['def_redzone_td_rate_allowed']:.3f} TD allowed")
    
    # Test individual team lookup
    print("\\nTesting team lookup:")
    kc_rating = calculator.get_team_redzone_rating('KC', redzone_db)
    print(f"KC red zone rating: {kc_rating}")
    
    return calculator, redzone_db


if __name__ == "__main__":
    calculator, redzone_db = test_redzone_calculator()
