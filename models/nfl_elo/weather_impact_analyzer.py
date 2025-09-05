"""Analyze weather impact in adverse weather conditions."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path

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


class WeatherImpactAnalyzer:
    """Analyze weather impact in adverse weather conditions."""
    
    def __init__(self, years: List[int] = [2022, 2023]):
        """Initialize the weather impact analyzer."""
        self.years = years
        self.results = {}
        
        # Load data
        print("Loading data for weather impact analysis...")
        self._load_data()
        
    def _load_data(self):
        """Load all required data."""
        # Load games data
        self.games = load_games(self.years)
        print(f"Loaded {len(self.games)} games")
        
        # Load weather data
        self.weather_data = load_weather_data_with_retry(self.games)
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
        
    def analyze_weather_conditions(self) -> Dict[str, Any]:
        """Analyze games by weather conditions."""
        print("\nAnalyzing weather conditions...")
        
        # Categorize games by weather severity
        weather_categories = self._categorize_weather_conditions()
        
        # Test each category
        results = {}
        for category, games in weather_categories.items():
            if len(games) < 5:  # Skip categories with too few games
                continue
                
            print(f"\nTesting {category} ({len(games)} games)...")
            result = self._test_weather_category(category, games)
            results[category] = result
            
        return results
    
    def _categorize_weather_conditions(self) -> Dict[str, pd.DataFrame]:
        """Categorize games by weather conditions."""
        categories = {}
        
        # Merge games with weather data, keeping all original game columns
        merged = self.games.merge(
            self.weather_data[['season', 'week', 'home_team', 'away_team', 'home_temp', 'home_wind', 'home_precip']], 
            on=['season', 'week', 'home_team', 'away_team'], 
            how='left'
        )
        
        # Define weather categories based on conditions
        categories['excellent'] = merged[
            (merged['home_temp'] >= 60) & (merged['home_temp'] <= 80) &
            (merged['home_wind'] <= 10) & (merged['home_precip'] <= 1)
        ].copy()
        
        categories['good'] = merged[
            ((merged['home_temp'] >= 50) & (merged['home_temp'] < 60)) |
            ((merged['home_temp'] > 80) & (merged['home_temp'] <= 90)) |
            ((merged['home_wind'] > 10) & (merged['home_wind'] <= 15)) |
            ((merged['home_precip'] > 1) & (merged['home_precip'] <= 3))
        ].copy()
        
        categories['adverse'] = merged[
            (merged['home_temp'] < 50) | (merged['home_temp'] > 90) |
            (merged['home_wind'] > 15) | (merged['home_precip'] > 3)
        ].copy()
        
        categories['extreme'] = merged[
            (merged['home_temp'] < 32) | (merged['home_temp'] > 100) |
            (merged['home_wind'] > 25) | (merged['home_precip'] > 10)
        ].copy()
        
        # Print category statistics
        for category, games in categories.items():
            print(f"{category}: {len(games)} games")
            if len(games) > 0:
                print(f"  Avg temp: {games['home_temp'].mean():.1f}°F")
                print(f"  Avg wind: {games['home_wind'].mean():.1f} mph")
                print(f"  Avg precip: {games['home_precip'].mean():.1f} mm")
        
        return categories
    
    def _test_weather_category(self, category: str, games: pd.DataFrame) -> Dict[str, Any]:
        """Test a specific weather category."""
        # Create configurations
        baseline_config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_weather_adjustment=False,
            use_travel_adjustment=False,
            use_qb_adjustment=False
        )
        
        weather_config = EloConfig(
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
        
        # Run baseline backtest
        baseline_result = run_backtest(games, baseline_config)
        
        # Run weather-adjusted backtest
        weather_result = run_backtest(games, weather_config, weather_data=self.weather_data)
        
        # Calculate improvement
        baseline_brier = baseline_result['metrics']['brier_score']
        weather_brier = weather_result['metrics']['brier_score']
        improvement = ((baseline_brier - weather_brier) / baseline_brier) * 100
        
        # Analyze weather impact
        weather_impact = self._analyze_weather_impact(games)
        
        return {
            'category': category,
            'num_games': len(games),
            'baseline_metrics': baseline_result['metrics'],
            'weather_metrics': weather_result['metrics'],
            'improvement_pct': improvement,
            'weather_impact': weather_impact,
            'weather_stats': {
                'avg_temp': games['home_temp'].mean(),
                'avg_wind': games['home_wind'].mean(),
                'avg_precip': games['home_precip'].mean(),
                'max_wind': games['home_wind'].max(),
                'max_precip': games['home_precip'].max()
            }
        }
    
    def _analyze_weather_impact(self, games: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the impact of weather on game outcomes."""
        # Calculate weather adjustments for each game
        weather_impacts = []
        
        for idx, game in games.iterrows():
            # Get weather data for this game
            weather_row = self.weather_data[
                (self.weather_data['season'] == game['season']) &
                (self.weather_data['week'] == game['week']) &
                (self.weather_data['home_team'] == game['home_team']) &
                (self.weather_data['away_team'] == game['away_team'])
            ]
            
            if len(weather_row) > 0:
                weather_row = weather_row.iloc[0]
                
                # Calculate weather impact
                temp_impact = self._calculate_temp_impact(weather_row['home_temp'])
                wind_impact = self._calculate_wind_impact(weather_row['home_wind'])
                precip_impact = self._calculate_precip_impact(weather_row['home_precip'])
                
                total_impact = temp_impact + wind_impact + precip_impact
                
                weather_impacts.append({
                    'game_id': f"{game['season']}_{game['week']}_{game['home_team']}_{game['away_team']}",
                    'temp': weather_row['home_temp'],
                    'wind': weather_row['home_wind'],
                    'precip': weather_row['home_precip'],
                    'temp_impact': temp_impact,
                    'wind_impact': wind_impact,
                    'precip_impact': precip_impact,
                    'total_impact': total_impact
                })
        
        if not weather_impacts:
            return {'error': 'No weather data available'}
        
        impacts_df = pd.DataFrame(weather_impacts)
        
        return {
            'total_games': len(impacts_df),
            'avg_impact': impacts_df['total_impact'].mean(),
            'max_impact': impacts_df['total_impact'].max(),
            'min_impact': impacts_df['total_impact'].min(),
            'temp_impact_avg': impacts_df['temp_impact'].mean(),
            'wind_impact_avg': impacts_df['wind_impact'].mean(),
            'precip_impact_avg': impacts_df['precip_impact'].mean(),
            'high_impact_games': len(impacts_df[impacts_df['total_impact'] > 2.0]),
            'extreme_weather_games': len(impacts_df[
                (impacts_df['wind'] > 20) | 
                (impacts_df['precip'] > 5) | 
                (impacts_df['temp'] < 32) | 
                (impacts_df['temp'] > 90)
            ])
        }
    
    def _calculate_temp_impact(self, temp: float) -> float:
        """Calculate temperature impact on game."""
        if temp < 32:
            return -2.0  # Very cold
        elif temp < 50:
            return -1.0  # Cold
        elif temp > 90:
            return -1.5  # Very hot
        elif temp > 80:
            return -0.5  # Hot
        else:
            return 0.0   # Optimal
    
    def _calculate_wind_impact(self, wind: float) -> float:
        """Calculate wind impact on game."""
        if wind > 25:
            return -2.0  # Very windy
        elif wind > 15:
            return -1.0  # Windy
        elif wind > 10:
            return -0.5  # Some wind
        else:
            return 0.0   # Calm
    
    def _calculate_precip_impact(self, precip: float) -> float:
        """Calculate precipitation impact on game."""
        if precip > 10:
            return -2.0  # Heavy rain/snow
        elif precip > 5:
            return -1.0  # Moderate rain/snow
        elif precip > 1:
            return -0.5  # Light rain/snow
        else:
            return 0.0   # Dry
    
    def print_weather_analysis(self, results: Dict[str, Any]):
        """Print weather impact analysis results."""
        print("\n" + "="*80)
        print("WEATHER IMPACT ANALYSIS")
        print("="*80)
        
        for category, result in results.items():
            print(f"\n{category.upper()} WEATHER CONDITIONS:")
            print(f"  Games: {result['num_games']}")
            print(f"  Weather Stats:")
            print(f"    Avg Temp: {result['weather_stats']['avg_temp']:.1f}°F")
            print(f"    Avg Wind: {result['weather_stats']['avg_wind']:.1f} mph")
            print(f"    Avg Precip: {result['weather_stats']['avg_precip']:.1f} mm")
            print(f"    Max Wind: {result['weather_stats']['max_wind']:.1f} mph")
            print(f"    Max Precip: {result['weather_stats']['max_precip']:.1f} mm")
            
            print(f"  Performance:")
            print(f"    Baseline Brier: {result['baseline_metrics']['brier_score']:.4f}")
            print(f"    Weather Brier: {result['weather_metrics']['brier_score']:.4f}")
            print(f"    Improvement: {result['improvement_pct']:.2f}%")
            
            if 'weather_impact' in result and 'error' not in result['weather_impact']:
                impact = result['weather_impact']
                print(f"  Weather Impact:")
                print(f"    Avg Impact: {impact['avg_impact']:.2f}")
                print(f"    Max Impact: {impact['max_impact']:.2f}")
                print(f"    High Impact Games: {impact['high_impact_games']}")
                print(f"    Extreme Weather Games: {impact['extreme_weather_games']}")
    
    def run_weather_analysis(self) -> Dict[str, Any]:
        """Run complete weather impact analysis."""
        print("Running weather impact analysis...")
        results = self.analyze_weather_conditions()
        self.print_weather_analysis(results)
        return results


def run_weather_impact_analysis(years: List[int] = [2022, 2023]):
    """Run weather impact analysis."""
    analyzer = WeatherImpactAnalyzer(years=years)
    return analyzer.run_weather_analysis()


if __name__ == "__main__":
    results = run_weather_impact_analysis()
