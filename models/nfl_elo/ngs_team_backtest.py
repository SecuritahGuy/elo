"""NGS team performance backtest for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from ingest.nfl.data_loader import load_games
from ingest.nfl.ngs_team_performance_calculator import NGSTeamPerformanceCalculator


def test_ngs_team_performance_integration(years: List[int] = [2024]) -> Dict[str, Any]:
    """
    Test NGS team performance integration with comprehensive backtesting.
    
    Args:
        years: Years to test
        
    Returns:
        Dictionary with test results
    """
    print(f"📊 TESTING NGS TEAM PERFORMANCE INTEGRATION")
    print("="*80)
    print(f"Testing NGS team performance integration for years {years}...")
    
    # Load games data
    games = load_games(years)
    print(f"Loaded {len(games)} games")
    
    # Load NGS team performance data
    calculator = NGSTeamPerformanceCalculator()
    ngs_db = calculator.create_ngs_team_database(years)
    print(f"Created NGS team database with {len(ngs_db)} teams")
    
    # Merge NGS team performance data into games
    games_with_ngs = merge_ngs_team_into_games(games, ngs_db)
    print(f"Merged NGS team performance data into {len(games_with_ngs)} games")
    
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
        'with_ngs_team': EloConfig(
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
            use_ngs_team_adjustment=True,
            ngs_team_adjustment_weight=1.0
        )
    }
    
    print("\\nRunning backtests...")
    results = {}
    
    for config_name, config in configs.items():
        print(f"\\nTesting {config_name} configuration...")
        
        # Use appropriate games data
        games_to_use = games_with_ngs if config_name == 'with_ngs_team' else games
        
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
    ngs_team = results['with_ngs_team']
    
    improvement = ((baseline['brier_score'] - ngs_team['brier_score']) / baseline['brier_score']) * 100
    
    print(f"\\n" + "="*80)
    print("NGS TEAM PERFORMANCE INTEGRATION TEST RESULTS")
    print("="*80)
    print(f"Years Tested: {years}")
    print(f"Games Processed: {baseline['games_processed']}")
    
    print(f"\\n📊 PERFORMANCE COMPARISON:")
    print(f"Baseline:")
    print(f"  Brier Score: {baseline['brier_score']:.4f}")
    print(f"  Accuracy: {baseline['accuracy']:.3f}")
    print(f"  Log Loss: {baseline['log_loss']:.4f}")
    print(f"  ECE: {baseline['ece']:.4f}")
    
    print(f"\\nWith NGS Team Performance:")
    print(f"  Brier Score: {ngs_team['brier_score']:.4f} ({improvement:+.2f}%)")
    print(f"  Accuracy: {ngs_team['accuracy']:.3f}")
    print(f"  Log Loss: {ngs_team['log_loss']:.4f}")
    print(f"  ECE: {ngs_team['ece']:.4f}")
    
    print(f"\\n📈 IMPROVEMENT ANALYSIS:")
    print(f"NGS Team Performance Impact: {improvement:+.2f}%")
    
    # Determine recommendation
    if improvement > 0.1:
        recommendation = "✅ SIGNIFICANT IMPROVEMENT - ENABLE NGS TEAM PERFORMANCE"
    elif improvement > 0.05:
        recommendation = "⚠️ MODERATE IMPROVEMENT - CONSIDER ENABLING"
    elif improvement > 0.0:
        recommendation = "📊 MINOR IMPROVEMENT - TECHNICALLY WORKING"
    else:
        recommendation = "❌ NO IMPROVEMENT - DISABLE NGS TEAM PERFORMANCE"
    
    print(f"\\n🎯 RECOMMENDATION: {recommendation}")
    
    # Test different weights
    print(f"\\nTesting different NGS team performance weights...")
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
            use_ngs_team_adjustment=True,
            ngs_team_adjustment_weight=weight
        )
        
        result = run_backtest(games_with_ngs, config)
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
    
    # Analyze NGS team performance data quality
    print(f"\\nNGS Team Performance Data Analysis:")
    print(f"Teams with data: {len(ngs_db)}")
    print(f"Average NGS performance: {ngs_db['ngs_performance_score'].mean():.3f}")
    print(f"Performance range: {ngs_db['ngs_performance_score'].min():.3f} to {ngs_db['ngs_performance_score'].max():.3f}")
    
    # Show top and bottom teams
    print(f"\\nTop 5 NGS team performance teams:")
    top_teams = ngs_db.sort_values('ngs_performance_score', ascending=False).head(5)
    for team, stats in top_teams.iterrows():
        print(f"  {team}: {stats['ngs_performance_score']:.3f} performance")
    
    print(f"\\nBottom 5 NGS team performance teams:")
    bottom_teams = ngs_db.sort_values('ngs_performance_score', ascending=True).head(5)
    for team, stats in bottom_teams.iterrows():
        print(f"  {team}: {stats['ngs_performance_score']:.3f} performance")
    
    # Compile comprehensive results
    test_results = {
        'years_tested': years,
        'games_processed': baseline['games_processed'],
        'configurations': results,
        'improvements': {
            'ngs_team_performance_impact': improvement,
            'best_weight': best_weight,
            'best_improvement': best_improvement
        },
        'recommendations': {
            'overall': recommendation,
            'ngs_team_performance': 'ENABLE' if improvement > 0.05 else 'DISABLE'
        },
        'data_quality': {
            'teams_with_data': len(ngs_db),
            'avg_performance': ngs_db['ngs_performance_score'].mean(),
            'performance_range': {
                'min': ngs_db['ngs_performance_score'].min(),
                'max': ngs_db['ngs_performance_score'].max()
            }
        },
        'weight_optimization': weight_results,
        'top_teams': top_teams.index.tolist(),
        'bottom_teams': bottom_teams.index.tolist()
    }
    
    return test_results


def merge_ngs_team_into_games(games: pd.DataFrame, ngs_db: pd.DataFrame) -> pd.DataFrame:
    """
    Merge NGS team performance data into games DataFrame.
    
    Args:
        games: Games DataFrame
        ngs_db: NGS team database
        
    Returns:
        Games DataFrame with NGS team performance impacts added
    """
    print("Merging NGS team performance data into games...")
    
    if ngs_db.empty:
        print("No NGS team performance data to merge")
        # Add empty columns
        games['home_ngs_team_impact'] = 0.0
        games['away_ngs_team_impact'] = 0.0
        return games
    
    # Create a copy to avoid modifying original
    games_with_ngs = games.copy()
    
    # Add NGS team performance impact columns
    games_with_ngs['home_ngs_team_impact'] = 0.0
    games_with_ngs['away_ngs_team_impact'] = 0.0
    
    # Map team names to NGS team performance impacts
    for idx, game in games_with_ngs.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get NGS team performance impacts
        if home_team in ngs_db.index:
            home_impact = ngs_db.loc[home_team, 'ngs_performance_score']
            games_with_ngs.at[idx, 'home_ngs_team_impact'] = home_impact
        
        if away_team in ngs_db.index:
            away_impact = ngs_db.loc[away_team, 'ngs_performance_score']
            games_with_ngs.at[idx, 'away_ngs_team_impact'] = away_impact
    
    print(f"Merged NGS team performance data into {len(games_with_ngs)} games")
    return games_with_ngs


def run_ngs_team_performance_comparison(years: List[int] = [2024]) -> None:
    """
    Run comprehensive NGS team performance comparison.
    
    Args:
        years: Years to test
    """
    print(f"📊 NGS TEAM PERFORMANCE COMPREHENSIVE COMPARISON")
    print("="*80)
    print(f"Running comprehensive NGS team performance comparison for years {years}...")
    
    # Run integration test
    results = test_ngs_team_performance_integration(years)
    
    # Print summary
    print(f"\\n" + "="*80)
    print("NGS TEAM PERFORMANCE INTEGRATION SUMMARY")
    print("="*80)
    print(f"Years Tested: {results['years_tested']}")
    print(f"Games Processed: {results['games_processed']}")
    print(f"Baseline Brier Score: {results['configurations']['baseline']['brier_score']:.4f}")
    print(f"NGS Team Brier Score: {results['configurations']['with_ngs_team']['brier_score']:.4f}")
    print(f"Improvement: {results['improvements']['ngs_team_performance_impact']:+.2f}%")
    print(f"Recommendation: {results['recommendations']['overall']}")
    print(f"Best Weight: {results['improvements']['best_weight']}")
    print(f"Best Improvement: {results['improvements']['best_improvement']:+.2f}%")
    
    # Data quality summary
    print(f"\\nData Quality:")
    print(f"  Teams with data: {results['data_quality']['teams_with_data']}")
    print(f"  Average performance: {results['data_quality']['avg_performance']:.3f}")
    print(f"  Performance range: {results['data_quality']['performance_range']['min']:.3f} - {results['data_quality']['performance_range']['max']:.3f}")
    
    # Top teams
    print(f"\\nTop NGS Team Performance Teams: {', '.join(results['top_teams'])}")
    print(f"Bottom NGS Team Performance Teams: {', '.join(results['bottom_teams'])}")
    
    return results


if __name__ == "__main__":
    results = run_ngs_team_performance_comparison()
