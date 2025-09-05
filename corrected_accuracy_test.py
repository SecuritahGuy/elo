#!/usr/bin/env python3
"""
Corrected accuracy test for ELO predictions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

from models.nfl_elo.prediction_interface import NFLPredictionInterface
from models.nfl_elo.config import EloConfig
from ingest.nfl.data_loader import load_games


def test_prediction_accuracy():
    """Test prediction accuracy using the prediction interface."""
    
    print("🏈 ELO PREDICTION ACCURACY TEST")
    print("="*50)
    
    # Create different configurations
    configs = {
        'Current (30% reg)': EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.30,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            start_season=2021,
            end_season=2025
        ),
        'Old (75% reg)': EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            start_season=2020,
            end_season=2025
        ),
        'Conservative (50% reg)': EloConfig(
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
    }
    
    # Test on 2024 season
    print("Testing on 2024 season data...")
    games_2024 = load_games([2024])
    completed_2024 = games_2024.dropna(subset=['home_score', 'away_score'])
    
    print(f"Loaded {len(completed_2024)} completed games from 2024")
    
    if len(completed_2024) < 10:
        print("Not enough games for testing")
        return
    
    # Test each configuration
    for config_name, config in configs.items():
        print(f"\n📊 Testing {config_name}:")
        
        try:
            # Create prediction interface
            interface = NFLPredictionInterface(config)
            
            # Load team ratings
            interface.load_team_ratings([2021, 2022, 2023, 2024])
            
            # Test predictions on 2024 games
            correct_predictions = 0
            total_predictions = 0
            confidence_scores = []
            brier_scores = []
            
            for _, game in completed_2024.iterrows():
                try:
                    # Get prediction
                    prediction = interface.predict_game(
                        game['home_team'], 
                        game['away_team']
                    )
                    
                    if prediction is None:
                        continue
                    
                    home_win_prob = prediction['home_win_probability']  # Corrected field name
                    actual_winner = 'home' if game['home_score'] > game['away_score'] else 'away'
                    
                    # Determine predicted winner
                    predicted_winner = 'home' if home_win_prob > 0.5 else 'away'
                    
                    # Calculate accuracy
                    if predicted_winner == actual_winner:
                        correct_predictions += 1
                    total_predictions += 1
                    
                    # Calculate confidence
                    confidence = abs(home_win_prob - 0.5) * 2
                    confidence_scores.append(confidence)
                    
                    # Calculate Brier score
                    actual_binary = 1 if actual_winner == 'home' else 0
                    brier_score = (home_win_prob - actual_binary) ** 2
                    brier_scores.append(brier_score)
                    
                except Exception as e:
                    continue
            
            if total_predictions > 0:
                accuracy = correct_predictions / total_predictions
                avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
                avg_brier_score = np.mean(brier_scores) if brier_scores else 1.0
                
                print(f"   Games tested: {total_predictions}")
                print(f"   Accuracy: {accuracy:.3f} ({correct_predictions}/{total_predictions})")
                print(f"   Avg Confidence: {avg_confidence:.3f}")
                print(f"   Brier Score: {avg_brier_score:.3f}")
                
                # Calculate confidence-based accuracy
                if confidence_scores:
                    high_conf_games = [i for i, conf in enumerate(confidence_scores) if conf > 0.3]
                    if high_conf_games:
                        high_conf_correct = 0
                        for i in high_conf_games:
                            game_idx = completed_2024.index[i]
                            game = completed_2024.loc[game_idx]
                            actual_winner = 'home' if game['home_score'] > game['away_score'] else 'away'
                            predicted_winner = 'home' if confidence_scores[i] > 0.3 else 'away'
                            if predicted_winner == actual_winner:
                                high_conf_correct += 1
                        high_conf_accuracy = high_conf_correct / len(high_conf_games)
                        print(f"   High Confidence (>60%) Accuracy: {high_conf_accuracy:.3f}")
            else:
                print(f"   No valid predictions generated")
                
        except Exception as e:
            print(f"   Error: {e}")


def test_philadelphia_prediction():
    """Test prediction accuracy for Philadelphia's 2025 win."""
    
    print(f"\n🏈 PHILADELPHIA 2025 WIN PREDICTION TEST")
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
    print(f"Game: {game['home_team']} vs {game['away_team']} ({game['home_score']}-{game['away_score']})")
    
    # Test different configurations
    configs = {
        'Current (30% reg)': EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.30,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            start_season=2021,
            end_season=2025
        ),
        'Old (75% reg)': EloConfig(
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
    }
    
    for config_name, config in configs.items():
        print(f"\n{config_name}:")
        
        try:
            interface = NFLPredictionInterface(config)
            interface.load_team_ratings([2021, 2022, 2023, 2024])
            
            prediction = interface.predict_game(
                game['home_team'], 
                game['away_team']
            )
            
            if prediction:
                home_win_prob = prediction['home_win_probability']  # Corrected field name
                predicted_winner = 'home' if home_win_prob > 0.5 else 'away'
                actual_winner = 'home' if game['home_score'] > game['away_score'] else 'away'
                
                print(f"   Predicted: {predicted_winner} ({home_win_prob:.3f})")
                print(f"   Actual: {actual_winner}")
                print(f"   Correct: {predicted_winner == actual_winner}")
                print(f"   Confidence: {abs(home_win_prob - 0.5) * 2:.3f}")
            else:
                print(f"   No prediction generated")
                
        except Exception as e:
            print(f"   Error: {e}")


