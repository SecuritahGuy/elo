"""Turnover adjustments backtest for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from ingest.nfl.data_loader import load_games
from ingest.nfl.turnover_calculator import TurnoverCalculator
from .turnover_adjustments import calculate_team_turnover_adjustments


def test_turnover_integration(years: List[int] = [2024]) -> Dict[str, Any]:
    """
    Test turnover integration with comprehensive backtesting.
    
    Args:
        years: Years to test
        
    Returns:
        Dictionary with test results
    """
    print(f"📊 TESTING TURNOVER INTEGRATION")
    print("="*80)
    print(f"Testing turnover integration for years {years}...")
    
    # Load games data
    games = load_games(years)
    print(f"Loaded {len(games)} games")
    
    # Load turnover data
    calculator = TurnoverCalculator()
    turnover_db = calculator.create_turnover_database(years)
    print(f"Created turnover database with {len(turnover_db)} teams")
    
    # Merge turnover data into games
    games_with_turnover = merge_turnover_into_games(games, turnover_db)
    print(f"Merged turnover data into {len(games_with_turnover)} games")
    
    # Test configurations
    configs = {
        'baseline': EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=False,
            use_redzone_adjustment=False,
            use_downs_adjustment=False,
            use_clock_management_adjustment=False,
            use_situational_adjustment=False,
            use_turnover_adjustment=False
        ),
        'with_turnover': EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=False,
            use_redzone_adjustment=False,
            use_downs_adjustment=False,
            use_clock_management_adjustment=False,
            use_situational_adjustment=False,
            use_turnover_adjustment=True,
            turnover_adjustment_weight=1.0
        )
    }
    
    print("\\nRunning backtests...")
    results = {}
    
    for config_name, config in configs.items():
        print(f"\\nTesting {config_name} configuration...")
        
        # Use appropriate games data
        games_to_use = games_with_turnover if config_name == 'with_turnover' else games
        
        result = run_backtest(games_to_use, config)
        metrics = result['metrics']
        results[config_name] = {
            'brier_score': metrics['brier_score'],
            'log_loss': metrics['log_loss'],
            'accuracy': metrics['accuracy'],
            'ece': metrics['ece'],
            'sharpness': metrics['sharpness'],
            'games_processed': len(games_to_use)
        }
        print(f"  Brier Score: {metrics['brier_score']:.4f}")
        print(f"  Accuracy: {metrics['accuracy']:.3f}")
        print(f"  Log Loss: {metrics['log_loss']:.4f}")
        print(f"  ECE: {metrics['ece']:.4f}")
    
    # Calculate improvement
    baseline = results['baseline']
    turnover = results['with_turnover']
    
    improvement = ((baseline['brier_score'] - turnover['brier_score']) / baseline['brier_score']) * 100
    
    print(f"\\n" + "="*80)
    print("TURNOVER INTEGRATION TEST RESULTS")
    print("="*80)
    print(f"Years Tested: {years}")
    print(f"Games Processed: {baseline['games_processed']}")
    
    print(f"\\n📊 PERFORMANCE COMPARISON:")
    print(f"Baseline:")
    print(f"  Brier Score: {baseline['brier_score']:.4f}")
    print(f"  Accuracy: {baseline['accuracy']:.3f}")
    print(f"  Log Loss: {baseline['log_loss']:.4f}")
    print(f"  ECE: {baseline['ece']:.4f}")
    
    print(f"\\nWith Turnover Adjustments:")
    print(f"  Brier Score: {turnover['brier_score']:.4f} ({improvement:+.2f}%)")
    print(f"  Accuracy: {turnover['accuracy']:.3f}")
    print(f"  Log Loss: {turnover['log_loss']:.4f}")
    print(f"  ECE: {turnover['ece']:.4f}")
    
    print(f"\\n📈 IMPROVEMENT ANALYSIS:")
    print(f"Turnover Impact: {improvement:+.2f}%")
    
    # Determine recommendation
    if improvement > 0.1:
        recommendation = "✅ SIGNIFICANT IMPROVEMENT - ENABLE TURNOVER ADJUSTMENTS"
    elif improvement > 0.05:
        recommendation = "⚠️ MODERATE IMPROVEMENT - CONSIDER ENABLING"
    elif improvement > 0.0:
        recommendation = "📊 MINOR IMPROVEMENT - TECHNICALLY WORKING"
    else:
        recommendation = "❌ NO IMPROVEMENT - DISABLE TURNOVER ADJUSTMENTS"
    
    print(f"\\n🎯 RECOMMENDATION: {recommendation}")
    
    # Test different weights
    print(f"\\nTesting different turnover weights...")
    weight_results = {}
    
    for weight in [0.5, 1.0, 1.5, 2.0, 3.0]:
        config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=False,
            use_redzone_adjustment=False,
            use_downs_adjustment=False,
            use_clock_management_adjustment=False,
            use_situational_adjustment=False,
            use_turnover_adjustment=True,
            turnover_adjustment_weight=weight
        )
        
        result = run_backtest(games_with_turnover, config)
        metrics = result['metrics']
        weight_results[weight] = {
            'brier_score': metrics['brier_score'],
            'accuracy': metrics['accuracy']
        }
        print(f"  Weight {weight}: Brier Score {metrics['brier_score']:.4f}, Accuracy {metrics['accuracy']:.3f}")
    
    # Find best weight
    best_weight = min(weight_results.keys(), key=lambda w: weight_results[w]['brier_score'])
    best_brier = weight_results[best_weight]['brier_score']
    best_improvement = ((baseline['brier_score'] - best_brier) / baseline['brier_score']) * 100
    
    print(f"\\nBest weight: {best_weight} (Brier Score: {best_brier:.4f}, Improvement: {best_improvement:+.2f}%)")
    
    # Analyze turnover data quality
    print(f"\\nTurnover Data Analysis:")
    print(f"Teams with data: {len(turnover_db)}")
    print(f"Average turnover score: {turnover_db['turnover_score'].mean():.3f}")
    print(f"Score range: {turnover_db['turnover_score'].min():.3f} to {turnover_db['turnover_score'].max():.3f}")
    
    # Show top and bottom teams
    print(f"\\nTop 5 turnover teams:")
    top_teams = turnover_db.sort_values('turnover_score', ascending=False).head(5)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['turnover_score']:.3f} score (diff: {stats['turnover_differential']:.1f})")
    
    print(f"\\nBottom 5 turnover teams:")
    bottom_teams = turnover_db.sort_values('turnover_score', ascending=True).head(5)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['turnover_score']:.3f} score (diff: {stats['turnover_differential']:.1f})")
    
    # Compile comprehensive results
    test_results = {
        'years_tested': years,
        'games_processed': baseline['games_processed'],
        'configurations': results,
        'improvements': {
            'turnover_impact': improvement,
            'best_weight': best_weight,
            'best_improvement': best_improvement
        },
        'recommendations': {
            'overall': recommendation,
            'turnover_adjustments': 'ENABLE' if improvement > 0.05 else 'DISABLE'
        },
        'data_quality': {
            'teams_with_data': len(turnover_db),
            'avg_turnover_score': turnover_db['turnover_score'].mean(),
            'score_range': {
                'min': turnover_db['turnover_score'].min(),
                'max': turnover_db['turnover_score'].max()
            }
        },
        'weight_optimization': weight_results,
        'top_teams': top_teams.index.tolist(),
        'bottom_teams': bottom_teams.index.tolist()
    }
    
    return test_results


def merge_turnover_into_games(games: pd.DataFrame, turnover_db: pd.DataFrame) -> pd.DataFrame:
    """
    Merge turnover data into games DataFrame.
    
    Args:
        games: Games DataFrame
        turnover_db: Turnover database
        
    Returns:
        Games DataFrame with turnover data added
    """
    print("Merging turnover data into games...")
    
    if turnover_db.empty:
        print("No turnover data to merge")
        # Add empty columns
        games['home_turnover_impact'] = 0.0
        games['away_turnover_impact'] = 0.0
        return games
    
    # Create a copy to avoid modifying original
    games_with_turnover = games.copy()
    
    # Add turnover impact columns
    games_with_turnover['home_turnover_impact'] = 0.0
    games_with_turnover['away_turnover_impact'] = 0.0
    
    # Map team names to turnover impacts
    for idx, game in games_with_turnover.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get turnover impacts
        if home_team in turnover_db.index:
            home_impact = turnover_db.loc[home_team, 'turnover_impact_normalized']
            games_with_turnover.at[idx, 'home_turnover_impact'] = home_impact
        
        if away_team in turnover_db.index:
            away_impact = turnover_db.loc[away_team, 'turnover_impact_normalized']
            games_with_turnover.at[idx, 'away_turnover_impact'] = away_impact
    
    print(f"Merged turnover data into {len(games_with_turnover)} games")
    return games_with_turnover


def run_turnover_comparison(years: List[int] = [2024]) -> None:
    """
    Run comprehensive turnover comparison.
    
    Args:
        years: Years to test
    """
    print(f"📊 TURNOVER COMPREHENSIVE COMPARISON")
    print("="*80)
    print(f"Running comprehensive turnover comparison for years {years}...")
    
    # Run integration test
    results = test_turnover_integration(years)
    
    # Print summary
    print(f"\\n" + "="*80)
    print("TURNOVER INTEGRATION SUMMARY")
    print("="*80)
    print(f"Years Tested: {results['years_tested']}")
    print(f"Games Processed: {results['games_processed']}")
    print(f"Baseline Brier Score: {results['configurations']['baseline']['brier_score']:.4f}")
    print(f"Turnover Brier Score: {results['configurations']['with_turnover']['brier_score']:.4f}")
    print(f"Improvement: {results['improvements']['turnover_impact']:+.2f}%")
    print(f"Recommendation: {results['recommendations']['overall']}")
    print(f"Best Weight: {results['improvements']['best_weight']}")
    print(f"Best Improvement: {results['improvements']['best_improvement']:+.2f}%")
    
    # Data quality summary
    print(f"\\nData Quality:")
    print(f"  Teams with data: {results['data_quality']['teams_with_data']}")
    print(f"  Average turnover score: {results['data_quality']['avg_turnover_score']:.3f}")
    print(f"  Score range: {results['data_quality']['score_range']['min']:.3f} - {results['data_quality']['score_range']['max']:.3f}")
    
    # Top teams
    print(f"\\nTop Turnover Teams: {', '.join(results['top_teams'])}")
    print(f"Bottom Turnover Teams: {', '.join(results['bottom_teams'])}")
    
    return results


if __name__ == "__main__":
    results = run_turnover_comparison()
