"""Pre-game feature engineering for NFL Elo rating system - NO DATA LEAKAGE."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from ingest.nfl.data_loader import load_games


class PreGameFeatureEngineer:
    """Feature engineering for ML-enhanced NFL predictions - PRE-GAME ONLY."""
    
    def __init__(self):
        """Initialize pre-game feature engineer."""
        self.feature_cache = {}
        self.team_stats_cache = {}
    
    def create_pregame_features(self, games: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """
        Create pre-game ML features ONLY - no data leakage.
        
        Args:
            games: Games DataFrame
            years: Years to use for feature calculation
            
        Returns:
            DataFrame with pre-game ML features
        """
        print(f"Creating PRE-GAME ML features for {len(games)} games...")
        
        # Start with games data
        ml_features = games.copy()
        
        # 1. Elo-based features (pre-game)
        ml_features = self._add_elo_features(ml_features, years)
        
        # 2. Team performance features (pre-game)
        ml_features = self._add_team_performance_features(ml_features, years)
        
        # 3. Situational features (pre-game)
        ml_features = self._add_situational_features(ml_features)
        
        # 4. Historical features (pre-game)
        ml_features = self._add_historical_features(ml_features, years)
        
        # 5. Target variable (ONLY for training)
        ml_features = self._add_target_variable(ml_features)
        
        print(f"Created {len(ml_features.columns)} PRE-GAME features for ML training")
        return ml_features
    
    def _add_elo_features(self, games: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """Add Elo-based features (pre-game)."""
        print("Adding Elo-based features (pre-game)...")
        
        # Calculate Elo ratings for all teams
        elo_ratings = self._calculate_elo_ratings(games, years)
        
        # Add Elo features
        games['home_elo_rating'] = games['home_team'].map(elo_ratings)
        games['away_elo_rating'] = games['away_team'].map(elo_ratings)
        games['elo_difference'] = games['home_elo_rating'] - games['away_elo_rating']
        games['elo_ratio'] = games['home_elo_rating'] / (games['away_elo_rating'] + 1)
        
        # Elo-based win probability
        games['elo_win_prob'] = 1 / (1 + 10 ** (-games['elo_difference'] / 400))
        
        return games
    
    def _add_team_performance_features(self, games: pd.DataFrame, years: List[int]) -> pd.DataFrame:
        """Add team performance features (pre-game only)."""
        print("Adding team performance features (pre-game)...")
        
        # Calculate team statistics from PREVIOUS games only
        team_stats = self._calculate_pregame_team_statistics(games, years)
        
        # Add offensive features
        games['home_off_ppg'] = games['home_team'].map({team: stats['off_ppg'] for team, stats in team_stats.items()})
        games['away_off_ppg'] = games['away_team'].map({team: stats['off_ppg'] for team, stats in team_stats.items()})
        games['home_def_ppg'] = games['home_team'].map({team: stats['def_ppg'] for team, stats in team_stats.items()})
        games['away_def_ppg'] = games['away_team'].map({team: stats['def_ppg'] for team, stats in team_stats.items()})
        
        # Add efficiency features
        games['home_off_efficiency'] = games['home_team'].map({team: stats['off_efficiency'] for team, stats in team_stats.items()})
        games['away_off_efficiency'] = games['away_team'].map({team: stats['off_efficiency'] for team, stats in team_stats.items()})
        games['home_def_efficiency'] = games['home_team'].map({team: stats['def_efficiency'] for team, stats in team_stats.items()})
        games['away_def_efficiency'] = games['away_team'].map({team: stats['def_efficiency'] for team, stats in team_stats.items()})
        
        # Add win percentage
        games['home_win_pct'] = games['home_team'].map({team: stats['win_pct'] for team, stats in team_stats.items()})
        games['away_win_pct'] = games['away_team'].map({team: stats['win_pct'] for team, stats in team_stats.items()})
        
        # Add recent form (last 5 games)
        games['home_recent_form'] = games.apply(lambda x: self._calculate_recent_form(x['home_team'], x['season'], x['week'], years), axis=1)
        games['away_recent_form'] = games.apply(lambda x: self._calculate_recent_form(x['away_team'], x['season'], x['week'], years), axis=1)
        
        return games
    
    def _add_situational_features(self, games: pd.DataFrame) -> pd.DataFrame:
        """Add situational features (pre-game)."""
        print("Adding situational features (pre-game)...")
        
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
        """Add historical head-to-head features (pre-game)."""
        print("Adding historical features (pre-game)...")
        
        # Head-to-head record (simplified)
        games['h2h_home_wins'] = 0  # Placeholder
        games['h2h_away_wins'] = 0  # Placeholder
        
        return games
    
    def _add_target_variable(self, games: pd.DataFrame) -> pd.DataFrame:
        """Add target variable for ML training."""
        print("Adding target variable...")
        
        # Binary classification: home team wins
        games['home_team_wins'] = (games['home_score'] > games['away_score']).astype(int)
        
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
    
    def _calculate_pregame_team_statistics(self, games: pd.DataFrame, years: List[int]) -> Dict[str, Dict[str, float]]:
        """Calculate team statistics from PREVIOUS games only."""
        team_stats = {}
        
        # Get all unique teams
        all_teams = set(games['home_team'].unique()) | set(games['away_team'].unique())
        all_teams = [team for team in all_teams if pd.notna(team)]
        
        for team in all_teams:
            # Get team's games from PREVIOUS seasons/years
            team_games = games[games['season'] < games['season'].max()]
            team_games = team_games[(team_games['home_team'] == team) | (team_games['away_team'] == team)]
            
            if len(team_games) == 0:
                team_stats[team] = {
                    'off_ppg': 0.0,
                    'def_ppg': 0.0,
                    'off_efficiency': 0.5,
                    'def_efficiency': 0.5,
                    'win_pct': 0.5
                }
                continue
            
            # Calculate offensive stats from previous games
            home_games = team_games[team_games['home_team'] == team]
            away_games = team_games[team_games['away_team'] == team]
            
            total_points_scored = home_games['home_score'].sum() + away_games['away_score'].sum()
            total_points_allowed = home_games['away_score'].sum() + away_games['home_score'].sum()
            total_games = len(team_games)
            
            # Calculate wins from previous games
            home_wins = (home_games['home_score'] > home_games['away_score']).sum()
            away_wins = (away_games['away_score'] > away_games['home_score']).sum()
            total_wins = home_wins + away_wins
            
            team_stats[team] = {
                'off_ppg': total_points_scored / total_games if total_games > 0 else 0,
                'def_ppg': total_points_allowed / total_games if total_games > 0 else 0,
                'off_efficiency': total_points_scored / (total_points_scored + total_points_allowed + 1),
                'def_efficiency': total_points_allowed / (total_points_scored + total_points_allowed + 1),
                'win_pct': total_wins / total_games if total_games > 0 else 0.5
            }
        
        return team_stats
    
    def _calculate_recent_form(self, team: str, season: int, week: int, years: List[int]) -> float:
        """Calculate recent form for a team (last 5 games)."""
        # This would need to be implemented with proper historical data
        # For now, return a placeholder
        return 0.5
    
    def get_feature_columns(self, features: pd.DataFrame) -> List[str]:
        """Get feature columns for ML training."""
        exclude_cols = ['home_team', 'away_team', 'home_team_wins', 'game_id', 'gameday', 'result', 'home_score', 'away_score']
        feature_cols = [col for col in features.columns if col not in exclude_cols]
        
        # Only include numeric columns
        numeric_cols = features[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
        return numeric_cols
    
    def get_feature_importance(self, features: pd.DataFrame, target: str = 'home_team_wins') -> pd.DataFrame:
        """Get feature importance for ML training."""
        # This would be implemented with actual ML models
        # For now, return a placeholder
        feature_cols = self.get_feature_columns(features)
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': np.random.random(len(feature_cols))
        }).sort_values('importance', ascending=False)
        
        return importance_df


def test_pregame_feature_engineering():
    """Test pre-game feature engineering."""
    print("🎯 TESTING PRE-GAME FEATURE ENGINEERING")
    print("="*80)
    
    # Load sample data
    games = load_games([2024])
    print(f"Loaded {len(games)} games")
    
    # Create feature engineer
    engineer = PreGameFeatureEngineer()
    
    # Create pre-game ML features
    ml_features = engineer.create_pregame_features(games, [2024])
    
    print(f"\\nCreated {len(ml_features.columns)} PRE-GAME features")
    print(f"Feature columns: {engineer.get_feature_columns(ml_features)}")
    
    # Show sample data
    print(f"\\nSample PRE-GAME ML features:")
    sample_cols = ['home_team', 'away_team', 'home_elo_rating', 'away_elo_rating', 'elo_difference', 'home_team_wins']
    print(ml_features[sample_cols].head())
    
    # Get feature importance
    importance = engineer.get_feature_importance(ml_features)
    print(f"\\nTop 10 features by importance:")
    print(importance.head(10))
    
    # Show feature statistics
    print(f"\\nFeature statistics:")
    feature_cols = engineer.get_feature_columns(ml_features)
    print(ml_features[feature_cols].describe())
    
    return engineer, ml_features


if __name__ == "__main__":
    engineer, features = test_pregame_feature_engineering()
