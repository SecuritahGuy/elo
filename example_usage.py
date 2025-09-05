#!/usr/bin/env python3
"""
Example usage of the NFL Elo rating system.

This script demonstrates how to use the system programmatically.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from ingest.nfl.data_loader import load_games, validate_game_data
from models.nfl_elo.config import EloConfig
from models.nfl_elo.backtest import run_backtest
from models.nfl_elo.evaluator import calculate_all_metrics


def main():
    """Run a simple example of the NFL Elo system."""
    print("🏈 NFL Elo Rating System Example")
    print("=" * 40)
    
    # Load recent NFL data
    print("📊 Loading NFL data for 2023...")
    games = load_games([2023])
    print(f"   Loaded {len(games)} games")
    
    # Validate data
    if not validate_game_data(games):
        print("❌ Data validation failed")
        return
    
    print("✅ Data validation passed")
    
    # Create configuration
    print("\n⚙️  Creating Elo configuration...")
    config = EloConfig(
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        start_season=2023,
        end_season=2023
    )
    print(f"   K-factor: {config.k}")
    print(f"   HFA points: {config.hfa_points}")
    print(f"   MOV enabled: {config.mov_enabled}")
    
    # Run backtest
    print("\n🔄 Running backtest...")
    results = run_backtest(games, config)
    
    if "error" in results:
        print(f"❌ Backtest failed: {results['error']}")
        return
    
    # Display results
    print("✅ Backtest completed successfully")
    
    metrics = results["metrics"]
    print(f"\n📈 Performance Metrics:")
    print(f"   Brier Score: {metrics['brier_score']:.4f}")
    print(f"   Log Loss: {metrics['log_loss']:.4f}")
    print(f"   Expected Calibration Error: {metrics['ece']:.4f}")
    print(f"   Accuracy: {metrics['accuracy']:.4f}")
    print(f"   Games processed: {metrics['n_games']}")
    
    # Show top 5 teams by final rating
    final_ratings = results["final_ratings"]
    sorted_teams = sorted(final_ratings.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n🏆 Top 5 Teams by Final Rating:")
    for i, (team, rating) in enumerate(sorted_teams[:5], 1):
        print(f"   {i}. {team}: {rating:.1f}")
    
    # Show bottom 5 teams
    print(f"\n📉 Bottom 5 Teams by Final Rating:")
    for i, (team, rating) in enumerate(sorted_teams[-5:], 1):
        print(f"   {i}. {team}: {rating:.1f}")
    
    print(f"\n💾 Results saved to artifacts/ directory")
    print("   - nfl_elo_history.csv: Game-by-game results")
    print("   - nfl_elo_final_ratings.json: Final team ratings")
    print("   - nfl_elo_metrics.json: Performance metrics")


if __name__ == "__main__":
    main()
