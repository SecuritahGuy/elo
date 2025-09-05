#!/usr/bin/env python3
"""
Comprehensive backtesting script to verify ELO accuracy with new parameters.
Tests both old (75% regression, 2020-2025) and new (30% regression, 2021-2025) configurations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path

from models.nfl_elo.prediction_interface import NFLPredictionInterface
from models.nfl_elo.config import EloConfig
from models.nfl_elo.backtest import run_backtest
from ingest.nfl.data_loader import load_games


def create_elo_configs() -> Dict[str, EloConfig]:
    """Create different ELO configurations for comparison."""
    
    # Old configuration (75% regression, 2020-2025)
    old_config = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.75,  # 75% carry-over
        use_travel_adjustment=True,
        use_qb_adjustment=True,
        start_season=2020,
        end_season=2025
    )
    
    # New configuration (30% regression, 2021-2025)
    new_config = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.30,  # 30% carry-over
        use_travel_adjustment=True,
        use_qb_adjustment=True,
        start_season=2021,
        end_season=2025
    )
    
    return {
        'old_75pct_2020': old_config,
        'new_30pct_2021': new_config
    }


def run_comprehensive_backtest(config_name: str, config: EloConfig, years: List[int]) -> Dict[str, Any]:
    """
    Run comprehensive backtest for a specific configuration.
    
    Args:
        config_name: Name of the configuration
        config: EloConfig object
        years: Years to process
        
    Returns:
        Dictionary with backtest results and metrics
    """
    print(f"\n🔄 Running backtest for {config_name}...")
    print(f"   Years: {years}")
    print(f"   Preseason regression: {config.preseason_regress*100:.0f}%")
    print(f"   Start season: {config.start_season}")
    
    try:
        # Load games data
        games = load_games(years)
        completed_games = games.dropna(subset=['home_score', 'away_score'])
        
        print(f"   Loaded {len(completed_games)} completed games")
        
        # Run backtest
        result = run_backtest(completed_games, config)
        
        # Extract key metrics
        metrics = result.get('metrics', {})
        
        # Calculate additional accuracy metrics
        game_results = result.get('game_results', [])
        if game_results:
            df_results = pd.DataFrame(game_results)
            
            # Calculate prediction accuracy
            correct_predictions = (df_results['predicted_winner'] == df_results['actual_winner']).sum()
            total_predictions = len(df_results)
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
            
            # Calculate Brier score (lower is better)
            brier_scores = []
            for _, game in df_results.iterrows():
                if game['actual_winner'] == 'home':
                    actual = 1.0
                else:
                    actual = 0.0
                predicted = game['home_win_prob']
                brier_score = (predicted - actual) ** 2
                brier_scores.append(brier_score)
            
            avg_brier_score = np.mean(brier_scores) if brier_scores else 1.0
            
            # Calculate log loss
            log_losses = []
            for _, game in df_results.iterrows():
                if game['actual_winner'] == 'home':
                    actual = 1.0
                else:
                    actual = 0.0
                predicted = max(min(game['home_win_prob'], 0.999), 0.001)  # Clip to avoid log(0)
                log_loss = -(actual * np.log(predicted) + (1 - actual) * np.log(1 - predicted))
                log_losses.append(log_loss)
            
            avg_log_loss = np.mean(log_losses) if log_losses else float('inf')
            
        else:
            accuracy = 0.0
            avg_brier_score = 1.0
            avg_log_loss = float('inf')
        
        # Get final team ratings
        final_ratings = result.get('final_ratings', {})
        
        return {
            'config_name': config_name,
            'config': config,
            'years_processed': years,
            'games_processed': len(completed_games),
            'accuracy': accuracy,
            'brier_score': avg_brier_score,
            'log_loss': avg_log_loss,
            'final_ratings': final_ratings,
            'backtest_metrics': metrics,
            'success': True
        }
        
    except Exception as e:
        print(f"   ❌ Error in backtest: {e}")
        return {
            'config_name': config_name,
            'config': config,
            'years_processed': years,
            'games_processed': 0,
            'accuracy': 0.0,
            'brier_score': 1.0,
            'log_loss': float('inf'),
            'final_ratings': {},
            'backtest_metrics': {},
            'success': False,
            'error': str(e)
        }


def compare_configurations() -> Dict[str, Any]:
    """Compare different ELO configurations."""
    
    print("🏈 ELO CONFIGURATION COMPARISON")
    print("="*80)
    
    # Create configurations
    configs = create_elo_configs()
    
    # Define year ranges
    old_years = [2020, 2021, 2022, 2023, 2024, 2025]
    new_years = [2021, 2022, 2023, 2024, 2025]
    
    # Run backtests
    results = {}
    
    # Test old configuration (75% regression, 2020-2025)
    results['old'] = run_comprehensive_backtest(
        'Old: 75% regression, 2020-2025', 
        configs['old_75pct_2020'], 
        old_years
    )
    
    # Test new configuration (30% regression, 2021-2025)
    results['new'] = run_comprehensive_backtest(
        'New: 30% regression, 2021-2025', 
        configs['new_30pct_2021'], 
        new_years
    )
    
    # Test new configuration on same years as old for fair comparison
    results['new_same_years'] = run_comprehensive_backtest(
        'New: 30% regression, 2020-2025', 
        configs['new_30pct_2021'], 
        old_years
    )
    
    return results


def analyze_results(results: Dict[str, Any]) -> None:
    """Analyze and display backtest results."""
    
    print(f"\n📊 BACKTEST RESULTS ANALYSIS")
    print("="*80)
    
    # Create comparison table
    print(f"\n{'Configuration':<30} {'Accuracy':<10} {'Brier Score':<12} {'Log Loss':<10} {'Games':<8}")
    print("-" * 80)
    
    for key, result in results.items():
        if result['success']:
            print(f"{result['config_name']:<30} "
                  f"{result['accuracy']:.3f}      "
                  f"{result['brier_score']:.3f}       "
                  f"{result['log_loss']:.3f}    "
                  f"{result['games_processed']:<8}")
        else:
            print(f"{result['config_name']:<30} FAILED - {result.get('error', 'Unknown error')}")
    
    # Detailed analysis
    print(f"\n🔍 DETAILED ANALYSIS")
    print("-" * 40)
    
    if 'old' in results and 'new' in results and results['old']['success'] and results['new']['success']:
        old_acc = results['old']['accuracy']
        new_acc = results['new']['accuracy']
        old_brier = results['old']['brier_score']
        new_brier = results['new']['brier_score']
        old_log = results['old']['log_loss']
        new_log = results['new']['log_loss']
        
        print(f"Accuracy comparison:")
        print(f"  Old (75% regression): {old_acc:.3f}")
        print(f"  New (30% regression): {new_acc:.3f}")
        print(f"  Difference: {new_acc - old_acc:+.3f}")
        
        print(f"\nBrier Score comparison (lower is better):")
        print(f"  Old (75% regression): {old_brier:.3f}")
        print(f"  New (30% regression): {new_brier:.3f}")
        print(f"  Difference: {new_brier - old_brier:+.3f}")
        
        print(f"\nLog Loss comparison (lower is better):")
        print(f"  Old (75% regression): {old_log:.3f}")
        print(f"  New (30% regression): {new_log:.3f}")
        print(f"  Difference: {new_log - old_log:+.3f}")
        
        # Determine if new config is better
        better_accuracy = new_acc > old_acc
        better_brier = new_brier < old_brier
        better_log = new_log < old_log
        
        print(f"\n🎯 CONCLUSION:")
        if better_accuracy and better_brier and better_log:
            print(f"  ✅ NEW CONFIGURATION IS BETTER across all metrics!")
        elif better_accuracy and (better_brier or better_log):
            print(f"  ✅ NEW CONFIGURATION IS BETTER overall!")
        elif better_accuracy:
            print(f"  ⚖️  NEW CONFIGURATION has better accuracy but mixed other metrics")
        elif better_brier and better_log:
            print(f"  ⚖️  NEW CONFIGURATION has better calibration but lower accuracy")
        else:
            print(f"  ❌ OLD CONFIGURATION appears better")
    
    # Show top teams for each configuration
    print(f"\n🏆 TOP 10 TEAMS BY RATING")
    print("-" * 40)
    
    for key, result in results.items():
        if result['success'] and result['final_ratings']:
            print(f"\n{result['config_name']}:")
            sorted_teams = sorted(result['final_ratings'].items(), key=lambda x: x[1], reverse=True)
            for i, (team, rating) in enumerate(sorted_teams[:10], 1):
                print(f"  {i:2d}. {team}: {rating:.1f}")


def test_philadelphia_win_impact() -> None:
    """Test how the Philadelphia win affects ratings in both configurations."""
    
    print(f"\n🏈 PHILADELPHIA WIN IMPACT ANALYSIS")
    print("="*50)
    
    # Load 2025 data
    games_2025 = load_games([2025])
    completed_2025 = games_2025.dropna(subset=['home_score', 'away_score'])
    
    if len(completed_2025) == 0:
        print("No completed 2025 games found")
        return
    
    # Find PHI vs DAL game
    phi_dal_game = completed_2025[
        ((completed_2025['home_team'] == 'PHI') & (completed_2025['away_team'] == 'DAL')) |
        ((completed_2025['home_team'] == 'DAL') & (completed_2025['away_team'] == 'PHI'))
    ]
    
    if len(phi_dal_game) == 0:
        print("PHI vs DAL game not found")
        return
    
    game = phi_dal_game.iloc[0]
    print(f"Found game: {game['home_team']} vs {game['away_team']} ({game['home_score']}-{game['away_score']})")
    
    # Test both configurations
    configs = create_elo_configs()
    
    for config_name, config in configs.items():
        print(f"\n{config_name}:")
        
        # Run backtest up to this game
        games_before = load_games([2021, 2022, 2023, 2024])
        all_games = pd.concat([games_before, phi_dal_game], ignore_index=True)
        
        try:
            result = run_backtest(all_games, config)
            final_ratings = result.get('final_ratings', {})
            
            phi_rating = final_ratings.get('PHI', 1500)
            dal_rating = final_ratings.get('DAL', 1500)
            
            print(f"  PHI rating: {phi_rating:.1f}")
            print(f"  DAL rating: {dal_rating:.1f}")
            print(f"  PHI advantage: {phi_rating - dal_rating:.1f} points")
            
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    print("🏈 COMPREHENSIVE ELO BACKTESTING")
    print("="*80)
    print("Testing new configuration: 30% regression, 2021-2025")
    print("vs old configuration: 75% regression, 2020-2025")
    print("="*80)
    
    # Run comprehensive comparison
    results = compare_configurations()
    
    # Analyze results
    analyze_results(results)
    
    # Test Philadelphia win impact
    test_philadelphia_win_impact()
    
    print(f"\n🎉 Backtesting completed!")
    print(f"Check the results above to determine if the new configuration improves accuracy.")
