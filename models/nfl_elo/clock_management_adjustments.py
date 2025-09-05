"""Clock management adjustments for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class ClockManagementAdjustments:
    """Calculates clock management adjustments for Elo ratings."""
    
    def __init__(self):
        """Initialize clock management adjustments."""
        pass
    
    def calculate_clock_management_delta(
        self, 
        team: str, 
        clock_management_impact: float,
        adjustment_weight: float = 1.0,
        max_delta: float = 4.0,
        impact_threshold: float = 0.01
    ) -> float:
        """
        Calculate Elo rating delta based on clock management impact.
        
        Args:
            team: Team abbreviation
            clock_management_impact: Clock management impact score (0-1)
            adjustment_weight: Weight for clock management adjustments
            max_delta: Maximum adjustment in points
            impact_threshold: Minimum impact to apply adjustment
            
        Returns:
            Elo rating delta
        """
        # Check if impact is significant enough
        if abs(clock_management_impact) < impact_threshold:
            return 0.0
        
        # Calculate base adjustment (clock management impact * weight)
        base_adjustment = clock_management_impact * adjustment_weight
        
        # Apply capping to prevent extreme adjustments
        capped_adjustment = max(-max_delta, min(max_delta, base_adjustment))
        
        return capped_adjustment
    
    def calculate_team_clock_management_advantage(
        self, 
        home_team: str, 
        away_team: str,
        clock_management_db: pd.DataFrame
    ) -> Tuple[float, float]:
        """
        Calculate clock management advantage for home and away teams.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            clock_management_db: Clock management database
            
        Returns:
            Tuple of (home_advantage, away_advantage)
        """
        # Get clock management ratings for both teams
        home_rating = self._get_team_clock_management_rating(home_team, clock_management_db)
        away_rating = self._get_team_clock_management_rating(away_team, clock_management_db)
        
        # Calculate advantage (positive = better clock management)
        home_advantage = home_rating - away_rating
        away_advantage = away_rating - home_rating
        
        return home_advantage, away_advantage
    
    def _get_team_clock_management_rating(self, team: str, clock_management_db: pd.DataFrame) -> float:
        """Get clock management rating for a team."""
        if team not in clock_management_db.index:
            return 0.5  # League average
        
        return clock_management_db.loc[team, 'clock_management_efficiency']
    
    def calculate_clock_management_adjustments(
        self,
        home_team: str,
        away_team: str,
        clock_management_db: pd.DataFrame,
        adjustment_weight: float = 1.0,
        max_delta: float = 4.0,
        impact_threshold: float = 0.01
    ) -> Tuple[float, float]:
        """
        Calculate clock management adjustments for both teams.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            clock_management_db: Clock management database
            adjustment_weight: Weight for clock management adjustments
            max_delta: Maximum adjustment in points
            impact_threshold: Minimum impact to apply adjustment
            
        Returns:
            Tuple of (home_adjustment, away_adjustment)
        """
        # Get clock management ratings
        home_rating = self._get_team_clock_management_rating(home_team, clock_management_db)
        away_rating = self._get_team_clock_management_rating(away_team, clock_management_db)
        
        # Calculate adjustments
        home_adjustment = self.calculate_clock_management_delta(
            home_team, home_rating, adjustment_weight, max_delta, impact_threshold
        )
        away_adjustment = self.calculate_clock_management_delta(
            away_team, away_rating, adjustment_weight, max_delta, impact_threshold
        )
        
        return home_adjustment, away_adjustment
    
    def analyze_clock_management_impact(
        self, 
        clock_management_db: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze clock management impact across teams.
        
        Args:
            clock_management_db: Clock management database
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            'total_teams': len(clock_management_db),
            'avg_clock_management_efficiency': clock_management_db['clock_management_efficiency'].mean(),
            'clock_management_range': {
                'min': clock_management_db['clock_management_efficiency'].min(),
                'max': clock_management_db['clock_management_efficiency'].max()
            },
            'top_5_teams': clock_management_db.nlargest(5, 'clock_management_efficiency').index.tolist(),
            'bottom_5_teams': clock_management_db.nsmallest(5, 'clock_management_efficiency').index.tolist(),
            'clock_management_std': clock_management_db['clock_management_efficiency'].std()
        }
        
        return analysis


def test_clock_management_adjustments():
    """Test clock management adjustments."""
    print("📊 TESTING CLOCK MANAGEMENT ADJUSTMENTS")
    print("="*80)
    
    # Create sample clock management database
    sample_data = {
        'KC': {'clock_management_efficiency': 0.365, 'clock_impact_score': 0.365},
        'BUF': {'clock_management_efficiency': 0.320, 'clock_impact_score': 0.320},
        'TB': {'clock_management_efficiency': 0.392, 'clock_impact_score': 0.392},
        'DET': {'clock_management_efficiency': 0.385, 'clock_impact_score': 0.385}
    }
    
    clock_db = pd.DataFrame(sample_data).T
    
    # Test adjustments
    adjustments = ClockManagementAdjustments()
    
    # Test individual team adjustment
    kc_adjustment = adjustments.calculate_clock_management_delta(
        'KC', 0.365, adjustment_weight=1.0, max_delta=4.0
    )
    print(f"KC clock management adjustment: {kc_adjustment:.3f}")
    
    # Test team vs team advantage
    home_adv, away_adv = adjustments.calculate_team_clock_management_advantage(
        'KC', 'BUF', clock_db
    )
    print(f"KC vs BUF advantage: KC {home_adv:.3f}, BUF {away_adv:.3f}")
    
    # Test full adjustments
    home_adj, away_adj = adjustments.calculate_clock_management_adjustments(
        'KC', 'BUF', clock_db, adjustment_weight=1.0, max_delta=4.0
    )
    print(f"KC vs BUF adjustments: KC {home_adj:.3f}, BUF {away_adj:.3f}")
    
    # Test analysis
    analysis = adjustments.analyze_clock_management_impact(clock_db)
    print(f"\\nClock management analysis: {analysis}")
    
    return adjustments


if __name__ == "__main__":
    adjustments = test_clock_management_adjustments()
