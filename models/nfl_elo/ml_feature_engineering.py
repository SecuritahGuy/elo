"""Machine Learning feature engineering for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from ingest.nfl.data_loader import load_games
from ingest.nfl.turnover_calculator import TurnoverCalculator


class MLFeatureEngineer:
    """Feature engineering for ML-enhanced NFL predictions."""
    
    def __init__(self):
        """Initialize ML feature engineer."""
        self.feature_cache = {}
        self.team_stats_cache = {}
    
    def create_ml_features(self, games: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """
        Create comprehensive ML features for games.
        
        Args:
            games: Games DataFrame
            years: Years to use for feature calculation
            
        Returns:
            DataFrame with ML features
        """
        print(f"Creating ML features for {len(games)} games...")
        
        # Start with games data
        ml_features = games.copy()
        
        # 1. Elo-based features
        ml_features = self._add_elo_features(ml_features, years)
        
        # 2. Team performance features
        ml_features = self._add_team_performance_features(ml_features, years)
        
        # 3. Situational features
        ml_features = self._add_situational_features(ml_features)
        
        # 4. Historical features
        ml_features = self._add_historical_features(ml_features, years)
        
        # 5. Advanced metrics
        ml_features = self._add_advanced_metrics(ml_features, years)
        
        # 6. Target variable
        ml_features = self._add_target_variable(ml_features)
        
        print(f"Created {len(ml_features.columns)} features for ML training")
        return ml_features
    
    def _add_elo_features(self, games: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """Add Elo-based features."""
        print("Adding Elo-based features...")
        
        # Calculate Elo ratings for all teams
        elo_ratings = self._calculate_elo_ratings(games, years)
        
        # Add Elo features
        games['home_elo_rating'] = games['home_team'].map(elo_ratings)
        games['away_elo_rating'] = games['away_team'].map(elo_ratings)
        games['elo_difference'] = games['home_elo_rating'] - games['away_elo_rating']
        games['elo_ratio'] = games['home_elo_rating'] / games['away_elo_rating']
        
        # Elo trends (last 5 games)
        games['home_elo_trend'] = games.apply(lambda x: self._calculate_elo_trend(x['home_team'], x['season'], x['week'], elo_ratings), axis=1)
        games['away_elo_trend'] = games.apply(lambda x: self._calculate_elo_trend(x['away_team'], x['season'], x['week'], elo_ratings), axis=1)
        
        return games
    
    def _add_team_performance_features(self, games: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """Add team performance features."""
        print("Adding team performance features...")
        
        # Calculate team statistics
        team_stats = self._calculate_team_statistics(games, years)
        
        # Add offensive features
        games['home_off_ppg'] = games['home_team'].map(team_stats['off_ppg'])
        games['away_off_ppg'] = games['away_team'].map(team_stats['off_ppg'])
        games['home_def_ppg'] = games['home_team'].map(team_stats['def_ppg'])
        games['away_def_ppg'] = games['away_team'].map(team_stats['def_ppg'])
        
        # Add efficiency features
        games['home_off_efficiency'] = games['home_team'].map(team_stats['off_efficiency'])
        games['away_off_efficiency'] = games['away_team'].map(team_stats['off_efficiency'])
        games['home_def_efficiency'] = games['home_team'].map(team_stats['def_efficiency'])
        games['away_def_efficiency'] = games['away_team'].map(team_stats['def_efficiency'])
        
        # Add turnover features
        turnover_calc = TurnoverCalculator()
        turnover_db = turnover_calc.create_turnover_database(years)
        
        games['home_turnover_rate'] = games['home_team'].map(turnover_db['giveaway_rate'])
        games['away_turnover_rate'] = games['away_team'].map(turnover_db['giveaway_rate'])
        games['home_takeaway_rate'] = games['home_team'].map(turnover_db['takeaway_rate'])
        games['away_takeaway_rate'] = games['away_team'].map(turnover_db['takeaway_rate'])
        
        return games
    
    def _add_situational_features(self, games: pd.DataFrame) -> pd.DataFrame:
        """Add situational features."""
        print("Adding situational features...")
        
        # Home field advantage
        games['is_home_team'] = 1  # All games are from home team perspective
        
        # Rest days (if available)
        if 'home_rest' in games.columns:
            games['rest_advantage'] = games['home_rest'] - games.get('away_rest', 0)
        else:
            games['rest_advantage'] = 0
        
        # Season progression
        games['week_number'] = games['week']
        games['season_progress'] = games['week'] / 18.0  # Normalize to 0-1
        
        # Divisional games (simplified - would need schedule data)
        games['is_divisional'] = 0  # Placeholder
        
        return games
    
    def _add_historical_features(self, games: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """Add historical head-to-head features."""
        print("Adding historical features...")
        
        # Head-to-head record (simplified)
        games['h2h_home_wins'] = 0  # Placeholder
        games['h2h_away_wins'] = 0  # Placeholder
        
        # Recent form (last 5 games)
        games['home_recent_form'] = games.apply(lambda x: self._calculate_recent_form(x['home_team'], x['season'], x['week']), axis=1)
        games['away_recent_form'] = games.apply(lambda x: self._calculate_recent_form(x['away_team'], x['season'], x['week']), axis=1)
        
        return games
    
    def _add_advanced_metrics(self, games: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """Add advanced metrics features."""
        print("Adding advanced metrics...")
        
        # Point differential
        games['home_point_diff'] = games['home_score'] - games['away_score']
        games['away_point_diff'] = games['away_score'] - games['home_score']
        
        # Score ratio
        games['score_ratio'] = games['home_score'] / (games['away_score'] + 1)  # Add 1 to avoid division by zero
        
        # Game total
        games['total_points'] = games['home_score'] + games['away_score']
        
        return games
    
    def _add_target_variable(self, games: pd.DataFrame) -> pd.DataFrame:
        """Add target variable for ML training."""
        print("Adding target variable...")
        
        # Binary classification: home team wins
        games['home_team_wins'] = (games['home_score'] > games['away_score']).astype(int)
        
        # Margin of victory
        games['margin_of_victory'] = games['home_score'] - games['away_score']
        
        return games
    
    def _calculate_elo_ratings(self, games: pd.DataFrame, years: List[int]) -> Dict[str, float]:
        """Calculate Elo ratings for all teams."""
        # Use our existing Elo system to get final ratings
        config = EloConfig(
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
        
        result = run_backtest(games, config)
        
        # Extract final ratings
        if 'final_ratings' in result:
            return result['final_ratings']
        else:
            # Fallback: return base rating for all teams
            teams = set(games['home_team'].unique()) | set(games['away_team'].unique())
            return {team: 1500.0 for team in teams if pd.notna(team)}
    
    def _calculate_team_statistics(self, games: pd.DataFrame, years: List[int]) -> Dict[str, Dict[str, float]]:
        """Calculate team statistics."""
        team_stats = {}
        
        for team in set(games['home_team'].unique()) | set(games['away_team'].unique()):
            if pd.isna(team):
                continue
            
            # Get team's games
            team_games = games[(games['home_team'] == team) | (games['away_team'] == team)]
            
            if len(team_games) == 0:
                continue
            
            # Calculate offensive stats
            home_games = team_games[team_games['home_team'] == team]
            away_games = team_games[team_games['away_team'] == team]
            
            total_points_scored = home_games['home_score'].sum() + away_games['away_score'].sum()
            total_points_allowed = home_games['away_score'].sum() + away_games['home_score'].sum()
            total_games = len(team_games)
            
            team_stats[team] = {
                'off_ppg': total_points_scored / total_games if total_games > 0 else 0,
                'def_ppg': total_points_allowed / total_games if total_games > 0 else 0,
                'off_efficiency': total_points_scored / (total_points_scored + total_points_allowed + 1),
                'def_efficiency': total_points_allowed / (total_points_scored + total_points_allowed + 1)
            }
        
        return team_stats
    
    def _calculate_elo_trend(self, team: str, season: int, week: int, elo_ratings: Dict[str, float]) -> float:
        """Calculate Elo trend for a team."""
        # Simplified: return current rating as trend
        return elo_ratings.get(team, 1500.0)
    
    def _calculate_recent_form(self, team: str, season: int, week: int) -> float:
        """Calculate recent form for a team."""
        # Simplified: return 0.5 (neutral)
        return 0.5
    
    def get_feature_importance(self, features: pd.DataFrame, target: str = 'home_team_wins') -> pd.DataFrame:
        """Get feature importance for ML training."""
        # This would be implemented with actual ML models
        # For now, return a placeholder
        feature_cols = [col for col in features.columns if col != target]
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': np.random.random(len(feature_cols))
        }).sort_values('importance', ascending=False)
        
        return importance_df


def test_ml_feature_engineering():
    """Test ML feature engineering."""
    print("📊 TESTING ML FEATURE ENGINEERING")
    print("="*80)
    
    # Load sample data
    games = load_games([2024])
    print(f"Loaded {len(games)} games")
    
    # Create feature engineer
    engineer = MLFeatureEngineer()
    
    # Create ML features
    ml_features = engineer.create_ml_features(games, [2024])
    
    print(f"\\nCreated {len(ml_features.columns)} features")
    print(f"Features: {list(ml_features.columns)}")
    
    # Show sample data
    print(f"\\nSample ML features:")
    print(ml_features[['home_team', 'away_team', 'home_elo_rating', 'away_elo_rating', 'elo_difference', 'home_team_wins']].head())
    
    # Get feature importance
    importance = engineer.get_feature_importance(ml_features)
    print(f"\\nTop 10 features by importance:")
    print(importance.head(10))
    
    return engineer, ml_features


if __name__ == "__main__":
    engineer, features = test_ml_feature_engineering()
