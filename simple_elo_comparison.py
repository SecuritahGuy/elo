#!/usr/bin/env python3
"""
Simple ELO comparison to test 30% vs 75% regression.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from typing import Dict, List, Any

from models.nfl_elo.prediction_interface import NFLPredictionInterface
from models.nfl_elo.config import EloConfig
from ingest.nfl.data_loader import load_games


def test_philadelphia_win_detailed():
    """Test how Philadelphia's win affects ratings with different regression rates."""
    
    print("🏈 PHILADELPHIA WIN IMPACT - DETAILED ANALYSIS")
    print("="*60)
    
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
    print()
    
    # Test different regression rates
    regression_rates = [0.30, 0.50, 0.75]
    
    for regress_rate in regression_rates:
        print(f"📊 Testing {regress_rate*100:.0f}% regression:")
        
        # Create config
        config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=regress_rate,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            start_season=2021,
            end_season=2025
        )
        
        # Load historical data (2021-2024)
        historical_games = load_games([2021, 2022, 2023, 2024])
        historical_completed = historical_games.dropna(subset=['home_score', 'away_score'])
        
        # Combine with 2025 game
        all_games = pd.concat([historical_completed, phi_dal_game], ignore_index=True)
        
        try:
            # Run backtest
            from models.nfl_elo.backtest import run_backtest
            result = run_backtest(all_games, config)
            final_ratings = result.get('final_ratings', {})
            
            # Get ratings before and after the game
            # For simplicity, let's just show final ratings
            phi_rating = final_ratings.get('PHI', 1500)
            dal_rating = final_ratings.get('DAL', 1500)
            
            print(f"  PHI final rating: {phi_rating:.1f}")
            print(f"  DAL final rating: {dal_rating:.1f}")
            print(f"  PHI advantage: {phi_rating - dal_rating:.1f} points")
            
            # Show top 5 teams
            sorted_teams = sorted(final_ratings.items(), key=lambda x: x[1], reverse=True)
            print(f"  Top 5: {', '.join([f'{team}({rating:.0f})' for team, rating in sorted_teams[:5]])}")
            
        except Exception as e:
            print(f"  Error: {e}")
        
        print()


def test_season_by_season_impact():
    """Test how different regression rates affect season-by-season ratings."""
    
    print("📈 SEASON-BY-SEASON RATING IMPACT")
    print("="*50)
    
    # Test different regression rates
    regression_rates = [0.30, 0.50, 0.75]
    seasons = [2021, 2022, 2023, 2024, 2025]
    
    for regress_rate in regression_rates:
        print(f"\n{regress_rate*100:.0f}% Regression:")
        
        # Create config
        config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=regress_rate,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            start_season=2021,
            end_season=2025
        )
        
        # Load all games
        all_games = load_games(seasons)
        completed_games = all_games.dropna(subset=['home_score', 'away_score'])
        
        try:
            # Run backtest
            from models.nfl_elo.backtest import run_backtest
            result = run_backtest(completed_games, config)
            final_ratings = result.get('final_ratings', {})
            
            # Show rating distribution
            ratings = list(final_ratings.values())
            print(f"  Rating range: {min(ratings):.1f} - {max(ratings):.1f}")
            print(f"  Rating std: {np.std(ratings):.1f}")
            print(f"  Teams above 1600: {sum(1 for r in ratings if r > 1600)}")
            print(f"  Teams below 1400: {sum(1 for r in ratings if r < 1400)}")
            
        except Exception as e:
            print(f"  Error: {e}")


def test_prediction_accuracy():
    """Test prediction accuracy with different configurations."""
    
    print("🎯 PREDICTION ACCURACY TEST")
    print("="*40)
    
    # Load 2024 data for testing
    games_2024 = load_games([2024])
    completed_2024 = games_2024.dropna(subset=['home_score', 'away_score'])
    
    if len(completed_2024) < 10:
        print("Not enough 2024 games for testing")
        return
    
    # Test different regression rates
    regression_rates = [0.30, 0.50, 0.75]
    
    for regress_rate in regression_rates:
        print(f"\n{regress_rate*100:.0f}% Regression:")
        
        # Create config
        config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=regress_rate,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            start_season=2021,
            end_season=2024
        )
        
        try:
            # Run backtest
            from models.nfl_elo.backtest import run_backtest
            result = run_backtest(completed_2024, config)
            
            # Get game results
            game_results = result.get('game_results', [])
            if game_results:
                df_results = pd.DataFrame(game_results)
                
                # Calculate accuracy
                correct = 0
                total = 0
                
                for _, game in df_results.iterrows():
                    if pd.notna(game.get('home_win_prob')) and pd.notna(game.get('actual_winner')):
                        predicted_winner = 'home' if game['home_win_prob'] > 0.5 else 'away'
                        actual_winner = game['actual_winner']
                        
                        if predicted_winner == actual_winner:
                            correct += 1
                        total += 1
                
                accuracy = correct / total if total > 0 else 0
                print(f"  Accuracy: {accuracy:.3f} ({correct}/{total})")
                
                # Calculate average prediction confidence
                avg_confidence = df_results['home_win_prob'].mean()
                print(f"  Avg confidence: {avg_confidence:.3f}")
                
            else:
                print("  No game results found")
                
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    print("🏈 SIMPLE ELO COMPARISON")
    print("="*50)
    print("Testing 30% vs 50% vs 75% regression rates")
    print("="*50)
    
    # Test Philadelphia win impact
    test_philadelphia_win_detailed()
    
    # Test season-by-season impact
    test_season_by_season_impact()
    
    # Test prediction accuracy
    test_prediction_accuracy()
    
    print("\n🎉 Comparison completed!")
