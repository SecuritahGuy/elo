"""Comprehensive system comparison for NFL Elo rating system."""

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


def run_comprehensive_system_comparison(years: List[int] = [2022, 2023, 2024]) -> Dict[str, Any]:
    """
    Run comprehensive comparison of the Elo system before and after recent integrations.
    
    Args:
        years: Years to test
        
    Returns:
        Dictionary with comprehensive comparison results
    """
    print(f"📊 COMPREHENSIVE SYSTEM COMPARISON")
    print("="*80)
    print(f"Comparing Elo system before and after recent integrations for years {years}...")
    
    # Load games data
    games = load_games(years)
    print(f"Loaded {len(games)} games")
    
    # Load clock management data
    clock_db = load_clock_management_data(years)
    print(f"Created clock management database with {len(clock_db)} teams")
    
    # Merge clock management data into games
    games_with_clock = merge_clock_management_into_games(games, clock_db)
    print(f"Merged clock management data into {len(games_with_clock)} games")
    
    # Define configurations to test
    configs = {
        'original_baseline': EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=False,
            use_qb_adjustment=False,
            use_injury_adjustment=False,
            use_redzone_adjustment=False,
            use_downs_adjustment=False,
            use_clock_management_adjustment=False
        ),
        'with_travel_qb': EloConfig(
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
        'with_all_features': EloConfig(
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
            clock_management_adjustment_weight=2.0  # Use best weight from testing
        )
    }
    
    print("\\nRunning comprehensive backtests...")
    results = {}
    
    for config_name, config in configs.items():
        print(f"\\nTesting {config_name} configuration...")
        
        # Use appropriate games data
        games_to_use = games_with_clock if config_name == 'with_all_features' else games
        
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
    
    # Calculate improvements
    baseline = results['original_baseline']
    travel_qb = results['with_travel_qb']
    all_features = results['with_all_features']
    
    travel_qb_improvement = ((baseline['brier_score'] - travel_qb['brier_score']) / baseline['brier_score']) * 100
    all_features_improvement = ((baseline['brier_score'] - all_features['brier_score']) / baseline['brier_score']) * 100
    clock_improvement = ((travel_qb['brier_score'] - all_features['brier_score']) / travel_qb['brier_score']) * 100
    
    print(f"\\n" + "="*80)
    print("COMPREHENSIVE SYSTEM COMPARISON RESULTS")
    print("="*80)
    print(f"Years Tested: {years}")
    print(f"Games Processed: {baseline['games_processed']}")
    
    print(f"\\n📊 PERFORMANCE COMPARISON:")
    print(f"Original Baseline:")
    print(f"  Brier Score: {baseline['brier_score']:.4f}")
    print(f"  Accuracy: {baseline['accuracy']:.3f}")
    print(f"  Log Loss: {baseline['log_loss']:.4f}")
    print(f"  ECE: {baseline['ece']:.4f}")
    
    print(f"\\nWith Travel + QB Adjustments:")
    print(f"  Brier Score: {travel_qb['brier_score']:.4f} ({travel_qb_improvement:+.2f}%)")
    print(f"  Accuracy: {travel_qb['accuracy']:.3f}")
    print(f"  Log Loss: {travel_qb['log_loss']:.4f}")
    print(f"  ECE: {travel_qb['ece']:.4f}")
    
    print(f"\\nWith All Features (including Clock Management):")
    print(f"  Brier Score: {all_features['brier_score']:.4f} ({all_features_improvement:+.2f}%)")
    print(f"  Accuracy: {all_features['accuracy']:.3f}")
    print(f"  Log Loss: {all_features['log_loss']:.4f}")
    print(f"  ECE: {all_features['ece']:.4f}")
    
    print(f"\\n📈 IMPROVEMENT ANALYSIS:")
    print(f"Travel + QB vs Baseline: {travel_qb_improvement:+.2f}%")
    print(f"All Features vs Baseline: {all_features_improvement:+.2f}%")
    print(f"Clock Management Impact: {clock_improvement:+.2f}%")
    
    # Determine overall recommendation
    if all_features_improvement > 0.5:
        overall_recommendation = "✅ SIGNIFICANT IMPROVEMENT - ENABLE ALL FEATURES"
    elif all_features_improvement > 0.1:
        overall_recommendation = "⚠️ MODERATE IMPROVEMENT - CONSIDER ENABLING"
    elif all_features_improvement > 0.0:
        overall_recommendation = "📊 MINOR IMPROVEMENT - TECHNICALLY WORKING"
    else:
        overall_recommendation = "❌ NO IMPROVEMENT - DISABLE FEATURES"
    
    print(f"\\n🎯 OVERALL RECOMMENDATION: {overall_recommendation}")
    
    # Feature-specific analysis
    print(f"\\n🔍 FEATURE-SPECIFIC ANALYSIS:")
    print(f"Travel + QB Adjustments: {travel_qb_improvement:+.2f}% improvement")
    if travel_qb_improvement > 0.1:
        print("  ✅ KEEP - Provides meaningful improvement")
    else:
        print("  ⚠️ CONSIDER - Minimal improvement")
    
    print(f"Clock Management: {clock_improvement:+.2f}% additional improvement")
    if clock_improvement > 0.05:
        print("  ✅ KEEP - Provides additional value")
    else:
        print("  ⚠️ CONSIDER - Minimal additional value")
    
    # Compile comprehensive results
    comparison_results = {
        'years_tested': years,
        'games_processed': baseline['games_processed'],
        'configurations': results,
        'improvements': {
            'travel_qb_vs_baseline': travel_qb_improvement,
            'all_features_vs_baseline': all_features_improvement,
            'clock_management_impact': clock_improvement
        },
        'recommendations': {
            'overall': overall_recommendation,
            'travel_qb': 'KEEP' if travel_qb_improvement > 0.1 else 'CONSIDER',
            'clock_management': 'KEEP' if clock_improvement > 0.05 else 'CONSIDER'
        },
        'performance_summary': {
            'best_brier_score': min(config['brier_score'] for config in results.values()),
            'best_accuracy': max(config['accuracy'] for config in results.values()),
            'best_config': min(results.keys(), key=lambda k: results[k]['brier_score'])
        }
    }
    
    return comparison_results


