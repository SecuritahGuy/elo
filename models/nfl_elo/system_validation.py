"""System validation and maintenance for NFL Elo rating system."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .config import EloConfig
from .backtest import run_backtest
from ingest.nfl.data_loader import load_games


def validate_production_system(years: List[int] = [2019, 2021, 2022, 2023, 2024]) -> Dict[str, Any]:
    """
    Validate the production system with comprehensive testing.
    
    Args:
        years: Years to test
        
    Returns:
        Dictionary with validation results
    """
    print(f"🔧 VALIDATING PRODUCTION SYSTEM")
    print("="*80)
    print(f"Validating production system with {len(years)} years of data...")
    
    # Load games data
    games = load_games(years)
    print(f"Loaded {len(games)} games")
    
    # Production configuration (Travel + QB enabled, others disabled)
    production_config = EloConfig(
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
        use_situational_adjustment=False
    )
    
    # Baseline configuration (no adjustments)
    baseline_config = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.75,
        use_weather_adjustment=False,
        use_travel_adjustment=False,
        use_qb_adjustment=False,
        use_injury_adjustment=False,
        use_redzone_adjustment=False,
        use_downs_adjustment=False,
        use_clock_management_adjustment=False,
        use_situational_adjustment=False
    )
    
    print("\\nRunning production system validation...")
    
    # Test production system
    production_result = run_backtest(games, production_config)
    production_metrics = production_result['metrics']
    
    # Test baseline system
    baseline_result = run_backtest(games, baseline_config)
    baseline_metrics = baseline_result['metrics']
    
    # Calculate improvement
    improvement = ((baseline_metrics['brier_score'] - production_metrics['brier_score']) / baseline_metrics['brier_score']) * 100
    
    print(f"\\n" + "="*80)
    print("PRODUCTION SYSTEM VALIDATION RESULTS")
    print("="*80)
    print(f"Years Tested: {years}")
    print(f"Games Processed: {len(games)}")
    
    print(f"\\n📊 PERFORMANCE COMPARISON:")
    print(f"Baseline System:")
    print(f"  Brier Score: {baseline_metrics['brier_score']:.4f}")
    print(f"  Accuracy: {baseline_metrics['accuracy']:.3f}")
    print(f"  Log Loss: {baseline_metrics['log_loss']:.4f}")
    print(f"  ECE: {baseline_metrics['ece']:.4f}")
    
    print(f"\\nProduction System (Travel + QB):")
    print(f"  Brier Score: {production_metrics['brier_score']:.4f} ({improvement:+.2f}%)")
    print(f"  Accuracy: {production_metrics['accuracy']:.3f}")
    print(f"  Log Loss: {production_metrics['log_loss']:.4f}")
    print(f"  ECE: {production_metrics['ece']:.4f}")
    
    # System health check
    print(f"\\n🔍 SYSTEM HEALTH CHECK:")
    
    # Check if production system is stable
    is_stable = abs(improvement) < 0.1  # Within 0.1% of baseline
    print(f"  System Stability: {'✅ STABLE' if is_stable else '⚠️ UNSTABLE'}")
    
    # Check if production system is better than baseline
    is_improved = improvement > 0.0
    print(f"  Performance: {'✅ IMPROVED' if is_improved else '❌ DEGRADED'}")
    
    # Check if metrics are reasonable
    reasonable_brier = 0.15 <= production_metrics['brier_score'] <= 0.35
    reasonable_accuracy = 0.50 <= production_metrics['accuracy'] <= 0.75
    print(f"  Brier Score Range: {'✅ REASONABLE' if reasonable_brier else '⚠️ OUT OF RANGE'}")
    print(f"  Accuracy Range: {'✅ REASONABLE' if reasonable_accuracy else '⚠️ OUT OF RANGE'}")
    
    # Overall system status
    overall_status = "✅ PRODUCTION READY" if (is_stable and reasonable_brier and reasonable_accuracy) else "⚠️ NEEDS ATTENTION"
    print(f"\\n🎯 OVERALL STATUS: {overall_status}")
    
    # Configuration summary
    print(f"\\n📋 PRODUCTION CONFIGURATION:")
    print(f"  Travel Adjustments: {'✅ ENABLED' if production_config.use_travel_adjustment else '❌ DISABLED'}")
    print(f"  QB Adjustments: {'✅ ENABLED' if production_config.use_qb_adjustment else '❌ DISABLED'}")
    print(f"  Weather Adjustments: {'✅ ENABLED' if production_config.use_weather_adjustment else '❌ DISABLED'}")
    print(f"  Injury Adjustments: {'✅ ENABLED' if production_config.use_injury_adjustment else '❌ DISABLED'}")
    print(f"  Red Zone Adjustments: {'✅ ENABLED' if production_config.use_redzone_adjustment else '❌ DISABLED'}")
    print(f"  Third Down Adjustments: {'✅ ENABLED' if production_config.use_downs_adjustment else '❌ DISABLED'}")
    print(f"  Clock Management: {'✅ ENABLED' if production_config.use_clock_management_adjustment else '❌ DISABLED'}")
    print(f"  Situational Adjustments: {'✅ ENABLED' if production_config.use_situational_adjustment else '❌ DISABLED'}")
    
    # Compile validation results
    validation_results = {
        'years_tested': years,
        'games_processed': len(games),
        'baseline_metrics': baseline_metrics,
        'production_metrics': production_metrics,
        'improvement': improvement,
        'system_health': {
            'is_stable': is_stable,
            'is_improved': is_improved,
            'reasonable_brier': reasonable_brier,
            'reasonable_accuracy': reasonable_accuracy,
            'overall_status': overall_status
        },
        'configuration': {
            'travel_enabled': production_config.use_travel_adjustment,
            'qb_enabled': production_config.use_qb_adjustment,
            'weather_enabled': production_config.use_weather_adjustment,
            'injury_enabled': production_config.use_injury_adjustment,
            'redzone_enabled': production_config.use_redzone_adjustment,
            'downs_enabled': production_config.use_downs_adjustment,
            'clock_management_enabled': production_config.use_clock_management_adjustment,
            'situational_enabled': production_config.use_situational_adjustment
        },
        'validation_timestamp': datetime.now().isoformat()
    }
    
    return validation_results


def run_system_maintenance_check() -> None:
    """
    Run comprehensive system maintenance check.
    """
    print(f"🔧 NFL ELO SYSTEM MAINTENANCE CHECK")
    print("="*80)
    print(f"Running comprehensive system maintenance check...")
    
    # Validate production system
    validation_results = validate_production_system()
    
    # Print maintenance summary
    print(f"\\n" + "="*80)
    print("SYSTEM MAINTENANCE SUMMARY")
    print("="*80)
    print(f"Validation Date: {validation_results['validation_timestamp']}")
    print(f"Years Tested: {validation_results['years_tested']}")
    print(f"Games Processed: {validation_results['games_processed']}")
    print(f"Overall Status: {validation_results['system_health']['overall_status']}")
    print(f"Performance Improvement: {validation_results['improvement']:+.2f}%")
    
    # Configuration status
    config = validation_results['configuration']
    print(f"\\nActive Features:")
    if config['travel_enabled']:
        print(f"  ✅ Travel Adjustments")
    if config['qb_enabled']:
        print(f"  ✅ QB Adjustments")
    if not config['weather_enabled']:
        print(f"  ❌ Weather Adjustments (disabled)")
    if not config['injury_enabled']:
        print(f"  ❌ Injury Adjustments (disabled)")
    if not config['redzone_enabled']:
        print(f"  ❌ Red Zone Adjustments (disabled)")
    if not config['downs_enabled']:
        print(f"  ❌ Third Down Adjustments (disabled)")
    if not config['clock_management_enabled']:
        print(f"  ❌ Clock Management (disabled)")
    if not config['situational_enabled']:
        print(f"  ❌ Situational Adjustments (disabled)")
    
    # Performance metrics
    prod_metrics = validation_results['production_metrics']
    print(f"\\nPerformance Metrics:")
    print(f"  Brier Score: {prod_metrics['brier_score']:.4f}")
    print(f"  Accuracy: {prod_metrics['accuracy']:.3f}")
    print(f"  Log Loss: {prod_metrics['log_loss']:.4f}")
    print(f"  ECE: {prod_metrics['ece']:.4f}")
    
    # Recommendations
    print(f"\\n🎯 MAINTENANCE RECOMMENDATIONS:")
    if validation_results['system_health']['overall_status'] == "✅ PRODUCTION READY":
        print(f"  ✅ System is production ready")
        print(f"  ✅ Continue monitoring performance")
        print(f"  ✅ No immediate action required")
    else:
        print(f"  ⚠️ System needs attention")
        print(f"  ⚠️ Review configuration settings")
        print(f"  ⚠️ Consider system adjustments")
    
    return validation_results


if __name__ == "__main__":
    results = run_system_maintenance_check()
