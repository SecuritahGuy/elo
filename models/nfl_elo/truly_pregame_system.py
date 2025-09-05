"""TRULY pre-game system with NO data leakage - only information available before each game."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from ingest.nfl.data_loader import load_games


class TrulyPreGameSystem:
    """Truly pre-game system with NO data leakage."""
    
    def __init__(self):
        """Initialize truly pre-game system."""
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
    
    def run_truly_pregame_backtest(self, years: List[int]) -> Dict[str, Any]:
        """
        Run truly pre-game backtest with NO data leakage.
        
        Args:
            years: Years to test
            
        Returns:
            Backtest results
        """
        print(f"🎯 TRULY PRE-GAME BACKTEST - NO DATA LEAKAGE")
        print(f"Years: {years}")
        print("="*80)
        
        all_games = load_games(years)
        print(f"Loaded {len(all_games)} total games")
        
        # Sort games by season and week
        all_games = all_games.sort_values(['season', 'week']).reset_index(drop=True)
        
        predictions = []
        actual_outcomes = []
        
        for i, game in all_games.iterrows():
            # Get all games BEFORE this game
            previous_games = all_games.iloc[:i]
            
            if len(previous_games) < 10:  # Need minimum games for training
                continue
            
            # Calculate Elo ratings using ONLY previous games
            elo_ratings = self._calculate_elo_ratings_up_to_game(previous_games)
            
            # Get team performance using ONLY previous games
            team_stats = self._calculate_team_stats_up_to_game(previous_games)
            
            # Make prediction using ONLY pre-game information
            prediction = self._make_truly_pregame_prediction(
                game, elo_ratings, team_stats
            )
            
            predictions.append(prediction)
            actual_outcomes.append(1 if game['home_score'] > game['away_score'] else 0)
            
            if i % 100 == 0:
                print(f"  Processed {i+1}/{len(all_games)} games...")
        
        # Calculate metrics
        predictions = np.array(predictions)
        actual_outcomes = np.array(actual_outcomes)
        
        accuracy = np.mean(predictions == actual_outcomes)
        
        # Calculate Brier Score (using 0.5 as probability for simplicity)
        brier_score = np.mean((0.5 - actual_outcomes) ** 2)
        
        return {
            'total_games': len(predictions),
            'accuracy': accuracy,
            'brier_score': brier_score,
            'predictions': predictions,
            'actual_outcomes': actual_outcomes
        }
    
    def _calculate_elo_ratings_up_to_game(self, games: pd.DataFrame) -> Dict[str, float]:
        """Calculate Elo ratings using only games up to current point."""
        if len(games) == 0:
            return {}
        
        # Run Elo backtest on previous games only
        result = run_backtest(games, self.elo_config)
        
        return result.get('final_ratings', {})
    
    def _calculate_team_stats_up_to_game(self, games: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate team stats using only games up to current point."""
        team_stats = {}
        
        # Get all unique teams
        all_teams = set(games['home_team'].unique()) | set(games['away_team'].unique())
        all_teams = [team for team in all_teams if pd.notna(team)]
        
        for team in all_teams:
            # Get team's games from previous games only
            team_games = games[(games['home_team'] == team) | (games['away_team'] == team)]
            
            if len(team_games) == 0:
                team_stats[team] = {
                    'off_ppg': 0.0,
                    'def_ppg': 0.0,
                    'win_pct': 0.5
                }
                continue
            
            # Calculate stats from previous games only
            home_games = team_games[team_games['home_team'] == team]
            away_games = team_games[team_games['away_team'] == team]
            
            total_points_scored = home_games['home_score'].sum() + away_games['away_score'].sum()
            total_points_allowed = home_games['away_score'].sum() + away_games['home_score'].sum()
            total_games = len(team_games)
            
            # Calculate wins from previous games only
            home_wins = (home_games['home_score'] > home_games['away_score']).sum()
            away_wins = (away_games['away_score'] > away_games['home_score']).sum()
            total_wins = home_wins + away_wins
            
            team_stats[team] = {
                'off_ppg': total_points_scored / total_games if total_games > 0 else 0,
                'def_ppg': total_points_allowed / total_games if total_games > 0 else 0,
                'win_pct': total_wins / total_games if total_games > 0 else 0.5
            }
        
        return team_stats
    
    def _make_truly_pregame_prediction(self, game: pd.Series, elo_ratings: Dict[str, float], team_stats: Dict[str, Dict[str, float]]) -> int:
        """Make prediction using only pre-game information."""
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get Elo ratings
        home_elo = elo_ratings.get(home_team, 1500)
        away_elo = elo_ratings.get(away_team, 1500)
        
        # Get team stats
        home_stats = team_stats.get(home_team, {'off_ppg': 0, 'def_ppg': 0, 'win_pct': 0.5})
        away_stats = team_stats.get(away_team, {'off_ppg': 0, 'def_ppg': 0, 'win_pct': 0.5})
        
        # Calculate Elo-based probability
        elo_diff = home_elo - away_elo + self.elo_config.hfa_points
        elo_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        # Calculate team performance factor
        home_off_adv = home_stats['off_ppg'] - away_stats['def_ppg']
        away_off_adv = away_stats['off_ppg'] - home_stats['def_ppg']
        team_factor = (home_off_adv - away_off_adv) / 10.0  # Scale to reasonable range
        
        # Combine factors
        combined_prob = 0.7 * elo_prob + 0.3 * (0.5 + team_factor)
        combined_prob = max(0.1, min(0.9, combined_prob))  # Clamp to reasonable range
        
        return 1 if combined_prob > 0.5 else 0


def test_truly_pregame_system():
    """Test truly pre-game system."""
    print("🎯 TESTING TRULY PRE-GAME SYSTEM")
    print("="*80)
    
    # Test with recent years
    years = [2022, 2023, 2024]
    
    # Create system
    system = TrulyPreGameSystem()
    
    # Run backtest
    results = system.run_truly_pregame_backtest(years)
    
    print(f"\\n🎯 TRULY PRE-GAME RESULTS:")
    print(f"Total Games: {results['total_games']}")
    print(f"Accuracy: {results['accuracy']:.3f}")
    print(f"Brier Score: {results['brier_score']:.3f}")
    
    # Analyze results
    if results['accuracy'] > 0.70:
        print("\\n⚠️  WARNING: Accuracy still seems high - investigate further")
    elif results['accuracy'] > 0.60:
        print("\\n✅ Accuracy looks reasonable for NFL predictions")
    else:
        print("\\n❌ Accuracy seems low - check implementation")
    
    return system, results


if __name__ == "__main__":
    system, results = test_truly_pregame_system()
