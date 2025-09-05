"""Situational efficiency backtest for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from ingest.nfl.data_loader import load_games
from ingest.nfl.situational_data_loader import load_situational_data, merge_situational_into_games


def test_situational_efficiency_integration(years: List[int] = [2024]) -> Dict[str, Any]:
    """
    Test situational efficiency integration with comprehensive backtesting.
    
    Args:
        years: Years to test
        
    Returns:
        Dictionary with test results
    """
    print(f"📊 TESTING SITUATIONAL EFFICIENCY INTEGRATION")
    print("="*80)
    print(f"Testing situational efficiency integration for years {years}...")
    
    # Load games data
    games = load_games(years)
    print(f"Loaded {len(games)} games")
    
    # Load situational efficiency data
    situational_db = load_situational_data(years)
    print(f"Created situational efficiency database with {len(situational_db)} teams")
    
    # Merge situational efficiency data into games
    games_with_situational = merge_situational_into_games(games, situational_db)
    print(f"Merged situational efficiency data into {len(games_with_situational)} games")
    
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
            use_situational_adjustment=False
        ),
        'with_situational': EloConfig(
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
            use_situational_adjustment=True,
            situational_adjustment_weight=1.0
        )
    }
    
    print("\\nRunning backtests...")
    results = {}
    
    for config_name, config in configs.items():
        print(f"\\nTesting {config_name} configuration...")
        
        # Use appropriate games data
        games_to_use = games_with_situational if config_name == 'with_situational' else games
        
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
    situational = results['with_situational']
    
    improvement = ((baseline['brier_score'] - situational['brier_score']) / baseline['brier_score']) * 100
    
    print(f"\\n" + "="*80)
    print("SITUATIONAL EFFICIENCY INTEGRATION TEST RESULTS")
    print("="*80)
    print(f"Years Tested: {years}")
    print(f"Games Processed: {baseline['games_processed']}")
    
    print(f"\\n📊 PERFORMANCE COMPARISON:")
    print(f"Baseline:")
    print(f"  Brier Score: {baseline['brier_score']:.4f}")
    print(f"  Accuracy: {baseline['accuracy']:.3f}")
    print(f"  Log Loss: {baseline['log_loss']:.4f}")
    print(f"  ECE: {baseline['ece']:.4f}")
    
    print(f"\\nWith Situational Efficiency:")
    print(f"  Brier Score: {situational['brier_score']:.4f} ({improvement:+.2f}%)")
    print(f"  Accuracy: {situational['accuracy']:.3f}")
    print(f"  Log Loss: {situational['log_loss']:.4f}")
    print(f"  ECE: {situational['ece']:.4f}")
    
    print(f"\\n📈 IMPROVEMENT ANALYSIS:")
    print(f"Situational Efficiency Impact: {improvement:+.2f}%")
    
    # Determine recommendation
    if improvement > 0.1:
        recommendation = "✅ SIGNIFICANT IMPROVEMENT - ENABLE SITUATIONAL EFFICIENCY"
    elif improvement > 0.05:
        recommendation = "⚠️ MODERATE IMPROVEMENT - CONSIDER ENABLING"
    elif improvement > 0.0:
        recommendation = "📊 MINOR IMPROVEMENT - TECHNICALLY WORKING"
    else:
        recommendation = "❌ NO IMPROVEMENT - DISABLE SITUATIONAL EFFICIENCY"
    
    print(f"\\n🎯 RECOMMENDATION: {recommendation}")
    
    # Test different weights
    print(f"\\nTesting different situational efficiency weights...")
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
            use_situational_adjustment=True,
            situational_adjustment_weight=weight
        )
        
        result = run_backtest(games_with_situational, config)
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
    
    # Analyze situational efficiency data quality
    print(f"\\nSituational Efficiency Data Analysis:")
    print(f"Teams with data: {len(situational_db)}")
    print(f"Average situational efficiency: {situational_db['situational_efficiency'].mean():.3f}")
    print(f"Efficiency range: {situational_db['situational_efficiency'].min():.3f} to {situational_db['situational_efficiency'].max():.3f}")
    
    # Show top and bottom teams
    print(f"\\nTop 5 situational efficiency teams:")
    top_teams = situational_db.sort_values('situational_efficiency', ascending=False).head(5)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['situational_efficiency']:.3f} efficiency")
    
    print(f"\\nBottom 5 situational efficiency teams:")
    bottom_teams = situational_db.sort_values('situational_efficiency', ascending=True).head(5)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['situational_efficiency']:.3f} efficiency")
    
    # Compile comprehensive results
    test_results = {
        'years_tested': years,
        'games_processed': baseline['games_processed'],
        'configurations': results,
        'improvements': {
            'situational_efficiency_impact': improvement,
            'best_weight': best_weight,
            'best_improvement': best_improvement
        },
        'recommendations': {
            'overall': recommendation,
            'situational_efficiency': 'ENABLE' if improvement > 0.05 else 'DISABLE'
        },
        'data_quality': {
            'teams_with_data': len(situational_db),
            'avg_efficiency': situational_db['situational_efficiency'].mean(),
            'efficiency_range': {
                'min': situational_db['situational_efficiency'].min(),
                'max': situational_db['situational_efficiency'].max()
            }
        },
        'weight_optimization': weight_results,
        'top_teams': top_teams.index.tolist(),
        'bottom_teams': bottom_teams.index.tolist()
    }
    
    return test_results


def run_situational_efficiency_comparison(years: List[int] = [2024]) -> None:
    """
    Run comprehensive situational efficiency comparison.
    
    Args:
        years: Years to test
    """
    print(f"📊 SITUATIONAL EFFICIENCY COMPREHENSIVE COMPARISON")
    print("="*80)
    print(f"Running comprehensive situational efficiency comparison for years {years}...")
    
    # Run integration test
    results = test_situational_efficiency_integration(years)
    
    # Print summary
    print(f"\\n" + "="*80)
    print("SITUATIONAL EFFICIENCY INTEGRATION SUMMARY")
    print("="*80)
    print(f"Years Tested: {results['years_tested']}")
    print(f"Games Processed: {results['games_processed']}")
    print(f"Baseline Brier Score: {results['configurations']['baseline']['brier_score']:.4f}")
    print(f"Situational Brier Score: {results['configurations']['with_situational']['brier_score']:.4f}")
    print(f"Improvement: {results['improvements']['situational_efficiency_impact']:+.2f}%")
    print(f"Recommendation: {results['recommendations']['overall']}")
    print(f"Best Weight: {results['improvements']['best_weight']}")
    print(f"Best Improvement: {results['improvements']['best_improvement']:+.2f}%")
    
    # Data quality summary
    print(f"\\nData Quality:")
    print(f"  Teams with data: {results['data_quality']['teams_with_data']}")
    print(f"  Average efficiency: {results['data_quality']['avg_efficiency']:.3f}")
    print(f"  Efficiency range: {results['data_quality']['efficiency_range']['min']:.3f} - {results['data_quality']['efficiency_range']['max']:.3f}")
    
    # Top teams
    print(f"\\nTop Situational Efficiency Teams: {', '.join(results['top_teams'])}")
    print(f"Bottom Situational Efficiency Teams: {', '.join(results['bottom_teams'])}")
    
    return results


if __name__ == "__main__":
    results = run_situational_efficiency_comparison()
