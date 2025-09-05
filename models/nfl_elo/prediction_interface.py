"""Production prediction interface for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from ingest.nfl.data_loader import load_games


class NFLPredictionInterface:
    """Production-ready prediction interface for NFL Elo system."""
    
    def __init__(self, config: Optional[EloConfig] = None):
        """
        Initialize prediction interface.
        
        Args:
            config: Elo configuration (uses production config if None)
        """
        if config is None:
            # Use production configuration
            self.config = EloConfig(
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
                use_situational_adjustment=False
            )
        else:
            self.config = config
        
        self.team_ratings = None
        self.last_updated = None
    
    def load_team_ratings(self, years: List[int] = [2019, 2021, 2022, 2023, 2024]) -> None:
        """
        Load and calculate current team ratings.
        
        Args:
            years: Years to use for rating calculation
        """
        print(f"Loading team ratings for years {years}...")
        
        # Load games data
        games = load_games(years)
        print(f"Loaded {len(games)} games")
        
        # Run backtest to get final ratings
        result = run_backtest(games, self.config)
        
        # Extract final team ratings
        if 'final_ratings' in result:
            self.team_ratings = result['final_ratings']
        else:
            # Fallback: create empty ratings
            self.team_ratings = {}
        
        self.last_updated = datetime.now()
        print(f"Team ratings loaded for {len(self.team_ratings)} teams")
    
    def predict_game(self, home_team: str, away_team: str, 
                    home_rating: Optional[float] = None, 
                    away_rating: Optional[float] = None) -> Dict[str, Any]:
        """
        Predict the outcome of a game.
        
        Args:
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            home_rating: Home team rating (uses current rating if None)
            away_rating: Away team rating (uses current rating if None)
            
        Returns:
            Dictionary with prediction details
        """
        if self.team_ratings is None:
            raise ValueError("Team ratings not loaded. Call load_team_ratings() first.")
        
        # Get team ratings
        if home_rating is None:
            home_rating = self.team_ratings.get(home_team, self.config.base_rating)
        if away_rating is None:
            away_rating = self.team_ratings.get(away_team, self.config.base_rating)
        
        # Calculate win probability
        from .updater import logistic_expectation
        p_home = logistic_expectation(home_rating, away_rating, self.config.scale)
        
        # Calculate expected margin
        expected_margin = (home_rating - away_rating) / self.config.scale * 100
        
        # Determine prediction
        predicted_winner = home_team if p_home > 0.5 else away_team
        confidence = max(p_home, 1 - p_home)
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_rating': home_rating,
            'away_rating': away_rating,
            'home_win_probability': p_home,
            'away_win_probability': 1 - p_home,
            'predicted_winner': predicted_winner,
            'confidence': confidence,
            'expected_margin': expected_margin,
            'prediction_timestamp': datetime.now().isoformat()
        }
    
    def predict_week(self, games: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """
        Predict outcomes for a week of games.
        
        Args:
            games: List of (home_team, away_team) tuples
            
        Returns:
            List of prediction dictionaries
        """
        predictions = []
        
        for home_team, away_team in games:
            prediction = self.predict_game(home_team, away_team)
            predictions.append(prediction)
        
        return predictions
    
    def get_team_rankings(self) -> pd.DataFrame:
        """
        Get current team rankings.
        
        Returns:
            DataFrame with team rankings
        """
        if self.team_ratings is None:
            raise ValueError("Team ratings not loaded. Call load_team_ratings() first.")
        
        # Create rankings DataFrame
        rankings_data = []
        for team, rating in self.team_ratings.items():
            rankings_data.append({
                'team': team,
                'rating': rating,
                'last_updated': self.last_updated.isoformat() if self.last_updated else None
            })
        
        rankings_df = pd.DataFrame(rankings_data)
        rankings_df = rankings_df.sort_values('rating', ascending=False).reset_index(drop=True)
        rankings_df['rank'] = range(1, len(rankings_df) + 1)
        
        return rankings_df[['rank', 'team', 'rating', 'last_updated']]
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status.
        
        Returns:
            Dictionary with system status
        """
        return {
            'config': {
                'base_rating': self.config.base_rating,
                'k': self.config.k,
                'hfa_points': self.config.hfa_points,
                'mov_enabled': self.config.mov_enabled,
                'preseason_regress': self.config.preseason_regress,
                'travel_enabled': self.config.use_travel_adjustment,
                'qb_enabled': self.config.use_qb_adjustment,
                'weather_enabled': self.config.use_weather_adjustment,
                'injury_enabled': self.config.use_injury_adjustment,
                'redzone_enabled': self.config.use_redzone_adjustment,
                'downs_enabled': self.config.use_downs_adjustment,
                'clock_management_enabled': self.config.use_clock_management_adjustment,
                'situational_enabled': self.config.use_situational_adjustment
            },
            'team_ratings_loaded': self.team_ratings is not None,
            'num_teams': len(self.team_ratings) if self.team_ratings else 0,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'status': 'READY' if self.team_ratings is not None else 'NOT_LOADED'
        }


def test_prediction_interface():
    """Test the prediction interface."""
    print("📊 TESTING PREDICTION INTERFACE")
    print("="*80)
    
    # Create prediction interface
    interface = NFLPredictionInterface()
    
    # Load team ratings
    interface.load_team_ratings()
    
    # Test single game prediction
    print("\\nTesting single game prediction...")
    prediction = interface.predict_game("KC", "BUF")
    print(f"KC vs BUF prediction:")
    print(f"  Home win probability: {prediction['home_win_probability']:.3f}")
    print(f"  Predicted winner: {prediction['predicted_winner']}")
    print(f"  Confidence: {prediction['confidence']:.3f}")
    print(f"  Expected margin: {prediction['expected_margin']:.1f} points")
    
    # Test week predictions
    print("\\nTesting week predictions...")
    week_games = [
        ("KC", "BUF"),
        ("TB", "GB"),
        ("SF", "DET"),
        ("BAL", "CIN")
    ]
    
    week_predictions = interface.predict_week(week_games)
    print(f"\\nWeek predictions:")
    for pred in week_predictions:
        print(f"  {pred['home_team']} vs {pred['away_team']}: {pred['predicted_winner']} ({pred['confidence']:.3f})")
    
    # Test team rankings
    print("\\nTesting team rankings...")
    rankings = interface.get_team_rankings()
    print(f"\\nTop 10 teams:")
    print(rankings.head(10).to_string(index=False))
    
    # Test system status
    print("\\nTesting system status...")
    status = interface.get_system_status()
    print(f"System status: {status['status']}")
    print(f"Teams loaded: {status['num_teams']}")
    print(f"Last updated: {status['last_updated']}")
    
    return interface


if __name__ == "__main__":
    interface = test_prediction_interface()
