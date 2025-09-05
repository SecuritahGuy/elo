"""Rigorous ML validation system to detect and prevent data leakage."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit

from .config import EloConfig
from ingest.nfl.data_loader import load_games


class RigorousMLValidation:
    """Rigorous ML validation system to detect data leakage."""
    
    def __init__(self):
        """Initialize rigorous validation system."""
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
    
    def run_rigorous_validation(self, years: List[int]) -> Dict[str, Any]:
        """
        Run rigorous validation to detect data leakage.
        
        Args:
            years: Years to test
            
        Returns:
            Validation results
        """
        print(f"🔍 RIGOROUS ML VALIDATION - DATA LEAKAGE DETECTION")
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
        
        # Test different validation approaches
        results = {}
        
        # 1. Simple Elo baseline
        print("\\n1. Testing Simple Elo Baseline...")
        elo_results = self._test_elo_baseline(all_games)
        results['elo_baseline'] = elo_results
        
        # 2. Simple ML with minimal features
        print("\\n2. Testing Simple ML with Minimal Features...")
        simple_ml_results = self._test_simple_ml(all_games)
        results['simple_ml'] = simple_ml_results
        
        # 3. ML with more features (potential leakage)
        print("\\n3. Testing ML with More Features (Potential Leakage)...")
        complex_ml_results = self._test_complex_ml(all_games)
        results['complex_ml'] = complex_ml_results
        
        # 4. Analyze results for data leakage
        print("\\n4. Analyzing Results for Data Leakage...")
        leakage_analysis = self._analyze_data_leakage(results)
        results['leakage_analysis'] = leakage_analysis
        
        return results
    
    def _test_elo_baseline(self, all_games: pd.DataFrame) -> Dict[str, Any]:
        """Test simple Elo baseline."""
        predictions = []
        actual_outcomes = []
        probabilities = []
        
        for i, game in all_games.iterrows():
            if i < 50:  # Need minimum games for feature calculation
                self._update_ratings(game)
                continue
            
            # Make prediction using current ratings
            prediction, probability = self._make_elo_prediction(game)
            
            predictions.append(prediction)
            actual_outcomes.append(1 if game['home_score'] > game['away_score'] else 0)
            probabilities.append(probability)
            
            # Update ratings after game
            self._update_ratings(game)
        
        # Calculate metrics
        predictions = np.array(predictions)
        actual_outcomes = np.array(actual_outcomes)
        probabilities = np.array(probabilities)
        
        accuracy = np.mean(predictions == actual_outcomes)
        brier = brier_score_loss(actual_outcomes, probabilities)
        log_loss_score = log_loss(actual_outcomes, probabilities)
        
        return {
            'accuracy': accuracy,
            'brier_score': brier,
            'log_loss': log_loss_score,
            'total_games': len(predictions)
        }
    
    def _test_simple_ml(self, all_games: pd.DataFrame) -> Dict[str, Any]:
        """Test simple ML with minimal features."""
        features_list = []
        targets = []
        
        for i, game in all_games.iterrows():
            if i < 50:  # Need minimum games for feature calculation
                self._update_ratings(game)
                continue
            
            # Create minimal features
            features = self._create_minimal_features(game, all_games.iloc[:i])
            
            if features is not None:
                features_list.append(features)
                targets.append(1 if game['home_score'] > game['away_score'] else 0)
            
            # Update ratings after game
            self._update_ratings(game)
        
        if len(features_list) == 0:
            return {'error': 'No features created'}
        
        # Convert to arrays
        X = np.array(features_list)
        y = np.array(targets)
        
        # Train simple model
        model = LogisticRegression(random_state=42, max_iter=1000, C=0.1)
        model.fit(X, y)
        
        # Make predictions
        y_pred = model.predict(X)
        y_pred_proba = model.predict_proba(X)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y, y_pred)
        brier = brier_score_loss(y, y_pred_proba)
        log_loss_score = log_loss(y, y_pred_proba)
        
        return {
            'accuracy': accuracy,
            'brier_score': brier,
            'log_loss': log_loss_score,
            'total_games': len(y),
            'features': X.shape[1]
        }
    
    def _test_complex_ml(self, all_games: pd.DataFrame) -> Dict[str, Any]:
        """Test complex ML with more features (potential leakage)."""
        features_list = []
        targets = []
        
        for i, game in all_games.iterrows():
            if i < 50:  # Need minimum games for feature calculation
                self._update_ratings(game)
                continue
            
            # Create complex features
            features = self._create_complex_features(game, all_games.iloc[:i])
            
            if features is not None:
                features_list.append(features)
                targets.append(1 if game['home_score'] > game['away_score'] else 0)
            
            # Update ratings after game
            self._update_ratings(game)
        
        if len(features_list) == 0:
            return {'error': 'No features created'}
        
        # Convert to arrays
        X = np.array(features_list)
        y = np.array(targets)
        
        # Train complex model
        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        model.fit(X, y)
        
        # Make predictions
        y_pred = model.predict(X)
        y_pred_proba = model.predict_proba(X)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y, y_pred)
        brier = brier_score_loss(y, y_pred_proba)
        log_loss_score = log_loss(y, y_pred_proba)
        
        return {
            'accuracy': accuracy,
            'brier_score': brier,
            'log_loss': log_loss_score,
            'total_games': len(y),
            'features': X.shape[1]
        }
    
    def _create_minimal_features(self, game: pd.Series, previous_games: pd.DataFrame) -> Optional[np.ndarray]:
        """Create minimal features (no leakage)."""
        try:
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Only Elo features
            home_rating = self.team_ratings.get(home_team, 1500.0)
            away_rating = self.team_ratings.get(away_team, 1500.0)
            elo_diff = home_rating - away_rating + self.elo_config.hfa_points
            
            return np.array([home_rating, away_rating, elo_diff])
            
        except Exception as e:
            return None
    
    def _create_complex_features(self, game: pd.Series, previous_games: pd.DataFrame) -> Optional[np.ndarray]:
        """Create complex features (potential leakage)."""
        try:
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Elo features
            home_rating = self.team_ratings.get(home_team, 1500.0)
            away_rating = self.team_ratings.get(away_team, 1500.0)
            elo_diff = home_rating - away_rating + self.elo_config.hfa_points
            
            # Team stats (potential leakage)
            home_stats = self._calculate_team_stats(home_team, previous_games)
            away_stats = self._calculate_team_stats(away_team, previous_games)
            
            # Situational features
            week = game['week']
            season_progress = week / 18.0
            
            return np.array([
                home_rating, away_rating, elo_diff,
                home_stats['off_ppg'], home_stats['def_ppg'], home_stats['win_pct'],
                away_stats['off_ppg'], away_stats['def_ppg'], away_stats['win_pct'],
                season_progress
            ])
            
        except Exception as e:
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
    
    def _make_elo_prediction(self, game: pd.Series) -> Tuple[int, float]:
        """Make Elo prediction."""
        home_team = game['home_team']
        away_team = game['away_team']
        
        home_rating = self.team_ratings.get(home_team, 1500.0)
        away_rating = self.team_ratings.get(away_team, 1500.0)
        
        elo_diff = home_rating - away_rating + self.elo_config.hfa_points
        win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        prediction = 1 if win_prob > 0.5 else 0
        
        return prediction, win_prob
    
    def _update_ratings(self, game: pd.Series):
        """Update Elo ratings after game."""
        home_team = game['home_team']
        away_team = game['away_team']
        home_score = game['home_score']
        away_score = game['away_score']
        
        home_rating = self.team_ratings.get(home_team, self.elo_config.base_rating)
        away_rating = self.team_ratings.get(away_team, self.elo_config.base_rating)
        
        elo_diff = home_rating - away_rating + self.elo_config.hfa_points
        expected_home = 1 / (1 + 10 ** (-elo_diff / 400))
        expected_away = 1 - expected_home
        
        actual_home = 1 if home_score > away_score else 0
        actual_away = 1 - actual_home
        
        if self.elo_config.mov_enabled:
            margin = abs(home_score - away_score)
            mov_multiplier = np.log(margin + 1) * (2.2 / (0.001 * (home_rating - away_rating) + 2.2))
        else:
            mov_multiplier = 1.0
        
        k_factor = self.elo_config.k * mov_multiplier
        
        home_change = k_factor * (actual_home - expected_home)
        away_change = k_factor * (actual_away - expected_away)
        
        self.team_ratings[home_team] = home_rating + home_change
        self.team_ratings[away_team] = away_rating + away_change
    
    def _analyze_data_leakage(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze results for data leakage indicators."""
        analysis = {
            'suspicious_metrics': [],
            'leakage_indicators': [],
            'recommendations': []
        }
        
        # Check for suspicious accuracy
        for name, result in results.items():
            if 'accuracy' in result:
                accuracy = result['accuracy']
                if accuracy > 0.75:
                    analysis['suspicious_metrics'].append(f"{name}: {accuracy:.3f} accuracy seems too high")
                elif accuracy > 0.70:
                    analysis['leakage_indicators'].append(f"{name}: {accuracy:.3f} accuracy is suspicious")
        
        # Compare simple vs complex ML
        if 'simple_ml' in results and 'complex_ml' in results:
            simple_acc = results['simple_ml'].get('accuracy', 0)
            complex_acc = results['complex_ml'].get('accuracy', 0)
            
            if complex_acc - simple_acc > 0.05:
                analysis['leakage_indicators'].append(f"Complex ML ({complex_acc:.3f}) significantly better than simple ML ({simple_acc:.3f}) - possible leakage")
        
        # Generate recommendations
        if analysis['suspicious_metrics']:
            analysis['recommendations'].append("Investigate suspiciously high accuracy metrics")
        
        if analysis['leakage_indicators']:
            analysis['recommendations'].append("Check for data leakage in complex features")
        
        if not analysis['suspicious_metrics'] and not analysis['leakage_indicators']:
            analysis['recommendations'].append("Results look reasonable - no obvious data leakage detected")
        
        return analysis


