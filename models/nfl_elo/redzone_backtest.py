"""Red zone integration backtesting and validation."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

from models.nfl_elo.config import EloConfig
from models.nfl_elo.backtest import run_backtest
from ingest.nfl.data_loader import load_games
from ingest.nfl.redzone_data_loader import add_redzone_data_to_games


def test_redzone_integration(years: List[int] = [2019, 2021, 2022, 2023, 2024]) -> Dict[str, Any]:
    """
    Test red zone integration with comprehensive backtesting.
    
    Args:
        years: Years to test
        
    Returns:
        Dictionary with test results
    """
    print("🔴 TESTING RED ZONE INTEGRATION")
    print("="*80)
    print(f"Testing red zone integration for years {years}")
    
    # Load games data
    games = load_games(years)
    print(f"Loaded {len(games)} games")
    
    # Add red zone data
    games_with_redzone = add_redzone_data_to_games(games, years)
    print(f"Added red zone data to {len(games_with_redzone)} games")
    
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
            use_redzone_adjustment=False
        ),
        'with_redzone': EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=False,
            use_redzone_adjustment=True,
            redzone_adjustment_weight=1.0,
            redzone_max_delta=5.0
        ),
        'redzone_high_weight': EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=False,
            use_redzone_adjustment=True,
            redzone_adjustment_weight=2.0,
            redzone_max_delta=5.0
        ),
        'redzone_low_weight': EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=False,
            use_redzone_adjustment=True,
            redzone_adjustment_weight=0.5,
            redzone_max_delta=5.0
        )
    }
    
    # Run backtests
    results = {}
    print("\\nRunning backtests...")
    
    for config_name, config in configs.items():
        print(f"\\nTesting {config_name} configuration...")
        result = run_backtest(games_with_redzone, config)
        metrics = result['metrics']
        results[config_name] = {
            'brier_score': metrics['brier_score'],
            'log_loss': metrics['log_loss'],
            'accuracy': metrics['accuracy'],
            'ece': metrics['ece'],
            'sharpness': metrics['sharpness'],
            'games_processed': len(games_with_redzone)
        }
        print(f"  Brier Score: {metrics['brier_score']:.4f}")
        print(f"  Accuracy: {metrics['accuracy']:.3f}")
        print(f"  Games: {len(games_with_redzone)}")
    
    # Calculate improvements
    baseline_brier = results['baseline']['brier_score']
    redzone_brier = results['with_redzone']['brier_score']
    redzone_high_brier = results['redzone_high_weight']['brier_score']
    redzone_low_brier = results['redzone_low_weight']['brier_score']
    
    improvements = {
        'redzone_1x': ((baseline_brier - redzone_brier) / baseline_brier) * 100,
        'redzone_2x': ((baseline_brier - redzone_high_brier) / baseline_brier) * 100,
        'redzone_0.5x': ((baseline_brier - redzone_low_brier) / baseline_brier) * 100
    }
    
    # Analyze red zone data quality
    redzone_analysis = analyze_redzone_data_quality(games_with_redzone)
    
    # Create summary
    summary = {
        'years_tested': years,
        'games_processed': len(games_with_redzone),
        'baseline_brier': baseline_brier,
        'redzone_brier': redzone_brier,
        'improvements': improvements,
        'redzone_analysis': redzone_analysis,
        'configurations': results
    }
    
    # Print results
    print(f"\\n" + "="*80)
    print("RED ZONE INTEGRATION TEST RESULTS")
    print("="*80)
    print(f"Baseline Brier Score: {baseline_brier:.4f}")
    print(f"With Red Zone (1x): {redzone_brier:.4f} ({improvements['redzone_1x']:+.2f}%)")
    print(f"With Red Zone (2x): {redzone_high_brier:.4f} ({improvements['redzone_2x']:+.2f}%)")
    print(f"With Red Zone (0.5x): {redzone_low_brier:.4f} ({improvements['redzone_0.5x']:+.2f}%)")
    
    # Determine best configuration
    best_config = min(results.keys(), key=lambda k: results[k]['brier_score'])
    best_improvement = improvements.get(f'redzone_{best_config.split("_")[-1]}x', 0.0)
    
    print(f"\\nBest Configuration: {best_config}")
    print(f"Best Improvement: {best_improvement:+.2f}%")
    
    if best_improvement > 0.1:
        print("✅ SIGNIFICANT IMPROVEMENT WITH RED ZONE!")
    elif best_improvement > 0.0:
        print("⚠️  MINOR IMPROVEMENT WITH RED ZONE")
    else:
        print("❌ NO IMPROVEMENT WITH RED ZONE")
    
    # Red zone data analysis
    print(f"\\nRed Zone Data Analysis:")
    print(f"  Teams with red zone data: {redzone_analysis['teams_with_data']}")
    print(f"  Average red zone impact: {redzone_analysis['avg_impact']:.3f}")
    print(f"  Red zone impact range: {redzone_analysis['impact_range'][0]:.3f} to {redzone_analysis['impact_range'][1]:.3f}")
    print(f"  Teams with positive impact: {redzone_analysis['positive_impact_teams']}")
    print(f"  Teams with negative impact: {redzone_analysis['negative_impact_teams']}")
    
    return summary


def analyze_redzone_data_quality(games: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze red zone data quality.
    
    Args:
        games: DataFrame with red zone data
        
    Returns:
        Dictionary with data quality metrics
    """
    # Get unique teams
    teams = set(games['home_team'].unique()) | set(games['away_team'].unique())
    
    # Calculate team red zone impact statistics
    team_impacts = {}
    for team in teams:
        home_games = games[games['home_team'] == team]
        away_games = games[games['away_team'] == team]
        
        home_impact = home_games['home_redzone_impact'].mean() if len(home_games) > 0 else 0.0
        away_impact = away_games['away_redzone_impact'].mean() if len(away_games) > 0 else 0.0
        
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


def test_redzone_weight_optimization(years: List[int] = [2019, 2021, 2022, 2023, 2024]) -> Dict[str, Any]:
    """
    Test different red zone weights to find optimal configuration.
    
    Args:
        years: Years to test
        
    Returns:
        Dictionary with weight optimization results
    """
    print("🔴 TESTING RED ZONE WEIGHT OPTIMIZATION")
    print("="*80)
    print(f"Testing red zone weight optimization for years {years}")
    
    # Load games data
    games = load_games(years)
    games_with_redzone = add_redzone_data_to_games(games, years)
    
    # Test different weights
    weights = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
    results = []
    
    print("\\nTesting different red zone weights...")
    
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
            use_redzone_adjustment=True,
            redzone_adjustment_weight=weight,
            redzone_max_delta=5.0
        )
        
        result = run_backtest(games_with_redzone, config)
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
    # Test red zone integration
    integration_results = test_redzone_integration()
    
    # Test weight optimization
    weight_results = test_redzone_weight_optimization()
    
    print("\\n" + "="*80)
    print("RED ZONE INTEGRATION TESTING COMPLETE!")
    print("="*80)
