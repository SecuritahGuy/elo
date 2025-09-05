"""Injury-adjusted backtesting system for NFL Elo ratings."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from .evaluator import calculate_all_metrics
from .injury_integration import InjuryImpactCalculator
from ingest.nfl.data_loader import load_games


class InjuryBacktestSystem:
    """Backtesting system with injury adjustments."""
    
    def __init__(self, years: List[int] = [2022, 2023]):
        """
        Initialize injury backtesting system.
        
        Args:
            years: Years to analyze
        """
        self.years = years
        self.games = None
        self.injuries = None
        self.team_injury_df = None
        self.games_with_injuries = None
        self.injury_calculator = InjuryImpactCalculator()
        
        # Load data
        self._load_data()
    
    def _load_data(self):
        """Load all required data for injury backtesting."""
        print("Loading data for injury backtesting...")
        
        # Load games
        self.games = load_games(self.years)
        print(f"Loaded {len(self.games)} games")
        
        # Load injury data
        self.injuries = self.injury_calculator.load_injury_data(self.years)
        print(f"Loaded {len(self.injuries)} injury records")
        
        # Create team injury database
        self.team_injury_df = self.injury_calculator.create_team_injury_database(self.injuries)
        
        # Add injury data to games
        self.games_with_injuries = self.injury_calculator.add_injury_data_to_games(
            self.games, self.team_injury_df
        )
        print(f"Added injury data to {len(self.games_with_injuries)} games")
    
    def run_injury_backtest(self, config: EloConfig, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Run backtest with injury adjustments.
        
        Args:
            config: Elo configuration
            sample_size: Optional limit on games for testing
            
        Returns:
            Dictionary with backtest results
        """
        print(f"\n🏥 RUNNING INJURY BACKTEST")
        print("="*60)
        
        # Use sample if specified
        games_to_test = self.games_with_injuries
        if sample_size:
            games_to_test = games_to_test.head(sample_size)
        
        print(f"Testing {len(games_to_test)} games with injury data")
        
        # Run standard backtest first
        print("Running standard backtest (no injury adjustments)...")
        standard_config = config.model_copy()
        standard_config.use_injury_adjustment = False
        
        standard_result = run_backtest(games_to_test, standard_config)
        standard_metrics = standard_result['metrics']
        
        print(f"Standard Brier Score: {standard_metrics['brier_score']:.4f}")
        print(f"Standard Accuracy: {standard_metrics['accuracy']:.3f}")
        
        # Run injury-adjusted backtest
        print("\nRunning injury-adjusted backtest...")
        injury_config = config.model_copy()
        injury_config.use_injury_adjustment = True
        
        injury_result = run_backtest(games_to_test, injury_config)
        injury_metrics = injury_result['metrics']
        
        print(f"Injury-adjusted Brier Score: {injury_metrics['brier_score']:.4f}")
        print(f"Injury-adjusted Accuracy: {injury_metrics['accuracy']:.3f}")
        
        # Calculate improvement
        brier_improvement = ((standard_metrics['brier_score'] - injury_metrics['brier_score']) / 
                           standard_metrics['brier_score']) * 100
        accuracy_improvement = injury_metrics['accuracy'] - standard_metrics['accuracy']
        
        print(f"\nIMPROVEMENT ANALYSIS:")
        print(f"Brier Score Improvement: {brier_improvement:+.2f}%")
        print(f"Accuracy Improvement: {accuracy_improvement:+.3f}")
        
        if brier_improvement > 0.1:
            print("✅ SIGNIFICANT IMPROVEMENT FOUND!")
        elif brier_improvement > 0.0:
            print("⚠️  MINOR IMPROVEMENT FOUND")
        else:
            print("❌ NO IMPROVEMENT FOUND")
        
        return {
            'standard_result': standard_result,
            'injury_result': injury_result,
            'standard_metrics': standard_metrics,
            'injury_metrics': injury_metrics,
            'brier_improvement_pct': brier_improvement,
            'accuracy_improvement': accuracy_improvement,
            'significant_improvement': brier_improvement > 0.1
        }
    
    def test_injury_weight_optimization(self, base_config: EloConfig, 
                                      weight_range: Tuple[float, float] = (0.0, 2.0),
                                      step_size: float = 0.2) -> Dict[str, Any]:
        """
        Test different injury adjustment weights to find optimal values.
        
        Args:
            base_config: Base Elo configuration
            weight_range: Range of weights to test
            step_size: Step size for weight testing
            
        Returns:
            Dictionary with optimization results
        """
        print(f"\n🔧 TESTING INJURY WEIGHT OPTIMIZATION")
        print("="*60)
        print(f"Testing weights from {weight_range[0]} to {weight_range[1]}...")
        
        weights = np.arange(weight_range[0], weight_range[1] + step_size, step_size)
        results = []
        
        for weight in weights:
            print(f"Testing injury weight: {weight:.1f}")
            
            # Create config with this injury weight
            config = base_config.model_copy()
            config.use_injury_adjustment = True
            config.injury_adjustment_weight = weight
            
            try:
                # Run backtest
                result = self.run_injury_backtest(config, sample_size=100)
                
                results.append({
                    'weight': weight,
                    'brier_score': result['injury_metrics']['brier_score'],
                    'log_loss': result['injury_metrics']['log_loss'],
                    'accuracy': result['injury_metrics']['accuracy'],
                    'ece': result['injury_metrics']['ece'],
                    'sharpness': result['injury_metrics']['sharpness'],
                    'brier_improvement_pct': result['brier_improvement_pct']
                })
                
                print(f"  Brier Score: {result['injury_metrics']['brier_score']:.4f}, "
                      f"Improvement: {result['brier_improvement_pct']:+.2f}%")
                
            except Exception as e:
                print(f"  Error: {e}")
                results.append({
                    'weight': weight,
                    'brier_score': float('inf'),
                    'log_loss': float('inf'),
                    'accuracy': 0.0,
                    'ece': float('inf'),
                    'sharpness': 0.0,
                    'brier_improvement_pct': 0.0
                })
        
        # Find best weight
        results_df = pd.DataFrame(results)
        best_idx = results_df['brier_score'].idxmin()
        best_result = results_df.iloc[best_idx]
        
        print(f"\nOPTIMIZATION RESULTS:")
        print(f"Best injury weight: {best_result['weight']:.1f}")
        print(f"Best Brier Score: {best_result['brier_score']:.4f}")
        print(f"Best Improvement: {best_result['brier_improvement_pct']:+.2f}%")
        
        return {
            'weights_tested': weights.tolist(),
            'results': results,
            'best_weight': best_result['weight'],
            'best_brier_score': best_result['brier_score'],
            'best_improvement_pct': best_result['brier_improvement_pct']
        }
    
    def analyze_injury_impact_by_severity(self, config: EloConfig) -> Dict[str, Any]:
        """
        Analyze injury impact by injury severity and position.
        
        Args:
            config: Elo configuration
            
        Returns:
            Dictionary with analysis results
        """
        print(f"\n📊 ANALYZING INJURY IMPACT BY SEVERITY")
        print("="*60)
        
        # Categorize games by injury severity
        games = self.games_with_injuries.copy()
        
        # High injury impact games
        high_injury_games = games[
            (games['home_injury_impact'] > 3.0) | (games['away_injury_impact'] > 3.0)
        ]
        
        # Medium injury impact games
        medium_injury_games = games[
            ((games['home_injury_impact'] > 1.0) & (games['home_injury_impact'] <= 3.0)) |
            ((games['away_injury_impact'] > 1.0) & (games['away_injury_impact'] <= 3.0))
        ]
        
        # Low injury impact games
        low_injury_games = games[
            (games['home_injury_impact'] <= 1.0) & (games['away_injury_impact'] <= 1.0)
        ]
        
        print(f"High injury games (>3.0 impact): {len(high_injury_games)}")
        print(f"Medium injury games (1.0-3.0 impact): {len(medium_injury_games)}")
        print(f"Low injury games (≤1.0 impact): {len(low_injury_games)}")
        
        # Test each category
        categories = {
            'high_injury': high_injury_games,
            'medium_injury': medium_injury_games,
            'low_injury': low_injury_games
        }
        
        category_results = {}
        
        for category_name, category_games in categories.items():
            if len(category_games) < 5:  # Skip if too few games
                continue
                
            print(f"\nTesting {category_name} games ({len(category_games)} games)...")
            
            # Run backtest on this category
            standard_config = config.model_copy()
            standard_config.use_injury_adjustment = False
            
            injury_config = config.model_copy()
            injury_config.use_injury_adjustment = True
            
            try:
                # Standard backtest
                standard_result = run_backtest(category_games, standard_config)
                standard_metrics = standard_result['metrics']
                
                # Injury-adjusted backtest
                injury_result = run_backtest(category_games, injury_config)
                injury_metrics = injury_result['metrics']
                
                # Calculate improvement
                brier_improvement = ((standard_metrics['brier_score'] - injury_metrics['brier_score']) / 
                                   standard_metrics['brier_score']) * 100
                
                category_results[category_name] = {
                    'games_count': len(category_games),
                    'standard_brier': standard_metrics['brier_score'],
                    'injury_brier': injury_metrics['brier_score'],
                    'brier_improvement_pct': brier_improvement,
                    'standard_accuracy': standard_metrics['accuracy'],
                    'injury_accuracy': injury_metrics['accuracy']
                }
                
                print(f"  Standard Brier: {standard_metrics['brier_score']:.4f}")
                print(f"  Injury Brier: {injury_metrics['brier_score']:.4f}")
                print(f"  Improvement: {brier_improvement:+.2f}%")
                
            except Exception as e:
                print(f"  Error testing {category_name}: {e}")
                category_results[category_name] = {'error': str(e)}
        
        return category_results
    
    def run_comprehensive_injury_analysis(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Run comprehensive injury analysis.
        
        Args:
            sample_size: Optional limit on games for testing
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        print("🏥 COMPREHENSIVE INJURY ANALYSIS")
        print("="*80)
        
        # Create base configuration
        base_config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            use_qb_adjustment=True,
            use_injury_adjustment=True,
            injury_adjustment_weight=1.0
        )
        
        # Run basic injury backtest
        basic_results = self.run_injury_backtest(base_config, sample_size)
        
        # Run weight optimization
        optimization_results = self.test_injury_weight_optimization(base_config)
        
        # Run severity analysis
        severity_results = self.analyze_injury_impact_by_severity(base_config)
        
        # Summary
        print(f"\n" + "="*80)
        print("INJURY ANALYSIS SUMMARY")
        print("="*80)
        
        print(f"Basic Backtest Improvement: {basic_results['brier_improvement_pct']:+.2f}%")
        print(f"Best Weight: {optimization_results['best_weight']:.1f}")
        print(f"Best Weight Improvement: {optimization_results['best_improvement_pct']:+.2f}%")
        
        print(f"\nSeverity Analysis:")
        for category, results in severity_results.items():
            if 'error' not in results:
                print(f"  {category}: {results['brier_improvement_pct']:+.2f}% improvement "
                      f"({results['games_count']} games)")
        
        # Overall assessment
        max_improvement = max(
            basic_results['brier_improvement_pct'],
            optimization_results['best_improvement_pct']
        )
        
        if max_improvement > 0.1:
            print(f"\n✅ INJURY ADJUSTMENTS PROVIDE SIGNIFICANT IMPROVEMENT!")
        elif max_improvement > 0.0:
            print(f"\n⚠️  INJURY ADJUSTMENTS PROVIDE MINOR IMPROVEMENT")
        else:
            print(f"\n❌ INJURY ADJUSTMENTS PROVIDE NO IMPROVEMENT")
        
        return {
            'basic_results': basic_results,
            'optimization_results': optimization_results,
            'severity_results': severity_results,
            'max_improvement': max_improvement,
            'recommendation': 'enable' if max_improvement > 0.1 else 'disable'
        }


def run_injury_backtest_analysis(years: List[int] = [2022, 2023], sample_size: Optional[int] = None):
    """Run comprehensive injury backtest analysis."""
    system = InjuryBacktestSystem(years)
    return system.run_comprehensive_injury_analysis(sample_size)


if __name__ == "__main__":
    results = run_injury_backtest_analysis(sample_size=100)
