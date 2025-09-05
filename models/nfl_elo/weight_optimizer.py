"""Optimize environmental adjustment weights based on backtest results."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json
from itertools import product
from concurrent.futures import ThreadPoolExecutor
import time

from .config import EloConfig
from .backtest import run_backtest
from .enhanced_elo_system import EnhancedEloSystem
from .evaluator import calculate_all_metrics
from ingest.nfl.data_loader import load_games
from ingest.nfl.enhanced_epa_loader import load_epa_with_weather_and_travel_context
from ingest.nfl.weather_loader import load_weather_data_with_retry
from ingest.nfl.qb_data_loader import load_qb_performance
from models.nfl_elo.enhanced_qb_performance import EnhancedQBPerformanceTracker
from models.nfl_elo.adjusted_epa_calculator import AdjustedEPACalculator


class WeightOptimizer:
    """Optimize environmental adjustment weights based on backtest performance."""
    
    def __init__(self, years: List[int] = [2022, 2023], sample_size: int = 100):
        """Initialize the weight optimizer."""
        self.years = years
        self.sample_size = sample_size
        self.results = {}
        
        # Load data
        print("Loading data for weight optimization...")
        self._load_data()
        
    def _load_data(self):
        """Load all required data."""
        # Load games data
        self.games = load_games(self.years)
        if self.sample_size:
            self.games = self.games.head(self.sample_size)
        print(f"Loaded {len(self.games)} games")
        
        # Load weather data
        self.weather_data = load_weather_data_with_retry(self.games)
        print(f"Loaded weather data for {len(self.weather_data)} games")
        
        # Load EPA data
        self.epa_data = load_epa_with_weather_and_travel_context(self.years, sample_size=2000)
        print(f"Loaded {len(self.epa_data)} EPA plays")
        
        # Load QB data
        self.qb_data = load_qb_performance(self.years)
        print(f"Loaded {len(self.qb_data)} QB performance records")
        
        # Initialize components
        self.enhanced_qb_tracker = EnhancedQBPerformanceTracker(
            qb_data=self.qb_data,
            games_data=self.games,
            adjusted_epa_data=self.epa_data
        )
        
        self.adjusted_epa_calculator = AdjustedEPACalculator(self.epa_data)
        
    def optimize_weights(self, param_ranges: Dict[str, List[float]] = None) -> Dict[str, Any]:
        """Optimize environmental adjustment weights."""
        if param_ranges is None:
            param_ranges = self._get_default_param_ranges()
        
        print(f"\nOptimizing weights with {len(param_ranges)} parameter sets...")
        
        # Generate all parameter combinations
        param_combinations = self._generate_param_combinations(param_ranges)
        print(f"Testing {len(param_combinations)} combinations...")
        
        # Test each combination
        best_score = float('inf')
        best_params = None
        results = []
        
        for i, params in enumerate(param_combinations):
            if i % 10 == 0:
                print(f"Testing combination {i+1}/{len(param_combinations)}...")
            
            try:
                score, metrics = self._test_parameter_set(params)
                results.append({
                    'params': params,
                    'brier_score': score,
                    'metrics': metrics
                })
                
                if score < best_score:
                    best_score = score
                    best_params = params
                    print(f"  New best: {score:.4f} with {params}")
                    
            except Exception as e:
                print(f"  Error testing {params}: {e}")
                continue
        
        # Sort results by Brier score
        results.sort(key=lambda x: x['brier_score'])
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'all_results': results[:10],  # Top 10 results
            'total_tested': len(results)
        }
    
    def _get_default_param_ranges(self) -> Dict[str, List[float]]:
        """Get default parameter ranges for optimization."""
        return {
            'weather_adjustment_weight': [0.5, 1.0, 1.5, 2.0],
            'weather_max_delta': [3.0, 5.0, 7.0, 10.0],
            'travel_adjustment_weight': [0.5, 1.0, 1.5, 2.0],
            'travel_max_delta': [2.0, 3.0, 4.0, 5.0],
            'qb_adjustment_weight': [0.5, 1.0, 1.5, 2.0],
            'qb_max_delta': [5.0, 10.0, 15.0, 20.0]
        }
    
    def _generate_param_combinations(self, param_ranges: Dict[str, List[float]]) -> List[Dict[str, float]]:
        """Generate all parameter combinations."""
        keys = list(param_ranges.keys())
        values = list(param_ranges.values())
        
        combinations = []
        for combo in product(*values):
            combinations.append(dict(zip(keys, combo)))
        
        return combinations
    
    def _test_parameter_set(self, params: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """Test a specific parameter set."""
        # Create configuration with optimized parameters
        config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=True,
            weather_adjustment_weight=params['weather_adjustment_weight'],
            weather_max_delta=params['weather_max_delta'],
            use_travel_adjustment=True,
            travel_adjustment_weight=params['travel_adjustment_weight'],
            travel_max_delta=params['travel_max_delta'],
            use_qb_adjustment=True,
            qb_adjustment_weight=params['qb_adjustment_weight'],
            qb_max_delta=params['qb_max_delta']
        )
        
        # Run backtest
        result = run_backtest(
            self.games, 
            config, 
            qb_data=self.qb_data, 
            epa_data=self.epa_data, 
            weather_data=self.weather_data
        )
        
        return result['metrics']['brier_score'], result['metrics']
    
    def optimize_enhanced_weights(self, param_ranges: Dict[str, List[float]] = None) -> Dict[str, Any]:
        """Optimize weights for enhanced Elo system with environmental EPA."""
        if param_ranges is None:
            param_ranges = self._get_enhanced_param_ranges()
        
        print(f"\nOptimizing enhanced weights with {len(param_ranges)} parameter sets...")
        
        # Generate all parameter combinations
        param_combinations = self._generate_param_combinations(param_ranges)
        print(f"Testing {len(param_combinations)} combinations...")
        
        # Test each combination
        best_score = float('inf')
        best_params = None
        results = []
        
        for i, params in enumerate(param_combinations):
            if i % 10 == 0:
                print(f"Testing enhanced combination {i+1}/{len(param_combinations)}...")
            
            try:
                score, metrics = self._test_enhanced_parameter_set(params)
                results.append({
                    'params': params,
                    'brier_score': score,
                    'metrics': metrics
                })
                
                if score < best_score:
                    best_score = score
                    best_params = params
                    print(f"  New best enhanced: {score:.4f} with {params}")
                    
            except Exception as e:
                print(f"  Error testing enhanced {params}: {e}")
                continue
        
        # Sort results by Brier score
        results.sort(key=lambda x: x['brier_score'])
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'all_results': results[:10],  # Top 10 results
            'total_tested': len(results)
        }
    
    def _get_enhanced_param_ranges(self) -> Dict[str, List[float]]:
        """Get parameter ranges for enhanced optimization."""
        return {
            'weather_adjustment_weight': [0.5, 1.0, 1.5],
            'weather_max_delta': [3.0, 5.0, 7.0],
            'travel_adjustment_weight': [0.5, 1.0, 1.5],
            'travel_max_delta': [2.0, 3.0, 4.0],
            'qb_adjustment_weight': [0.5, 1.0, 1.5],
            'qb_max_delta': [5.0, 10.0, 15.0]
        }
    
    def _test_enhanced_parameter_set(self, params: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """Test enhanced parameter set."""
        # Create configuration
        config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=True,
            weather_adjustment_weight=params['weather_adjustment_weight'],
            weather_max_delta=params['weather_max_delta'],
            use_travel_adjustment=True,
            travel_adjustment_weight=params['travel_adjustment_weight'],
            travel_max_delta=params['travel_max_delta'],
            use_qb_adjustment=True,
            qb_adjustment_weight=params['qb_adjustment_weight'],
            qb_max_delta=params['qb_max_delta']
        )
        
        # Use enhanced Elo system
        elo_system = EnhancedEloSystem(
            config=config,
            enhanced_qb_tracker=self.enhanced_qb_tracker,
            adjusted_epa_calculator=self.adjusted_epa_calculator
        )
        
        # Process games
        game_results = []
        for idx, game in self.games.iterrows():
            try:
                result = elo_system.process_game(game)
                game_results.append(result)
            except Exception as e:
                print(f"Error processing game {idx}: {e}")
                continue
        
        if not game_results:
            return float('inf'), {}
        
        # Convert to DataFrame for metrics
        results_df = pd.DataFrame([
            {
                'home_team': gr.home_team,
                'away_team': gr.away_team,
                'home_score': gr.home_score,
                'away_score': gr.away_score,
                'p_home': gr.p_home,
                'actual_result': gr.actual_result
            }
            for gr in game_results
        ])
        
        # Calculate metrics
        metrics_df = pd.DataFrame({
            'p_home': results_df['p_home'],
            'home_win': results_df['actual_result']
        })
        metrics = calculate_all_metrics(metrics_df)
        
        return metrics['brier_score'], metrics
    
    def print_optimization_results(self, results: Dict[str, Any]):
        """Print optimization results."""
        print("\n" + "="*80)
        print("WEIGHT OPTIMIZATION RESULTS")
        print("="*80)
        
        print(f"\nBest Parameters:")
        for param, value in results['best_params'].items():
            print(f"  {param}: {value}")
        
        print(f"\nBest Brier Score: {results['best_score']:.4f}")
        print(f"Total Combinations Tested: {results['total_tested']}")
        
        print(f"\nTop 10 Results:")
        for i, result in enumerate(results['all_results'][:10], 1):
            print(f"{i:2d}. Brier: {result['brier_score']:.4f} - {result['params']}")
    
    def save_optimized_config(self, results: Dict[str, Any], filename: str = None):
        """Save optimized configuration to file."""
        if filename is None:
            timestamp = int(time.time())
            filename = f"optimized_config_{timestamp}.json"
        
        config = {
            "base_rating": 1500.0,
            "k": 20.0,
            "hfa_points": 55.0,
            "mov_enabled": True,
            "preseason_regress": 0.75,
            "use_weather_adjustment": True,
            "weather_adjustment_weight": results['best_params']['weather_adjustment_weight'],
            "weather_max_delta": results['best_params']['weather_max_delta'],
            "use_travel_adjustment": True,
            "travel_adjustment_weight": results['best_params']['travel_adjustment_weight'],
            "travel_max_delta": results['best_params']['travel_max_delta'],
            "use_qb_adjustment": True,
            "qb_adjustment_weight": results['best_params']['qb_adjustment_weight'],
            "qb_max_delta": results['best_params']['qb_max_delta']
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Optimized configuration saved to {filename}")
        return filename


def run_weight_optimization(years: List[int] = [2022, 2023], sample_size: int = 100, enhanced: bool = True):
    """Run weight optimization."""
    optimizer = WeightOptimizer(years=years, sample_size=sample_size)
    
    if enhanced:
        results = optimizer.optimize_enhanced_weights()
    else:
        results = optimizer.optimize_weights()
    
    optimizer.print_optimization_results(results)
    config_file = optimizer.save_optimized_config(results)
    
    return results, config_file


if __name__ == "__main__":
    results, config_file = run_weight_optimization(sample_size=50, enhanced=True)
