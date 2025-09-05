"""Red zone efficiency adjustments for NFL Elo ratings."""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from ingest.nfl.redzone_calculator import RedZoneCalculator


class RedZoneAdjustmentCalculator:
    """Calculates red zone efficiency adjustments for Elo ratings."""
    
    def __init__(self):
        """Initialize red zone adjustment calculator."""
        self.redzone_calc = RedZoneCalculator()
        self.redzone_db: Optional[pd.DataFrame] = None
        self.last_years: Optional[list] = None
    
    def load_redzone_data(self, years: list) -> None:
        """
        Load red zone data for specified years.
        
        Args:
            years: Years to load data for
        """
        if self.last_years != years or self.redzone_db is None:
            print(f"Loading red zone data for years {years}...")
            self.redzone_db = self.redzone_calc.create_redzone_database(years)
            self.last_years = years
            print(f"Red zone database loaded with {len(self.redzone_db)} teams")
    
    def calculate_redzone_adjustment(self, team: str, years: list) -> float:
        """
        Calculate red zone adjustment for a team.
        
        Args:
            team: Team abbreviation
            years: Years to analyze
            
        Returns:
            Red zone adjustment delta
        """
        # Load red zone data if needed
        self.load_redzone_data(years)
        
        if self.redzone_db is None or team not in self.redzone_db.index:
            return 0.0
        
        # Get team red zone rating
        team_rating = self.redzone_calc.get_team_redzone_rating(team, self.redzone_db)
        
        # Calculate adjustment based on red zone impact
        redzone_impact = team_rating['redzone_impact_score']
        
        # Apply adjustment (positive impact = positive adjustment)
        adjustment = redzone_impact * 10.0  # Scale factor
        
        return adjustment
    
    def calculate_redzone_adjustments(self, home_team: str, away_team: str, years: list) -> Tuple[float, float]:
        """
        Calculate red zone adjustments for both teams.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            years: Years to analyze
            
        Returns:
            Tuple of (home_adjustment, away_adjustment)
        """
        home_adj = self.calculate_redzone_adjustment(home_team, years)
        away_adj = self.calculate_redzone_adjustment(away_team, years)
        
        return home_adj, away_adj
    
    def get_team_redzone_stats(self, team: str, years: list) -> Dict[str, Any]:
        """
        Get comprehensive red zone stats for a team.
        
        Args:
            team: Team abbreviation
            years: Years to analyze
            
        Returns:
            Dictionary with team red zone statistics
        """
        # Load red zone data if needed
        self.load_redzone_data(years)
        
        if self.redzone_db is None or team not in self.redzone_db.index:
            return {
                'redzone_impact_score': 0.0,
                'redzone_advantage': 0.0,
                'off_redzone_td_rate': 0.135,  # League average
                'def_redzone_td_rate_allowed': 0.135,  # League average
                'net_redzone_efficiency': 0.0,
                'redzone_adjustment': 0.0
            }
        
        # Get team red zone rating
        team_rating = self.redzone_calc.get_team_redzone_rating(team, self.redzone_db)
        
        # Calculate adjustment
        adjustment = self.calculate_redzone_adjustment(team, years)
        
        # Add adjustment to stats
        team_rating['redzone_adjustment'] = adjustment
        
        return team_rating
    
    def analyze_redzone_impact(self, years: list) -> pd.DataFrame:
        """
        Analyze red zone impact across all teams.
        
        Args:
            years: Years to analyze
            
        Returns:
            DataFrame with red zone impact analysis
        """
        # Load red zone data if needed
        self.load_redzone_data(years)
        
        if self.redzone_db is None:
            return pd.DataFrame()
        
        # Calculate adjustments for all teams
        adjustments = []
        for team in self.redzone_db.index:
            team_stats = self.get_team_redzone_stats(team, years)
            adjustments.append({
                'team': team,
                'redzone_impact_score': team_stats['redzone_impact_score'],
                'redzone_advantage': team_stats['redzone_advantage'],
                'off_redzone_td_rate': team_stats['off_redzone_td_rate'],
                'def_redzone_td_rate_allowed': team_stats['def_redzone_td_rate_allowed'],
                'net_redzone_efficiency': team_stats['net_redzone_efficiency'],
                'redzone_adjustment': team_stats['redzone_adjustment']
            })
        
        return pd.DataFrame(adjustments)
    
    def get_redzone_summary(self, years: list) -> Dict[str, Any]:
        """
        Get summary statistics for red zone impact.
        
        Args:
            years: Years to analyze
            
        Returns:
            Dictionary with red zone summary statistics
        """
        # Load red zone data if needed
        self.load_redzone_data(years)
        
        if self.redzone_db is None:
            return {
                'total_teams': 0,
                'avg_redzone_impact': 0.0,
                'redzone_impact_range': (0.0, 0.0),
                'teams_with_positive_impact': 0,
                'teams_with_negative_impact': 0,
                'avg_adjustment': 0.0,
                'adjustment_range': (0.0, 0.0)
            }
        
        # Calculate summary statistics
        impact_scores = self.redzone_db['redzone_impact_score']
        adjustments = [self.calculate_redzone_adjustment(team, years) for team in self.redzone_db.index]
        
        return {
            'total_teams': len(self.redzone_db),
            'avg_redzone_impact': impact_scores.mean(),
            'redzone_impact_range': (impact_scores.min(), impact_scores.max()),
            'teams_with_positive_impact': (impact_scores > 0).sum(),
            'teams_with_negative_impact': (impact_scores < 0).sum(),
            'avg_adjustment': np.mean(adjustments),
            'adjustment_range': (min(adjustments), max(adjustments))
        }


def test_redzone_adjustments():
    """Test the red zone adjustment calculator."""
    print("🔴 TESTING RED ZONE ADJUSTMENT CALCULATOR")
    print("="*80)
    
    calc = RedZoneAdjustmentCalculator()
    
    # Test with 2024 data
    years = [2024]
    calc.load_redzone_data(years)
    
    # Test individual team adjustments
    print("\\nTesting individual team adjustments:")
    test_teams = ['KC', 'BAL', 'DAL', 'NE']
    for team in test_teams:
        stats = calc.get_team_redzone_stats(team, years)
        print(f"  {team}: {stats['redzone_adjustment']:.3f} adjustment, "
              f"{stats['redzone_impact_score']:.3f} impact")
    
    # Test team vs team adjustments
    print("\\nTesting team vs team adjustments:")
    home_adj, away_adj = calc.calculate_redzone_adjustments('KC', 'BAL', years)
    print(f"  KC (home) vs BAL (away): {home_adj:.3f} vs {away_adj:.3f}")
    
    # Analyze red zone impact
    print("\\nAnalyzing red zone impact:")
    analysis = calc.analyze_redzone_impact(years)
    print(f"  Teams analyzed: {len(analysis)}")
    print(f"  Average adjustment: {analysis['redzone_adjustment'].mean():.3f}")
    print(f"  Adjustment range: {analysis['redzone_adjustment'].min():.3f} to {analysis['redzone_adjustment'].max():.3f}")
    
    # Get summary
    summary = calc.get_redzone_summary(years)
    print(f"\\nRed zone summary:")
    print(f"  Total teams: {summary['total_teams']}")
    print(f"  Average impact: {summary['avg_redzone_impact']:.3f}")
    print(f"  Teams with positive impact: {summary['teams_with_positive_impact']}")
    print(f"  Teams with negative impact: {summary['teams_with_negative_impact']}")
    
    return calc


if __name__ == "__main__":
    calc = test_redzone_adjustments()
