#!/usr/bin/env python3
"""
Comprehensive ELO accuracy analysis across different configurations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from models.nfl_elo.prediction_interface import NFLPredictionInterface
from models.nfl_elo.config import EloConfig
from models.nfl_elo.backtest import run_backtest
from ingest.nfl.data_loader import load_games


def create_test_configurations() -> Dict[str, EloConfig]:
    """Create different ELO configurations for accuracy testing."""
    
    configs = {}
    
    # Current production config (30% regression, 2021+)
    configs['current_30pct'] = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.30,
        use_travel_adjustment=True,
        use_qb_adjustment=True,
        start_season=2021,
        end_season=2025
    )
    
    # Previous config (75% regression, 2020+)
    configs['old_75pct'] = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.75,
        use_travel_adjustment=True,
        use_qb_adjustment=True,
        start_season=2020,
        end_season=2025
    )
    
    # Conservative config (50% regression)
    configs['conservative_50pct'] = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.50,
        use_travel_adjustment=True,
        use_qb_adjustment=True,
        start_season=2021,
        end_season=2025
    )
    
    # High K-factor config (more reactive)
    configs['reactive_k30'] = EloConfig(
        base_rating=1500.0,
        k=30.0,  # Higher K-factor
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.30,
        use_travel_adjustment=True,
        use_qb_adjustment=True,
        start_season=2021,
        end_season=2025
    )
    
    # Low K-factor config (more stable)
    configs['stable_k10'] = EloConfig(
        base_rating=1500.0,
        k=10.0,  # Lower K-factor
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.30,
        use_travel_adjustment=True,
        use_qb_adjustment=True,
        start_season=2021,
        end_season=2025
    )
    
    # No MOV config
    configs['no_mov'] = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=False,  # No margin of victory
        preseason_regress=0.30,
        use_travel_adjustment=True,
        use_qb_adjustment=True,
        start_season=2021,
        end_season=2025
    )
    
    # No HFA config
    configs['no_hfa'] = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=0.0,  # No home field advantage
        mov_enabled=True,
        preseason_regress=0.30,
        use_travel_adjustment=True,
        use_qb_adjustment=True,
        start_season=2021,
        end_season=2025
    )
    
    return configs


def calculate_accuracy_metrics(games_df: pd.DataFrame, config: EloConfig) -> Dict[str, float]:
    """Calculate comprehensive accuracy metrics for a configuration."""
    
    try:
        # Run backtest
        result = run_backtest(games_df, config)
        game_results = result.get('game_results', [])
        
        if not game_results:
            return {'error': 'No game results found'}
        
        df_results = pd.DataFrame(game_results)
        
        # Basic accuracy metrics
        correct_predictions = 0
        total_predictions = 0
        confidence_scores = []
        brier_scores = []
        log_losses = []
        
        for _, game in df_results.iterrows():
            if pd.isna(game.get('home_win_prob')) or pd.isna(game.get('actual_winner')):
                continue
            
            # Get prediction and actual result
            home_win_prob = game['home_win_prob']
            actual_winner = game['actual_winner']
            
            # Determine predicted winner
            predicted_winner = 'home' if home_win_prob > 0.5 else 'away'
            
            # Calculate accuracy
            if predicted_winner == actual_winner:
                correct_predictions += 1
            total_predictions += 1
            
            # Calculate confidence (distance from 0.5)
            confidence = abs(home_win_prob - 0.5) * 2
            confidence_scores.append(confidence)
            
            # Calculate Brier score
            actual_binary = 1 if actual_winner == 'home' else 0
            brier_score = (home_win_prob - actual_binary) ** 2
            brier_scores.append(brier_score)
            
            # Calculate log loss
            if actual_winner == 'home':
                actual_prob = 1.0
            else:
                actual_prob = 0.0
            
            # Clip probabilities to avoid log(0)
            clipped_prob = max(min(home_win_prob, 0.999), 0.001)
            log_loss = -(actual_prob * np.log(clipped_prob) + (1 - actual_prob) * np.log(1 - clipped_prob))
            log_losses.append(log_loss)
        
        if total_predictions == 0:
            return {'error': 'No valid predictions found'}
        
        # Calculate final metrics
        accuracy = correct_predictions / total_predictions
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
        avg_brier_score = np.mean(brier_scores) if brier_scores else 1.0
        avg_log_loss = np.mean(log_losses) if log_losses else float('inf')
        
        # Calculate calibration metrics
        # Group predictions by confidence bins
        confidence_bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        calibration_errors = []
        
        for i in range(len(confidence_bins) - 1):
            bin_start = confidence_bins[i]
            bin_end = confidence_bins[i + 1]
            
            # Find games in this confidence bin
            bin_games = df_results[
                (df_results['home_win_prob'] >= bin_start) & 
                (df_results['home_win_prob'] < bin_end)
            ]
            
            if len(bin_games) > 0:
                # Calculate actual win rate in this bin
                actual_wins = (bin_games['actual_winner'] == 'home').sum()
                actual_win_rate = actual_wins / len(bin_games)
                
                # Calculate predicted win rate (average of predictions in bin)
                predicted_win_rate = bin_games['home_win_prob'].mean()
                
                # Calibration error is the difference
                calibration_error = abs(actual_win_rate - predicted_win_rate)
                calibration_errors.append(calibration_error)
        
        avg_calibration_error = np.mean(calibration_errors) if calibration_errors else 0
        
        return {
            'accuracy': accuracy,
            'total_predictions': total_predictions,
            'correct_predictions': correct_predictions,
            'avg_confidence': avg_confidence,
            'brier_score': avg_brier_score,
            'log_loss': avg_log_loss,
            'calibration_error': avg_calibration_error,
            'success': True
        }
        
    except Exception as e:
        return {'error': str(e), 'success': False}


def analyze_season_accuracy():
    """Analyze accuracy by season."""
    
    print("📊 SEASON-BY-SEASON ACCURACY ANALYSIS")
    print("="*60)
    
    configs = create_test_configurations()
    seasons = [2021, 2022, 2023, 2024]
    
    # Test current config on each season
    current_config = configs['current_30pct']
    
    for season in seasons:
        print(f"\n🏈 {season} Season:")
        
        try:
            # Load season data
            games = load_games([season])
            completed_games = games.dropna(subset=['home_score', 'away_score'])
            
            if len(completed_games) < 10:
                print(f"   Not enough games ({len(completed_games)})")
                continue
            
            # Calculate metrics
            metrics = calculate_accuracy_metrics(completed_games, current_config)
            
            if metrics.get('success'):
                print(f"   Games: {metrics['total_predictions']}")
                print(f"   Accuracy: {metrics['accuracy']:.3f} ({metrics['correct_predictions']}/{metrics['total_predictions']})")
                print(f"   Brier Score: {metrics['brier_score']:.3f}")
                print(f"   Log Loss: {metrics['log_loss']:.3f}")
                print(f"   Avg Confidence: {metrics['avg_confidence']:.3f}")
                print(f"   Calibration Error: {metrics['calibration_error']:.3f}")
            else:
                print(f"   Error: {metrics.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"   Error: {e}")


def compare_configurations():
    """Compare accuracy across different configurations."""
    
    print("\n🔬 CONFIGURATION COMPARISON")
    print("="*60)
    
    configs = create_test_configurations()
    
    # Load test data (2022-2024 for fair comparison)
    test_games = load_games([2022, 2023, 2024])
    completed_games = test_games.dropna(subset=['home_score', 'away_score'])
    
    print(f"Test data: {len(completed_games)} games from 2022-2024")
    print()
    
    results = {}
    
    for config_name, config in configs.items():
        print(f"Testing {config_name}...")
        
        try:
            metrics = calculate_accuracy_metrics(completed_games, config)
            
            if metrics.get('success'):
                results[config_name] = metrics
                print(f"   ✅ Accuracy: {metrics['accuracy']:.3f}")
                print(f"   ✅ Brier Score: {metrics['brier_score']:.3f}")
                print(f"   ✅ Log Loss: {metrics['log_loss']:.3f}")
            else:
                print(f"   ❌ Error: {metrics.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
    
    # Create comparison table
    if results:
        print("📋 CONFIGURATION COMPARISON TABLE")
        print("-" * 80)
        print(f"{'Configuration':<20} {'Accuracy':<10} {'Brier Score':<12} {'Log Loss':<10} {'Calibration':<12}")
        print("-" * 80)
        
        for config_name, metrics in results.items():
            print(f"{config_name:<20} "
                  f"{metrics['accuracy']:.3f}      "
                  f"{metrics['brier_score']:.3f}       "
                  f"{metrics['log_loss']:.3f}    "
                  f"{metrics['calibration_error']:.3f}")
        
        # Find best configuration
        best_accuracy = max(results.items(), key=lambda x: x[1]['accuracy'])
        best_brier = min(results.items(), key=lambda x: x[1]['brier_score'])
        best_log_loss = min(results.items(), key=lambda x: x[1]['log_loss'])
        
        print(f"\n🏆 BEST CONFIGURATIONS:")
        print(f"   Highest Accuracy: {best_accuracy[0]} ({best_accuracy[1]['accuracy']:.3f})")
        print(f"   Best Brier Score: {best_brier[0]} ({best_brier[1]['brier_score']:.3f})")
        print(f"   Best Log Loss: {best_log_loss[0]} ({best_log_loss[1]['log_loss']:.3f})")


def analyze_prediction_confidence():
    """Analyze how prediction confidence relates to accuracy."""
    
    print("\n🎯 PREDICTION CONFIDENCE ANALYSIS")
    print("="*50)
    
    config = create_test_configurations()['current_30pct']
    
    # Load test data
    test_games = load_games([2022, 2023, 2024])
    completed_games = test_games.dropna(subset=['home_score', 'away_score'])
    
    try:
        result = run_backtest(completed_games, config)
        game_results = result.get('game_results', [])
        
        if not game_results:
            print("No game results found")
            return
        
        df_results = pd.DataFrame(game_results)
        
        # Group by confidence levels
        confidence_bins = [
            (0.5, 0.6, "50-60%"),
            (0.6, 0.7, "60-70%"),
            (0.7, 0.8, "70-80%"),
            (0.8, 0.9, "80-90%"),
            (0.9, 1.0, "90-100%")
        ]
        
        print("Confidence Level | Games | Accuracy | Avg Confidence")
        print("-" * 50)
        
        for bin_min, bin_max, label in confidence_bins:
            bin_games = df_results[
                (df_results['home_win_prob'] >= bin_min) & 
                (df_results['home_win_prob'] < bin_max)
            ]
            
            if len(bin_games) > 0:
                correct = (bin_games['actual_winner'] == 'home').sum()
                accuracy = correct / len(bin_games)
                avg_conf = bin_games['home_win_prob'].mean()
                
                print(f"{label:<15} | {len(bin_games):<5} | {accuracy:.3f}    | {avg_conf:.3f}")
            else:
                print(f"{label:<15} | 0     | N/A     | N/A")
                
    except Exception as e:
        print(f"Error: {e}")


def analyze_team_specific_accuracy():
    """Analyze accuracy for specific teams."""
    
    print("\n🏈 TEAM-SPECIFIC ACCURACY ANALYSIS")
    print("="*50)
    
    config = create_test_configurations()['current_30pct']
    
    # Load test data
    test_games = load_games([2022, 2023, 2024])
    completed_games = test_games.dropna(subset=['home_score', 'away_score'])
    
    try:
        result = run_backtest(completed_games, config)
        game_results = result.get('game_results', [])
        
        if not game_results:
            print("No game results found")
            return
        
        df_results = pd.DataFrame(game_results)
        
        # Get all teams
        all_teams = set(df_results['home_team'].unique()) | set(df_results['away_team'].unique())
        
        team_accuracy = {}
        
        for team in all_teams:
            if pd.isna(team):
                continue
            
            # Get games where this team played
            team_games = df_results[
                (df_results['home_team'] == team) | (df_results['away_team'] == team)
            ]
            
            if len(team_games) < 5:  # Need at least 5 games
                continue
            
            correct = 0
            total = 0
            
            for _, game in team_games.iterrows():
                if pd.isna(game.get('home_win_prob')) or pd.isna(game.get('actual_winner')):
                    continue
                
                # Determine if prediction was correct
                predicted_winner = 'home' if game['home_win_prob'] > 0.5 else 'away'
                actual_winner = game['actual_winner']
                
                if predicted_winner == actual_winner:
                    correct += 1
                total += 1
            
            if total > 0:
                accuracy = correct / total
                team_accuracy[team] = {
                    'accuracy': accuracy,
                    'games': total,
                    'correct': correct
                }
        
        # Sort by accuracy
        sorted_teams = sorted(team_accuracy.items(), key=lambda x: x[1]['accuracy'], reverse=True)
        
        print("Team | Games | Correct | Accuracy")
        print("-" * 35)
        
        for team, stats in sorted_teams[:15]:  # Top 15 teams
            print(f"{team:<4} | {stats['games']:<5} | {stats['correct']:<7} | {stats['accuracy']:.3f}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("🏈 COMPREHENSIVE ELO ACCURACY ANALYSIS")
    print("="*70)
    print("Analyzing prediction accuracy across different configurations")
    print("="*70)
    
    # Season-by-season analysis
    analyze_season_accuracy()
    
    # Configuration comparison
    compare_configurations()
    
    # Confidence analysis
    analyze_prediction_confidence()
    
    # Team-specific analysis
    analyze_team_specific_accuracy()
    
    print("\n🎉 ACCURACY ANALYSIS COMPLETE!")
    print("Use these results to optimize the ELO system configuration.")
