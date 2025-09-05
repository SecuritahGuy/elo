"""Enhanced backtest suite for validating environmental integrations."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
from datetime import datetime

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


class EnhancedBacktestSuite:
    """Comprehensive backtest suite for environmental integrations."""
    
    def __init__(self, years: List[int] = [2023], sample_size: Optional[int] = None):
        """
        Initialize the enhanced backtest suite.
        
        Args:
            years: Years to test
            sample_size: Optional limit on games for testing
        """
        self.years = years
        self.sample_size = sample_size
        self.results = {}
        
        # Load all required data
        print("Loading data for enhanced backtesting...")
        self._load_data()
        
    def _load_data(self):
        """Load all required data for backtesting."""
        # Load games data
        self.games = load_games(self.years)
        if self.sample_size:
            self.games = self.games.head(self.sample_size)
        print(f"Loaded {len(self.games)} games")
        
        # Load EPA data with environmental context
        self.epa_data = load_epa_with_weather_and_travel_context(self.years, sample_size=5000)
        print(f"Loaded {len(self.epa_data)} EPA plays with environmental context")
        
        # Load weather data
        self.weather_data = load_weather_data_with_retry(self.games)
        print(f"Loaded weather data for {len(self.weather_data)} games")
        
        # Load QB data
        self.qb_data = load_qb_performance(self.years)
        print(f"Loaded {len(self.qb_data)} QB performance records")
        
        # Initialize enhanced components
        self.enhanced_qb_tracker = EnhancedQBPerformanceTracker(
            qb_data=self.qb_data,
            games_data=self.games,
            adjusted_epa_data=self.epa_data
        )
        
        self.adjusted_epa_calculator = AdjustedEPACalculator(self.epa_data)
        
    def run_comprehensive_backtests(self) -> Dict[str, Any]:
        """
        Run comprehensive backtests comparing different configurations.
        
        Returns:
            Dictionary with all backtest results
        """
        print("\n" + "="*80)
        print("RUNNING COMPREHENSIVE ENHANCED BACKTESTS")
        print("="*80)
        
        # Test configurations
        configs = self._create_test_configurations()
        
        # Run backtests
        for config_name, config in configs.items():
            print(f"\n{'='*20} Testing {config_name} {'='*20}")
            result = self._run_single_backtest(config_name, config)
            self.results[config_name] = result
            
        # Generate comparison analysis
        comparison = self._generate_comparison_analysis()
        self.results['comparison'] = comparison
        
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
        
        # 2. Weather only
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
        
        # 4. QB only (standard)
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
        
        # 5. QB with environmental EPA
        configs['qb_enhanced'] = EloConfig(
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
        
        # 6. Weather + Travel
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
        
        # 7. All environmental adjustments
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
        
        # 8. All with enhanced QB (environmental EPA)
        configs['all_enhanced'] = EloConfig(
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
        
        return configs
    
    def _run_single_backtest(self, config_name: str, config: EloConfig) -> Dict[str, Any]:
        """Run a single backtest configuration."""
        print(f"Running backtest for {config_name}...")
        
        # Prepare data based on configuration
        if config.use_weather_adjustment:
            weather_data = self.weather_data
        else:
            weather_data = None
            
        if config.use_qb_adjustment:
            qb_data = self.qb_data
            epa_data = self.epa_data if 'enhanced' in config_name else None
        else:
            qb_data = None
            epa_data = None
        
        # Run backtest
        if 'enhanced' in config_name:
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
            
            # Convert to DataFrame for metrics
            if game_results:
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
                
                # Add environmental breakdown
                environmental_breakdown = elo_system.get_environmental_breakdown()
                
                return {
                    'config_name': config_name,
                    'metrics': metrics,
                    'environmental_breakdown': environmental_breakdown,
                    'game_results': results_df,
                    'total_games': len(game_results)
                }
            else:
                return {'error': 'No games processed successfully'}
        else:
            # Use standard backtest
            result = run_backtest(
                self.games, config, 
                qb_data=qb_data, 
                epa_data=epa_data, 
                weather_data=weather_data
            )
            
            # Add environmental breakdown if available
            environmental_breakdown = {}
            if hasattr(result, 'environmental_breakdown'):
                environmental_breakdown = result['environmental_breakdown']
            
            return {
                'config_name': config_name,
                'metrics': result['metrics'],
                'environmental_breakdown': environmental_breakdown,
                'game_results': result['history'],
                'total_games': len(result['history'])
            }
    
    def _generate_comparison_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive comparison analysis."""
        print("\nGenerating comparison analysis...")
        
        comparison = {
            'summary_table': self._create_summary_table(),
            'metric_comparisons': self._compare_metrics(),
            'environmental_impact_analysis': self._analyze_environmental_impacts(),
            'recommendations': self._generate_recommendations()
        }
        
        return comparison
    
    def _create_summary_table(self) -> pd.DataFrame:
        """Create summary table of all results."""
        summary_data = []
        
        for config_name, result in self.results.items():
            if config_name == 'comparison':
                continue
                
            if 'error' in result:
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
    
    def _compare_metrics(self) -> Dict[str, Any]:
        """Compare metrics across configurations."""
        baseline_metrics = self.results.get('baseline', {}).get('metrics', {})
        
        comparisons = {}
        for config_name, result in self.results.items():
            if config_name in ['comparison', 'baseline'] or 'error' in result:
                continue
                
            metrics = result.get('metrics', {})
            comparison = {}
            
            for metric_name in ['brier_score', 'log_loss', 'accuracy', 'mae', 'calibration', 'ece', 'sharpness']:
                baseline_value = baseline_metrics.get(metric_name, 0.0)
                current_value = metrics.get(metric_name, 0.0)
                
                if baseline_value != 0:
                    improvement = ((current_value - baseline_value) / baseline_value) * 100
                else:
                    improvement = 0.0
                
                comparison[metric_name] = {
                    'baseline': baseline_value,
                    'current': current_value,
                    'improvement_pct': improvement,
                    'is_better': self._is_metric_better(metric_name, current_value, baseline_value)
                }
            
            comparisons[config_name] = comparison
        
        return comparisons
    
    def _is_metric_better(self, metric_name: str, current: float, baseline: float) -> bool:
        """Determine if current metric is better than baseline."""
        # Lower is better for these metrics
        lower_is_better = ['brier_score', 'log_loss', 'mae', 'ece']
        # Higher is better for these metrics
        higher_is_better = ['accuracy', 'calibration', 'sharpness']
        
        if metric_name in lower_is_better:
            return current < baseline
        elif metric_name in higher_is_better:
            return current > baseline
        else:
            return current == baseline
    
    def _analyze_environmental_impacts(self) -> Dict[str, Any]:
        """Analyze environmental impact effectiveness."""
        analysis = {}
        
        for config_name, result in self.results.items():
            if config_name == 'comparison' or 'error' in result:
                continue
                
            env_breakdown = result.get('environmental_breakdown', {})
            if env_breakdown:
                analysis[config_name] = {
                    'total_environmental_impact': env_breakdown.get('overall', {}).get('total_environmental_impact', 0.0),
                    'avg_environmental_impact_per_game': env_breakdown.get('overall', {}).get('avg_environmental_impact_per_game', 0.0),
                    'weather_impact': env_breakdown.get('weather', {}).get('total_impact', 0.0),
                    'travel_impact': env_breakdown.get('travel', {}).get('total_impact', 0.0),
                    'qb_impact': env_breakdown.get('qb', {}).get('total_impact', 0.0),
                    'epa_impact': env_breakdown.get('epa', {}).get('total_impact', 0.0)
                }
        
        return analysis
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on results."""
        recommendations = []
        
        # Find best performing configuration
        best_config = None
        best_brier = float('inf')
        
        for config_name, result in self.results.items():
            if config_name == 'comparison' or 'error' in result:
                continue
                
            brier_score = result.get('metrics', {}).get('brier_score', float('inf'))
            if brier_score < best_brier:
                best_brier = brier_score
                best_config = config_name
        
        if best_config:
            recommendations.append(f"Best performing configuration: {best_config} (Brier Score: {best_brier:.4f})")
        
        # Analyze environmental impact effectiveness
        env_analysis = self._analyze_environmental_impacts()
        
        if 'weather_travel' in env_analysis and 'baseline' in self.results:
            weather_travel_brier = self.results['weather_travel'].get('metrics', {}).get('brier_score', 0.0)
            baseline_brier = self.results['baseline'].get('metrics', {}).get('brier_score', 0.0)
            
            if weather_travel_brier < baseline_brier:
                improvement = ((baseline_brier - weather_travel_brier) / baseline_brier) * 100
                recommendations.append(f"Weather + Travel adjustments improve Brier Score by {improvement:.2f}%")
        
        if 'all_enhanced' in env_analysis and 'all_environmental' in env_analysis:
            enhanced_brier = self.results['all_enhanced'].get('metrics', {}).get('brier_score', 0.0)
            standard_brier = self.results['all_environmental'].get('metrics', {}).get('brier_score', 0.0)
            
            if enhanced_brier < standard_brier:
                improvement = ((standard_brier - enhanced_brier) / standard_brier) * 100
                recommendations.append(f"Enhanced QB tracking (environmental EPA) improves Brier Score by {improvement:.2f}%")
        
        return recommendations
    
    def print_results(self):
        """Print comprehensive results."""
        print("\n" + "="*80)
        print("ENHANCED BACKTEST RESULTS")
        print("="*80)
        
        # Print summary table
        if 'comparison' in self.results:
            summary_table = self.results['comparison']['summary_table']
            print("\nSUMMARY TABLE:")
            print(summary_table.to_string(index=False))
        
        # Print metric comparisons
        if 'comparison' in self.results:
            print("\nMETRIC COMPARISONS (vs Baseline):")
            comparisons = self.results['comparison']['metric_comparisons']
            
            for config_name, comparison in comparisons.items():
                print(f"\n{config_name}:")
                for metric_name, data in comparison.items():
                    improvement = data['improvement_pct']
                    status = "✓" if data['is_better'] else "✗"
                    print(f"  {metric_name}: {data['current']:.4f} ({improvement:+.2f}%) {status}")
        
        # Print environmental impact analysis
        if 'comparison' in self.results:
            print("\nENVIRONMENTAL IMPACT ANALYSIS:")
            env_analysis = self.results['comparison']['environmental_impact_analysis']
            
            for config_name, analysis in env_analysis.items():
                print(f"\n{config_name}:")
                print(f"  Total Environmental Impact: {analysis['total_environmental_impact']:.2f}")
                print(f"  Avg Impact per Game: {analysis['avg_environmental_impact_per_game']:.2f}")
                print(f"  Weather Impact: {analysis['weather_impact']:.2f}")
                print(f"  Travel Impact: {analysis['travel_impact']:.2f}")
                print(f"  QB Impact: {analysis['qb_impact']:.2f}")
                print(f"  EPA Impact: {analysis['epa_impact']:.2f}")
        
        # Print recommendations
        if 'comparison' in self.results:
            print("\nRECOMMENDATIONS:")
            recommendations = self.results['comparison']['recommendations']
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
    
    def save_results(self, filename: str = None):
        """Save results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_backtest_results_{timestamp}.json"
        
        # Convert results to JSON-serializable format
        json_results = {}
        for config_name, result in self.results.items():
            if config_name == 'comparison':
                # Convert comparison results to JSON-serializable format
                json_comparison = {}
                for key, value in result.items():
                    if isinstance(value, pd.DataFrame):
                        json_comparison[key] = value.to_dict('records')
                    else:
                        json_comparison[key] = value
                json_results[config_name] = json_comparison
            else:
                json_results[config_name] = {
                    'config_name': result.get('config_name'),
                    'metrics': result.get('metrics'),
                    'environmental_breakdown': result.get('environmental_breakdown'),
                    'total_games': result.get('total_games')
                }
        
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        json_results = convert_numpy_types(json_results)
        
        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"Results saved to {filename}")


def run_enhanced_backtest_suite(years: List[int] = [2023], sample_size: Optional[int] = None):
    """Run the enhanced backtest suite."""
    suite = EnhancedBacktestSuite(years=years, sample_size=sample_size)
    results = suite.run_comprehensive_backtests()
    suite.print_results()
    suite.save_results()
    return results


if __name__ == "__main__":
    # Run comprehensive backtests
    results = run_enhanced_backtest_suite(years=[2023], sample_size=50)
