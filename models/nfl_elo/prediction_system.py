"""Prediction system for NFL Elo ratings - 2025 season ready."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from .evaluator import calculate_all_metrics
from .injury_integration import InjuryImpactCalculator
from ingest.nfl.data_loader import load_games


class NFLPredictionSystem:
    """NFL prediction system with current Elo ratings and 2025 readiness."""
    
    def __init__(self, training_years: List[int] = [2019, 2021, 2022, 2023, 2024]):
        """
        Initialize prediction system.
        
        Args:
            training_years: Years to use for training (excluding 2020 COVID season)
        """
        self.training_years = training_years
        self.games = None
        self.injuries = None
        self.team_injury_df = None
        self.games_with_injuries = None
        self.final_ratings = None
        self.injury_calculator = InjuryImpactCalculator()
        
        # Load training data
        self._load_training_data()
        self._train_system()
    
    def _load_training_data(self):
        """Load training data for the system."""
        print("Loading training data for prediction system...")
        
        # Load games
        self.games = load_games(self.training_years)
        print(f"Loaded {len(self.games)} training games")
        
        # Load injury data
        self.injuries = self.injury_calculator.load_injury_data(self.training_years)
        print(f"Loaded {len(self.injuries)} injury records")
        
        # Create team injury database
        self.team_injury_df = self.injury_calculator.create_team_injury_database(self.injuries)
        
        # Add injury data to games
        self.games_with_injuries = self.injury_calculator.add_injury_data_to_games(
            self.games, self.team_injury_df
        )
        print(f"Added injury data to {len(self.games_with_injuries)} games")
    
    def _train_system(self):
        """Train the system to get final Elo ratings."""
        print("Training prediction system...")
        
        # Use optimal configuration based on our analysis
        config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=False  # Disabled based on analysis
        )
        
        # Run backtest to get final ratings
        result = run_backtest(self.games_with_injuries, config)
        self.final_ratings = result['final_ratings']
        
        print(f"System trained with final ratings for {len(self.final_ratings)} teams")
        
        # Show top and bottom teams
        sorted_ratings = sorted(self.final_ratings.items(), key=lambda x: x[1], reverse=True)
        print(f"\\nTop 5 teams:")
        for i, (team, rating) in enumerate(sorted_ratings[:5]):
            print(f"  {i+1}. {team}: {rating:.1f}")
        
        print(f"\\nBottom 5 teams:")
        for i, (team, rating) in enumerate(sorted_ratings[-5:]):
            print(f"  {i+1}. {team}: {rating:.1f}")
    
    def predict_game(self, home_team: str, away_team: str, 
                    home_rest_days: Optional[float] = None,
                    away_rest_days: Optional[float] = None) -> Dict[str, Any]:
        """
        Predict the outcome of a single game.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            home_rest_days: Home team rest days (optional)
            away_rest_days: Away team rest days (optional)
            
        Returns:
            Dictionary with prediction details
        """
        if self.final_ratings is None:
            raise ValueError("System not trained yet. Call _train_system() first.")
        
        # Get team ratings
        home_rating = self.final_ratings.get(home_team, 1500.0)
        away_rating = self.final_ratings.get(away_team, 1500.0)
        
        # Calculate home field advantage
        hfa = 55.0  # From config
        
        # Calculate rest advantage
        rest_advantage = 0.0
        if home_rest_days is not None and away_rest_days is not None:
            rest_advantage = (home_rest_days - away_rest_days) * 1.0  # 1 point per day
        
        # Calculate expected win probability
        from .updater import logistic_expectation
        adjusted_home = home_rating + hfa + rest_advantage
        adjusted_away = away_rating
        
        p_home = logistic_expectation(adjusted_home, adjusted_away, 400.0)
        p_away = 1.0 - p_home
        
        # Calculate expected margin
        expected_margin = (adjusted_home - adjusted_away) / 25.0  # Rough conversion to points
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_rating': home_rating,
            'away_rating': away_rating,
            'home_win_probability': p_home,
            'away_win_probability': p_away,
            'expected_margin': expected_margin,
            'home_rest_days': home_rest_days,
            'away_rest_days': away_rest_days,
            'rest_advantage': rest_advantage,
            'prediction': home_team if p_home > 0.5 else away_team,
            'confidence': abs(p_home - 0.5) * 2  # 0-1 scale
        }
    
    def predict_week(self, week: int, season: int = 2025) -> List[Dict[str, Any]]:
        """
        Predict all games for a specific week.
        
        Args:
            week: Week number
            season: Season year (default 2025)
            
        Returns:
            List of game predictions
        """
        print(f"Predicting Week {week} of {season} season...")
        
        # Load schedule for the week
        try:
            schedule = load_games([season])
            week_games = schedule[schedule['week'] == week]
            
            if len(week_games) == 0:
                print(f"No games found for Week {week} of {season}")
                return []
            
            predictions = []
            for _, game in week_games.iterrows():
                home_team = game['home_team']
                away_team = game['away_team']
                
                # Calculate rest days (simplified - would need actual game dates)
                home_rest_days = 7.0  # Default to 7 days
                away_rest_days = 7.0  # Default to 7 days
                
                prediction = self.predict_game(
                    home_team, away_team, 
                    home_rest_days, away_rest_days
                )
                predictions.append(prediction)
            
            return predictions
            
        except Exception as e:
            print(f"Error loading schedule for Week {week}: {e}")
            return []
    
    def get_team_rankings(self) -> List[Dict[str, Any]]:
        """Get current team rankings."""
        if self.final_ratings is None:
            return []
        
        sorted_ratings = sorted(self.final_ratings.items(), key=lambda x: x[1], reverse=True)
        
        rankings = []
        for rank, (team, rating) in enumerate(sorted_ratings, 1):
            rankings.append({
                'rank': rank,
                'team': team,
                'rating': rating,
                'tier': self._get_team_tier(rating)
            })
        
        return rankings
    
    def _get_team_tier(self, rating: float) -> str:
        """Get team tier based on rating."""
        if rating > 1600:
            return "Elite"
        elif rating > 1500:
            return "Strong"
        elif rating > 1400:
            return "Average"
        else:
            return "Weak"
    
    def track_prediction_accuracy(self, predictions: List[Dict], actual_results: List[Dict]) -> Dict[str, Any]:
        """
        Track prediction accuracy.
        
        Args:
            predictions: List of predictions
            actual_results: List of actual results
            
        Returns:
            Dictionary with accuracy metrics
        """
        if len(predictions) != len(actual_results):
            raise ValueError("Predictions and results must have same length")
        
        correct_predictions = 0
        total_predictions = len(predictions)
        
        for pred, actual in zip(predictions, actual_results):
            if pred['prediction'] == actual['winner']:
                correct_predictions += 1
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
        
        return {
            'total_predictions': total_predictions,
            'correct_predictions': correct_predictions,
            'accuracy': accuracy,
            'accuracy_percentage': accuracy * 100
        }


def test_prediction_system():
    """Test the prediction system."""
    print("🏈 TESTING NFL PREDICTION SYSTEM")
    print("="*80)
    
    # Initialize system
    system = NFLPredictionSystem()
    
    # Test individual game prediction
    print("\\nTesting individual game prediction...")
    prediction = system.predict_game("KC", "BUF", home_rest_days=7.0, away_rest_days=6.0)
    
    print(f"Game: {prediction['away_team']} @ {prediction['home_team']}")
    print(f"Home Win Probability: {prediction['home_win_probability']:.3f}")
    print(f"Away Win Probability: {prediction['away_win_probability']:.3f}")
    print(f"Expected Margin: {prediction['expected_margin']:+.1f} points")
    print(f"Prediction: {prediction['prediction']} wins")
    print(f"Confidence: {prediction['confidence']:.3f}")
    
    # Test team rankings
    print("\\nCurrent Team Rankings:")
    rankings = system.get_team_rankings()
    for team in rankings[:10]:  # Top 10
        print(f"  {team['rank']:2d}. {team['team']:3s} - {team['rating']:6.1f} ({team['tier']})")
    
    # Test week prediction
    print("\\nTesting Week 1 prediction for 2025...")
    week1_predictions = system.predict_week(1, 2025)
    
    if week1_predictions:
        print(f"Found {len(week1_predictions)} games for Week 1, 2025:")
        for pred in week1_predictions[:5]:  # Show first 5
            print(f"  {pred['away_team']} @ {pred['home_team']}: {pred['home_win_probability']:.3f}")
    else:
        print("No games found for Week 1, 2025")
    
    return system


if __name__ == "__main__":
    system = test_prediction_system()
