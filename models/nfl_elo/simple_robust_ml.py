"""Simple robust ML system with proper data leakage prevention."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.preprocessing import StandardScaler

from .config import EloConfig
from ingest.nfl.data_loader import load_games


class SimpleRobustML:
    """Simple robust ML system with proper data leakage prevention."""
    
    def __init__(self):
        """Initialize simple robust ML system."""
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
    
    def run_simple_robust_backtest(self, years: List[int]) -> Dict[str, Any]:
        """
        Run simple robust backtest with proper data leakage prevention.
        
        Args:
            years: Years to test
            
        Returns:
            Backtest results
        """
        print(f"🔬 SIMPLE ROBUST ML BACKTEST - PROPER DATA LEAKAGE PREVENTION")
        print(f"Years: {years}")
        print("="*80)
        
        # Load all data
        all_games = load_games(years)
        print(f"Loaded {len(all_games)} total games")
        
        # Sort by season and week (temporal order)
        all_games = all_games.sort_values(['season', 'week']).reset_index(drop=True)
        
        # Initialize all teams at base rating
        all_teams = set(all_games['home_team'].unique()) | set(all_games['away_team'].unique())
        for team in all_teams:
            if pd.notna(team):
                self.team_ratings[team] = self.elo_config.base_rating
        
        # Create features and predictions
        predictions = []
        actual_outcomes = []
        probabilities = []
        
        for i, game in all_games.iterrows():
            if i < 50:  # Need minimum games for feature calculation
                # Update ratings after game
                self._update_ratings(game)
                continue
            
            # Create features using ONLY previous games
            features = self._create_simple_features(game, all_games.iloc[:i])
            
            if features is not None:
                # Make prediction
                prediction, probability = self._make_simple_prediction(features)
                
                predictions.append(prediction)
                actual_outcomes.append(1 if game['home_score'] > game['away_score'] else 0)
                probabilities.append(probability)
            
            # Update ratings after game
            self._update_ratings(game)
            
            if i % 100 == 0:
                print(f"  Processed {i+1}/{len(all_games)} games...")
        
        # Calculate metrics
        predictions = np.array(predictions)
        actual_outcomes = np.array(actual_outcomes)
        probabilities = np.array(probabilities)
        
        accuracy = np.mean(predictions == actual_outcomes)
        brier = brier_score_loss(actual_outcomes, probabilities)
        log_loss_score = log_loss(actual_outcomes, probabilities)
        
        return {
            'total_games': len(predictions),
            'accuracy': accuracy,
            'brier_score': brier,
            'log_loss': log_loss_score,
            'predictions': predictions,
            'actual_outcomes': actual_outcomes,
            'probabilities': probabilities
        }
    
    def _create_simple_features(self, game: pd.Series, previous_games: pd.DataFrame) -> Optional[np.ndarray]:
        """Create simple features using ONLY previous games."""
        try:
            home_team = game['home_team']
            away_team = game['away_team']
            
            # 1. Elo features (current ratings)
            home_rating = self.team_ratings.get(home_team, 1500.0)
            away_rating = self.team_ratings.get(away_team, 1500.0)
            elo_diff = home_rating - away_rating + self.elo_config.hfa_points
            elo_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
            
            # 2. Team performance features (from previous games only)
            home_stats = self._calculate_team_stats(home_team, previous_games)
            away_stats = self._calculate_team_stats(away_team, previous_games)
            
            # 3. Situational features
            week = game['week']
            season_progress = week / 18.0
            
            # Combine features
            features = np.array([
                home_rating, away_rating, elo_diff, elo_win_prob,
                home_stats['off_ppg'], home_stats['def_ppg'], home_stats['win_pct'],
                away_stats['off_ppg'], away_stats['def_ppg'], away_stats['win_pct'],
                season_progress
            ])
            
            return features
            
        except Exception as e:
            print(f"Error creating features for game {game.get('game_id', 'unknown')}: {e}")
            return None
    
    def _calculate_team_stats(self, team: str, previous_games: pd.DataFrame) -> Dict[str, float]:
        """Calculate team stats using only previous games."""
        team_games = previous_games[(previous_games['home_team'] == team) | (previous_games['away_team'] == team)]
        
        if len(team_games) == 0:
            return {'off_ppg': 0.0, 'def_ppg': 0.0, 'win_pct': 0.5}
        
        points_scored = 0
        points_allowed = 0
        wins = 0
        
        for _, game in team_games.iterrows():
            if game['home_team'] == team:
                points_scored += game['home_score']
                points_allowed += game['away_score']
                wins += 1 if game['home_score'] > game['away_score'] else 0
            else:
                points_scored += game['away_score']
                points_allowed += game['home_score']
                wins += 1 if game['away_score'] > game['home_score'] else 0
        
        return {
            'off_ppg': points_scored / len(team_games),
            'def_ppg': points_allowed / len(team_games),
            'win_pct': wins / len(team_games)
        }
    
    def _make_simple_prediction(self, features: np.ndarray) -> Tuple[int, float]:
        """Make simple prediction using features."""
        # Simple weighted combination
        elo_win_prob = features[3]  # Elo win probability
        home_off_ppg = features[4]
        home_def_ppg = features[5]
        home_win_pct = features[6]
        away_off_ppg = features[7]
        away_def_ppg = features[8]
        away_win_pct = features[9]
        
        # Team performance factor
        home_off_adv = home_off_ppg - away_def_ppg
        away_off_adv = away_off_ppg - home_def_ppg
        team_factor = (home_off_adv - away_off_adv) / 10.0
        
        # Win percentage factor
        win_pct_factor = (home_win_pct - away_win_pct) * 0.3
        
        # Combine factors
        combined_prob = 0.7 * elo_win_prob + 0.2 * (0.5 + team_factor) + 0.1 * (0.5 + win_pct_factor)
        combined_prob = max(0.1, min(0.9, combined_prob))
        
        prediction = 1 if combined_prob > 0.5 else 0
        
        return prediction, combined_prob
    
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


def test_simple_robust_ml():
    """Test simple robust ML system."""
    print("🔬 TESTING SIMPLE ROBUST ML SYSTEM")
    print("="*80)
    
    # Test with recent years
    years = [2022, 2023, 2024]
    
    # Create system
    system = SimpleRobustML()
    
    # Run backtest
    results = system.run_simple_robust_backtest(years)
    
    print(f"\\n🔬 SIMPLE ROBUST ML RESULTS:")
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
    system, results = test_simple_robust_ml()
