"""Robust ML system with proper data leakage prevention for NFL predictions."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

from .config import EloConfig
from ingest.nfl.data_loader import load_games


class RobustMLSystem:
    """Robust ML system with proper data leakage prevention."""
    
    def __init__(self):
        """Initialize robust ML system."""
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
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.is_trained = False
    
    def run_robust_backtest(self, years: List[int]) -> Dict[str, Any]:
        """
        Run robust backtest with proper data leakage prevention.
        
        Args:
            years: Years to test
            
        Returns:
            Backtest results
        """
        print(f"🔬 ROBUST ML BACKTEST - PROPER DATA LEAKAGE PREVENTION")
        print(f"Years: {years}")
        print("="*80)
        
        # Load all data
        all_games = load_games(years)
        print(f"Loaded {len(all_games)} total games")
        
        # Sort by season and week (temporal order)
        all_games = all_games.sort_values(['season', 'week']).reset_index(drop=True)
        
        # Create features for each game using ONLY previous data
        features_list = []
        targets = []
        
        for i, game in all_games.iterrows():
            if i < 50:  # Need minimum games for feature calculation
                continue
            
            # Get all games BEFORE this game
            previous_games = all_games.iloc[:i]
            
            # Create features using ONLY previous games
            features = self._create_pregame_features(game, previous_games)
            
            if features is not None:
                features_list.append(features)
                targets.append(1 if game['home_score'] > game['away_score'] else 0)
            
            if i % 100 == 0:
                print(f"  Processed {i+1}/{len(all_games)} games...")
        
        # Convert to arrays
        X = np.array(features_list)
        y = np.array(targets)
        
        print(f"\\nCreated {len(X)} samples with {X.shape[1]} features")
        
        # Use Time Series Split for proper validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Train and evaluate models
        results = self._train_and_evaluate_models(X, y, tscv)
        
        return results
    
    def _create_pregame_features(self, game: pd.Series, previous_games: pd.DataFrame) -> Optional[np.ndarray]:
        """Create features using ONLY previous games (no data leakage)."""
        try:
            home_team = game['home_team']
            away_team = game['away_team']
            season = game['season']
            week = game['week']
            
            # 1. Elo-based features (using only previous games)
            elo_features = self._calculate_elo_features(home_team, away_team, previous_games)
            
            # 2. Team performance features (using only previous games)
            team_features = self._calculate_team_features(home_team, away_team, previous_games)
            
            # 3. Situational features (pre-game only)
            situational_features = self._calculate_situational_features(game)
            
            # 4. Historical features (using only previous games)
            historical_features = self._calculate_historical_features(home_team, away_team, previous_games)
            
            # Combine all features
            features = np.concatenate([
                elo_features,
                team_features,
                situational_features,
                historical_features
            ])
            
            return features
            
        except Exception as e:
            print(f"Error creating features for game {game.get('game_id', 'unknown')}: {e}")
            return None
    
    def _calculate_elo_features(self, home_team: str, away_team: str, previous_games: pd.DataFrame) -> np.ndarray:
        """Calculate Elo features using only previous games."""
        # Initialize ratings
        home_rating = 1500.0
        away_rating = 1500.0
        
        # Update ratings based on previous games
        for _, prev_game in previous_games.iterrows():
            if prev_game['home_team'] == home_team or prev_game['away_team'] == home_team:
                # Update home team rating
                if prev_game['home_team'] == home_team:
                    # Home team was home
                    elo_diff = home_rating - (1500.0 if prev_game['away_team'] != away_team else away_rating) + self.elo_config.hfa_points
                    expected = 1 / (1 + 10 ** (-elo_diff / 400))
                    actual = 1 if prev_game['home_score'] > prev_game['away_score'] else 0
                    margin = abs(prev_game['home_score'] - prev_game['away_score'])
                    mov_multiplier = np.log(margin + 1) * (2.2 / (0.001 * elo_diff + 2.2))
                    home_rating += self.elo_config.k * mov_multiplier * (actual - expected)
                else:
                    # Home team was away
                    elo_diff = (1500.0 if prev_game['home_team'] != away_team else away_rating) - home_rating + self.elo_config.hfa_points
                    expected = 1 / (1 + 10 ** (-elo_diff / 400))
                    actual = 1 if prev_game['away_score'] > prev_game['home_score'] else 0
                    margin = abs(prev_game['away_score'] - prev_game['home_score'])
                    mov_multiplier = np.log(margin + 1) * (2.2 / (0.001 * elo_diff + 2.2))
                    home_rating += self.elo_config.k * mov_multiplier * (actual - expected)
            
            if prev_game['home_team'] == away_team or prev_game['away_team'] == away_team:
                # Update away team rating
                if prev_game['home_team'] == away_team:
                    # Away team was home
                    elo_diff = away_rating - (1500.0 if prev_game['away_team'] != home_team else home_rating) + self.elo_config.hfa_points
                    expected = 1 / (1 + 10 ** (-elo_diff / 400))
                    actual = 1 if prev_game['home_score'] > prev_game['away_score'] else 0
                    margin = abs(prev_game['home_score'] - prev_game['away_score'])
                    mov_multiplier = np.log(margin + 1) * (2.2 / (0.001 * elo_diff + 2.2))
                    away_rating += self.elo_config.k * mov_multiplier * (actual - expected)
                else:
                    # Away team was away
                    elo_diff = (1500.0 if prev_game['home_team'] != home_team else home_rating) - away_rating + self.elo_config.hfa_points
                    expected = 1 / (1 + 10 ** (-elo_diff / 400))
                    actual = 1 if prev_game['away_score'] > prev_game['home_score'] else 0
                    margin = abs(prev_game['away_score'] - prev_game['home_score'])
                    mov_multiplier = np.log(margin + 1) * (2.2 / (0.001 * elo_diff + 2.2))
                    away_rating += self.elo_config.k * mov_multiplier * (actual - expected)
        
        # Calculate Elo features
        elo_diff = home_rating - away_rating + self.elo_config.hfa_points
        elo_ratio = home_rating / (away_rating + 1)
        elo_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        return np.array([home_rating, away_rating, elo_diff, elo_ratio, elo_win_prob])
    
    def _calculate_team_features(self, home_team: str, away_team: str, previous_games: pd.DataFrame) -> np.ndarray:
        """Calculate team performance features using only previous games."""
        # Get team games
        home_games = previous_games[(previous_games['home_team'] == home_team) | (previous_games['away_team'] == home_team)]
        away_games = previous_games[(previous_games['home_team'] == away_team) | (previous_games['away_team'] == away_team)]
        
        # Calculate home team stats
        home_off_ppg = 0.0
        home_def_ppg = 0.0
        home_win_pct = 0.5
        
        if len(home_games) > 0:
            home_points_scored = 0
            home_points_allowed = 0
            home_wins = 0
            
            for _, game in home_games.iterrows():
                if game['home_team'] == home_team:
                    home_points_scored += game['home_score']
                    home_points_allowed += game['away_score']
                    home_wins += 1 if game['home_score'] > game['away_score'] else 0
                else:
                    home_points_scored += game['away_score']
                    home_points_allowed += game['home_score']
                    home_wins += 1 if game['away_score'] > game['home_score'] else 0
            
            home_off_ppg = home_points_scored / len(home_games)
            home_def_ppg = home_points_allowed / len(home_games)
            home_win_pct = home_wins / len(home_games)
        
        # Calculate away team stats
        away_off_ppg = 0.0
        away_def_ppg = 0.0
        away_win_pct = 0.5
        
        if len(away_games) > 0:
            away_points_scored = 0
            away_points_allowed = 0
            away_wins = 0
            
            for _, game in away_games.iterrows():
                if game['home_team'] == away_team:
                    away_points_scored += game['home_score']
                    away_points_allowed += game['away_score']
                    away_wins += 1 if game['home_score'] > game['away_score'] else 0
                else:
                    away_points_scored += game['away_score']
                    away_points_allowed += game['home_score']
                    away_wins += 1 if game['away_score'] > game['home_score'] else 0
            
            away_off_ppg = away_points_scored / len(away_games)
            away_def_ppg = away_points_allowed / len(away_games)
            away_win_pct = away_wins / len(away_games)
        
        return np.array([
            home_off_ppg, home_def_ppg, home_win_pct,
            away_off_ppg, away_def_ppg, away_win_pct
        ])
    
    def _calculate_situational_features(self, game: pd.Series) -> np.ndarray:
        """Calculate situational features (pre-game only)."""
        # Home field advantage
        is_home = 1.0
        
        # Rest days (if available)
        home_rest = game.get('home_rest', 7)
        away_rest = game.get('away_rest', 7)
        rest_advantage = home_rest - away_rest
        
        # Season progression
        week = game['week']
        season_progress = week / 18.0
        
        return np.array([is_home, rest_advantage, season_progress])
    
    def _calculate_historical_features(self, home_team: str, away_team: str, previous_games: pd.DataFrame) -> np.ndarray:
        """Calculate historical features using only previous games."""
        # Head-to-head record
        h2h_games = previous_games[
            ((previous_games['home_team'] == home_team) & (previous_games['away_team'] == away_team)) |
            ((previous_games['home_team'] == away_team) & (previous_games['away_team'] == home_team))
        ]
        
        home_h2h_wins = 0
        away_h2h_wins = 0
        
        if len(h2h_games) > 0:
            for _, game in h2h_games.iterrows():
                if game['home_team'] == home_team:
                    if game['home_score'] > game['away_score']:
                        home_h2h_wins += 1
                    else:
                        away_h2h_wins += 1
                else:
                    if game['away_score'] > game['home_score']:
                        home_h2h_wins += 1
                    else:
                        away_h2h_wins += 1
        
        return np.array([home_h2h_wins, away_h2h_wins])
    
    def _train_and_evaluate_models(self, X: np.ndarray, y: np.ndarray, tscv: TimeSeriesSplit) -> Dict[str, Any]:
        """Train and evaluate models using time series cross-validation."""
        print("\\n🔬 Training and evaluating models...")
        
        # Define models
        models = {
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000, C=0.1),
            'random_forest': RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42),
            'gradient_boosting': GradientBoostingClassifier(n_estimators=50, learning_rate=0.05, max_depth=3, random_state=42),
            'neural_network': MLPClassifier(hidden_layer_sizes=(50, 25), random_state=42, max_iter=500, alpha=0.01)
        }
        
        results = {}
        
        for name, model in models.items():
            print(f"  Training {name}...")
            
            # Use pipeline for neural network scaling
            if name == 'neural_network':
                pipeline = Pipeline([
                    ('scaler', StandardScaler()),
                    ('model', model)
                ])
                model = pipeline
            
            # Time series cross-validation
            cv_scores = []
            cv_predictions = []
            cv_probabilities = []
            
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                
                # Train model
                model.fit(X_train, y_train)
                
                # Make predictions
                if hasattr(model, 'predict_proba'):
                    y_pred_proba = model.predict_proba(X_val)[:, 1]
                    y_pred = (y_pred_proba > 0.5).astype(int)
                else:
                    y_pred = model.predict(X_val)
                    y_pred_proba = np.full(len(y_val), 0.5)
                
                # Calculate accuracy
                accuracy = accuracy_score(y_val, y_pred)
                cv_scores.append(accuracy)
                cv_predictions.extend(y_pred)
                cv_probabilities.extend(y_pred_proba)
            
            # Calculate metrics
            mean_accuracy = np.mean(cv_scores)
            std_accuracy = np.std(cv_scores)
            
            # Calculate Brier Score and Log Loss
            brier = brier_score_loss(y, cv_probabilities)
            log_loss_score = log_loss(y, cv_probabilities)
            
            results[name] = {
                'model': model,
                'cv_scores': cv_scores,
                'mean_accuracy': mean_accuracy,
                'std_accuracy': std_accuracy,
                'brier_score': brier,
                'log_loss': log_loss_score,
                'predictions': cv_predictions,
                'probabilities': cv_probabilities
            }
            
            print(f"    {name}: Accuracy={mean_accuracy:.3f}±{std_accuracy:.3f}, Brier={brier:.3f}")
        
        return results


def test_robust_ml_system():
    """Test robust ML system."""
    print("🔬 TESTING ROBUST ML SYSTEM")
    print("="*80)
    
    # Test with recent years
    years = [2022, 2023, 2024]
    
    # Create system
    system = RobustMLSystem()
    
    # Run backtest
    results = system.run_robust_backtest(years)
    
    print(f"\\n🔬 ROBUST ML RESULTS:")
    print("-" * 50)
    
    for name, result in results.items():
        print(f"{name:20}: Accuracy={result['mean_accuracy']:.3f}±{result['std_accuracy']:.3f}, Brier={result['brier_score']:.3f}")
    
    # Find best model
    best_model = min(results.items(), key=lambda x: x[1]['brier_score'])
    print(f"\\n🏆 Best Model: {best_model[0]} (Brier Score: {best_model[1]['brier_score']:.3f})")
    
    return system, results


if __name__ == "__main__":
    system, results = test_robust_ml_system()
