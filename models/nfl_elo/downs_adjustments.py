"""Third and fourth down efficiency adjustments for NFL Elo ratings."""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from ingest.nfl.downs_calculator import DownsCalculator


class DownsAdjustmentCalculator:
    """Calculates third and fourth down efficiency adjustments for Elo ratings."""
    
    def __init__(self):
        """Initialize down efficiency adjustment calculator."""
        self.downs_calc = DownsCalculator()
        self.downs_db: Optional[pd.DataFrame] = None
        self.last_years: Optional[list] = None
    
    def load_downs_data(self, years: list) -> None:
        """
        Load down efficiency data for specified years.
        
        Args:
            years: Years to load data for
        """
        if self.last_years != years or self.downs_db is None:
            print(f"Loading down efficiency data for years {years}...")
            self.downs_db = self.downs_calc.create_downs_database(years)
            self.last_years = years
            print(f"Down efficiency database loaded with {len(self.downs_db)} teams")
    
    def calculate_downs_adjustment(self, team: str, years: list) -> float:
        """
        Calculate down efficiency adjustment for a team.
        
        Args:
            team: Team abbreviation
            years: Years to analyze
            
        Returns:
            Down efficiency adjustment delta
        """
        # Load down efficiency data if needed
        self.load_downs_data(years)
        
        if self.downs_db is None or team not in self.downs_db.index:
            return 0.0
        
        # Get team down efficiency rating
        team_rating = self.downs_calc.get_team_downs_rating(team, self.downs_db)
        
        # Calculate adjustment based on down efficiency impact
        downs_impact = team_rating['downs_impact_score']
        
        # Apply adjustment (positive impact = positive adjustment)
        adjustment = downs_impact * 15.0  # Scale factor
        
        return adjustment
    
    def calculate_downs_adjustments(self, home_team: str, away_team: str, years: list) -> Tuple[float, float]:
        """
        Calculate down efficiency adjustments for both teams.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            years: Years to analyze
            
        Returns:
            Tuple of (home_adjustment, away_adjustment)
        """
        home_adj = self.calculate_downs_adjustment(home_team, years)
        away_adj = self.calculate_downs_adjustment(away_team, years)
        
        return home_adj, away_adj
    
    def get_team_downs_stats(self, team: str, years: list) -> Dict[str, Any]:
        """
        Get comprehensive down efficiency stats for a team.
        
        Args:
            team: Team abbreviation
            years: Years to analyze
            
        Returns:
            Dictionary with team down efficiency statistics
        """
        # Load down efficiency data if needed
        self.load_downs_data(years)
        
        if self.downs_db is None or team not in self.downs_db.index:
            return {
                'downs_impact_score': 0.0,
                'downs_advantage': 0.0,
                'off_third_down_rate': 0.36,  # League average
                'def_third_down_rate_allowed': 0.36,  # League average
                'off_fourth_down_rate': 0.11,  # League average
                'def_fourth_down_rate_allowed': 0.11,  # League average
                'net_downs_efficiency': 0.0,
                'downs_adjustment': 0.0
            }
        
        # Get team down efficiency rating
        team_rating = self.downs_calc.get_team_downs_rating(team, self.downs_db)
        
        # Calculate adjustment
        adjustment = self.calculate_downs_adjustment(team, years)
        
        # Add adjustment to stats
        team_rating['downs_adjustment'] = adjustment
        
        return team_rating
    
    def analyze_downs_impact(self, years: list) -> pd.DataFrame:
        """
        Analyze down efficiency impact across all teams.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with down efficiency impact analysis
        """
        # Load down efficiency data if needed
        self.load_downs_data(years)
        
        if self.downs_db is None:
            return pd.DataFrame()
        
        # Calculate adjustments for all teams
        adjustments = []
        for team in self.downs_db.index:
            team_stats = self.get_team_downs_stats(team, years)
            adjustments.append({
                'team': team,
                'downs_impact_score': team_stats['downs_impact_score'],
                'downs_advantage': team_stats['downs_advantage'],
                'off_third_down_rate': team_stats['off_third_down_rate'],
                'def_third_down_rate_allowed': team_stats['def_third_down_rate_allowed'],
                'off_fourth_down_rate': team_stats['off_fourth_down_rate'],
                'def_fourth_down_rate_allowed': team_stats['def_fourth_down_rate_allowed'],
                'net_downs_efficiency': team_stats['net_downs_efficiency'],
                'downs_adjustment': team_stats['downs_adjustment']
            })
        
        return pd.DataFrame(adjustments)
    
    def get_downs_summary(self, years: list) -> Dict[str, Any]:
        """
        Get summary statistics for down efficiency impact.
        
        Args:
            years: Years to analyze
            
        Returns:
            Dictionary with down efficiency summary statistics
        """
        # Load down efficiency data if needed
        self.load_downs_data(years)
        
        if self.downs_db is None:
            return {
                'total_teams': 0,
                'avg_downs_impact': 0.0,
                'downs_impact_range': (0.0, 0.0),
                'teams_with_positive_impact': 0,
                'teams_with_negative_impact': 0,
                'avg_adjustment': 0.0,
                'adjustment_range': (0.0, 0.0)
            }
        
        # Calculate summary statistics
        impact_scores = self.downs_db['downs_impact_score']
        adjustments = [self.calculate_downs_adjustment(team, years) for team in self.downs_db.index]
        
        return {
            'total_teams': len(self.downs_db),
            'avg_downs_impact': impact_scores.mean(),
            'downs_impact_range': (impact_scores.min(), impact_scores.max()),
            'teams_with_positive_impact': (impact_scores > 0).sum(),
            'teams_with_negative_impact': (impact_scores < 0).sum(),
            'avg_adjustment': np.mean(adjustments),
            'adjustment_range': (min(adjustments), max(adjustments))
        }


