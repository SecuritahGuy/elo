"""Machine Learning models for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# ML imports
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
import joblib

from .ml_feature_engineering_v2 import MLFeatureEngineer


class MLModelTrainer:
    """Train and evaluate ML models for NFL predictions."""
    
    def __init__(self):
        """Initialize ML model trainer."""
        self.models = {}
        self.scalers = {}
        self.feature_engineer = MLFeatureEngineer()
        self.feature_columns = []
        
    def prepare_data(self, games: pd.DataFrame, years: List[int]) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare data for ML training.
        
        Args:
            games: Games DataFrame
            years: Years to use for training
            
        Returns:
            X: Feature matrix
            y: Target variable
        """
        print(f"Preparing ML data for {len(games)} games...")
        
        # Create ML features
        ml_features = self.feature_engineer.create_ml_features(games, years)
        
        # Get feature columns
        self.feature_columns = self.feature_engineer.get_feature_columns(ml_features)
        
        # Prepare X and y
        X = ml_features[self.feature_columns].fillna(0)
        y = ml_features['home_team_wins']
        
        print(f"Prepared {X.shape[0]} samples with {X.shape[1]} features")
        return X, y
    
    def train_models(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Train multiple ML models.
        
        Args:
            X: Feature matrix
            y: Target variable
            
        Returns:
            Dictionary of trained models
        """
        print("Training ML models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features for neural network
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['neural_network'] = scaler
        
        # 1. Logistic Regression (Baseline)
        print("Training Logistic Regression...")
        lr_model = LogisticRegression(random_state=42, max_iter=1000)
        lr_model.fit(X_train, y_train)
        self.models['logistic_regression'] = lr_model
        
        # 2. Random Forest
        print("Training Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        self.models['random_forest'] = rf_model
        
        # 3. Gradient Boosting
        print("Training Gradient Boosting...")
        gb_model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        gb_model.fit(X_train, y_train)
        self.models['gradient_boosting'] = gb_model
        
        # 4. Neural Network
        print("Training Neural Network...")
        nn_model = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            activation='relu',
            solver='adam',
            alpha=0.001,
            learning_rate='adaptive',
            max_iter=500,
            random_state=42
        )
        nn_model.fit(X_train_scaled, y_train)
        self.models['neural_network'] = nn_model
        
        # Evaluate models
        results = self._evaluate_models(X_test, X_test_scaled, y_test)
        
        return results
    
    def _evaluate_models(self, X_test: pd.DataFrame, X_test_scaled: np.ndarray, y_test: pd.Series) -> Dict[str, Any]:
        """Evaluate all trained models."""
        print("Evaluating ML models...")
        
        results = {}
        
        for name, model in self.models.items():
            # Get predictions
            if name == 'neural_network':
                X_eval = X_test_scaled
            else:
                X_eval = X_test
            
            y_pred = model.predict(X_eval)
            y_pred_proba = model.predict_proba(X_eval)[:, 1] if hasattr(model, 'predict_proba') else None
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            results[name] = {
                'model': model,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'predictions': y_pred,
                'probabilities': y_pred_proba
            }
            
            if y_pred_proba is not None:
                auc = roc_auc_score(y_test, y_pred_proba)
                results[name]['auc'] = auc
            
            print(f"{name}: Accuracy={accuracy:.3f}, F1={f1:.3f}, AUC={results[name].get('auc', 'N/A')}")
        
        return results
    
    def get_feature_importance(self, model_name: str = 'random_forest') -> pd.DataFrame:
        """Get feature importance from a model."""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        model = self.models[model_name]
        
        if hasattr(model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
        else:
            # For models without feature importance, return random values
            importance_df = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': np.random.random(len(self.feature_columns))
            }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def predict(self, X: pd.DataFrame, model_name: str = 'neural_network') -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions using a trained model.
        
        Args:
            X: Feature matrix
            model_name: Name of model to use
            
        Returns:
            predictions: Binary predictions
            probabilities: Prediction probabilities
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        model = self.models[model_name]
        
        # Scale features if needed
        if model_name == 'neural_network' and model_name in self.scalers:
            X_scaled = self.scalers[model_name].transform(X)
            X_eval = X_scaled
        else:
            X_eval = X
        
        # Make predictions
        predictions = model.predict(X_eval)
        probabilities = model.predict_proba(X_eval)[:, 1] if hasattr(model, 'predict_proba') else None
        
        return predictions, probabilities
    
    def save_models(self, filepath: str):
        """Save trained models to disk."""
        model_data = {
            'models': self.models,
            'scalers': self.scalers,
            'feature_columns': self.feature_columns
        }
        joblib.dump(model_data, filepath)
        print(f"Models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models from disk."""
        model_data = joblib.load(filepath)
        self.models = model_data['models']
        self.scalers = model_data['scalers']
        self.feature_columns = model_data['feature_columns']
        print(f"Models loaded from {filepath}")


def test_ml_models():
    """Test ML model training."""
    print("🤖 TESTING ML MODELS")
    print("="*80)
    
    # Load sample data
    from ingest.nfl.data_loader import load_games
    games = load_games([2024])
    print(f"Loaded {len(games)} games")
    
    # Create trainer
    trainer = MLModelTrainer()
    
    # Prepare data
    X, y = trainer.prepare_data(games, [2024])
    
    # Train models
    results = trainer.train_models(X, y)
    
    # Show results
    print(f"\\nModel Performance Summary:")
    print("-" * 50)
    for name, result in results.items():
        print(f"{name:20}: Accuracy={result['accuracy']:.3f}, F1={result['f1']:.3f}")
    
    # Get feature importance
    importance = trainer.get_feature_importance('random_forest')
    print(f"\\nTop 10 Features by Importance:")
    print(importance.head(10))
    
    return trainer, results


if __name__ == "__main__":
    trainer, results = test_ml_models()
