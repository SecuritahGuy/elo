"""Market integration system for NFL Elo baseline comparison."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json

from .config import EloConfig
from .evaluator import calculate_all_metrics
from ingest.nfl.data_loader import load_games


class MarketIntegration:
    """Market integration system for baseline comparison and blending."""
    
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
    
    def create_market_baseline(self) -> Dict[str, Any]:
        """
        Create a market baseline using historical performance data.
        
        This simulates betting market behavior using:
        1. Historical team performance
        2. Home field advantage
        3. Recent form trends
        4. Public perception factors
        
        Returns:
            Dictionary with market baseline data
        """
        print("\n" + "="*60)
        print("CREATING MARKET BASELINE")
        print("="*60)
        
        # Calculate team performance metrics
        team_metrics = self._calculate_team_performance_metrics()
        
        # Calculate market-implied probabilities
        market_probs = self._calculate_market_probabilities(team_metrics)
        
        # Create market baseline
        market_baseline = {
            'team_metrics': team_metrics,
            'market_probabilities': market_probs,
            'baseline_metrics': self._calculate_baseline_metrics(market_probs),
            'created_at': datetime.now().isoformat()
        }
        
        self.market_baseline = market_baseline
        
        print(f"Market baseline created for {len(team_metrics)} teams")
        print(f"Market probabilities calculated for {len(market_probs)} games")
        
        return market_baseline
    
    def _calculate_team_performance_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculate team performance metrics for market baseline."""
        team_metrics = {}
        
        # Get all unique teams
        all_teams = set(self.games['home_team'].unique()) | set(self.games['away_team'].unique())
        
        for team in all_teams:
            # Get team's games
            team_games = self.games[
                (self.games['home_team'] == team) | (self.games['away_team'] == team)
            ].copy()
            
            if len(team_games) == 0:
                continue
            
            # Calculate metrics
            home_games = team_games[team_games['home_team'] == team]
            away_games = team_games[team_games['away_team'] == team]
            
            # Win rate
            home_wins = len(home_games[home_games['home_score'] > home_games['away_score']])
            away_wins = len(away_games[away_games['away_score'] > away_games['home_score']])
            total_wins = home_wins + away_wins
            win_rate = total_wins / len(team_games) if len(team_games) > 0 else 0.5
            
            # Points per game
            home_ppg = home_games['home_score'].mean() if len(home_games) > 0 else 0
            away_ppg = away_games['away_score'].mean() if len(away_games) > 0 else 0
            avg_ppg = (home_ppg + away_ppg) / 2 if len(home_games) > 0 and len(away_games) > 0 else home_ppg or away_ppg
            
            # Points allowed per game
            home_papg = home_games['away_score'].mean() if len(home_games) > 0 else 0
            away_papg = away_games['home_score'].mean() if len(away_games) > 0 else 0
            avg_papg = (home_papg + away_papg) / 2 if len(home_games) > 0 and len(away_games) > 0 else home_papg or away_papg
            
            # Point differential
            point_diff = avg_ppg - avg_papg
            
            # Recent form (last 5 games)
            recent_games = team_games.tail(5)
            recent_wins = 0
            for _, game in recent_games.iterrows():
                if game['home_team'] == team and game['home_score'] > game['away_score']:
                    recent_wins += 1
                elif game['away_team'] == team and game['away_score'] > game['home_score']:
                    recent_wins += 1
            recent_form = recent_wins / len(recent_games) if len(recent_games) > 0 else 0.5
            
            # Home field advantage
            home_win_rate = home_wins / len(home_games) if len(home_games) > 0 else 0.5
            away_win_rate = away_wins / len(away_games) if len(away_games) > 0 else 0.5
            hfa = home_win_rate - away_win_rate
            
            team_metrics[team] = {
                'win_rate': win_rate,
                'points_per_game': avg_ppg,
                'points_allowed_per_game': avg_papg,
                'point_differential': point_diff,
                'recent_form': recent_form,
                'home_field_advantage': hfa,
                'total_games': len(team_games)
            }
        
        return team_metrics
    
    def _calculate_market_probabilities(self, team_metrics: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """Calculate market-implied probabilities for all games."""
        market_probs = []
        
        for _, game in self.games.iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Get team metrics
            home_metrics = team_metrics.get(home_team, {})
            away_metrics = team_metrics.get(away_team, {})
            
            if not home_metrics or not away_metrics:
                # Default to 50/50 if no data
                market_prob = 0.5
            else:
                # Calculate market probability using multiple factors
                market_prob = self._calculate_single_market_probability(
                    home_metrics, away_metrics, game
                )
            
            market_probs.append({
                'game_id': game['game_id'],
                'home_team': home_team,
                'away_team': away_team,
                'market_prob_home': market_prob,
                'market_prob_away': 1.0 - market_prob,
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'home_win': 1 if game['home_score'] > game['away_score'] else 0
            })
        
        return pd.DataFrame(market_probs)
    
    def _calculate_single_market_probability(self, home_metrics: Dict, away_metrics: Dict, game: pd.Series) -> float:
        """Calculate market probability for a single game."""
        # Base probability from win rates
        home_win_rate = home_metrics.get('win_rate', 0.5)
        away_win_rate = away_metrics.get('win_rate', 0.5)
        
        # Point differential factor
        home_point_diff = home_metrics.get('point_differential', 0.0)
        away_point_diff = away_metrics.get('point_differential', 0.0)
        point_diff_factor = (home_point_diff - away_point_diff) / 10.0  # Scale to reasonable range
        
        # Recent form factor
        home_recent_form = home_metrics.get('recent_form', 0.5)
        away_recent_form = away_metrics.get('recent_form', 0.5)
        recent_form_factor = (home_recent_form - away_recent_form) * 0.3  # Scale to reasonable range
        
        # Home field advantage
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
            raise ValueError("Market baseline not created. Call create_market_baseline() first.")
        
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
    
    def run_market_comparison(self, elo_config: EloConfig) -> Dict[str, Any]:
        """
        Run comprehensive comparison between Elo and market baseline.
        
        Args:
            elo_config: Elo configuration to test
            
        Returns:
            Dictionary with comparison results
        """
        print("\n" + "="*60)
        print("RUNNING MARKET COMPARISON")
        print("="*60)
        
        # Create market baseline
        market_baseline = self.create_market_baseline()
        
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
        print(f"\nCOMPARISON RESULTS:")
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


def run_market_integration_analysis(years: List[int] = [2022, 2023], sample_size: Optional[int] = None):
    """Run comprehensive market integration analysis."""
    # Load games
    games = load_games(years)
    if sample_size:
        games = games.head(sample_size)
    
    # Create market integration system
    market_system = MarketIntegration(years)
    
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
    
    comparison = market_system.run_market_comparison(elo_config)
    
    return comparison


if __name__ == "__main__":
    results = run_market_integration_analysis(sample_size=100)
