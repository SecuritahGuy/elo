"""Simple pre-game system with NO data leakage - basic Elo only."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from ingest.nfl.data_loader import load_games


class SimplePreGameSystem:
    """Simple pre-game system with NO data leakage - basic Elo only."""
    
    def __init__(self):
        """Initialize simple pre-game system."""
        self.elo_config = EloConfig(
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
            use_turnover_adjustment=False
        )
        self.team_ratings = {}
    
    def run_simple_pregame_backtest(self, years: List[int]) -> Dict[str, Any]:
        """
        Run simple pre-game backtest with NO data leakage.
        
        Args:
            years: Years to test
            
        Returns:
            Backtest results
        """
        print(f"🎯 SIMPLE PRE-GAME BACKTEST - NO DATA LEAKAGE")
        print(f"Years: {years}")
        print("="*80)
        
        all_games = load_games(years)
        print(f"Loaded {len(all_games)} total games")
        
        # Sort games by season and week
        all_games = all_games.sort_values(['season', 'week']).reset_index(drop=True)
        
        # Initialize all teams at base rating
        all_teams = set(all_games['home_team'].unique()) | set(all_games['away_team'].unique())
        for team in all_teams:
            if pd.notna(team):
                self.team_ratings[team] = self.elo_config.base_rating
        
        predictions = []
        actual_outcomes = []
        probabilities = []
        
        for i, game in all_games.iterrows():
            # Make prediction using current ratings
            prediction, probability = self._make_simple_prediction(game)
            
            predictions.append(prediction)
            actual_outcomes.append(1 if game['home_score'] > game['away_score'] else 0)
            probabilities.append(probability)
            
            # Update ratings AFTER making prediction
            self._update_ratings(game)
            
            if i % 100 == 0:
                print(f"  Processed {i+1}/{len(all_games)} games...")
        
        # Calculate metrics
        predictions = np.array(predictions)
        actual_outcomes = np.array(actual_outcomes)
        probabilities = np.array(probabilities)
        
        accuracy = np.mean(predictions == actual_outcomes)
        
        # Calculate Brier Score
        brier_score = np.mean((probabilities - actual_outcomes) ** 2)
        
        # Calculate Log Loss
        epsilon = 1e-15
        probabilities_clipped = np.clip(probabilities, epsilon, 1 - epsilon)
        log_loss = -np.mean(actual_outcomes * np.log(probabilities_clipped) + (1 - actual_outcomes) * np.log(1 - probabilities_clipped))
        
        return {
            'total_games': len(predictions),
            'accuracy': accuracy,
            'brier_score': brier_score,
            'log_loss': log_loss,
            'predictions': predictions,
            'actual_outcomes': actual_outcomes,
            'probabilities': probabilities
        }
    
    def _make_simple_prediction(self, game: pd.Series) -> Tuple[int, float]:
        """Make prediction using current Elo ratings."""
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get current ratings
        home_rating = self.team_ratings.get(home_team, self.elo_config.base_rating)
        away_rating = self.team_ratings.get(away_team, self.elo_config.base_rating)
        
        # Calculate win probability
        elo_diff = home_rating - away_rating + self.elo_config.hfa_points
        win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        # Make prediction
        prediction = 1 if win_prob > 0.5 else 0
        
        return prediction, win_prob
    
    def _update_ratings(self, game: pd.Series):
        """Update Elo ratings after game."""
        home_team = game['home_team']
        away_team = game['away_team']
        home_score = game['home_score']
        away_score = game['away_score']
        
        # Get current ratings
        home_rating = self.team_ratings.get(home_team, self.elo_config.base_rating)
        away_rating = self.team_ratings.get(away_team, self.elo_config.base_rating)
        
        # Calculate expected score
        elo_diff = home_rating - away_rating + self.elo_config.hfa_points
        expected_home = 1 / (1 + 10 ** (-elo_diff / 400))
        expected_away = 1 - expected_home
        
        # Calculate actual score
        actual_home = 1 if home_score > away_score else 0
        actual_away = 1 - actual_home
        
        # Calculate margin of victory multiplier
        if self.elo_config.mov_enabled:
            margin = abs(home_score - away_score)
            mov_multiplier = np.log(margin + 1) * (2.2 / (0.001 * (home_rating - away_rating) + 2.2))
        else:
            mov_multiplier = 1.0
        
        # Update ratings
        k_factor = self.elo_config.k * mov_multiplier
        
        home_change = k_factor * (actual_home - expected_home)
        away_change = k_factor * (actual_away - expected_away)
        
        self.team_ratings[home_team] = home_rating + home_change
        self.team_ratings[away_team] = away_rating + away_change


def test_simple_pregame_system():
    """Test simple pre-game system."""
    print("🎯 TESTING SIMPLE PRE-GAME SYSTEM")
    print("="*80)
    
    # Test with recent years
    years = [2022, 2023, 2024]
    
    # Create system
    system = SimplePreGameSystem()
    
    # Run backtest
    results = system.run_simple_pregame_backtest(years)
    
    print(f"\\n🎯 SIMPLE PRE-GAME RESULTS:")
    print(f"Total Games: {results['total_games']}")
    print(f"Accuracy: {results['accuracy']:.3f}")
    print(f"Brier Score: {results['brier_score']:.3f}")
    print(f"Log Loss: {results['log_loss']:.3f}")
    
    # Analyze results
    if results['accuracy'] > 0.70:
        print("\\n⚠️  WARNING: Accuracy still seems high - investigate further")
    elif results['accuracy'] > 0.60:
        print("\\n✅ Accuracy looks reasonable for NFL predictions")
    else:
        print("\\n❌ Accuracy seems low - check implementation")
    
    # Show some example predictions
    print(f"\\n📊 SAMPLE PREDICTIONS:")
    for i in range(min(10, len(results['predictions']))):
        pred = results['predictions'][i]
        actual = results['actual_outcomes'][i]
        prob = results['probabilities'][i]
        correct = "✓" if pred == actual else "✗"
        print(f"  Game {i+1}: Pred={pred}, Actual={actual}, Prob={prob:.3f} {correct}")
    
    return system, results


if __name__ == "__main__":
    system, results = test_simple_pregame_system()
