#!/usr/bin/env python3
"""
Deep dive analysis to detect data leakage in ELO calculations.
This script implements proper walk-forward backtesting to ensure no future data is used.
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


def proper_walk_forward_backtest(games_df: pd.DataFrame, config: EloConfig, test_season: int = 2024) -> Dict[str, Any]:
    """
    Implement proper walk-forward backtesting to prevent data leakage.
    
    Args:
        games_df: DataFrame with all game data
        config: EloConfig for the system
        test_season: Season to test predictions on
        
    Returns:
        Dictionary with backtest results and accuracy metrics
    """
    print(f"🔍 PROPER WALK-FORWARD BACKTESTING")
    print(f"Testing season: {test_season}")
    print("="*60)
    
    # Split data into training and test sets
    training_games = games_df[games_df['season'] < test_season].copy()
    test_games = games_df[games_df['season'] == test_season].copy()
    
    print(f"Training data: {len(training_games)} games (seasons < {test_season})")
    print(f"Test data: {len(test_games)} games (season {test_season})")
    
    if len(training_games) == 0 or len(test_games) == 0:
        return {'error': 'Insufficient data for walk-forward backtest'}
    
    # Train the model on historical data only
    print(f"\n🏋️ Training model on historical data...")
    
    try:
        # Run backtest on training data to get final ratings
        training_result = run_backtest(training_games, config)
        final_ratings = training_result.get('final_ratings', {})
        
        print(f"✅ Training complete. Final ratings for {len(final_ratings)} teams")
        
        # Show some training results
        if final_ratings:
            sorted_teams = sorted(final_ratings.items(), key=lambda x: x[1], reverse=True)
            print(f"Top 5 teams after training: {', '.join([f'{team}({rating:.0f})' for team, rating in sorted_teams[:5]])}")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        return {'error': f'Training failed: {e}'}
    
    # Test predictions on future data using only historical ratings
    print(f"\n🎯 Testing predictions on {test_season} season...")
    
    # Create prediction interface with trained ratings
    interface = NFLPredictionInterface(config)
    interface.team_ratings = final_ratings  # Use only historical ratings
    
    # Test each game in chronological order
    test_games_sorted = test_games.sort_values(['week', 'game_id'])
    
    predictions = []
    correct_predictions = 0
    total_predictions = 0
    
    for _, game in test_games_sorted.iterrows():
        try:
            # Make prediction using only historical data
            prediction = interface.predict_game(
                game['home_team'], 
                game['away_team']
            )
            
            if prediction is None:
                continue
            
            # Get actual result
            actual_winner = 'home' if game['home_score'] > game['away_score'] else 'away'
            predicted_winner = 'home' if prediction['home_win_probability'] > 0.5 else 'away'
            
            # Check if prediction was correct
            is_correct = predicted_winner == actual_winner
            
            if is_correct:
                correct_predictions += 1
            total_predictions += 1
            
            # Store prediction details
            predictions.append({
                'week': game['week'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'predicted_winner': predicted_winner,
                'actual_winner': actual_winner,
                'home_win_prob': prediction['home_win_probability'],
                'confidence': prediction['confidence'],
                'correct': is_correct,
                'home_rating': prediction['home_rating'],
                'away_rating': prediction['away_rating']
            })
            
            # Update ratings after each game (simulating real-time updates)
            # This is where we would update the ELO ratings based on the game result
            # For now, we'll just track the predictions without updating
            
        except Exception as e:
            print(f"Error predicting game {game['home_team']} vs {game['away_team']}: {e}")
            continue
    
    # Calculate accuracy metrics
    if total_predictions > 0:
        accuracy = correct_predictions / total_predictions
        
        # Calculate additional metrics
        confidences = [p['confidence'] for p in predictions]
        brier_scores = []
        
        for p in predictions:
            actual_binary = 1 if p['actual_winner'] == 'home' else 0
            brier_score = (p['home_win_prob'] - actual_binary) ** 2
            brier_scores.append(brier_score)
        
        avg_confidence = np.mean(confidences) if confidences else 0
        avg_brier_score = np.mean(brier_scores) if brier_scores else 1.0
        
        # Calculate confidence-based accuracy
        high_conf_predictions = [p for p in predictions if p['confidence'] > 0.6]
        high_conf_correct = sum(1 for p in high_conf_predictions if p['correct'])
        high_conf_accuracy = high_conf_correct / len(high_conf_predictions) if high_conf_predictions else 0
        
        print(f"\n📊 WALK-FORWARD BACKTEST RESULTS")
        print(f"   Total predictions: {total_predictions}")
        print(f"   Correct predictions: {correct_predictions}")
        print(f"   Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
        print(f"   Average confidence: {avg_confidence:.3f}")
        print(f"   Brier score: {avg_brier_score:.3f}")
        print(f"   High confidence (>60%) accuracy: {high_conf_accuracy:.3f}")
        
        # Show some example predictions
        print(f"\n📋 SAMPLE PREDICTIONS (First 10 games)")
        print("-" * 80)
        for i, p in enumerate(predictions[:10]):
            status = "✅" if p['correct'] else "❌"
            print(f"{i+1:2d}. {p['home_team']} vs {p['away_team']} "
                  f"({p['home_score']}-{p['away_score']}) "
                  f"Pred: {p['predicted_winner']} ({p['home_win_prob']:.3f}) "
                  f"{status}")
        
        return {
            'accuracy': accuracy,
            'total_predictions': total_predictions,
            'correct_predictions': correct_predictions,
            'avg_confidence': avg_confidence,
            'brier_score': avg_brier_score,
            'high_conf_accuracy': high_conf_accuracy,
            'predictions': predictions,
            'training_ratings': final_ratings,
            'success': True
        }
    
    else:
        print("❌ No valid predictions generated")
        return {'error': 'No valid predictions generated'}


def test_different_seasons():
    """Test accuracy on different seasons to check for consistency."""
    
    print(f"\n🗓️ MULTI-SEASON ACCURACY TEST")
    print("="*50)
    
    config = EloConfig(
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
    
    # Load all available data
    all_games = load_games([2021, 2022, 2023, 2024, 2025])
    completed_games = all_games.dropna(subset=['home_score', 'away_score'])
    
    print(f"Total games loaded: {len(completed_games)}")
    
    # Test each season
    seasons = [2022, 2023, 2024]
    results = {}
    
    for season in seasons:
        print(f"\n🏈 Testing {season} season...")
        
        try:
            result = proper_walk_forward_backtest(completed_games, config, season)
            
            if result.get('success'):
                results[season] = result
                print(f"   ✅ {season}: {result['accuracy']:.3f} accuracy")
            else:
                print(f"   ❌ {season}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ {season}: Exception - {e}")
    
    # Analyze results
    if results:
        print(f"\n📊 MULTI-SEASON SUMMARY")
        print("-" * 40)
        print(f"{'Season':<8} {'Accuracy':<10} {'Games':<8} {'Confidence':<12}")
        print("-" * 40)
        
        for season, result in results.items():
            print(f"{season:<8} {result['accuracy']:.3f}      "
                  f"{result['total_predictions']:<8} {result['avg_confidence']:.3f}")
        
        # Calculate overall statistics
        accuracies = [r['accuracy'] for r in results.values()]
        avg_accuracy = np.mean(accuracies)
        std_accuracy = np.std(accuracies)
        
        print(f"\nOverall Statistics:")
        print(f"   Average accuracy: {avg_accuracy:.3f}")
        print(f"   Standard deviation: {std_accuracy:.3f}")
        print(f"   Accuracy range: {min(accuracies):.3f} - {max(accuracies):.3f}")
        
        # Check for suspicious patterns
        if avg_accuracy > 0.70:
            print(f"\n⚠️  WARNING: Average accuracy ({avg_accuracy:.3f}) is very high!")
            print(f"   This could indicate data leakage or overfitting.")
        elif avg_accuracy > 0.60:
            print(f"✅ Good accuracy ({avg_accuracy:.3f}) - within expected range")
        else:
            print(f"❌ Low accuracy ({avg_accuracy:.3f}) - may need system improvements")


def analyze_prediction_quality():
    """Analyze the quality of predictions to detect potential issues."""
    
    print(f"\n🔍 PREDICTION QUALITY ANALYSIS")
    print("="*50)
    
    config = EloConfig(
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
    
    # Test on 2024 season
    all_games = load_games([2021, 2022, 2023, 2024])
    result = proper_walk_forward_backtest(all_games, config, 2024)
    
    if not result.get('success'):
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        return
    
    predictions = result['predictions']
    
    # Analyze confidence distribution
    print(f"\n📊 CONFIDENCE DISTRIBUTION")
    confidences = [p['confidence'] for p in predictions]
    
    confidence_bins = {
        '50-60%': 0,
        '60-70%': 0,
        '70-80%': 0,
        '80-90%': 0,
        '90-100%': 0
    }
    
    for conf in confidences:
        if conf < 0.6:
            confidence_bins['50-60%'] += 1
        elif conf < 0.7:
            confidence_bins['60-70%'] += 1
        elif conf < 0.8:
            confidence_bins['70-80%'] += 1
        elif conf < 0.9:
            confidence_bins['80-90%'] += 1
        else:
            confidence_bins['90-100%'] += 1
    
    for bin_name, count in confidence_bins.items():
        percentage = (count / len(confidences) * 100) if confidences else 0
        print(f"   {bin_name}: {count} ({percentage:.1f}%)")
    
    # Analyze accuracy by confidence level
    print(f"\n🎯 ACCURACY BY CONFIDENCE LEVEL")
    for bin_name, bin_min, bin_max in [
        ('50-60%', 0.5, 0.6),
        ('60-70%', 0.6, 0.7),
        ('70-80%', 0.7, 0.8),
        ('80-90%', 0.8, 0.9),
        ('90-100%', 0.9, 1.0)
    ]:
        bin_predictions = [p for p in predictions if bin_min <= p['confidence'] < bin_max]
        if bin_predictions:
            correct = sum(1 for p in bin_predictions if p['correct'])
            accuracy = correct / len(bin_predictions)
            print(f"   {bin_name}: {accuracy:.3f} ({correct}/{len(bin_predictions)})")
        else:
            print(f"   {bin_name}: No predictions")
    
    # Check for suspicious patterns
    print(f"\n🔍 LEAKAGE DETECTION CHECKS")
    
    # Check if accuracy is too high
    if result['accuracy'] > 0.75:
        print(f"   ⚠️  WARNING: Accuracy ({result['accuracy']:.3f}) is suspiciously high")
        print(f"      Expected NFL prediction accuracy: 60-70%")
    else:
        print(f"   ✅ Accuracy ({result['accuracy']:.3f}) is within expected range")
    
    # Check confidence calibration
    high_conf_predictions = [p for p in predictions if p['confidence'] > 0.8]
    if high_conf_predictions:
        high_conf_accuracy = sum(1 for p in high_conf_predictions if p['correct']) / len(high_conf_predictions)
        if high_conf_accuracy < 0.8:
            print(f"   ⚠️  WARNING: High confidence predictions not well calibrated")
            print(f"      High conf accuracy: {high_conf_accuracy:.3f}")
        else:
            print(f"   ✅ High confidence predictions well calibrated: {high_conf_accuracy:.3f}")
    
    # Check for perfect predictions
    perfect_weeks = {}
    for p in predictions:
        week = p['week']
        if week not in perfect_weeks:
            perfect_weeks[week] = []
        perfect_weeks[week].append(p['correct'])
    
    perfect_week_count = sum(1 for week_correct in perfect_weeks.values() if all(week_correct))
    if perfect_week_count > 0:
        print(f"   ⚠️  WARNING: {perfect_week_count} weeks with 100% accuracy")
        print(f"      This could indicate data leakage")
    else:
        print(f"   ✅ No perfect weeks detected")


if __name__ == "__main__":
    print("🔍 ELO DATA LEAKAGE ANALYSIS")
    print("="*60)
    print("Deep dive analysis to detect data leakage in ELO calculations")
    print("="*60)
    
    # Test different seasons
    test_different_seasons()
    
    # Analyze prediction quality
    analyze_prediction_quality()
    
    print(f"\n🎉 DATA LEAKAGE ANALYSIS COMPLETE!")
    print("Review the results above to identify any potential data leakage issues.")
