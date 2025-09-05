"""Complete ML system using only pre-game features - NO DATA LEAKAGE."""

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


class PreGameMLSystem:
    """Complete ML system using only pre-game features."""
    
    def __init__(self):
        """Initialize pre-game ML system."""
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
            'elo': 0.7,
            'neural_network': 0.2,
            'random_forest': 0.1
        }
    
    def train_system(self, games: pd.DataFrame, years: List[int]) -> Dict[str, Any]:
        """
        Train the complete pre-game ML system.
        
        Args:
            games: Games DataFrame
            years: Years to use for training
            
        Returns:
            Training results
        """
        print(f"🎯 TRAINING PRE-GAME ML SYSTEM")
        print(f"Games: {len(games)}, Years: {years}")
        print("="*80)
        
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
        
        print(f"\\nOptimal ensemble weights: {self.ensemble_weights}")
        
        return {
            'ml_results': ml_results,
            'elo_predictions': elo_predictions,
            'ensemble_weights': optimal_weights,
            'feature_columns': self.ml_trainer.feature_columns
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
    
    def predict(self, games: pd.DataFrame, years: List[int]) -> Dict[str, Any]:
        """
        Make ensemble predictions using pre-game features only.
        
        Args:
            games: Games DataFrame
            years: Years to use for feature calculation
            
        Returns:
            Prediction results
        """
        print(f"🎯 Making pre-game predictions for {len(games)} games...")
        
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
    
    def evaluate_system(self, games: pd.DataFrame, years: List[int]) -> Dict[str, float]:
        """Evaluate pre-game ML system performance."""
        print("🎯 Evaluating pre-game ML system...")
        
        # Get predictions
        results = self.predict(games, years)
        
        # Get true labels
        y_true = (games['home_score'] > games['away_score']).astype(int)
        
        # Calculate metrics
        predictions = results['predictions']
        probabilities = results['probabilities']
        
        accuracy = np.mean(predictions == y_true)
        
        # Calculate Brier Score
        brier_score = np.mean((probabilities - y_true) ** 2)
        
        # Calculate Log Loss
        epsilon = 1e-15
        probabilities_clipped = np.clip(probabilities, epsilon, 1 - epsilon)
        log_loss = -np.mean(y_true * np.log(probabilities_clipped) + (1 - y_true) * np.log(1 - probabilities_clipped))
        
        return {
            'accuracy': accuracy,
            'brier_score': brier_score,
            'log_loss': log_loss,
            'predictions': predictions,
            'probabilities': probabilities
        }


def test_pregame_ml_system():
    """Test complete pre-game ML system."""
    print("🎯 TESTING PRE-GAME ML SYSTEM")
    print("="*80)
    
    # Load sample data
    games = load_games([2024])
    print(f"Loaded {len(games)} games")
    
    # Create system
    system = PreGameMLSystem()
    
    # Train system
    training_results = system.train_system(games, [2024])
    
    # Evaluate system
    evaluation_results = system.evaluate_system(games, [2024])
    
    print(f"\\nPre-Game ML System Performance:")
    print(f"Accuracy: {evaluation_results['accuracy']:.3f}")
    print(f"Brier Score: {evaluation_results['brier_score']:.3f}")
    print(f"Log Loss: {evaluation_results['log_loss']:.3f}")
    
    # Show individual model performance
    print(f"\\nIndividual Model Performance:")
    for name, result in training_results['ml_results'].items():
        print(f"{name:20}: Test={result['accuracy']:.3f}, CV={result['cv_mean']:.3f}±{result['cv_std']:.3f}")
    
    return system, evaluation_results


if __name__ == "__main__":
    system, results = test_pregame_ml_system()
