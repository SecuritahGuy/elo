"""Down efficiency integration backtesting and validation."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

from models.nfl_elo.config import EloConfig
from models.nfl_elo.backtest import run_backtest
from ingest.nfl.data_loader import load_games
from ingest.nfl.downs_data_loader import add_downs_data_to_games


def test_downs_integration(years: List[int] = [2019, 2021, 2022, 2023, 2024]) -> Dict[str, Any]:
    """
    Test down efficiency integration with comprehensive backtesting.
    
    Args:
        years: Years to test
        
    Returns:
        Dictionary with test results
    """
    print("📊 TESTING DOWN EFFICIENCY INTEGRATION")
    print("="*80)
    print(f"Testing down efficiency integration for years {years}")
    
    # Load games data
    games = load_games(years)
    print(f"Loaded {len(games)} games")
    
    # Add down efficiency data
    games_with_downs = add_downs_data_to_games(games, years)
    print(f"Added down efficiency data to {len(games_with_downs)} games")
    
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
            use_downs_adjustment=False
        ),
        'with_downs': EloConfig(
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
            use_downs_adjustment=True,
            downs_adjustment_weight=1.0,
            downs_max_delta=3.0
        ),
        'downs_high_weight': EloConfig(
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
            use_downs_adjustment=True,
            downs_adjustment_weight=2.0,
            downs_max_delta=3.0
        ),
        'downs_low_weight': EloConfig(
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
            use_downs_adjustment=True,
            downs_adjustment_weight=0.5,
            downs_max_delta=3.0
        )
    }
    
    # Run backtests
    results = {}
    print("\\nRunning backtests...")
    
    for config_name, config in configs.items():
        print(f"\\nTesting {config_name} configuration...")
        result = run_backtest(games_with_downs, config)
        metrics = result['metrics']
        results[config_name] = {
            'brier_score': metrics['brier_score'],
            'log_loss': metrics['log_loss'],
            'accuracy': metrics['accuracy'],
            'ece': metrics['ece'],
            'sharpness': metrics['sharpness'],
            'games_processed': len(games_with_downs)
        }
        print(f"  Brier Score: {metrics['brier_score']:.4f}")
        print(f"  Accuracy: {metrics['accuracy']:.3f}")
        print(f"  Games: {len(games_with_downs)}")
    
    # Calculate improvements
    baseline_brier = results['baseline']['brier_score']
    downs_brier = results['with_downs']['brier_score']
    downs_high_brier = results['downs_high_weight']['brier_score']
    downs_low_brier = results['downs_low_weight']['brier_score']
    
    improvements = {
        'downs_1x': ((baseline_brier - downs_brier) / baseline_brier) * 100,
        'downs_2x': ((baseline_brier - downs_high_brier) / baseline_brier) * 100,
        'downs_0.5x': ((baseline_brier - downs_low_brier) / baseline_brier) * 100
    }
    
    # Analyze down efficiency data quality
    downs_analysis = analyze_downs_data_quality(games_with_downs)
    
    # Create summary
    summary = {
        'years_tested': years,
        'games_processed': len(games_with_downs),
        'baseline_brier': baseline_brier,
        'downs_brier': downs_brier,
        'improvements': improvements,
        'downs_analysis': downs_analysis,
        'configurations': results
    }
    
    # Print results
    print(f"\\n" + "="*80)
    print("DOWN EFFICIENCY INTEGRATION TEST RESULTS")
    print("="*80)
    print(f"Baseline Brier Score: {baseline_brier:.4f}")
    print(f"With Down Efficiency (1x): {downs_brier:.4f} ({improvements['downs_1x']:+.2f}%)")
    print(f"With Down Efficiency (2x): {downs_high_brier:.4f} ({improvements['downs_2x']:+.2f}%)")
    print(f"With Down Efficiency (0.5x): {downs_low_brier:.4f} ({improvements['downs_0.5x']:+.2f}%)")
    
    # Determine best configuration
    best_config = min(results.keys(), key=lambda k: results[k]['brier_score'])
    best_improvement = improvements.get(f'downs_{best_config.split("_")[-1]}x', 0.0)
    
    print(f"\\nBest Configuration: {best_config}")
    print(f"Best Improvement: {best_improvement:+.2f}%")
    
    if best_improvement > 0.1:
        print("✅ SIGNIFICANT IMPROVEMENT WITH DOWN EFFICIENCY!")
    elif best_improvement > 0.0:
        print("⚠️  MINOR IMPROVEMENT WITH DOWN EFFICIENCY")
    else:
        print("❌ NO IMPROVEMENT WITH DOWN EFFICIENCY")
    
    # Down efficiency data analysis
    print(f"\\nDown Efficiency Data Analysis:")
    print(f"  Teams with down efficiency data: {downs_analysis['teams_with_data']}")
    print(f"  Average down efficiency impact: {downs_analysis['avg_impact']:.3f}")
    print(f"  Down efficiency impact range: {downs_analysis['impact_range'][0]:.3f} to {downs_analysis['impact_range'][1]:.3f}")
    print(f"  Teams with positive impact: {downs_analysis['positive_impact_teams']}")
    print(f"  Teams with negative impact: {downs_analysis['negative_impact_teams']}")
    
    return summary


def analyze_downs_data_quality(games: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze down efficiency data quality.
    
    Args:
        games: DataFrame with down efficiency data
        
    Returns:
        Dictionary with data quality metrics
    """
    # Get unique teams
    teams = set(games['home_team'].unique()) | set(games['away_team'].unique())
    
    # Calculate team down efficiency impact statistics
    team_impacts = {}
    for team in teams:
        home_games = games[games['home_team'] == team]
        away_games = games[games['away_team'] == team]
        
        home_impact = home_games['home_downs_impact'].mean() if len(home_games) > 0 else 0.0
        away_impact = away_games['away_downs_impact'].mean() if len(away_games) > 0 else 0.0
        
        team_impacts[team] = (home_impact + away_impact) / 2
    
    # Calculate statistics
    impacts = list(team_impacts.values())
    
    return {
        'teams_with_data': len(teams),
        'avg_impact': np.mean(impacts),
        'impact_range': (min(impacts), max(impacts)),
        'positive_impact_teams': sum(1 for imp in impacts if imp > 0),
        'negative_impact_teams': sum(1 for imp in impacts if imp < 0),
        'impact_std': np.std(impacts)
    }


