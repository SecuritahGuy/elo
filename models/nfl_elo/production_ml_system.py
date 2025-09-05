"""Production ML system for 2025 NFL predictions."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from .ml_feature_engineering_pregame import PreGameFeatureEngineer
from .ml_models_regularized import RegularizedMLTrainer
from ingest.nfl.data_loader import load_games


class ProductionMLSystem:
    """Production-ready ML system for NFL predictions."""
    
    def __init__(self):
        """Initialize production ML system."""
        self.feature_engineer = PreGameFeatureEngineer()
        self.ml_trainer = RegularizedMLTrainer()
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
        self.ensemble_weights = {
            'elo': 0.6,
            'neural_network': 0.4,
            'random_forest': 0.0
        }
        self.is_trained = False
        self.training_years = []
    
    def train_production_system(self, years: List[int]) -> Dict[str, Any]:
        """
        Train the production system on historical data.
        
        Args:
            years: Years to use for training
            
        Returns:
            Training results
        """
        print(f"🏭 TRAINING PRODUCTION ML SYSTEM")
        print(f"Training years: {years}")
        print("="*80)
        
        # Load training data
        games = load_games(years)
        print(f"Loaded {len(games)} games for training")
        
        # 1. Create pre-game features
        print("\\n1. Creating pre-game features...")
        ml_features = self.feature_engineer.create_pregame_features(games, years)
        
        # 2. Prepare ML data
        print("\\n2. Preparing ML data...")
        X, y = self.ml_trainer.prepare_data(games, years)
        
        # 3. Train ML models
        print("\\n3. Training ML models...")
        ml_results = self.ml_trainer.train_regularized_models(X, y)
        
        # 4. Calculate Elo predictions
        print("\\n4. Calculating Elo predictions...")
        elo_predictions = self._calculate_elo_predictions(games, years)
        
        # 5. Optimize ensemble weights
        print("\\n5. Optimizing ensemble weights...")
        optimal_weights = self._optimize_ensemble_weights(ml_results, elo_predictions, y)
        self.ensemble_weights = optimal_weights
        
        # Mark as trained
        self.is_trained = True
        self.training_years = years
        
        print(f"\\n✅ Production system trained successfully!")
        print(f"Optimal ensemble weights: {self.ensemble_weights}")
        
        return {
            'ml_results': ml_results,
            'elo_predictions': elo_predictions,
            'ensemble_weights': optimal_weights,
            'training_games': len(games),
            'feature_columns': self.ml_trainer.feature_columns
        }
    
    def predict_game(self, home_team: str, away_team: str, season: int, week: int) -> Dict[str, Any]:
        """
        Predict a single game outcome.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            season: Season year
            week: Week number
            
        Returns:
            Prediction results
        """
        if not self.is_trained:
            raise ValueError("System must be trained before making predictions")
        
        # Create game data with all required columns
        game_data = pd.DataFrame({
            'season': [season],
            'week': [week],
            'home_team': [home_team],
            'away_team': [away_team],
            'home_score': [0],  # Placeholder
            'away_score': [0],  # Placeholder
            'home_rest': [7],   # Default rest
            'away_rest': [7],   # Default rest
            'gameday': [f"{season}-09-01"],  # Placeholder
            'result': [0]       # Placeholder
        })
        
        # Get predictions
        results = self._predict_games(game_data, [season])
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'season': season,
            'week': week,
            'home_win_probability': results['probabilities'][0],
            'away_win_probability': 1 - results['probabilities'][0],
            'predicted_winner': home_team if results['predictions'][0] == 1 else away_team,
            'confidence': abs(results['probabilities'][0] - 0.5) * 2,  # 0-1 scale
            'elo_probability': results['elo_predictions'][0],
            'ml_probability': results['ml_predictions'].get('neural_network', {}).get('probabilities', [0.5])[0]
        }
    
    def predict_week(self, season: int, week: int) -> List[Dict[str, Any]]:
        """
        Predict all games for a specific week.
        
        Args:
            season: Season year
            week: Week number
            
        Returns:
            List of game predictions
        """
        if not self.is_trained:
            raise ValueError("System must be trained before making predictions")
        
        # Load games for the week
        games = load_games([season])
        week_games = games[games['week'] == week]
        
        if len(week_games) == 0:
            print(f"No games found for {season} Week {week}")
            return []
        
        # Get predictions
        results = self._predict_games(week_games, [season])
        
        # Format results
        predictions = []
        for i, (_, game) in enumerate(week_games.iterrows()):
            prediction = {
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'season': season,
                'week': week,
                'home_win_probability': results['probabilities'][i],
                'away_win_probability': 1 - results['probabilities'][i],
                'predicted_winner': game['home_team'] if results['predictions'][i] == 1 else game['away_team'],
                'confidence': abs(results['probabilities'][i] - 0.5) * 2,
                'elo_probability': results['elo_predictions'][i],
                'ml_probability': results['ml_predictions'].get('neural_network', {}).get('probabilities', [0.5])[i]
            }
            predictions.append(prediction)
        
        return predictions
    
    def _predict_games(self, games: pd.DataFrame, years: List[int]) -> Dict[str, Any]:
        """Internal method to predict games."""
        # 1. Get ML predictions
        X, _ = self.ml_trainer.prepare_data(games, years)
        ml_predictions = {}
        
        for model_name in ['neural_network', 'random_forest']:
            if model_name in self.ml_trainer.models:
                pred, prob = self.ml_trainer.predict(X, model_name)
                ml_predictions[model_name] = {
                    'predictions': pred,
                    'probabilities': prob
                }
        
        # 2. Get Elo predictions
        elo_predictions = self._calculate_elo_predictions(games, years)
        
        # 3. Combine predictions
        ensemble_predictions = []
        ensemble_probabilities = []
        
        for i in range(len(games)):
            # Weighted average of predictions
            elo_prob = elo_predictions[i]
            nn_prob = ml_predictions.get('neural_network', {}).get('probabilities', [0.5])[i]
            rf_prob = ml_predictions.get('random_forest', {}).get('probabilities', [0.5])[i]
            
            ensemble_prob = (
                self.ensemble_weights['elo'] * elo_prob +
                self.ensemble_weights['neural_network'] * nn_prob +
                self.ensemble_weights['random_forest'] * rf_prob
            )
            
            ensemble_predictions.append(1 if ensemble_prob > 0.5 else 0)
            ensemble_probabilities.append(ensemble_prob)
        
        return {
            'predictions': np.array(ensemble_predictions),
            'probabilities': np.array(ensemble_probabilities),
            'elo_predictions': elo_predictions,
            'ml_predictions': ml_predictions
        }
    
    def _calculate_elo_predictions(self, games: pd.DataFrame, years: List[int]) -> np.ndarray:
        """Calculate Elo-based predictions."""
        # Run Elo backtest to get ratings
        elo_result = run_backtest(games, self.elo_config)
        
        # Calculate win probabilities from Elo ratings
        elo_predictions = []
        
        for _, game in games.iterrows():
            home_rating = elo_result.get('final_ratings', {}).get(game['home_team'], 1500)
            away_rating = elo_result.get('final_ratings', {}).get(game['away_team'], 1500)
            
            # Calculate win probability
            elo_diff = home_rating - away_rating + self.elo_config.hfa_points
            win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
            elo_predictions.append(win_prob)
        
        return np.array(elo_predictions)
    
    def _optimize_ensemble_weights(self, ml_results: Dict, elo_predictions: np.ndarray, y_true: pd.Series) -> Dict[str, float]:
        """Optimize ensemble weights using grid search."""
        # Get ML predictions
        nn_probs = ml_results['neural_network']['probabilities']
        rf_probs = ml_results['random_forest']['probabilities']
        
        # Ensure all arrays have the same length
        min_length = min(len(elo_predictions), len(nn_probs), len(rf_probs), len(y_true))
        elo_pred = elo_predictions[:min_length]
        nn_pred = nn_probs[:min_length]
        rf_pred = rf_probs[:min_length]
        y_true_trimmed = y_true.iloc[:min_length]
        
        best_score = 0
        best_weights = self.ensemble_weights.copy()
        
        # Grid search over weight combinations
        weight_ranges = np.arange(0.1, 1.0, 0.1)
        
        for elo_w in weight_ranges:
            for nn_w in weight_ranges:
                rf_w = 1.0 - elo_w - nn_w
                if rf_w < 0:
                    continue
                
                # Calculate ensemble predictions
                ensemble_pred = (
                    elo_w * elo_pred +
                    nn_w * nn_pred +
                    rf_w * rf_pred
                )
                
                # Calculate accuracy
                ensemble_binary = (ensemble_pred > 0.5).astype(int)
                accuracy = np.mean(ensemble_binary == y_true_trimmed)
                
                if accuracy > best_score:
                    best_score = accuracy
                    best_weights = {
                        'elo': elo_w,
                        'neural_network': nn_w,
                        'random_forest': rf_w
                    }
        
        print(f"Best ensemble accuracy: {best_score:.3f}")
        return best_weights
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'is_trained': self.is_trained,
            'training_years': self.training_years,
            'ensemble_weights': self.ensemble_weights,
            'feature_columns': self.ml_trainer.feature_columns if self.is_trained else [],
            'elo_config': {
                'base_rating': self.elo_config.base_rating,
                'k': self.elo_config.k,
                'hfa_points': self.elo_config.hfa_points,
                'mov_enabled': self.elo_config.mov_enabled
            }
        }


def test_production_system():
    """Test production ML system."""
    print("🏭 TESTING PRODUCTION ML SYSTEM")
    print("="*80)
    
    # Create production system
    system = ProductionMLSystem()
    
    # Train on historical data
    training_years = [2022, 2023, 2024]
    training_results = system.train_production_system(training_years)
    
    # Test single game prediction
    print("\\n🎯 Testing single game prediction...")
    prediction = system.predict_game("KC", "BUF", 2025, 1)
    print(f"Prediction: {prediction['home_team']} vs {prediction['away_team']}")
    print(f"Winner: {prediction['predicted_winner']}")
    print(f"Home Win Probability: {prediction['home_win_probability']:.3f}")
    print(f"Confidence: {prediction['confidence']:.3f}")
    
    # Test week prediction
    print("\\n📅 Testing week prediction...")
    week_predictions = system.predict_week(2025, 1)
    print(f"Found {len(week_predictions)} games for 2025 Week 1")
    
    # Show system status
    print("\\n📊 System Status:")
    status = system.get_system_status()
    print(f"Trained: {status['is_trained']}")
    print(f"Training Years: {status['training_years']}")
    print(f"Ensemble Weights: {status['ensemble_weights']}")
    
    return system, training_results


if __name__ == "__main__":
    system, results = test_production_system()