def test_rating_stability():
    """Test rating stability across configurations."""
    
    print(f"\n📈 RATING STABILITY ANALYSIS")
    print("="*40)
    
    configs = {
        'Current (30% reg)': EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.30,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            start_season=2021,
            end_season=2025
        ),
        'Old (75% reg)': EloConfig(
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
    }
    
    for config_name, config in configs.items():
        print(f"\n{config_name}:")
        
        try:
            interface = NFLPredictionInterface(config)
            interface.load_team_ratings([2021, 2022, 2023, 2024, 2025])
            
            # Get ratings from the interface
            ratings = interface.team_ratings
            
            if ratings:
                rating_values = list(ratings.values())
                print(f"   Rating range: {min(rating_values):.1f} - {max(rating_values):.1f}")
                print(f"   Standard deviation: {np.std(rating_values):.1f}")
                print(f"   Teams above 1600: {sum(1 for r in rating_values if r > 1600)}")
                print(f"   Teams below 1400: {sum(1 for r in rating_values if r < 1400)}")
                
                # Show top 5 teams
                sorted_teams = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
                print(f"   Top 5: {', '.join([f'{team}({rating:.0f})' for team, rating in sorted_teams[:5]])}")
            else:
                print(f"   No ratings available")
                
        except Exception as e:
            print(f"   Error: {e}")


def test_confidence_distribution():
    """Test confidence distribution of predictions."""
    
    print(f"\n🎯 CONFIDENCE DISTRIBUTION ANALYSIS")
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
    
    # Load 2024 data
    games_2024 = load_games([2024])
    completed_2024 = games_2024.dropna(subset=['home_score', 'away_score'])
    
    try:
        interface = NFLPredictionInterface(config)
        interface.load_team_ratings([2021, 2022, 2023, 2024])
        
        confidence_bins = {
            '50-60%': 0,
            '60-70%': 0,
            '70-80%': 0,
            '80-90%': 0,
            '90-100%': 0
        }
        
        total_predictions = 0
        
        for _, game in completed_2024.iterrows():
            try:
                prediction = interface.predict_game(
                    game['home_team'], 
                    game['away_team']
                )
                
                if prediction:
                    confidence = prediction['confidence']
                    total_predictions += 1
                    
                    if confidence < 0.6:
                        confidence_bins['50-60%'] += 1
                    elif confidence < 0.7:
                        confidence_bins['60-70%'] += 1
                    elif confidence < 0.8:
                        confidence_bins['70-80%'] += 1
                    elif confidence < 0.9:
                        confidence_bins['80-90%'] += 1
                    else:
                        confidence_bins['90-100%'] += 1
                        
            except Exception:
                continue
        
        print(f"Total predictions: {total_predictions}")
        print("\nConfidence distribution:")
        for bin_name, count in confidence_bins.items():
            percentage = (count / total_predictions * 100) if total_predictions > 0 else 0
            print(f"   {bin_name}: {count} ({percentage:.1f}%)")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("🏈 CORRECTED ELO ACCURACY TEST")
    print("="*50)
    
    # Test prediction accuracy
    test_prediction_accuracy()
    
    # Test Philadelphia prediction
    test_philadelphia_prediction()
    
    # Test rating stability
    test_rating_stability()
    
    # Test confidence distribution
    test_confidence_distribution()
    
    print(f"\n🎉 ACCURACY TEST COMPLETE!")
