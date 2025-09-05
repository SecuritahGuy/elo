"""Advanced ML system with multiple models, ensemble methods, and hyperparameter tuning."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, classification_report
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.pipeline import Pipeline
import joblib

from .config import EloConfig
from ingest.nfl.data_loader import load_games


class AdvancedMLSystem:
    """Advanced ML system with multiple models and ensemble methods."""
    
    def __init__(self):
        """Initialize advanced ML system."""
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
        self.models = {}
        self.scalers = {}
        self.feature_selectors = {}
        self.ensemble_model = None
        self.is_trained = False
    
    def run_advanced_backtest(self, years: List[int]) -> Dict[str, Any]:
        """
        Run advanced backtest with multiple models and ensemble methods.
        
        Args:
            years: Years to test
            
        Returns:
            Backtest results
        """
        print(f"🚀 ADVANCED ML BACKTEST - MULTIPLE MODELS & ENSEMBLE")
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
        features_list = []
        targets = []
        
        for i, game in all_games.iterrows():
            if i < 50:  # Need minimum games for feature calculation
                # Update ratings after game
                self._update_ratings(game)
                continue
            
            # Create features using ONLY previous games
            features = self._create_advanced_features(game, all_games.iloc[:i])
            
            if features is not None:
                features_list.append(features)
                targets.append(1 if game['home_score'] > game['away_score'] else 0)
            
            # Update ratings after game
            self._update_ratings(game)
            
            if i % 100 == 0:
                print(f"  Processed {i+1}/{len(all_games)} games...")
        
        # Convert to arrays
        X = np.array(features_list)
        y = np.array(targets)
        
        print(f"\\nCreated {len(X)} samples with {X.shape[1]} features")
        
        # Use Time Series Split for proper validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Train and evaluate models
        results = self._train_and_evaluate_advanced_models(X, y, tscv)
        
        return results
    
    def _create_advanced_features(self, game: pd.Series, previous_games: pd.DataFrame) -> Optional[np.ndarray]:
        """Create advanced features using ONLY previous games."""
        try:
            home_team = game['home_team']
            away_team = game['away_team']
            season = game['season']
            week = game['week']
            
            # 1. Elo-based features
            elo_features = self._calculate_elo_features(home_team, away_team, previous_games)
            
            # 2. Team performance features
            team_features = self._calculate_team_features(home_team, away_team, previous_games)
            
            # 3. Situational features
            situational_features = self._calculate_situational_features(game)
            
            # 4. Historical features
            historical_features = self._calculate_historical_features(home_team, away_team, previous_games)
            
            # 5. Advanced features
            advanced_features = self._calculate_advanced_features(home_team, away_team, previous_games, season, week)
            
            # Combine all features
            features = np.concatenate([
                elo_features,
                team_features,
                situational_features,
                historical_features,
                advanced_features
            ])
            
            return features
            
        except Exception as e:
            print(f"Error creating features for game {game.get('game_id', 'unknown')}: {e}")
            return None
    
    def _calculate_elo_features(self, home_team: str, away_team: str, previous_games: pd.DataFrame) -> np.ndarray:
        """Calculate Elo features using only previous games."""
        home_rating = self.team_ratings.get(home_team, 1500.0)
        away_rating = self.team_ratings.get(away_team, 1500.0)
        
        elo_diff = home_rating - away_rating + self.elo_config.hfa_points
        elo_ratio = home_rating / (away_rating + 1)
        elo_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        return np.array([home_rating, away_rating, elo_diff, elo_ratio, elo_win_prob])
    
    def _calculate_team_features(self, home_team: str, away_team: str, previous_games: pd.DataFrame) -> np.ndarray:
        """Calculate team performance features using only previous games."""
        home_stats = self._calculate_team_stats(home_team, previous_games)
        away_stats = self._calculate_team_stats(away_team, previous_games)
        
        return np.array([
            home_stats['off_ppg'], home_stats['def_ppg'], home_stats['win_pct'],
            away_stats['off_ppg'], away_stats['def_ppg'], away_stats['win_pct']
        ])
    
    def _calculate_situational_features(self, game: pd.Series) -> np.ndarray:
        """Calculate situational features (pre-game only)."""
        week = game['week']
        season_progress = week / 18.0
        
        # Rest days (if available)
        home_rest = game.get('home_rest', 7)
        away_rest = game.get('away_rest', 7)
        rest_advantage = home_rest - away_rest
        
        return np.array([season_progress, rest_advantage])
    
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
    
    def _calculate_advanced_features(self, home_team: str, away_team: str, previous_games: pd.DataFrame, season: int, week: int) -> np.ndarray:
        """Calculate advanced features using only previous games."""
        # Recent form (last 5 games)
        home_recent = self._calculate_recent_form(home_team, previous_games, 5)
        away_recent = self._calculate_recent_form(away_team, previous_games, 5)
        
        # Season performance
        home_season = self._calculate_season_performance(home_team, previous_games, season)
        away_season = self._calculate_season_performance(away_team, previous_games, season)
        
        # Momentum (trend over last 3 games)
        home_momentum = self._calculate_momentum(home_team, previous_games, 3)
        away_momentum = self._calculate_momentum(away_team, previous_games, 3)
        
        return np.array([
            home_recent, away_recent,
            home_season, away_season,
            home_momentum, away_momentum
        ])
    
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
    
    def _calculate_recent_form(self, team: str, previous_games: pd.DataFrame, n_games: int) -> float:
        """Calculate recent form over last n games."""
        team_games = previous_games[(previous_games['home_team'] == team) | (previous_games['away_team'] == team)]
        
        if len(team_games) < n_games:
            return 0.5
        
        recent_games = team_games.tail(n_games)
        wins = 0
        
        for _, game in recent_games.iterrows():
            if game['home_team'] == team:
                wins += 1 if game['home_score'] > game['away_score'] else 0
            else:
                wins += 1 if game['away_score'] > game['home_score'] else 0
        
        return wins / len(recent_games)
    
    def _calculate_season_performance(self, team: str, previous_games: pd.DataFrame, season: int) -> float:
        """Calculate season performance."""
        season_games = previous_games[previous_games['season'] == season]
        team_games = season_games[(season_games['home_team'] == team) | (season_games['away_team'] == team)]
        
        if len(team_games) == 0:
            return 0.5
        
        wins = 0
        for _, game in team_games.iterrows():
            if game['home_team'] == team:
                wins += 1 if game['home_score'] > game['away_score'] else 0
            else:
                wins += 1 if game['away_score'] > game['home_score'] else 0
        
        return wins / len(team_games)
    
    def _calculate_momentum(self, team: str, previous_games: pd.DataFrame, n_games: int) -> float:
        """Calculate momentum trend over last n games."""
        team_games = previous_games[(previous_games['home_team'] == team) | (previous_games['away_team'] == team)]
        
        if len(team_games) < n_games:
            return 0.0
        
        recent_games = team_games.tail(n_games)
        wins = []
        
        for _, game in recent_games.iterrows():
            if game['home_team'] == team:
                wins.append(1 if game['home_score'] > game['away_score'] else 0)
            else:
                wins.append(1 if game['away_score'] > game['home_score'] else 0)
        
        # Calculate trend (positive = improving, negative = declining)
        if len(wins) >= 2:
            return np.polyfit(range(len(wins)), wins, 1)[0]
        else:
            return 0.0
    
    def _train_and_evaluate_advanced_models(self, X: np.ndarray, y: np.array, tscv: TimeSeriesSplit) -> Dict[str, Any]:
        """Train and evaluate advanced models with hyperparameter tuning."""
        print("\\n🚀 Training and evaluating advanced models...")
        
        # Define models with hyperparameter grids
        models = {
            'logistic_regression': {
                'model': LogisticRegression(random_state=42, max_iter=1000),
                'params': {'C': [0.01, 0.1, 1.0, 10.0], 'penalty': ['l1', 'l2']}
            },
            'random_forest': {
                'model': RandomForestClassifier(random_state=42),
                'params': {'n_estimators': [50, 100, 200], 'max_depth': [3, 5, 10], 'min_samples_split': [2, 5, 10]}
            },
            'gradient_boosting': {
                'model': GradientBoostingClassifier(random_state=42),
                'params': {'n_estimators': [50, 100, 200], 'learning_rate': [0.01, 0.1, 0.2], 'max_depth': [3, 5, 7]}
            },
            'neural_network': {
                'model': MLPClassifier(random_state=42, max_iter=1000),
                'params': {'hidden_layer_sizes': [(50,), (100,), (50, 25)], 'alpha': [0.001, 0.01, 0.1]}
            },
            'svm': {
                'model': SVC(random_state=42, probability=True),
                'params': {'C': [0.1, 1.0, 10.0], 'kernel': ['rbf', 'linear']}
            }
        }
        
        results = {}
        
        for name, model_config in models.items():
            print(f"  Training {name} with hyperparameter tuning...")
            
            # Use pipeline for scaling
            pipeline = Pipeline([
                ('scaler', RobustScaler()),
                ('model', model_config['model'])
            ])
            
            # Grid search with time series cross-validation
            grid_search = GridSearchCV(
                pipeline,
                {'model__' + k: v for k, v in model_config['params'].items()},
                cv=tscv,
                scoring='accuracy',
                n_jobs=-1,
                verbose=0
            )
            
            grid_search.fit(X, y)
            
            # Get best model
            best_model = grid_search.best_estimator_
            
            # Make predictions
            y_pred = best_model.predict(X)
            y_pred_proba = best_model.predict_proba(X)[:, 1]
            
            # Calculate metrics
            accuracy = accuracy_score(y, y_pred)
            brier = brier_score_loss(y, y_pred_proba)
            log_loss_score = log_loss(y, y_pred_proba)
            
            results[name] = {
                'model': best_model,
                'best_params': grid_search.best_params_,
                'accuracy': accuracy,
                'brier_score': brier,
                'log_loss': log_loss_score,
                'predictions': y_pred,
                'probabilities': y_pred_proba
            }
            
            print(f"    {name}: Accuracy={accuracy:.3f}, Brier={brier:.3f}, Best Params={grid_search.best_params_}")
        
        # Create ensemble model
        print("\\n  Creating ensemble model...")
        self._create_ensemble_model(results, X, y, tscv)
        
        return results
    
    def _create_ensemble_model(self, individual_results: Dict, X: np.ndarray, y: np.array, tscv: TimeSeriesSplit):
        """Create ensemble model from individual models."""
        # Get best performing models
        best_models = []
        for name, result in individual_results.items():
            if result['brier_score'] < 0.25:  # Only include good models
                best_models.append((name, result['model']))
        
        if len(best_models) < 2:
            print("    Not enough good models for ensemble")
            return
        
        # Create voting classifier
        estimators = [(name, model) for name, model in best_models]
        ensemble = VotingClassifier(estimators=estimators, voting='soft')
        
        # Train ensemble
        ensemble.fit(X, y)
        
        # Make predictions
        y_pred = ensemble.predict(X)
        y_pred_proba = ensemble.predict_proba(X)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y, y_pred)
        brier = brier_score_loss(y, y_pred_proba)
        log_loss_score = log_loss(y, y_pred_proba)
        
        individual_results['ensemble'] = {
            'model': ensemble,
            'accuracy': accuracy,
            'brier_score': brier,
            'log_loss': log_loss_score,
            'predictions': y_pred,
            'probabilities': y_pred_proba
        }
        
        print(f"    Ensemble: Accuracy={accuracy:.3f}, Brier={brier:.3f}")
    
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


def test_advanced_ml_system():
    """Test advanced ML system."""
    print("🚀 TESTING ADVANCED ML SYSTEM")
    print("="*80)
    
    # Test with recent years
    years = [2022, 2023, 2024]
    
    # Create system
    system = AdvancedMLSystem()
    
    # Run backtest
    results = system.run_advanced_backtest(years)
    
    print(f"\\n🚀 ADVANCED ML RESULTS:")
    print("-" * 50)
    
    for name, result in results.items():
        print(f"{name:20}: Accuracy={result['accuracy']:.3f}, Brier={result['brier_score']:.3f}")
    
    # Find best model
    best_model = min(results.items(), key=lambda x: x[1]['brier_score'])
    print(f"\\n🏆 Best Model: {best_model[0]} (Brier Score: {best_model[1]['brier_score']:.3f})")
    
    return system, results


if __name__ == "__main__":
    system, results = test_advanced_ml_system()
