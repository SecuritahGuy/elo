"""Weather diagnostic analyzer for NFL Elo system."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Optional plotting imports
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

from .config import EloConfig
from .backtest import run_backtest
from .evaluator import calculate_all_metrics
from ingest.nfl.data_loader import load_games
from ingest.nfl.weather_loader import load_weather_data_with_retry
from ingest.nfl.qb_data_loader import load_qb_performance
from ingest.nfl.enhanced_epa_loader import load_epa_with_weather_and_travel_context


class WeatherDiagnosticAnalyzer:
    """Comprehensive weather impact analysis and optimization."""
    
    def __init__(self, years: List[int] = [2022, 2023], sample_size: Optional[int] = None):
        """
        Initialize weather diagnostic analyzer.
        
        Args:
            years: Years to analyze
            sample_size: Optional limit on games for testing
        """
        self.years = years
        self.sample_size = sample_size
        self.games = None
        self.weather_data = None
        self.qb_data = None
        self.epa_data = None
        self.results = {}
        
        # Load data
        self._load_data()
    
    def _load_data(self):
        """Load all required data for analysis."""
        print("Loading data for weather diagnostic analysis...")
        
        # Load games
        self.games = load_games(self.years)
        if self.sample_size:
            self.games = self.games.head(self.sample_size)
        print(f"Loaded {len(self.games)} games")
        
        # Load weather data with real API
        print("Loading real weather data...")
        self.weather_data = load_weather_data_with_retry(
            self.games, 
            use_fallback=False
        )
        print(f"Loaded weather data for {len(self.weather_data)} games")
        
        # Load QB data
        self.qb_data = load_qb_performance(self.years)
        print(f"Loaded {len(self.qb_data)} QB performance records")
        
        # Load EPA data
        self.epa_data = load_epa_with_weather_and_travel_context(self.years, sample_size=5000)
        print(f"Loaded {len(self.epa_data)} EPA plays")
    
    def analyze_weather_conditions(self) -> Dict[str, Any]:
        """
        Analyze weather conditions in the dataset.
        
        Returns:
            Dictionary with weather condition analysis
        """
        print("\n" + "="*60)
        print("WEATHER CONDITIONS ANALYSIS")
        print("="*60)
        
        # Merge games with weather data
        games_with_weather = self.games.merge(
            self.weather_data[['game_id', 'home_temp', 'home_wind', 'home_precip', 
                             'away_temp', 'away_wind', 'away_precip']], 
            on='game_id', 
            how='left'
        )
        
        # Basic weather statistics
        weather_stats = {
            'total_games': len(games_with_weather),
            'games_with_weather_data': len(games_with_weather.dropna(subset=['home_temp'])),
            'temperature_stats': {
                'home_temp_mean': games_with_weather['home_temp'].mean(),
                'home_temp_std': games_with_weather['home_temp'].std(),
                'home_temp_min': games_with_weather['home_temp'].min(),
                'home_temp_max': games_with_weather['home_temp'].max(),
                'away_temp_mean': games_with_weather['away_temp'].mean(),
                'away_temp_std': games_with_weather['away_temp'].std(),
            },
            'wind_stats': {
                'home_wind_mean': games_with_weather['home_wind'].mean(),
                'home_wind_std': games_with_weather['home_wind'].std(),
                'home_wind_max': games_with_weather['home_wind'].max(),
                'away_wind_mean': games_with_weather['away_wind'].mean(),
                'away_wind_std': games_with_weather['away_wind'].std(),
            },
            'precipitation_stats': {
                'home_precip_mean': games_with_weather['home_precip'].mean(),
                'home_precip_std': games_with_weather['home_precip'].std(),
                'home_precip_max': games_with_weather['home_precip'].max(),
                'away_precip_mean': games_with_weather['away_precip'].mean(),
                'away_precip_std': games_with_weather['away_precip'].std(),
            }
        }
        
        # Weather condition categories
        games_with_weather['weather_category'] = self._categorize_weather_conditions(games_with_weather)
        weather_categories = games_with_weather['weather_category'].value_counts()
        
        weather_stats['weather_categories'] = weather_categories.to_dict()
        
        # Print analysis
        print(f"Total games: {weather_stats['total_games']}")
        print(f"Games with weather data: {weather_stats['games_with_weather_data']}")
        print(f"Weather data coverage: {weather_stats['games_with_weather_data']/weather_stats['total_games']*100:.1f}%")
        
        print(f"\nTemperature Analysis:")
        print(f"  Home temp: {weather_stats['temperature_stats']['home_temp_mean']:.1f}°F ± {weather_stats['temperature_stats']['home_temp_std']:.1f}°F")
        print(f"  Away temp: {weather_stats['temperature_stats']['away_temp_mean']:.1f}°F ± {weather_stats['temperature_stats']['away_temp_std']:.1f}°F")
        print(f"  Range: {weather_stats['temperature_stats']['home_temp_min']:.1f}°F to {weather_stats['temperature_stats']['home_temp_max']:.1f}°F")
        
        print(f"\nWind Analysis:")
        print(f"  Home wind: {weather_stats['wind_stats']['home_wind_mean']:.1f} mph ± {weather_stats['wind_stats']['home_wind_std']:.1f} mph")
        print(f"  Away wind: {weather_stats['wind_stats']['away_wind_mean']:.1f} mph ± {weather_stats['wind_stats']['away_wind_std']:.1f} mph")
        print(f"  Max wind: {weather_stats['wind_stats']['home_wind_max']:.1f} mph")
        
        print(f"\nPrecipitation Analysis:")
        print(f"  Home precip: {weather_stats['precipitation_stats']['home_precip_mean']:.2f} mm ± {weather_stats['precipitation_stats']['home_precip_std']:.2f} mm")
        print(f"  Away precip: {weather_stats['precipitation_stats']['away_precip_mean']:.2f} mm ± {weather_stats['precipitation_stats']['away_precip_std']:.2f} mm")
        print(f"  Max precip: {weather_stats['precipitation_stats']['home_precip_max']:.2f} mm")
        
        print(f"\nWeather Categories:")
        for category, count in weather_categories.items():
            print(f"  {category}: {count} games ({count/len(games_with_weather)*100:.1f}%)")
        
        self.results['weather_conditions'] = weather_stats
        return weather_stats
    
    def _categorize_weather_conditions(self, games_df: pd.DataFrame) -> pd.Series:
        """Categorize games by weather conditions."""
        categories = []
        
        for _, game in games_df.iterrows():
            if pd.isna(game['home_temp']):
                categories.append('no_data')
                continue
                
            temp = game['home_temp']
            wind = game['home_wind']
            precip = game['home_precip']
            
            if temp < 32 and wind > 15:
                categories.append('extreme_cold_windy')
            elif temp < 32:
                categories.append('extreme_cold')
            elif temp < 45 and wind > 15:
                categories.append('cold_windy')
            elif temp < 45:
                categories.append('cold')
            elif wind > 20:
                categories.append('very_windy')
            elif wind > 15:
                categories.append('windy')
            elif precip > 5:
                categories.append('rainy')
            elif temp > 85:
                categories.append('hot')
            else:
                categories.append('mild')
        
        return pd.Series(categories, index=games_df.index)
    
    def test_weather_weight_optimization(self) -> Dict[str, Any]:
        """
        Test different weather adjustment weights to find optimal values.
        
        Returns:
            Dictionary with optimization results
        """
        print("\n" + "="*60)
        print("WEATHER WEIGHT OPTIMIZATION")
        print("="*60)
        
        # Test weights from 0.0 to 3.0 in 0.2 increments
        weights = np.arange(0.0, 3.2, 0.2)
        results = []
        
        print(f"Testing {len(weights)} different weather weights...")
        
        for weight in weights:
            print(f"Testing weather weight: {weight:.1f}")
            
            # Create config with this weather weight
            config = EloConfig(
                base_rating=1500.0,
                k=20.0,
                hfa_points=55.0,
                mov_enabled=True,
                preseason_regress=0.75,
                use_weather_adjustment=True,
                weather_adjustment_weight=weight,
                weather_max_delta=5.0,
                use_travel_adjustment=False,
                use_qb_adjustment=False
            )
            
            # Run backtest
            try:
                result = run_backtest(
                    self.games, config,
                    qb_data=self.qb_data,
                    epa_data=self.epa_data,
                    weather_data=self.weather_data
                )
                
                metrics = result['metrics']
                results.append({
                    'weight': weight,
                    'brier_score': metrics['brier_score'],
                    'log_loss': metrics['log_loss'],
                    'accuracy': metrics['accuracy'],
                    'mae': 0.0,  # Not calculated in current metrics
                    'calibration': 0.0,  # Not calculated in current metrics
                    'ece': metrics['ece'],
                    'sharpness': metrics['sharpness']
                })
                
                print(f"  Brier Score: {metrics['brier_score']:.4f}, Accuracy: {metrics['accuracy']:.3f}")
                
            except Exception as e:
                print(f"  Error: {e}")
                results.append({
                    'weight': weight,
                    'brier_score': float('inf'),
                    'log_loss': float('inf'),
                    'accuracy': 0.0,
                    'mae': 0.0,
                    'calibration': 0.0,
                    'ece': float('inf'),
                    'sharpness': 0.0
                })
        
        # Find best weight
        results_df = pd.DataFrame(results)
        best_idx = results_df['brier_score'].idxmin()
        best_result = results_df.iloc[best_idx]
        
        print(f"\nOPTIMIZATION RESULTS:")
        print(f"Best weather weight: {best_result['weight']:.1f}")
        print(f"Best Brier Score: {best_result['brier_score']:.4f}")
        print(f"Best Accuracy: {best_result['accuracy']:.3f}")
        
        # Compare to baseline (weight = 0.0)
        baseline = results_df[results_df['weight'] == 0.0].iloc[0]
        improvement = ((baseline['brier_score'] - best_result['brier_score']) / baseline['brier_score']) * 100
        
        print(f"\nIMPROVEMENT ANALYSIS:")
        print(f"Baseline Brier Score (weight=0.0): {baseline['brier_score']:.4f}")
        print(f"Best Brier Score (weight={best_result['weight']:.1f}): {best_result['brier_score']:.4f}")
        print(f"Improvement: {improvement:.2f}%")
        
        if improvement > 0.1:
            print("✅ SIGNIFICANT IMPROVEMENT FOUND!")
        elif improvement > 0.0:
            print("⚠️  MINOR IMPROVEMENT FOUND")
        else:
            print("❌ NO IMPROVEMENT FOUND")
        
        optimization_results = {
            'weights_tested': weights.tolist(),
            'results': results,
            'best_weight': best_result['weight'],
            'best_brier_score': best_result['brier_score'],
            'improvement_pct': improvement,
            'significant_improvement': improvement > 0.1
        }
        
        self.results['weight_optimization'] = optimization_results
        return optimization_results
    
    def test_adverse_weather_games(self) -> Dict[str, Any]:
        """
        Test weather adjustments specifically on adverse weather games.
        
        Returns:
            Dictionary with adverse weather analysis
        """
        print("\n" + "="*60)
        print("ADVERSE WEATHER GAMES ANALYSIS")
        print("="*60)
        
        # Merge games with weather data
        games_with_weather = self.games.merge(
            self.weather_data[['game_id', 'home_temp', 'home_wind', 'home_precip']], 
            on='game_id', 
            how='left'
        )
        
        # Define adverse weather conditions
        adverse_conditions = (
            (games_with_weather['home_temp'] < 32) |  # Very cold
            (games_with_weather['home_wind'] > 15) |  # Windy
            (games_with_weather['home_precip'] > 2)   # Rainy
        )
        
        adverse_games = games_with_weather[adverse_conditions].copy()
        normal_games = games_with_weather[~adverse_conditions].copy()
        
        print(f"Total games: {len(games_with_weather)}")
        print(f"Adverse weather games: {len(adverse_games)} ({len(adverse_games)/len(games_with_weather)*100:.1f}%)")
        print(f"Normal weather games: {len(normal_games)} ({len(normal_games)/len(games_with_weather)*100:.1f}%)")
        
        if len(adverse_games) < 10:
            print("⚠️  WARNING: Too few adverse weather games for reliable analysis")
            return {'error': 'Insufficient adverse weather games'}
        
        # Test weather adjustments on adverse games
        config_no_weather = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=False,
            use_travel_adjustment=False, use_qb_adjustment=False
        )
        
        config_with_weather = EloConfig(
            base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
            preseason_regress=0.75, use_weather_adjustment=True,
            weather_adjustment_weight=1.0, weather_max_delta=5.0,
            use_travel_adjustment=False, use_qb_adjustment=False
        )
        
        # Test on adverse games
        print(f"\nTesting on {len(adverse_games)} adverse weather games...")
        
        try:
            result_no_weather = run_backtest(
                adverse_games, config_no_weather,
                qb_data=self.qb_data, epa_data=self.epa_data, weather_data=self.weather_data
            )
            
            result_with_weather = run_backtest(
                adverse_games, config_with_weather,
                qb_data=self.qb_data, epa_data=self.epa_data, weather_data=self.weather_data
            )
            
            no_weather_metrics = result_no_weather['metrics']
            with_weather_metrics = result_with_weather['metrics']
            
            improvement = ((no_weather_metrics['brier_score'] - with_weather_metrics['brier_score']) / 
                          no_weather_metrics['brier_score']) * 100
            
            print(f"\nADVERSE WEATHER RESULTS:")
            print(f"No weather adjustment - Brier: {no_weather_metrics['brier_score']:.4f}, Accuracy: {no_weather_metrics['accuracy']:.3f}")
            print(f"With weather adjustment - Brier: {with_weather_metrics['brier_score']:.4f}, Accuracy: {with_weather_metrics['accuracy']:.3f}")
            print(f"Improvement: {improvement:.2f}%")
            
            adverse_results = {
                'adverse_games_count': len(adverse_games),
                'normal_games_count': len(normal_games),
                'no_weather_metrics': no_weather_metrics,
                'with_weather_metrics': with_weather_metrics,
                'improvement_pct': improvement,
                'significant_improvement': improvement > 0.1
            }
            
            self.results['adverse_weather'] = adverse_results
            return adverse_results
            
        except Exception as e:
            print(f"Error testing adverse weather games: {e}")
            return {'error': str(e)}
    
    def analyze_stadium_weather_sensitivity(self) -> Dict[str, Any]:
        """
        Analyze weather sensitivity by stadium type (dome vs outdoor).
        
        Returns:
            Dictionary with stadium analysis
        """
        print("\n" + "="*60)
        print("STADIUM WEATHER SENSITIVITY ANALYSIS")
        print("="*60)
        
        # Load stadium database
        from ingest.nfl.stadium_database import StadiumDatabase
        stadium_db = StadiumDatabase()
        
        # Add stadium type to games
        games_with_stadium = self.games.copy()
        games_with_stadium['home_stadium_type'] = games_with_stadium['home_team'].apply(
            lambda team: stadium_db.get_stadium(team).stadium_type if stadium_db.get_stadium(team) else 'unknown'
        )
        
        # Merge with weather data
        games_with_weather = games_with_stadium.merge(
            self.weather_data[['game_id', 'home_temp', 'home_wind', 'home_precip']], 
            on='game_id', 
            how='left'
        )
        
        # Analyze by stadium type
        stadium_analysis = {}
        
        for stadium_type in ['dome', 'outdoor']:
            stadium_games = games_with_weather[games_with_weather['home_stadium_type'] == stadium_type]
            
            if len(stadium_games) < 5:
                continue
                
            print(f"\n{stadium_type.upper()} STADIUMS ({len(stadium_games)} games):")
            
            # Weather statistics
            temp_mean = stadium_games['home_temp'].mean()
            temp_std = stadium_games['home_temp'].std()
            wind_mean = stadium_games['home_wind'].mean()
            wind_std = stadium_games['home_wind'].std()
            
            print(f"  Temperature: {temp_mean:.1f}°F ± {temp_std:.1f}°F")
            print(f"  Wind: {wind_mean:.1f} mph ± {wind_std:.1f} mph")
            
            # Test weather adjustments
            config_no_weather = EloConfig(
                base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
                preseason_regress=0.75, use_weather_adjustment=False,
                use_travel_adjustment=False, use_qb_adjustment=False
            )
            
            config_with_weather = EloConfig(
                base_rating=1500.0, k=20.0, hfa_points=55.0, mov_enabled=True,
                preseason_regress=0.75, use_weather_adjustment=True,
                weather_adjustment_weight=1.0, weather_max_delta=5.0,
                use_travel_adjustment=False, use_qb_adjustment=False
            )
            
            try:
                result_no_weather = run_backtest(
                    stadium_games, config_no_weather,
                    qb_data=self.qb_data, epa_data=self.epa_data, weather_data=self.weather_data
                )
                
                result_with_weather = run_backtest(
                    stadium_games, config_with_weather,
                    qb_data=self.qb_data, epa_data=self.epa_data, weather_data=self.weather_data
                )
                
                no_weather_brier = result_no_weather['metrics']['brier_score']
                with_weather_brier = result_with_weather['metrics']['brier_score']
                improvement = ((no_weather_brier - with_weather_brier) / no_weather_brier) * 100
                
                print(f"  No weather - Brier: {no_weather_brier:.4f}")
                print(f"  With weather - Brier: {with_weather_brier:.4f}")
                print(f"  Improvement: {improvement:.2f}%")
                
                stadium_analysis[stadium_type] = {
                    'games_count': len(stadium_games),
                    'temp_mean': temp_mean,
                    'temp_std': temp_std,
                    'wind_mean': wind_mean,
                    'wind_std': wind_std,
                    'no_weather_brier': no_weather_brier,
                    'with_weather_brier': with_weather_brier,
                    'improvement_pct': improvement
                }
                
            except Exception as e:
                print(f"  Error testing {stadium_type} stadiums: {e}")
                stadium_analysis[stadium_type] = {'error': str(e)}
        
        self.results['stadium_analysis'] = stadium_analysis
        return stadium_analysis
    
    def run_comprehensive_diagnosis(self) -> Dict[str, Any]:
        """
        Run comprehensive weather diagnosis.
        
        Returns:
            Dictionary with all diagnostic results
        """
        print("🌤️ WEATHER DIAGNOSTIC ANALYSIS")
        print("="*80)
        
        # Run all analyses
        weather_conditions = self.analyze_weather_conditions()
        weight_optimization = self.test_weather_weight_optimization()
        adverse_weather = self.test_adverse_weather_games()
        stadium_analysis = self.analyze_stadium_weather_sensitivity()
        
        # Summary
        print("\n" + "="*80)
        print("WEATHER DIAGNOSTIC SUMMARY")
        print("="*80)
        
        print(f"1. Weather Data Coverage: {weather_conditions['games_with_weather_data']/weather_conditions['total_games']*100:.1f}%")
        print(f"2. Best Weather Weight: {weight_optimization['best_weight']:.1f}")
        print(f"3. Weight Optimization Improvement: {weight_optimization['improvement_pct']:.2f}%")
        
        if 'error' not in adverse_weather:
            print(f"4. Adverse Weather Games: {adverse_weather['adverse_games_count']} games")
            print(f"5. Adverse Weather Improvement: {adverse_weather['improvement_pct']:.2f}%")
        else:
            print(f"4. Adverse Weather Analysis: {adverse_weather['error']}")
        
        print(f"6. Stadium Analysis: {len(stadium_analysis)} stadium types analyzed")
        
        # Overall assessment
        significant_improvements = []
        if weight_optimization['significant_improvement']:
            significant_improvements.append("Weight optimization")
        if 'error' not in adverse_weather and adverse_weather['significant_improvement']:
            significant_improvements.append("Adverse weather games")
        
        if significant_improvements:
            print(f"\n✅ SIGNIFICANT IMPROVEMENTS FOUND:")
            for improvement in significant_improvements:
                print(f"  - {improvement}")
        else:
            print(f"\n❌ NO SIGNIFICANT IMPROVEMENTS FOUND")
            print("   Weather adjustments may need feature engineering or data quality improvements")
        
        return {
            'weather_conditions': weather_conditions,
            'weight_optimization': weight_optimization,
            'adverse_weather': adverse_weather,
            'stadium_analysis': stadium_analysis,
            'significant_improvements': significant_improvements
        }


def run_weather_diagnostic_analysis(years: List[int] = [2022, 2023], sample_size: Optional[int] = None):
    """Run comprehensive weather diagnostic analysis."""
    analyzer = WeatherDiagnosticAnalyzer(years=years, sample_size=sample_size)
    return analyzer.run_comprehensive_diagnosis()


if __name__ == "__main__":
    results = run_weather_diagnostic_analysis(sample_size=100)
