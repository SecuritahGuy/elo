"""Turnover calculator for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class TurnoverCalculator:
    """Calculates turnover-based metrics for team performance analysis."""
    
    def __init__(self):
        """Initialize turnover calculator."""
        # Turnover metrics weights (based on research findings)
        self.turnover_weights = {
            'turnover_differential': 1.0,      # Most important - net turnover impact
            'takeaway_rate': 0.8,              # Defensive turnover creation
            'giveaway_rate': 0.7,              # Offensive turnover prevention (inverted)
            'turnover_efficiency': 0.9,        # Overall turnover efficiency
            'turnover_consistency': 0.6        # Consistency of turnover performance
        }
    
    def load_turnover_data(self, years: List[int]) -> pd.DataFrame:
        """
        Load turnover data for specified years.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with turnover data
        """
        import nfl_data_py as nfl
        
        print(f"Loading turnover data for years {years}...")
        
        # Load play-by-play data
        pbp = nfl.import_pbp_data(years, downcast=True)
        print(f"Loaded {len(pbp)} plays")
        
        # Calculate offensive turnovers (giveaways)
        offensive_turnovers = pbp.groupby(['posteam', 'season']).agg({
            'interception': 'sum',
            'fumble_lost': 'sum',
            'play_id': 'count'
        }).rename(columns={'play_id': 'total_plays'})
        
        offensive_turnovers['giveaways'] = offensive_turnovers['interception'] + offensive_turnovers['fumble_lost']
        offensive_turnovers['giveaway_rate'] = offensive_turnovers['giveaways'] / offensive_turnovers['total_plays']
        
        # Calculate defensive turnovers (takeaways)
        defensive_turnovers = pbp.groupby(['defteam', 'season']).agg({
            'interception': 'sum',
            'fumble_lost': 'sum',
            'play_id': 'count'
        }).rename(columns={'play_id': 'total_plays'})
        
        defensive_turnovers['takeaways'] = defensive_turnovers['interception'] + defensive_turnovers['fumble_lost']
        defensive_turnovers['takeaway_rate'] = defensive_turnovers['takeaways'] / defensive_turnovers['total_plays']
        
        # Combine offensive and defensive data
        turnover_data = pd.DataFrame()
        
        for team in offensive_turnovers.index.get_level_values('posteam').unique():
            if pd.isna(team):
                continue
                
            for season in offensive_turnovers.index.get_level_values('season').unique():
                if pd.isna(season):
                    continue
                
                # Get offensive data
                off_data = offensive_turnovers.loc[(team, season)]
                def_data = defensive_turnovers.loc[(team, season)]
                
                turnover_data = pd.concat([turnover_data, pd.DataFrame({
                    'team': team,
                    'season': season,
                    'giveaways': off_data['giveaways'],
                    'takeaways': def_data['takeaways'],
                    'turnover_differential': def_data['takeaways'] - off_data['giveaways'],
                    'giveaway_rate': off_data['giveaway_rate'],
                    'takeaway_rate': def_data['takeaway_rate'],
                    'total_plays': off_data['total_plays']
                }, index=[0])], ignore_index=True)
        
        print(f"Calculated turnover data for {len(turnover_data)} team-seasons")
        return turnover_data
    
    def calculate_turnover_metrics(self, turnover_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive turnover metrics for each team.
        
        Args:
            turnover_data: Raw turnover data
            
        Returns:
            DataFrame with calculated turnover metrics
        """
        print("Calculating turnover metrics...")
        
        # Calculate team averages across seasons
        team_metrics = turnover_data.groupby('team').agg({
            'giveaway_rate': 'mean',
            'takeaway_rate': 'mean',
            'turnover_differential': 'mean',
            'total_plays': 'sum',
            'giveaways': 'sum',
            'takeaways': 'sum'
        }).round(4)
        
        # Calculate additional metrics
        team_metrics['turnover_efficiency'] = self._calculate_turnover_efficiency(team_metrics)
        team_metrics['turnover_consistency'] = self._calculate_turnover_consistency(turnover_data)
        team_metrics['net_turnover_impact'] = team_metrics['turnover_differential']
        
        # Calculate weighted turnover score
        team_metrics['turnover_score'] = self._calculate_weighted_turnover_score(team_metrics)
        
        # Normalize turnover score to 0-1 scale
        min_score = team_metrics['turnover_score'].min()
        max_score = team_metrics['turnover_score'].max()
        if max_score > min_score:
            team_metrics['turnover_score_normalized'] = (
                (team_metrics['turnover_score'] - min_score) / (max_score - min_score)
            )
        else:
            team_metrics['turnover_score_normalized'] = 0.5
        
        print(f"Calculated turnover metrics for {len(team_metrics)} teams")
        return team_metrics
    
    def _calculate_turnover_efficiency(self, team_metrics: pd.DataFrame) -> pd.Series:
        """Calculate turnover efficiency score."""
        # Efficiency = (takeaway_rate - giveaway_rate) / (takeaway_rate + giveaway_rate + 0.001)
        # This gives a score between -1 and 1, where positive is good
        efficiency = (
            (team_metrics['takeaway_rate'] - team_metrics['giveaway_rate']) / 
            (team_metrics['takeaway_rate'] + team_metrics['giveaway_rate'] + 0.001)
        )
        return efficiency
    
    def _calculate_turnover_consistency(self, turnover_data: pd.DataFrame) -> pd.Series:
        """Calculate turnover consistency (lower variance is better)."""
        # Calculate variance in turnover differential across seasons
        consistency = turnover_data.groupby('team')['turnover_differential'].std()
        # Invert so lower variance = higher consistency score
        consistency = 1.0 / (consistency + 1.0)
        return consistency
    
    def _calculate_weighted_turnover_score(self, team_metrics: pd.DataFrame) -> pd.Series:
        """Calculate weighted turnover score."""
        score = 0.0
        
        for metric, weight in self.turnover_weights.items():
            if metric in team_metrics.columns:
                # Normalize each metric to 0-1 scale
                metric_values = team_metrics[metric]
                if metric_values.max() > metric_values.min():
                    normalized = (metric_values - metric_values.min()) / (metric_values.max() - metric_values.min())
                else:
                    normalized = 0.5
                
                # For giveaway_rate, invert since lower is better
                if metric == 'giveaway_rate':
                    normalized = 1.0 - normalized
                
                score += normalized * weight
        
        # Normalize to 0-1 scale
        total_weight = sum(self.turnover_weights.values())
        return score / total_weight
    
    def calculate_turnover_impact(self, team_metrics: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate turnover impact scores for Elo adjustments.
        
        Args:
            team_metrics: Team turnover metrics
            
        Returns:
            DataFrame with turnover impact scores
        """
        print("Calculating turnover impact scores...")
        
        # Calculate turnover advantage
        team_metrics['turnover_advantage'] = team_metrics['turnover_score_normalized']
        
        # Calculate overall turnover impact score
        team_metrics['turnover_impact_score'] = (
            team_metrics['turnover_score_normalized'] * 0.6 +
            team_metrics['turnover_advantage'] * 0.4
        )
        
        # Normalize impact score to 0-1 scale
        min_impact = team_metrics['turnover_impact_score'].min()
        max_impact = team_metrics['turnover_impact_score'].max()
        if max_impact > min_impact:
            team_metrics['turnover_impact_normalized'] = (
                (team_metrics['turnover_impact_score'] - min_impact) / (max_impact - min_impact)
            )
        else:
            team_metrics['turnover_impact_normalized'] = 0.5
        
        print(f"Calculated turnover impact for {len(team_metrics)} teams")
        return team_metrics
    
    def create_turnover_database(self, years: List[int]) -> pd.DataFrame:
        """
        Create comprehensive turnover database for specified years.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with turnover impact scores
        """
        print(f"Creating turnover database for years {years}...")
        
        # Load turnover data
        turnover_data = self.load_turnover_data(years)
        
        # Calculate metrics
        team_metrics = self.calculate_turnover_metrics(turnover_data)
        
        # Calculate impact scores
        turnover_impact = self.calculate_turnover_impact(team_metrics)
        
        # Add year information
        turnover_impact['years_analyzed'] = str(years)
        turnover_impact['last_updated'] = datetime.now().isoformat()
        
        print(f"Turnover database created with {len(turnover_impact)} teams")
        return turnover_impact
    
    def get_team_turnover_rating(self, team: str, turnover_db: pd.DataFrame) -> Dict[str, float]:
        """
        Get turnover rating for a specific team.
        
        Args:
            team: Team abbreviation
            turnover_db: Turnover database
            
        Returns:
            Dictionary with team turnover metrics
        """
        if team not in turnover_db.index:
            return {
                'turnover_impact_score': 0.0,
                'turnover_advantage': 0.0,
                'turnover_score': 0.5,  # League average
                'turnover_differential': 0.0,
                'turnover_impact_normalized': 0.5
            }
        
        team_stats = turnover_db.loc[team]
        
        return {
            'turnover_impact_score': team_stats['turnover_impact_score'],
            'turnover_advantage': team_stats['turnover_advantage'],
            'turnover_score': team_stats['turnover_score'],
            'turnover_differential': team_stats['turnover_differential'],
            'turnover_impact_normalized': team_stats['turnover_impact_normalized']
        }


def test_turnover_calculator():
    """Test the turnover calculator."""
    print("📊 TESTING TURNOVER CALCULATOR")
    print("="*80)
    
    calculator = TurnoverCalculator()
    
    # Test with 2024 data
    turnover_db = calculator.create_turnover_database([2024])
    
    if turnover_db.empty:
        print("No data loaded, cannot test")
        return calculator, turnover_db
    
    print(f"\\nTurnover database created with {len(turnover_db)} teams")
    
    # Show top 10 teams by turnover score
    print("\\nTop 10 teams by turnover score:")
    top_teams = turnover_db.sort_values('turnover_score', ascending=False).head(10)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['turnover_score']:.3f} score (diff: {stats['turnover_differential']:.1f})")
    
    # Show bottom 10 teams
    print("\\nBottom 10 teams by turnover score:")
    bottom_teams = turnover_db.sort_values('turnover_score', ascending=True).head(10)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['turnover_score']:.3f} score (diff: {stats['turnover_differential']:.1f})")
    
    # Test individual team lookup
    print("\\nTesting team lookup:")
    kc_rating = calculator.get_team_turnover_rating('KC', turnover_db)
    print(f"KC turnover rating: {kc_rating}")
    
    return calculator, turnover_db


if __name__ == "__main__":
    calculator, turnover_db = test_turnover_calculator()
