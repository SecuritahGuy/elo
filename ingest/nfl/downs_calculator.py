"""Third and fourth down efficiency calculator for NFL Elo ratings."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class DownsCalculator:
    """Calculates third and fourth down efficiency metrics for NFL teams."""
    
    def __init__(self):
        """Initialize downs calculator."""
        # Down efficiency weights (based on NFL analytics research)
        self.downs_weights = {
            'third_down_rate': 1.0,           # Third down conversion rate (most important)
            'fourth_down_rate': 0.8,          # Fourth down conversion rate
            'third_down_short': 1.2,          # Third and short (1-3 yards)
            'third_down_medium': 1.0,         # Third and medium (4-7 yards)
            'third_down_long': 0.8,           # Third and long (8+ yards)
            'fourth_down_short': 1.0,         # Fourth and short (1-3 yards)
            'fourth_down_medium': 0.8,        # Fourth and medium (4-7 yards)
            'fourth_down_long': 0.6,          # Fourth and long (8+ yards)
            'situational_efficiency': 0.9     # Situational efficiency
        }
        
        # Distance categories
        self.distance_categories = {
            'short': (1, 3),      # 1-3 yards
            'medium': (4, 7),     # 4-7 yards
            'long': (8, 20)       # 8+ yards
        }
    
    def load_downs_data(self, years: List[int]) -> pd.DataFrame:
        """
        Load third and fourth down data from play-by-play data.
        
        Args:
            years: Years to load data for
            
        Returns:
            DataFrame with down plays
        """
        import nfl_data_py as nfl
        
        print(f"Loading downs data for years {years}...")
        
        # Load play-by-play data
        pbp = nfl.import_pbp_data(years, downcast=True)
        print(f"Loaded {len(pbp)} total plays")
        
        # Filter for third and fourth down plays
        downs_plays = pbp[pbp['down'].isin([3, 4])].copy()
        print(f"Found {len(downs_plays)} third and fourth down plays")
        
        # Add distance categories
        downs_plays['distance_category'] = downs_plays['ydstogo'].apply(self._categorize_distance)
        
        return downs_plays
    
    def _categorize_distance(self, yards: float) -> str:
        """Categorize down and distance."""
        if yards <= 3:
            return 'short'
        elif yards <= 7:
            return 'medium'
        else:
            return 'long'
    
    def calculate_team_downs_offense(self, downs_plays: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate down efficiency for each team on offense.
        
        Args:
            downs_plays: DataFrame with down plays
            
        Returns:
            DataFrame with team down offensive stats
        """
        print("Calculating down offensive efficiency...")
        
        # Group by team and calculate offensive stats
        offense_stats = downs_plays.groupby('posteam').agg({
            'play_id': 'count',                    # Total down plays
            'first_down': 'sum',                   # Total conversions
            'third_down_converted': 'sum',         # Third down conversions
            'fourth_down_converted': 'sum',        # Fourth down conversions
            'touchdown': 'sum',                    # Touchdowns on down plays
            'distance_category': lambda x: x.value_counts().to_dict()  # Distance distribution
        }).rename(columns={
            'play_id': 'downs_plays',
            'first_down': 'downs_conversions',
            'third_down_converted': 'third_down_conversions',
            'fourth_down_converted': 'fourth_down_conversions',
            'touchdown': 'downs_touchdowns'
        })
        
        # Calculate overall conversion rates
        offense_stats['downs_conversion_rate'] = offense_stats['downs_conversions'] / offense_stats['downs_plays']
        
        # Calculate third down stats
        third_down_plays = downs_plays[downs_plays['down'] == 3]
        third_down_stats = third_down_plays.groupby('posteam').agg({
            'play_id': 'count',
            'first_down': 'sum',
            'touchdown': 'sum'
        }).rename(columns={
            'play_id': 'third_down_plays',
            'first_down': 'third_down_conversions',
            'touchdown': 'third_down_touchdowns'
        })
        
        offense_stats['third_down_rate'] = third_down_stats['third_down_conversions'] / third_down_stats['third_down_plays']
        offense_stats['third_down_plays'] = third_down_stats['third_down_plays']
        offense_stats['third_down_conversions'] = third_down_stats['third_down_conversions']
        
        # Calculate fourth down stats
        fourth_down_plays = downs_plays[downs_plays['down'] == 4]
        fourth_down_stats = fourth_down_plays.groupby('posteam').agg({
            'play_id': 'count',
            'first_down': 'sum',
            'touchdown': 'sum'
        }).rename(columns={
            'play_id': 'fourth_down_plays',
            'first_down': 'fourth_down_conversions',
            'touchdown': 'fourth_down_touchdowns'
        })
        
        offense_stats['fourth_down_rate'] = fourth_down_stats['fourth_down_conversions'] / fourth_down_stats['fourth_down_plays']
        offense_stats['fourth_down_plays'] = fourth_down_stats['fourth_down_plays']
        offense_stats['fourth_down_conversions'] = fourth_down_stats['fourth_down_conversions']
        
        # Calculate situational efficiency
        offense_stats = self._calculate_situational_efficiency(offense_stats, downs_plays)
        
        # Calculate weighted efficiency score
        offense_stats['downs_efficiency'] = self._calculate_weighted_efficiency(offense_stats)
        
        # Fill NaN values
        offense_stats = offense_stats.fillna(0.0)
        
        print(f"Calculated down offense for {len(offense_stats)} teams")
        return offense_stats
    
    def calculate_team_downs_defense(self, downs_plays: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate down efficiency for each team on defense.
        
        Args:
            downs_plays: DataFrame with down plays
            
        Returns:
            DataFrame with team down defensive stats
        """
        print("Calculating down defensive efficiency...")
        
        # Group by defensive team and calculate defensive stats
        defense_stats = downs_plays.groupby('defteam').agg({
            'play_id': 'count',                    # Total down plays against
            'first_down': 'sum',                   # Conversions allowed
            'third_down_converted': 'sum',         # Third down conversions allowed
            'fourth_down_converted': 'sum',        # Fourth down conversions allowed
            'touchdown': 'sum',                    # Touchdowns allowed on down plays
            'distance_category': lambda x: x.value_counts().to_dict()  # Distance distribution
        }).rename(columns={
            'play_id': 'downs_plays_against',
            'first_down': 'downs_conversions_allowed',
            'third_down_converted': 'third_down_conversions_allowed',
            'fourth_down_converted': 'fourth_down_conversions_allowed',
            'touchdown': 'downs_touchdowns_allowed'
        })
        
        # Calculate overall conversion rates allowed
        defense_stats['downs_conversion_rate_allowed'] = defense_stats['downs_conversions_allowed'] / defense_stats['downs_plays_against']
        
        # Calculate third down defense stats
        third_down_plays = downs_plays[downs_plays['down'] == 3]
        third_down_def_stats = third_down_plays.groupby('defteam').agg({
            'play_id': 'count',
            'first_down': 'sum',
            'touchdown': 'sum'
        }).rename(columns={
            'play_id': 'third_down_plays_against',
            'first_down': 'third_down_conversions_allowed',
            'touchdown': 'third_down_touchdowns_allowed'
        })
        
        defense_stats['third_down_rate_allowed'] = third_down_def_stats['third_down_conversions_allowed'] / third_down_def_stats['third_down_plays_against']
        defense_stats['third_down_plays_against'] = third_down_def_stats['third_down_plays_against']
        defense_stats['third_down_conversions_allowed'] = third_down_def_stats['third_down_conversions_allowed']
        
        # Calculate fourth down defense stats
        fourth_down_plays = downs_plays[downs_plays['down'] == 4]
        fourth_down_def_stats = fourth_down_plays.groupby('defteam').agg({
            'play_id': 'count',
            'first_down': 'sum',
            'touchdown': 'sum'
        }).rename(columns={
            'play_id': 'fourth_down_plays_against',
            'first_down': 'fourth_down_conversions_allowed',
            'touchdown': 'fourth_down_touchdowns_allowed'
        })
        
        defense_stats['fourth_down_rate_allowed'] = fourth_down_def_stats['fourth_down_conversions_allowed'] / fourth_down_def_stats['fourth_down_plays_against']
        defense_stats['fourth_down_plays_against'] = fourth_down_def_stats['fourth_down_plays_against']
        defense_stats['fourth_down_conversions_allowed'] = fourth_down_def_stats['fourth_down_conversions_allowed']
        
        # Calculate situational defensive efficiency
        defense_stats = self._calculate_situational_defense_efficiency(defense_stats, downs_plays)
        
        # Calculate weighted defensive efficiency (lower is better)
        defense_stats['downs_defense_efficiency'] = self._calculate_weighted_defense_efficiency(defense_stats)
        
        # Fill NaN values
        defense_stats = defense_stats.fillna(0.0)
        
        print(f"Calculated down defense for {len(defense_stats)} teams")
        return defense_stats
    
    def _calculate_situational_efficiency(self, stats: pd.DataFrame, downs_plays: pd.DataFrame) -> pd.DataFrame:
        """Calculate situational efficiency for different down and distance combinations."""
        for team in stats.index:
            team_plays = downs_plays[downs_plays['posteam'] == team]
            
            # Third down situational efficiency
            for category, (min_dist, max_dist) in self.distance_categories.items():
                third_down_category = team_plays[
                    (team_plays['down'] == 3) & 
                    (team_plays['ydstogo'] >= min_dist) & 
                    (team_plays['ydstogo'] <= max_dist)
                ]
                
                if len(third_down_category) > 0:
                    conversion_rate = third_down_category['first_down'].sum() / len(third_down_category)
                    stats.at[team, f'third_down_{category}_rate'] = conversion_rate
                else:
                    stats.at[team, f'third_down_{category}_rate'] = 0.0
                
                # Fourth down situational efficiency
                fourth_down_category = team_plays[
                    (team_plays['down'] == 4) & 
                    (team_plays['ydstogo'] >= min_dist) & 
                    (team_plays['ydstogo'] <= max_dist)
                ]
                
                if len(fourth_down_category) > 0:
                    conversion_rate = fourth_down_category['first_down'].sum() / len(fourth_down_category)
                    stats.at[team, f'fourth_down_{category}_rate'] = conversion_rate
                else:
                    stats.at[team, f'fourth_down_{category}_rate'] = 0.0
        
        return stats
    
    def _calculate_situational_defense_efficiency(self, stats: pd.DataFrame, downs_plays: pd.DataFrame) -> pd.DataFrame:
        """Calculate situational defensive efficiency for different down and distance combinations."""
        for team in stats.index:
            team_plays = downs_plays[downs_plays['defteam'] == team]
            
            # Third down situational defense efficiency
            for category, (min_dist, max_dist) in self.distance_categories.items():
                third_down_category = team_plays[
                    (team_plays['down'] == 3) & 
                    (team_plays['ydstogo'] >= min_dist) & 
                    (team_plays['ydstogo'] <= max_dist)
                ]
                
                if len(third_down_category) > 0:
                    conversion_rate_allowed = third_down_category['first_down'].sum() / len(third_down_category)
                    stats.at[team, f'third_down_{category}_rate_allowed'] = conversion_rate_allowed
                else:
                    stats.at[team, f'third_down_{category}_rate_allowed'] = 0.0
                
                # Fourth down situational defense efficiency
                fourth_down_category = team_plays[
                    (team_plays['down'] == 4) & 
                    (team_plays['ydstogo'] >= min_dist) & 
                    (team_plays['ydstogo'] <= max_dist)
                ]
                
                if len(fourth_down_category) > 0:
                    conversion_rate_allowed = fourth_down_category['first_down'].sum() / len(fourth_down_category)
                    stats.at[team, f'fourth_down_{category}_rate_allowed'] = conversion_rate_allowed
                else:
                    stats.at[team, f'fourth_down_{category}_rate_allowed'] = 0.0
        
        return stats
    
    def _calculate_weighted_efficiency(self, stats: pd.DataFrame) -> pd.Series:
        """Calculate weighted down efficiency score."""
        efficiency = (
            stats['third_down_rate'] * self.downs_weights['third_down_rate'] +
            stats['fourth_down_rate'] * self.downs_weights['fourth_down_rate'] +
            stats.get('third_down_short_rate', 0.0) * self.downs_weights['third_down_short'] +
            stats.get('third_down_medium_rate', 0.0) * self.downs_weights['third_down_medium'] +
            stats.get('third_down_long_rate', 0.0) * self.downs_weights['third_down_long'] +
            stats.get('fourth_down_short_rate', 0.0) * self.downs_weights['fourth_down_short'] +
            stats.get('fourth_down_medium_rate', 0.0) * self.downs_weights['fourth_down_medium'] +
            stats.get('fourth_down_long_rate', 0.0) * self.downs_weights['fourth_down_long']
        )
        
        # Normalize to 0-1 scale
        return efficiency / sum(self.downs_weights.values())
    
    def _calculate_weighted_defense_efficiency(self, stats: pd.DataFrame) -> pd.Series:
        """Calculate weighted down defensive efficiency score (lower is better)."""
        # For defense, we want to minimize these rates
        efficiency = (
            stats['third_down_rate_allowed'] * self.downs_weights['third_down_rate'] +
            stats['fourth_down_rate_allowed'] * self.downs_weights['fourth_down_rate'] +
            stats.get('third_down_short_rate_allowed', 0.0) * self.downs_weights['third_down_short'] +
            stats.get('third_down_medium_rate_allowed', 0.0) * self.downs_weights['third_down_medium'] +
            stats.get('third_down_long_rate_allowed', 0.0) * self.downs_weights['third_down_long'] +
            stats.get('fourth_down_short_rate_allowed', 0.0) * self.downs_weights['fourth_down_short'] +
            stats.get('fourth_down_medium_rate_allowed', 0.0) * self.downs_weights['fourth_down_medium'] +
            stats.get('fourth_down_long_rate_allowed', 0.0) * self.downs_weights['fourth_down_long']
        )
        
        # Normalize to 0-1 scale (lower is better for defense)
        return efficiency / sum(self.downs_weights.values())
    
    def calculate_downs_impact(self, offense_stats: pd.DataFrame, defense_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate down efficiency impact scores for each team.
        
        Args:
            offense_stats: Team down offensive stats
            defense_stats: Team down defensive stats
            
        Returns:
            DataFrame with down impact scores
        """
        print("Calculating down impact scores...")
        
        # Combine offense and defense stats
        downs_impact = pd.DataFrame(index=offense_stats.index)
        
        # Copy offensive stats
        for col in offense_stats.columns:
            downs_impact[f'off_{col}'] = offense_stats[col]
        
        # Copy defensive stats
        for col in defense_stats.columns:
            downs_impact[f'def_{col}'] = defense_stats[col]
        
        # Calculate net down efficiency (offense - defense)
        downs_impact['net_downs_efficiency'] = (
            downs_impact['off_downs_efficiency'] - 
            downs_impact['def_downs_defense_efficiency']
        )
        
        # Calculate down advantage (positive = good, negative = bad)
        downs_impact['downs_advantage'] = (
            downs_impact['off_third_down_rate'] - 
            downs_impact['def_third_down_rate_allowed']
        )
        
        # Calculate overall down impact score
        downs_impact['downs_impact_score'] = (
            downs_impact['net_downs_efficiency'] * 0.6 +
            downs_impact['downs_advantage'] * 0.4
        )
        
        # Normalize impact score to 0-1 scale
        downs_impact['downs_impact_normalized'] = (
            (downs_impact['downs_impact_score'] - downs_impact['downs_impact_score'].min()) /
            (downs_impact['downs_impact_score'].max() - downs_impact['downs_impact_score'].min())
        )
        
        print(f"Calculated down impact for {len(downs_impact)} teams")
        return downs_impact
    
    def create_downs_database(self, years: List[int]) -> pd.DataFrame:
        """
        Create comprehensive down efficiency database for specified years.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with down impact scores
        """
        print(f"Creating down efficiency database for years {years}...")
        
        # Load down data
        downs_plays = self.load_downs_data(years)
        
        # Calculate offensive and defensive stats
        offense_stats = self.calculate_team_downs_offense(downs_plays)
        defense_stats = self.calculate_team_downs_defense(downs_plays)
        
        # Calculate impact scores
        downs_impact = self.calculate_downs_impact(offense_stats, defense_stats)
        
        # Add year information
        downs_impact['years_analyzed'] = str(years)
        downs_impact['last_updated'] = datetime.now().isoformat()
        
        print(f"Down efficiency database created with {len(downs_impact)} teams")
        return downs_impact
    
    def get_team_downs_rating(self, team: str, downs_db: pd.DataFrame) -> Dict[str, float]:
        """
        Get down efficiency rating for a specific team.
        
        Args:
            team: Team abbreviation
            downs_db: Down efficiency database
            
        Returns:
            Dictionary with team down metrics
        """
        if team not in downs_db.index:
            return {
                'downs_impact_score': 0.0,
                'downs_advantage': 0.0,
                'off_third_down_rate': 0.36,  # League average
                'def_third_down_rate_allowed': 0.36,  # League average
                'off_fourth_down_rate': 0.11,  # League average
                'def_fourth_down_rate_allowed': 0.11,  # League average
                'net_downs_efficiency': 0.0
            }
        
        team_stats = downs_db.loc[team]
        
        return {
            'downs_impact_score': team_stats['downs_impact_score'],
            'downs_advantage': team_stats['downs_advantage'],
            'off_third_down_rate': team_stats['off_third_down_rate'],
            'def_third_down_rate_allowed': team_stats['def_third_down_rate_allowed'],
            'off_fourth_down_rate': team_stats['off_fourth_down_rate'],
            'def_fourth_down_rate_allowed': team_stats['def_fourth_down_rate_allowed'],
            'net_downs_efficiency': team_stats['net_downs_efficiency'],
            'downs_impact_normalized': team_stats['downs_impact_normalized']
        }


def test_downs_calculator():
    """Test the down efficiency calculator."""
    print("📊 TESTING DOWN EFFICIENCY CALCULATOR")
    print("="*80)
    
    calculator = DownsCalculator()
    
    # Test with 2024 data
    downs_db = calculator.create_downs_database([2024])
    
    print(f"\\nDown efficiency database created with {len(downs_db)} teams")
    
    # Show top 10 teams by down impact
    print("\\nTop 10 teams by down impact:")
    top_teams = downs_db.sort_values('downs_impact_score', ascending=False).head(10)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['downs_impact_score']:.3f} impact, "
              f"{stats['off_third_down_rate']:.3f} 3rd down, "
              f"{stats['def_third_down_rate_allowed']:.3f} 3rd down allowed")
    
    # Show bottom 10 teams
    print("\\nBottom 10 teams by down impact:")
    bottom_teams = downs_db.sort_values('downs_impact_score', ascending=True).head(10)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['downs_impact_score']:.3f} impact, "
              f"{stats['off_third_down_rate']:.3f} 3rd down, "
              f"{stats['def_third_down_rate_allowed']:.3f} 3rd down allowed")
    
    # Test individual team lookup
    print("\\nTesting team lookup:")
    kc_rating = calculator.get_team_downs_rating('KC', downs_db)
    print(f"KC down rating: {kc_rating}")
    
    return calculator, downs_db


if __name__ == "__main__":
    calculator, downs_db = test_downs_calculator()
