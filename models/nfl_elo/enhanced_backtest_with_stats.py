"""Enhanced backtest with real weather data and stats storage."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import time
from datetime import datetime

from .config import EloConfig
from .backtest import run_backtest
from .enhanced_elo_system import EnhancedEloSystem
from .evaluator import calculate_all_metrics
from .stats_storage import get_stats_storage
from ingest.nfl.data_loader import load_games
from ingest.nfl.enhanced_epa_loader import load_epa_with_weather_and_travel_context
from ingest.nfl.weather_loader import load_weather_data_with_retry
from ingest.nfl.qb_data_loader import load_qb_performance
from models.nfl_elo.enhanced_qb_performance import EnhancedQBPerformanceTracker
from models.nfl_elo.adjusted_epa_calculator import AdjustedEPACalculator


class EnhancedBacktestWithStats:
    """Enhanced backtest with real weather data and comprehensive stats storage."""
    
    def __init__(self, years: List[int] = [2022, 2023], sample_size: Optional[int] = None):
        """
        Initialize enhanced backtest with stats storage.
        
        Args:
            years: Years to test
            sample_size: Optional limit on games for testing
        """
        self.years = years
        self.sample_size = sample_size
        self.stats_storage = get_stats_storage()
        self.results = {}
        
        # Load all required data
        print("Loading data for enhanced backtesting with real weather...")
        self._load_data()
        
    def _load_data(self):
        """Load all required data."""
        # Load games data
        self.games = load_games(self.years)
        if self.sample_size:
            self.games = self.games.head(self.sample_size)
        print(f"Loaded {len(self.games)} games")
        
        # Load weather data with real API (no fallback)
        print("Loading real weather data (this may take a few minutes)...")
        self.weather_data = load_weather_data_with_retry(
            self.games, 
            use_fallback=False  # Use real weather data
        )
        print(f"Loaded weather data for {len(self.weather_data)} games")
        
        # Load EPA data
        self.epa_data = load_epa_with_weather_and_travel_context(self.years, sample_size=5000)
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
        
    def run_comprehensive_backtests(self) -> Dict[str, Any]:
        """
        Run comprehensive backtests with real weather data and stats storage.
        
        Returns:
            Dictionary with all backtest results
        """
        print("\n" + "="*80)
        print("RUNNING ENHANCED BACKTESTS WITH REAL WEATHER DATA")
        print("="*80)
        
        # Test configurations
        configs = self._create_test_configurations()
        
        # Run backtests
        for config_name, config in configs.items():
            print(f"\n{'='*20} Testing {config_name} {'='*20}")
            start_time = time.time()
            
            result = self._run_single_backtest(config_name, config)
            self.results[config_name] = result
            
            # Store results in database
            if 'error' not in result:
                self._store_backtest_result(config_name, config, result)
            
            elapsed_time = time.time() - start_time
            print(f"Completed {config_name} in {elapsed_time:.2f} seconds")
            
        # Generate comparison analysis
        comparison = self._generate_comparison_analysis()
        self.results['comparison'] = comparison
        
        # Store environmental impacts
        self._store_environmental_impacts()
        
        return self.results
    
    def _create_test_configurations(self) -> Dict[str, EloConfig]:
        """Create test configurations for comparison."""
        configs = {}
        
        # 1. Baseline (no environmental adjustments)
        configs['baseline'] = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=False,
            use_qb_adjustment=False
        )
        
        # 2. Weather only (with real weather data)
        configs['weather_only'] = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=True,
            weather_adjustment_weight=1.0,
            weather_max_delta=5.0,
            use_travel_adjustment=False,
            use_qb_adjustment=False
        )
        
        # 3. Travel only
        configs['travel_only'] = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=True,
            travel_adjustment_weight=1.0,
            travel_max_delta=3.0,
            use_qb_adjustment=False
        )
        
        # 4. QB only
        configs['qb_only'] = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=False,
            use_qb_adjustment=True,
            qb_adjustment_weight=1.0,
            qb_max_delta=10.0
        )
        
        # 5. Weather + Travel
        configs['weather_travel'] = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=True,
            weather_adjustment_weight=1.0,
            weather_max_delta=5.0,
            use_travel_adjustment=True,
            travel_adjustment_weight=1.0,
            travel_max_delta=3.0,
            use_qb_adjustment=False
        )
        
        # 6. All environmental
        configs['all_environmental'] = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=True,
            weather_adjustment_weight=1.0,
            weather_max_delta=5.0,
            use_travel_adjustment=True,
            travel_adjustment_weight=1.0,
            travel_max_delta=3.0,
            use_qb_adjustment=True,
            qb_adjustment_weight=1.0,
            qb_max_delta=10.0
        )
        
        # 7. Enhanced (with environmental EPA)
        configs['enhanced'] = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=True,
            weather_adjustment_weight=0.5,
            weather_max_delta=3.0,
            use_travel_adjustment=True,
            travel_adjustment_weight=0.5,
            travel_max_delta=2.0,
            use_qb_adjustment=True,
            qb_adjustment_weight=1.5,
            qb_max_delta=5.0
        )
        
        return configs
    
    def _run_single_backtest(self, config_name: str, config: EloConfig) -> Dict[str, Any]:
        """Run a single backtest configuration."""
        print(f"Running backtest for {config_name}...")
        
        try:
            if config_name == 'enhanced':
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
                    return {'error': 'No games processed successfully'}
                
                # Convert to DataFrame for metrics
                results_df = pd.DataFrame([
                    {
                        'home_team': gr.home_team,
                        'away_team': gr.away_team,
                        'home_score': gr.home_score,
                        'away_score': gr.away_score,
                        'p_home': gr.p_home,
                        'actual_result': gr.actual_result,
                        'weather_impact': gr.weather_impact,
                        'travel_impact': gr.travel_impact,
                        'qb_impact': gr.qb_impact,
                        'epa_impact': gr.epa_impact,
                        'total_environmental_impact': gr.total_environmental_impact
                    }
                    for gr in game_results
                ])
                
                # Calculate metrics
                metrics_df = pd.DataFrame({
                    'p_home': results_df['p_home'],
                    'home_win': results_df['actual_result']
                })
                metrics = calculate_all_metrics(metrics_df)
                
                # Environmental breakdown
                environmental_breakdown = elo_system.get_environmental_breakdown()
                
                return {
                    'config_name': config_name,
                    'metrics': metrics,
                    'environmental_breakdown': environmental_breakdown,
                    'game_results': results_df,
                    'total_games': len(game_results)
                }
            else:
                # Use standard backtest
                result = run_backtest(
                    self.games, config, 
                    qb_data=self.qb_data, 
                    epa_data=self.epa_data, 
                    weather_data=self.weather_data
                )
                
                return {
                    'config_name': config_name,
                    'metrics': result['metrics'],
                    'environmental_breakdown': {},
                    'game_results': result['history'],
                    'total_games': len(result['history'])
                }
                
        except Exception as e:
            print(f"Error running backtest for {config_name}: {e}")
            return {'error': str(e)}
    
    def _store_backtest_result(self, config_name: str, config: EloConfig, result: Dict[str, Any]):
        """Store backtest result in database."""
        try:
            metrics = result['metrics']
            environmental_breakdown = result.get('environmental_breakdown', {})
            
            # Calculate total environmental impact
            total_impact = 0.0
            if environmental_breakdown:
                overall = environmental_breakdown.get('overall', {})
                total_impact = overall.get('total_environmental_impact', 0.0)
            
            self.stats_storage.store_backtest_result(
                config_name=config_name,
                years=self.years,
                sample_size=self.sample_size,
                metrics=metrics,
                environmental_impact=total_impact,
                config=config
            )
            
            print(f"Stored backtest result for {config_name}")
            
        except Exception as e:
            print(f"Error storing backtest result for {config_name}: {e}")
    
    def _store_environmental_impacts(self):
        """Store environmental impact data."""
        try:
            for config_name, result in self.results.items():
                if config_name == 'comparison' or 'error' in result:
                    continue
                
                env_breakdown = result.get('environmental_breakdown', {})
                if env_breakdown:
                    weather = env_breakdown.get('weather', {})
                    travel = env_breakdown.get('travel', {})
                    qb = env_breakdown.get('qb', {})
                    epa = env_breakdown.get('epa', {})
                    overall = env_breakdown.get('overall', {})
                    
                    self.stats_storage.store_environmental_impact(
                        config_name=config_name,
                        weather_impact=weather.get('total_impact', 0.0),
                        travel_impact=travel.get('total_impact', 0.0),
                        qb_impact=qb.get('total_impact', 0.0),
                        epa_impact=epa.get('total_impact', 0.0),
                        total_impact=overall.get('total_environmental_impact', 0.0),
                        avg_impact_per_game=overall.get('avg_environmental_impact_per_game', 0.0)
                    )
            
            print("Stored environmental impact data")
            
        except Exception as e:
            print(f"Error storing environmental impacts: {e}")
    
    def _generate_comparison_analysis(self) -> Dict[str, Any]:
        """Generate comparison analysis."""
        comparison = {
            'summary_table': self._create_summary_table(),
            'performance_ranking': self._rank_performances(),
            'improvement_analysis': self._analyze_improvements(),
            'environmental_impact_summary': self._summarize_environmental_impacts()
        }
        
        return comparison
    
    def _create_summary_table(self) -> pd.DataFrame:
        """Create summary table of all results."""
        summary_data = []
        
        for config_name, result in self.results.items():
            if config_name == 'comparison' or 'error' in result:
                continue
                
            metrics = result['metrics']
            summary_data.append({
                'Configuration': config_name,
                'Brier Score': metrics.get('brier_score', 0.0),
                'Log Loss': metrics.get('log_loss', 0.0),
                'Accuracy': metrics.get('accuracy', 0.0),
                'MAE': metrics.get('mae', 0.0),
                'Calibration': metrics.get('calibration', 0.0),
                'ECE': metrics.get('ece', 0.0),
                'Sharpness': metrics.get('sharpness', 0.0),
                'Total Games': result.get('total_games', 0)
            })
        
        return pd.DataFrame(summary_data)
    
    def _rank_performances(self) -> List[Dict[str, Any]]:
        """Rank configurations by performance."""
        rankings = []
        
        for config_name, result in self.results.items():
            if config_name == 'comparison' or 'error' in result:
                continue
                
            metrics = result['metrics']
            rankings.append({
                'configuration': config_name,
                'brier_score': metrics.get('brier_score', 0.0),
                'accuracy': metrics.get('accuracy', 0.0),
                'calibration': metrics.get('calibration', 0.0)
            })
        
        # Sort by Brier score (lower is better)
        rankings.sort(key=lambda x: x['brier_score'])
        
        return rankings
    
    def _analyze_improvements(self) -> Dict[str, Any]:
        """Analyze improvements over baseline."""
        baseline_brier = self.results.get('baseline', {}).get('metrics', {}).get('brier_score', 0.0)
        
        improvements = {}
        for config_name, result in self.results.items():
            if config_name in ['comparison', 'baseline'] or 'error' in result:
                continue
                
            brier_score = result['metrics']['brier_score']
            improvement = ((baseline_brier - brier_score) / baseline_brier) * 100
            
            improvements[config_name] = {
                'brier_score': brier_score,
                'improvement_pct': improvement,
                'is_better': improvement > 0
            }
        
        return improvements
    
    def _summarize_environmental_impacts(self) -> Dict[str, Any]:
        """Summarize environmental impacts across configurations."""
        impacts = {}
        
        for config_name, result in self.results.items():
            if config_name == 'comparison' or 'error' in result:
                continue
                
            env_breakdown = result.get('environmental_breakdown', {})
            if env_breakdown:
                impacts[config_name] = {
                    'total_environmental_impact': env_breakdown.get('overall', {}).get('total_environmental_impact', 0.0),
                    'avg_environmental_impact_per_game': env_breakdown.get('overall', {}).get('avg_environmental_impact_per_game', 0.0),
                    'weather_impact': env_breakdown.get('weather', {}).get('total_impact', 0.0),
                    'travel_impact': env_breakdown.get('travel', {}).get('total_impact', 0.0),
                    'qb_impact': env_breakdown.get('qb', {}).get('total_impact', 0.0),
                    'epa_impact': env_breakdown.get('epa', {}).get('total_impact', 0.0)
                }
        
        return impacts
    
    def print_results(self):
        """Print comprehensive results."""
        print("\n" + "="*80)
        print("ENHANCED BACKTEST RESULTS WITH REAL WEATHER DATA")
        print("="*80)
        
        # Print summary table
        if 'comparison' in self.results:
            summary_table = self.results['comparison']['summary_table']
            print("\nSUMMARY TABLE:")
            print(summary_table.to_string(index=False))
        
        # Print performance ranking
        if 'comparison' in self.results:
            print("\nPERFORMANCE RANKING:")
            rankings = self.results['comparison']['performance_ranking']
            for i, ranking in enumerate(rankings, 1):
                print(f"{i:2d}. {ranking['configuration']:20s} - Brier: {ranking['brier_score']:.4f}, Accuracy: {ranking['accuracy']:.3f}")
        
        # Print improvement analysis
        if 'comparison' in self.results:
            print("\nIMPROVEMENT ANALYSIS (vs Baseline):")
            improvements = self.results['comparison']['improvement_analysis']
            for config_name, improvement in improvements.items():
                status = "✓" if improvement['is_better'] else "✗"
                print(f"  {config_name:20s}: {improvement['improvement_pct']:+6.2f}% {status}")
        
        # Print environmental impact summary
        if 'comparison' in self.results:
            print("\nENVIRONMENTAL IMPACT SUMMARY:")
            impacts = self.results['comparison']['environmental_impact_summary']
            for config_name, impact in impacts.items():
                print(f"\n{config_name}:")
                print(f"  Total Environmental Impact: {impact['total_environmental_impact']:.2f}")
                print(f"  Avg Impact per Game: {impact['avg_environmental_impact_per_game']:.2f}")
                print(f"  Weather Impact: {impact['weather_impact']:.2f}")
                print(f"  Travel Impact: {impact['travel_impact']:.2f}")
                print(f"  QB Impact: {impact['qb_impact']:.2f}")
                print(f"  EPA Impact: {impact['epa_impact']:.2f}")
    
    def get_performance_summary(self):
        """Get performance summary from stats storage."""
        summary = self.stats_storage.get_performance_summary(days_back=1)
        print("\nPERFORMANCE SUMMARY FROM DATABASE:")
        for key, value in summary.items():
            print(f"  {key}: {value}")


def run_enhanced_backtest_with_real_weather(years: List[int] = [2022, 2023], sample_size: Optional[int] = None):
    """Run enhanced backtest with real weather data and stats storage."""
    backtest = EnhancedBacktestWithStats(years=years, sample_size=sample_size)
    results = backtest.run_comprehensive_backtests()
    backtest.print_results()
    backtest.get_performance_summary()
    return results


if __name__ == "__main__":
    results = run_enhanced_backtest_with_real_weather(sample_size=50)
