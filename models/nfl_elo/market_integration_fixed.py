"""Market integration system with proper walk-forward validation (no data leakage)."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json

from .config import EloConfig
from .evaluator import calculate_all_metrics
from ingest.nfl.data_loader import load_games


class MarketIntegrationFixed:
    """Market integration system with proper walk-forward validation."""
    
    def __init__(self, years: List[int] = [2022, 2023]):
        """
        Initialize market integration system.
        
        Args:
            years: Years to analyze for market baseline
        """
        self.years = years
        self.games = None
        self.market_baseline = None
        self.team_performance = None
        
        # Load data
        self._load_data()
    
    def _load_data(self):
        """Load games data for market analysis."""
        print("Loading games data for market integration...")
        self.games = load_games(self.years)
        print(f"Loaded {len(self.games)} games")
    
    def create_market_baseline_walk_forward(self) -> Dict[str, Any]:
        """
        Create market baseline using walk-forward validation (no data leakage).
        
        This simulates betting market behavior using only pre-game information:
        1. Historical team performance (up to that point in time)
        2. Home field advantage (historical)
        3. Recent form trends (pre-game)
        4. Public perception factors (pre-game)
        
        Returns:
            Dictionary with market baseline data
        """
        print("\n" + "="*60)
        print("CREATING MARKET BASELINE (WALK-FORWARD)")
        print("="*60)
        
        # Sort games by date to ensure proper temporal order
        games_sorted = self.games.sort_values('gameday').reset_index(drop=True)
        
        # Calculate market probabilities for each game using only pre-game data
        market_probs = []
        
        for idx, game in games_sorted.iterrows():
            # Get historical data up to this point (no future data)
            historical_games = games_sorted.iloc[:idx]
            
            # Calculate team metrics using only historical data
            home_metrics = self._calculate_team_metrics_pre_game(
                game['home_team'], historical_games, game['gameday']
            )
            away_metrics = self._calculate_team_metrics_pre_game(
                game['away_team'], historical_games, game['gameday']
            )
            
            # Calculate market probability for this game
            market_prob = self._calculate_single_market_probability(
                home_metrics, away_metrics, game
            )
            
            market_probs.append({
                'game_id': game['game_id'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'market_prob_home': market_prob,
                'market_prob_away': 1.0 - market_prob,
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'home_win': 1 if game['home_score'] > game['away_score'] else 0,
                'gameday': game['gameday']
            })
        
        market_probs_df = pd.DataFrame(market_probs)
        
        # Calculate baseline metrics
        baseline_metrics = self._calculate_baseline_metrics(market_probs_df)
        
        market_baseline = {
            'market_probabilities': market_probs_df,
            'baseline_metrics': baseline_metrics,
            'created_at': datetime.now().isoformat()
        }
        
        self.market_baseline = market_baseline
        
        print(f"Market baseline created for {len(market_probs_df)} games")
        print(f"Market Brier Score: {baseline_metrics['brier_score']:.4f}")
        print(f"Market Accuracy: {baseline_metrics['accuracy']:.3f}")
        
        return market_baseline
    
    def _calculate_team_metrics_pre_game(self, team: str, historical_games: pd.DataFrame, 
                                       current_game_date: str) -> Dict[str, float]:
        """
        Calculate team metrics using only pre-game historical data.
        
        Args:
            team: Team abbreviation
            historical_games: Games that occurred before current game
            current_game_date: Date of current game (for context)
            
        Returns:
            Dictionary with team metrics
        """
        # Get team's historical games (before current game)
        team_games = historical_games[
            (historical_games['home_team'] == team) | (historical_games['away_team'] == team)
        ].copy()
        
        if len(team_games) == 0:
            # No historical data - return default values
            return {
                'win_rate': 0.5,
                'points_per_game': 21.0,  # League average
                'points_allowed_per_game': 21.0,
                'point_differential': 0.0,
                'recent_form': 0.5,
                'home_field_advantage': 0.0,
                'total_games': 0
            }
        
        # Calculate metrics using only historical data
        home_games = team_games[team_games['home_team'] == team]
        away_games = team_games[team_games['away_team'] == team]
        
        # Win rate (historical)
        home_wins = len(home_games[home_games['home_score'] > home_games['away_score']])
        away_wins = len(away_games[away_games['away_score'] > away_games['home_score']])
        total_wins = home_wins + away_wins
        win_rate = total_wins / len(team_games) if len(team_games) > 0 else 0.5
        
        # Points per game (historical)
        home_ppg = home_games['home_score'].mean() if len(home_games) > 0 else 21.0
        away_ppg = away_games['away_score'].mean() if len(away_games) > 0 else 21.0
        avg_ppg = (home_ppg + away_ppg) / 2 if len(home_games) > 0 and len(away_games) > 0 else home_ppg or away_ppg
        
        # Points allowed per game (historical)
        home_papg = home_games['away_score'].mean() if len(home_games) > 0 else 21.0
        away_papg = away_games['home_score'].mean() if len(away_games) > 0 else 21.0
        avg_papg = (home_papg + away_papg) / 2 if len(home_games) > 0 and len(away_games) > 0 else home_papg or away_papg
        
        # Point differential (historical)
        point_diff = avg_ppg - avg_papg
        
        # Recent form (last 5 games, historical only)
        recent_games = team_games.tail(5)
        recent_wins = 0
        for _, game in recent_games.iterrows():
            if game['home_team'] == team and game['home_score'] > game['away_score']:
                recent_wins += 1
            elif game['away_team'] == team and game['away_score'] > game['home_score']:
                recent_wins += 1
        recent_form = recent_wins / len(recent_games) if len(recent_games) > 0 else 0.5
        
        # Home field advantage (historical)
        home_win_rate = home_wins / len(home_games) if len(home_games) > 0 else 0.5
        away_win_rate = away_wins / len(away_games) if len(away_games) > 0 else 0.5
        hfa = home_win_rate - away_win_rate
        
        return {
            'win_rate': win_rate,
            'points_per_game': avg_ppg,
            'points_allowed_per_game': avg_papg,
            'point_differential': point_diff,
            'recent_form': recent_form,
            'home_field_advantage': hfa,
            'total_games': len(team_games)
        }
    
    def _calculate_single_market_probability(self, home_metrics: Dict, away_metrics: Dict, game: pd.Series) -> float:
        """Calculate market probability for a single game using pre-game data only."""
        # Base probability from historical win rates
        home_win_rate = home_metrics.get('win_rate', 0.5)
        away_win_rate = away_metrics.get('win_rate', 0.5)
        
        # Point differential factor (historical)
        home_point_diff = home_metrics.get('point_differential', 0.0)
        away_point_diff = away_metrics.get('point_differential', 0.0)
        point_diff_factor = (home_point_diff - away_point_diff) / 10.0  # Scale to reasonable range
        
        # Recent form factor (pre-game)
        home_recent_form = home_metrics.get('recent_form', 0.5)
        away_recent_form = away_metrics.get('recent_form', 0.5)
        recent_form_factor = (home_recent_form - away_recent_form) * 0.3  # Scale to reasonable range
        
        # Home field advantage (historical)
        hfa = home_metrics.get('home_field_advantage', 0.0)
        hfa_factor = hfa * 0.2  # Scale to reasonable range
        
        # Combine factors
        raw_prob = 0.5 + point_diff_factor + recent_form_factor + hfa_factor
        
        # Apply logistic function to keep in [0, 1] range
        market_prob = 1 / (1 + np.exp(-raw_prob * 2))  # Scale factor of 2 for sensitivity
        
        # Ensure reasonable bounds
        market_prob = max(0.1, min(0.9, market_prob))
        
        return market_prob
    
    def _calculate_baseline_metrics(self, market_probs: pd.DataFrame) -> Dict[str, float]:
        """Calculate baseline metrics for market probabilities."""
        if len(market_probs) == 0:
            return {}
        
        # Calculate metrics
        metrics_df = pd.DataFrame({
            'p_home': market_probs['market_prob_home'],
            'home_win': market_probs['home_win']
        })
        
        metrics = calculate_all_metrics(metrics_df)
        
        return metrics
    
    def create_elo_market_blend(self, elo_probs: pd.DataFrame, blend_weight: float = 0.5) -> pd.DataFrame:
        """
        Create blended probabilities between Elo and market.
        
        Args:
            elo_probs: DataFrame with Elo probabilities
            blend_weight: Weight for market (0.0 = pure Elo, 1.0 = pure market)
            
        Returns:
            DataFrame with blended probabilities
        """
        if self.market_baseline is None:
            raise ValueError("Market baseline not created. Call create_market_baseline_walk_forward() first.")
        
        # Merge with market probabilities
        blended = elo_probs.merge(
            self.market_baseline['market_probabilities'][['game_id', 'market_prob_home']],
            on='game_id',
            how='left'
        )
        
        # Fill missing market probabilities with 0.5
        blended['market_prob_home'] = blended['market_prob_home'].fillna(0.5)
        
        # Calculate blended probabilities
        blended['blended_prob_home'] = (
            (1 - blend_weight) * blended['p_home'] + 
            blend_weight * blended['market_prob_home']
        )
        
        # Ensure probabilities are in [0, 1] range
        blended['blended_prob_home'] = np.clip(blended['blended_prob_home'], 0.01, 0.99)
        
        return blended
    
    def optimize_blend_weight(self, elo_probs: pd.DataFrame, 
                            weight_range: Tuple[float, float] = (0.0, 1.0),
                            step_size: float = 0.1) -> Dict[str, Any]:
        """
        Optimize the blend weight between Elo and market.
        
        Args:
            elo_probs: DataFrame with Elo probabilities
            weight_range: Range of weights to test
            step_size: Step size for weight testing
            
        Returns:
            Dictionary with optimization results
        """
        print(f"\nOptimizing blend weight from {weight_range[0]} to {weight_range[1]}...")
        
        weights = np.arange(weight_range[0], weight_range[1] + step_size, step_size)
        results = []
        
        for weight in weights:
            try:
                # Create blended probabilities
                blended = self.create_elo_market_blend(elo_probs, weight)
                
                # Calculate metrics
                metrics_df = pd.DataFrame({
                    'p_home': blended['blended_prob_home'],
                    'home_win': blended['home_win']
                })
                
                metrics = calculate_all_metrics(metrics_df)
                
                results.append({
                    'weight': weight,
                    'brier_score': metrics['brier_score'],
                    'log_loss': metrics['log_loss'],
                    'accuracy': metrics['accuracy'],
                    'ece': metrics['ece'],
                    'sharpness': metrics['sharpness']
                })
                
                print(f"  Weight {weight:.1f}: Brier {metrics['brier_score']:.4f}, Accuracy {metrics['accuracy']:.3f}")
                
            except Exception as e:
                print(f"  Weight {weight:.1f}: Error - {e}")
                results.append({
                    'weight': weight,
                    'brier_score': float('inf'),
                    'log_loss': float('inf'),
                    'accuracy': 0.0,
                    'ece': float('inf'),
                    'sharpness': 0.0
                })
        
        # Find best weight
        results_df = pd.DataFrame(results)
        best_idx = results_df['brier_score'].idxmin()
        best_result = results_df.iloc[best_idx]
        
        print(f"\nBest blend weight: {best_result['weight']:.1f}")
        print(f"Best Brier Score: {best_result['brier_score']:.4f}")
        print(f"Best Accuracy: {best_result['accuracy']:.3f}")
        
        return {
            'weights_tested': weights.tolist(),
            'results': results,
            'best_weight': best_result['weight'],
            'best_brier_score': best_result['brier_score'],
            'best_accuracy': best_result['accuracy']
        }
    
    def run_market_comparison_walk_forward(self, elo_config: EloConfig) -> Dict[str, Any]:
        """
        Run comprehensive comparison between Elo and market baseline using walk-forward validation.
        
        Args:
            elo_config: Elo configuration to test
            
        Returns:
            Dictionary with comparison results
        """
        print("\n" + "="*60)
        print("RUNNING MARKET COMPARISON (WALK-FORWARD)")
        print("="*60)
        
        # Create market baseline with walk-forward validation
        market_baseline = self.create_market_baseline_walk_forward()
        
        # Run Elo backtest
        from .backtest import run_backtest
        elo_result = run_backtest(self.games, elo_config)
        
        # Create comparison
        comparison = {
            'elo_metrics': elo_result['metrics'],
            'market_metrics': market_baseline['baseline_metrics'],
            'market_baseline': market_baseline,
            'elo_vs_market': {
                'brier_score_diff': elo_result['metrics']['brier_score'] - market_baseline['baseline_metrics']['brier_score'],
                'accuracy_diff': elo_result['metrics']['accuracy'] - market_baseline['baseline_metrics']['accuracy'],
                'elo_better': elo_result['metrics']['brier_score'] < market_baseline['baseline_metrics']['brier_score']
            }
        }
        
        # Print comparison
        print(f"\nCOMPARISON RESULTS (WALK-FORWARD):")
        print(f"Elo Brier Score: {elo_result['metrics']['brier_score']:.4f}")
        print(f"Market Brier Score: {market_baseline['baseline_metrics']['brier_score']:.4f}")
        print(f"Difference: {comparison['elo_vs_market']['brier_score_diff']:+.4f}")
        print(f"Elo Accuracy: {elo_result['metrics']['accuracy']:.3f}")
        print(f"Market Accuracy: {market_baseline['baseline_metrics']['accuracy']:.3f}")
        print(f"Difference: {comparison['elo_vs_market']['accuracy_diff']:+.3f}")
        
        if comparison['elo_vs_market']['elo_better']:
            print("✅ Elo performs better than market baseline")
        else:
            print("❌ Market baseline performs better than Elo")
        
        return comparison


def run_market_integration_analysis_fixed(years: List[int] = [2022, 2023], sample_size: Optional[int] = None):
    """Run comprehensive market integration analysis with proper walk-forward validation."""
    # Load games
    games = load_games(years)
    if sample_size:
        games = games.head(sample_size)
    
    # Create market integration system
    market_system = MarketIntegrationFixed(years)
    
    # Run comparison
    from .config import EloConfig
    elo_config = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.75,
        use_weather_adjustment=False,
        use_travel_adjustment=True,
        use_qb_adjustment=True
    )
    
    comparison = market_system.run_market_comparison_walk_forward(elo_config)
    
    return comparison


if __name__ == "__main__":
    results = run_market_integration_analysis_fixed(sample_size=100)
