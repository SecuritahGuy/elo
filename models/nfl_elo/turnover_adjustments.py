"""Turnover adjustments for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig


def calculate_turnover_delta(turnover_impact: float, cfg: EloConfig) -> float:
    """
    Calculate Elo rating delta based on turnover impact.
    
    Args:
        turnover_impact: Team's turnover impact score (0-1 scale)
        cfg: Elo configuration
        
    Returns:
        Rating delta to apply
    """
    if not cfg.use_turnover_adjustment:
        return 0.0
    
    # Skip if impact is below threshold
    if turnover_impact < cfg.turnover_impact_threshold:
        return 0.0
    
    # Calculate base adjustment
    # Convert 0-1 scale to -1 to +1 scale (centered around 0.5)
    normalized_impact = (turnover_impact - 0.5) * 2.0
    
    # Apply weight
    adjustment = normalized_impact * cfg.turnover_adjustment_weight
    
    # Cap the adjustment
    adjustment = max(-cfg.turnover_max_delta, min(cfg.turnover_max_delta, adjustment))
    
    return adjustment


def calculate_team_turnover_adjustments(home_team: str, away_team: str, 
                                       turnover_db: pd.DataFrame, 
                                       cfg: EloConfig) -> Tuple[float, float]:
    """
    Calculate turnover adjustments for both teams.
    
    Args:
        home_team: Home team abbreviation
        away_team: Away team abbreviation
        turnover_db: Turnover database
        cfg: Elo configuration
        
    Returns:
        Tuple of (home_turnover_delta, away_turnover_delta)
    """
    if not cfg.use_turnover_adjustment:
        return 0.0, 0.0
    
    # Get team turnover impacts
    home_impact = turnover_db.get(home_team, {}).get('turnover_impact_normalized', 0.5)
    away_impact = turnover_db.get(away_team, {}).get('turnover_impact_normalized', 0.5)
    
    # Calculate deltas
    home_delta = calculate_turnover_delta(home_impact, cfg)
    away_delta = calculate_turnover_delta(away_impact, cfg)
    
    return home_delta, away_delta


def create_turnover_adjustment_summary(turnover_db: pd.DataFrame, cfg: EloConfig) -> Dict[str, Any]:
    """
    Create summary of turnover adjustments for all teams.
    
    Args:
        turnover_db: Turnover database
        cfg: Elo configuration
        
    Returns:
        Dictionary with adjustment summary
    """
    if not cfg.use_turnover_adjustment:
        return {
            'adjustments_enabled': False,
            'total_teams': 0,
            'adjustments': {}
        }
    
    adjustments = {}
    
    for team, stats in turnover_db.iterrows():
        impact = stats.get('turnover_impact_normalized', 0.5)
        delta = calculate_turnover_delta(impact, cfg)
        
        adjustments[team] = {
            'turnover_impact': impact,
            'turnover_differential': stats.get('turnover_differential', 0.0),
            'adjustment_delta': delta,
            'adjustment_applied': abs(delta) >= cfg.turnover_impact_threshold
        }
    
    # Calculate summary statistics
    deltas = [adj['adjustment_delta'] for adj in adjustments.values()]
    applied_count = sum(1 for adj in adjustments.values() if adj['adjustment_applied'])
    
    return {
        'adjustments_enabled': True,
        'total_teams': len(adjustments),
        'teams_with_adjustments': applied_count,
        'avg_adjustment': np.mean(deltas),
        'max_adjustment': max(deltas),
        'min_adjustment': min(deltas),
        'adjustments': adjustments
    }


def test_turnover_adjustments():
    """Test turnover adjustments functionality."""
    print("📊 TESTING TURNOVER ADJUSTMENTS")
    print("="*80)
    
    # Create test configuration
    cfg = EloConfig(
        use_turnover_adjustment=True,
        turnover_adjustment_weight=1.0,
        turnover_max_delta=6.0,
        turnover_impact_threshold=0.01
    )
    
    # Create test turnover database
    test_turnover_db = pd.DataFrame({
        'turnover_impact_normalized': [0.9, 0.1, 0.5, 0.7, 0.3],
        'turnover_differential': [26.0, -18.0, 0.0, 13.0, -10.0]
    }, index=['BUF', 'CLE', 'KC', 'LAC', 'TEN'])
    
    print("\\nTest turnover database:")
    print(test_turnover_db)
    
    # Test individual team adjustments
    print("\\nTesting individual team adjustments:")
    for team in ['BUF', 'CLE', 'KC', 'LAC', 'TEN']:
        impact = test_turnover_db.loc[team, 'turnover_impact_normalized']
        delta = calculate_turnover_delta(impact, cfg)
        print(f"  {team}: impact={impact:.3f}, delta={delta:.3f}")
    
    # Test team vs team adjustments
    print("\\nTesting team vs team adjustments:")
    home_delta, away_delta = calculate_team_turnover_adjustments('BUF', 'CLE', test_turnover_db, cfg)
    print(f"  BUF vs CLE: home_delta={home_delta:.3f}, away_delta={away_delta:.3f}")
    
    home_delta, away_delta = calculate_team_turnover_adjustments('KC', 'LAC', test_turnover_db, cfg)
    print(f"  KC vs LAC: home_delta={home_delta:.3f}, away_delta={away_delta:.3f}")
    
    # Test adjustment summary
    print("\\nTesting adjustment summary:")
    summary = create_turnover_adjustment_summary(test_turnover_db, cfg)
    print(f"  Adjustments enabled: {summary['adjustments_enabled']}")
    print(f"  Total teams: {summary['total_teams']}")
    print(f"  Teams with adjustments: {summary['teams_with_adjustments']}")
    print(f"  Average adjustment: {summary['avg_adjustment']:.3f}")
    print(f"  Max adjustment: {summary['max_adjustment']:.3f}")
    print(f"  Min adjustment: {summary['min_adjustment']:.3f}")
    
    return cfg, test_turnover_db


if __name__ == "__main__":
    cfg, turnover_db = test_turnover_adjustments()