def test_downs_adjustments():
    """Test the down efficiency adjustment calculator."""
    print("📊 TESTING DOWN EFFICIENCY ADJUSTMENT CALCULATOR")
    print("="*80)
    
    calc = DownsAdjustmentCalculator()
    
    # Test with 2024 data
    years = [2024]
    calc.load_downs_data(years)
    
    # Test individual team adjustments
    print("\\nTesting individual team adjustments:")
    test_teams = ['KC', 'BAL', 'DET', 'CAR']
    for team in test_teams:
        stats = calc.get_team_downs_stats(team, years)
        print(f"  {team}: {stats['downs_adjustment']:.3f} adjustment, "
              f"{stats['downs_impact_score']:.3f} impact")
    
    # Test team vs team adjustments
    print("\\nTesting team vs team adjustments:")
    home_adj, away_adj = calc.calculate_downs_adjustments('KC', 'BAL', years)
    print(f"  KC (home) vs BAL (away): {home_adj:.3f} vs {away_adj:.3f}")
    
    # Analyze down efficiency impact
    print("\\nAnalyzing down efficiency impact:")
    analysis = calc.analyze_downs_impact(years)
    print(f"  Teams analyzed: {len(analysis)}")
    print(f"  Average adjustment: {analysis['downs_adjustment'].mean():.3f}")
    print(f"  Adjustment range: {analysis['downs_adjustment'].min():.3f} to {analysis['downs_adjustment'].max():.3f}")
    
    # Get summary
    summary = calc.get_downs_summary(years)
    print(f"\\nDown efficiency summary:")
    print(f"  Total teams: {summary['total_teams']}")
    print(f"  Average impact: {summary['avg_downs_impact']:.3f}")
    print(f"  Teams with positive impact: {summary['teams_with_positive_impact']}")
    print(f"  Teams with negative impact: {summary['teams_with_negative_impact']}")
    
    return calc


if __name__ == "__main__":
    calc = test_downs_adjustments()