def test_rigorous_validation():
    """Test rigorous validation system."""
    print("🔍 TESTING RIGOROUS ML VALIDATION")
    print("="*80)
    
    # Test with recent years
    years = [2022, 2023, 2024]
    
    # Create system
    system = RigorousMLValidation()
    
    # Run validation
    results = system.run_rigorous_validation(years)
    
    print(f"\\n🔍 RIGOROUS VALIDATION RESULTS:")
    print("-" * 50)
    
    for name, result in results.items():
        if name == 'leakage_analysis':
            continue
        
        if 'error' in result:
            print(f"{name:20}: {result['error']}")
        else:
            print(f"{name:20}: Accuracy={result['accuracy']:.3f}, Brier={result['brier_score']:.3f}")
    
    # Show leakage analysis
    if 'leakage_analysis' in results:
        analysis = results['leakage_analysis']
        print(f"\\n🔍 DATA LEAKAGE ANALYSIS:")
        print("-" * 50)
        
        if analysis['suspicious_metrics']:
            print("⚠️  SUSPICIOUS METRICS:")
            for metric in analysis['suspicious_metrics']:
                print(f"  - {metric}")
        
        if analysis['leakage_indicators']:
            print("\\n⚠️  LEAKAGE INDICATORS:")
            for indicator in analysis['leakage_indicators']:
                print(f"  - {indicator}")
        
        if analysis['recommendations']:
            print("\\n💡 RECOMMENDATIONS:")
            for rec in analysis['recommendations']:
                print(f"  - {rec}")
    
    return system, results


if __name__ == "__main__":
    system, results = test_rigorous_validation()