def test_downs_weight_optimization(years: List[int] = [2019, 2021, 2022, 2023, 2024]) -> Dict[str, Any]:
    """
    Test different down efficiency weights to find optimal configuration.
    
    Args:
        years: Years to test
        
    Returns:
        Dictionary with weight optimization results
    """
    print("📊 TESTING DOWN EFFICIENCY WEIGHT OPTIMIZATION")
    print("="*80)
    print(f"Testing down efficiency weight optimization for years {years}")
    
    # Load games data
    games = load_games(years)
    games_with_downs = add_downs_data_to_games(games, years)
    
    # Test different weights
    weights = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
    results = []
    
    print("\\nTesting different down efficiency weights...")
    
    for weight in weights:
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
            use_downs_adjustment=True,
            downs_adjustment_weight=weight,
            downs_max_delta=3.0
        )
        
        result = run_backtest(games_with_downs, config)
        metrics = result['metrics']
        
        results.append({
            'weight': weight,
            'brier_score': metrics['brier_score'],
            'accuracy': metrics['accuracy'],
            'log_loss': metrics['log_loss']
        })
        
        print(f"  Weight {weight}: Brier {metrics['brier_score']:.4f}, Accuracy {metrics['accuracy']:.3f}")
    
    # Find best weight
    best_result = min(results, key=lambda x: x['brier_score'])
    
    print(f"\\nBest Weight: {best_result['weight']}")
    print(f"Best Brier Score: {best_result['brier_score']:.4f}")
    print(f"Best Accuracy: {best_result['accuracy']:.3f}")
    
    return {
        'weight_results': results,
        'best_weight': best_result['weight'],
        'best_brier_score': best_result['brier_score'],
        'best_accuracy': best_result['accuracy']
    }


if __name__ == "__main__":
    # Test down efficiency integration
    integration_results = test_downs_integration()
    
    # Test weight optimization
    weight_results = test_downs_weight_optimization()
    
    print("\\n" + "="*80)
    print("DOWN EFFICIENCY INTEGRATION TESTING COMPLETE!")
    print("="*80)
