"""Clock management backtest for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from ingest.nfl.data_loader import load_games
from ingest.nfl.clock_management_data_loader import load_clock_management_data, merge_clock_management_into_games


def test_clock_management_integration(years: List[int] = [2024]) -> Dict[str, Any]:
    """
    Test clock management integration with comprehensive backtesting.
    
    Args:
        years: Years to test
        
    Returns:
        Dictionary with test results
    """
    print(f"📊 TESTING CLOCK MANAGEMENT INTEGRATION")
    print("="*80)
    print(f"Testing clock management integration for years {years}...")
    
    # Load games data
    games = load_games(years)
    print(f"Loaded {len(games)} games")
    
    # Load clock management data
    clock_db = load_clock_management_data(years)
    print(f"Created clock management database with {len(clock_db)} teams")
    
    # Merge clock management data into games
    games_with_clock = merge_clock_management_into_games(games, clock_db)
    print(f"Merged clock management data into {len(games_with_clock)} games")
    
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
            use_clock_management_adjustment=False
        ),
        'with_clock_management': EloConfig(
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
            use_clock_management_adjustment=True,
            clock_management_adjustment_weight=1.0
        )
    }
    
    print("\\nRunning backtests...")
    results = {}
    
    for config_name, config in configs.items():
        print(f"\\nTesting {config_name} configuration...")
        
        # Use appropriate games data
        games_to_use = games_with_clock if config_name == 'with_clock_management' else games
        
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
        print(f"  Games Processed: {len(games_to_use)}")
    
    # Calculate improvement
    baseline_brier = results['baseline']['brier_score']
    clock_brier = results['with_clock_management']['brier_score']
    improvement = ((baseline_brier - clock_brier) / baseline_brier) * 100
    
    print(f"\\n" + "="*80)
    print("CLOCK MANAGEMENT INTEGRATION TEST RESULTS")
    print("="*80)
    print(f"Baseline Brier Score: {baseline_brier:.4f}")
    print(f"With Clock Management Brier Score: {clock_brier:.4f}")
    print(f"Improvement: {improvement:+.2f}%")
    
    if improvement > 0.1:
        print("✅ SIGNIFICANT IMPROVEMENT WITH CLOCK MANAGEMENT!")
        recommendation = "ENABLE"
    elif improvement > 0.0:
        print("⚠️  MINOR IMPROVEMENT WITH CLOCK MANAGEMENT")
        recommendation = "CONSIDER"
    else:
        print("❌ NO IMPROVEMENT WITH CLOCK MANAGEMENT")
        recommendation = "DISABLE"
    
    # Analyze clock management data quality
    print(f"\\nClock Management Data Analysis:")
    print(f"Teams with clock management data: {len(clock_db)}")
    print(f"Average clock management efficiency: {clock_db['clock_management_efficiency'].mean():.3f}")
    print(f"Clock management range: {clock_db['clock_management_efficiency'].min():.3f} to {clock_db['clock_management_efficiency'].max():.3f}")
    
    # Show top and bottom teams
    print(f"\\nTop 5 clock management teams:")
    top_teams = clock_db.sort_values('clock_management_efficiency', ascending=False).head(5)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['clock_management_efficiency']:.3f} efficiency")
    
    print(f"\\nBottom 5 clock management teams:")
    bottom_teams = clock_db.sort_values('clock_management_efficiency', ascending=True).head(5)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['clock_management_efficiency']:.3f} efficiency")
    
    # Test different weights
    print(f"\\nTesting different clock management weights...")
    weight_results = {}
    
    for weight in [0.5, 1.0, 1.5, 2.0]:
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
            use_clock_management_adjustment=True,
            clock_management_adjustment_weight=weight
        )
        
        result = run_backtest(games_with_clock, config)
        metrics = result['metrics']
        weight_results[weight] = {
            'brier_score': metrics['brier_score'],
            'accuracy': metrics['accuracy']
        }
        print(f"  Weight {weight}: Brier Score {metrics['brier_score']:.4f}, Accuracy {metrics['accuracy']:.3f}")
    
    # Find best weight
    best_weight = min(weight_results.keys(), key=lambda w: weight_results[w]['brier_score'])
    best_brier = weight_results[best_weight]['brier_score']
    best_improvement = ((baseline_brier - best_brier) / baseline_brier) * 100
    
    print(f"\\nBest weight: {best_weight} (Brier Score: {best_brier:.4f}, Improvement: {best_improvement:+.2f}%)")
    
    # Compile results
    test_results = {
        'years_tested': years,
        'games_processed': results['baseline']['games_processed'],
        'baseline_brier_score': baseline_brier,
        'clock_management_brier_score': clock_brier,
        'improvement_percent': improvement,
        'recommendation': recommendation,
        'clock_management_data_quality': {
            'teams_with_data': len(clock_db),
            'avg_efficiency': clock_db['clock_management_efficiency'].mean(),
            'efficiency_range': {
                'min': clock_db['clock_management_efficiency'].min(),
                'max': clock_db['clock_management_efficiency'].max()
            }
        },
        'weight_optimization': {
            'best_weight': best_weight,
            'best_brier_score': best_brier,
            'best_improvement_percent': best_improvement,
            'all_weights': weight_results
        },
        'top_teams': top_teams.index.tolist(),
        'bottom_teams': bottom_teams.index.tolist()
    }
    
    return test_results


def run_clock_management_comparison(years: List[int] = [2024]) -> None:
    """
    Run comprehensive clock management comparison.
    
    Args:
        years: Years to test
    """
    print(f"📊 CLOCK MANAGEMENT COMPREHENSIVE COMPARISON")
    print("="*80)
    print(f"Running comprehensive clock management comparison for years {years}...")
    
    # Run integration test
    results = test_clock_management_integration(years)
    
    # Print summary
    print(f"\\n" + "="*80)
    print("CLOCK MANAGEMENT INTEGRATION SUMMARY")
    print("="*80)
    print(f"Years Tested: {results['years_tested']}")
    print(f"Games Processed: {results['games_processed']}")
    print(f"Baseline Brier Score: {results['baseline_brier_score']:.4f}")
    print(f"Clock Management Brier Score: {results['clock_management_brier_score']:.4f}")
    print(f"Improvement: {results['improvement_percent']:+.2f}%")
    print(f"Recommendation: {results['recommendation']}")
    print(f"Best Weight: {results['weight_optimization']['best_weight']}")
    print(f"Best Improvement: {results['weight_optimization']['best_improvement_percent']:+.2f}%")
    
    # Data quality summary
    print(f"\\nData Quality:")
    print(f"  Teams with data: {results['clock_management_data_quality']['teams_with_data']}")
    print(f"  Average efficiency: {results['clock_management_data_quality']['avg_efficiency']:.3f}")
    print(f"  Efficiency range: {results['clock_management_data_quality']['efficiency_range']['min']:.3f} - {results['clock_management_data_quality']['efficiency_range']['max']:.3f}")
    
    # Top teams
    print(f"\\nTop Clock Management Teams: {', '.join(results['top_teams'])}")
    print(f"Bottom Clock Management Teams: {', '.join(results['bottom_teams'])}")
    
    return results


if __name__ == "__main__":
    results = run_clock_management_comparison()