def print_detailed_comparison_table(results: Dict[str, Any]) -> None:
    """Print a detailed comparison table."""
    print(f"\\n" + "="*80)
    print("DETAILED COMPARISON TABLE")
    print("="*80)
    
    configs = results['configurations']
    
    # Create comparison table
    table_data = []
    for config_name, metrics in configs.items():
        table_data.append({
            'Configuration': config_name.replace('_', ' ').title(),
            'Brier Score': f"{metrics['brier_score']:.4f}",
            'Accuracy': f"{metrics['accuracy']:.3f}",
            'Log Loss': f"{metrics['log_loss']:.4f}",
            'ECE': f"{metrics['ece']:.4f}",
            'Games': metrics['games_processed']
        })
    
    # Print table
    df = pd.DataFrame(table_data)
    print(df.to_string(index=False))
    
    # Print improvement summary
    print(f"\\n📊 IMPROVEMENT SUMMARY:")
    improvements = results['improvements']
    print(f"Travel + QB vs Baseline: {improvements['travel_qb_vs_baseline']:+.2f}%")
    print(f"All Features vs Baseline: {improvements['all_features_vs_baseline']:+.2f}%")
    print(f"Clock Management Impact: {improvements['clock_management_impact']:+.2f}%")
    
    # Print recommendations
    print(f"\\n🎯 RECOMMENDATIONS:")
    recommendations = results['recommendations']
    print(f"Overall: {recommendations['overall']}")
    print(f"Travel + QB: {recommendations['travel_qb']}")
    print(f"Clock Management: {recommendations['clock_management']}")


if __name__ == "__main__":
    # Run comprehensive comparison
    results = run_comprehensive_system_comparison()
    
    # Print detailed comparison
    print_detailed_comparison_table(results)
    
    print(f"\\n" + "="*80)
    print("COMPREHENSIVE SYSTEM COMPARISON COMPLETE!")
    print("="*80)
