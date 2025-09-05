"""Command-line interface for NFL Elo system."""

import typer
import json
import pandas as pd
from pathlib import Path
from rich import print
from rich.table import Table
from rich.console import Console
from typing import Optional, List
import sys
import os

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ingest.nfl.data_loader import load_games, load_team_reference, validate_game_data
from .config import EloConfig
from .backtest import run_backtest, run_comparison_backtest, analyze_rating_trajectories, calculate_rating_volatility

app = typer.Typer(no_args_is_help=True, help="NFL Elo Rating System CLI")
console = Console()


@app.command()
def backtest(
    start: int = typer.Option(2010, help="Starting season"),
    end: int = typer.Option(2024, help="Ending season"),
    config_path: Optional[str] = typer.Option(None, help="Path to JSON config file"),
    output_dir: str = typer.Option("artifacts", help="Output directory for results"),
    save_history: bool = typer.Option(True, help="Save detailed game history"),
    verbose: bool = typer.Option(False, help="Verbose output")
):
    """Run backtest on NFL data."""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Load configuration
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        cfg = EloConfig(**config_dict)
    else:
        cfg = EloConfig(start_season=start, end_season=end)
    
    if verbose:
        print(f"Configuration: {cfg.model_dump()}")
    
    # Load data
    years = list(range(start, end + 1))
    print(f"Loading data for seasons {start}-{end}...")
    
    try:
        games = load_games(years)
        print(f"Loaded {len(games)} games")
        
        # Validate data
        if not validate_game_data(games):
            print("❌ Data validation failed")
            return
        
        print("✅ Data validation passed")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Run backtest
    print("Running backtest...")
    try:
        results = run_backtest(games, cfg)
        
        if "error" in results:
            print(f"❌ Backtest failed: {results['error']}")
            return
        
        # Display metrics
        metrics = results["metrics"]
        print("\n📊 Backtest Results:")
        
        # Create metrics table
        table = Table(title="Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for metric, value in metrics.items():
            if isinstance(value, float):
                table.add_row(metric, f"{value:.4f}")
            else:
                table.add_row(metric, str(value))
        
        console.print(table)
        
        # Save results
        if save_history:
            history_file = output_path / "nfl_elo_history.csv"
            results["history"].to_csv(history_file, index=False)
            print(f"💾 Game history saved to {history_file}")
        
        # Save metrics
        metrics_file = output_path / "nfl_elo_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"💾 Metrics saved to {metrics_file}")
        
        # Save final ratings
        ratings_file = output_path / "nfl_elo_final_ratings.json"
        with open(ratings_file, 'w') as f:
            json.dump(results["final_ratings"], f, indent=2)
        print(f"💾 Final ratings saved to {ratings_file}")
        
        print("✅ Backtest completed successfully")
        
    except Exception as e:
        print(f"❌ Error running backtest: {e}")
        if verbose:
            import traceback
            traceback.print_exc()


@app.command()
def compare(
    start: int = typer.Option(2010, help="Starting season"),
    end: int = typer.Option(2024, help="Ending season"),
    config_dir: str = typer.Option("configs", help="Directory containing config files"),
    output_dir: str = typer.Option("artifacts", help="Output directory for results")
):
    """Compare multiple Elo configurations."""
    
    config_path = Path(config_dir)
    if not config_path.exists():
        print(f"❌ Config directory not found: {config_dir}")
        return
    
    # Find all JSON config files
    config_files = list(config_path.glob("*.json"))
    if not config_files:
        print(f"❌ No JSON config files found in {config_dir}")
        return
    
    print(f"Found {len(config_files)} config files")
    
    # Load configurations
    configs = {}
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                config_dict = json.load(f)
            config_name = config_file.stem
            configs[config_name] = EloConfig(**config_dict)
            print(f"✅ Loaded config: {config_name}")
        except Exception as e:
            print(f"❌ Error loading {config_file}: {e}")
    
    if not configs:
        print("❌ No valid configurations loaded")
        return
    
    # Load data
    years = list(range(start, end + 1))
    print(f"Loading data for seasons {start}-{end}...")
    
    try:
        games = load_games(years)
        print(f"Loaded {len(games)} games")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Run comparison
    print("Running comparison backtest...")
    try:
        results = run_comparison_backtest(games, configs)
        
        # Create comparison table
        table = Table(title="Configuration Comparison")
        table.add_column("Config", style="cyan")
        table.add_column("Brier Score", style="green")
        table.add_column("Log Loss", style="green")
        table.add_column("ECE", style="green")
        table.add_column("Games", style="blue")
        
        for config_name, result in results.items():
            if "error" in result:
                table.add_row(config_name, "ERROR", "ERROR", "ERROR", "0")
            else:
                metrics = result["metrics"]
                table.add_row(
                    config_name,
                    f"{metrics.get('brier_score', 0):.4f}",
                    f"{metrics.get('log_loss', 0):.4f}",
                    f"{metrics.get('ece', 0):.4f}",
                    str(metrics.get('n_games', 0))
                )
        
        console.print(table)
        
        # Save comparison results
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        comparison_file = output_path / "elo_comparison.json"
        comparison_data = {}
        for config_name, result in results.items():
            if "error" not in result:
                comparison_data[config_name] = result["metrics"]
        
        with open(comparison_file, 'w') as f:
            json.dump(comparison_data, f, indent=2)
        print(f"💾 Comparison results saved to {comparison_file}")
        
        print("✅ Comparison completed successfully")
        
    except Exception as e:
        print(f"❌ Error running comparison: {e}")


@app.command()
def analyze(
    history_file: str = typer.Option("artifacts/nfl_elo_history.csv", help="Path to game history file"),
    output_dir: str = typer.Option("artifacts", help="Output directory for analysis")
):
    """Analyze rating trajectories and volatility."""
    
    history_path = Path(history_file)
    if not history_path.exists():
        print(f"❌ History file not found: {history_file}")
        return
    
    try:
        # Load history
        history = pd.read_csv(history_path)
        print(f"Loaded {len(history)} games from history")
        
        # Create results dict for analysis functions
        results = {"history": history}
        
        # Analyze trajectories
        print("Analyzing rating trajectories...")
        trajectories = analyze_rating_trajectories(results)
        
        if len(trajectories) > 0:
            traj_file = Path(output_dir) / "rating_trajectories.csv"
            trajectories.to_csv(traj_file, index=False)
            print(f"💾 Trajectories saved to {traj_file}")
        
        # Calculate volatility
        print("Calculating rating volatility...")
        volatility = calculate_rating_volatility(results)
        
        if len(volatility) > 0:
            vol_file = Path(output_dir) / "rating_volatility.csv"
            volatility.to_csv(vol_file, index=False)
            print(f"💾 Volatility analysis saved to {vol_file}")
            
            # Display top 10 most volatile teams
            print("\n📈 Most Volatile Teams:")
            top_volatile = volatility.head(10)
            for _, row in top_volatile.iterrows():
                print(f"  {row['team']}: {row['change_std']:.2f} std dev")
        
        print("✅ Analysis completed successfully")
        
    except Exception as e:
        print(f"❌ Error in analysis: {e}")


@app.command()
def simulate_week(
    season: int = typer.Option(2024, help="Season to simulate"),
    week: int = typer.Option(1, help="Week to simulate"),
    ratings_file: str = typer.Option("artifacts/nfl_elo_final_ratings.json", help="Path to ratings file")
):
    """Simulate a specific week (placeholder for future implementation)."""
    print(f"Simulating season={season} week={week}")
    print("⚠️  This feature is not yet implemented")
    print("   Future implementation will:")
    print("   - Load current ratings")
    print("   - Load upcoming schedule")
    print("   - Calculate win probabilities")
    print("   - Display predictions")


@app.command()
def validate_data(
    start: int = typer.Option(2010, help="Starting season"),
    end: int = typer.Option(2024, help="Ending season")
):
    """Validate NFL data quality."""
    
    years = list(range(start, end + 1))
    print(f"Validating data for seasons {start}-{end}...")
    
    try:
        games = load_games(years)
        print(f"Loaded {len(games)} games")
        
        # Basic validation
        if validate_game_data(games):
            print("✅ Data validation passed")
        else:
            print("❌ Data validation failed")
            return
        
        # Additional checks
        print("\n📊 Data Quality Report:")
        
        # Season coverage
        seasons = sorted(games["season"].unique())
        print(f"  Seasons: {len(seasons)} ({min(seasons)}-{max(seasons)})")
        
        # Games per season
        games_per_season = games.groupby("season").size()
        print(f"  Games per season: {games_per_season.mean():.1f} ± {games_per_season.std():.1f}")
        
        # Team coverage
        teams = set(games["home_team"].unique()) | set(games["away_team"].unique())
        print(f"  Unique teams: {len(teams)}")
        
        # Missing data
        missing_data = games.isnull().sum()
        if missing_data.sum() > 0:
            print("  Missing data:")
            for col, count in missing_data[missing_data > 0].items():
                print(f"    {col}: {count} ({count/len(games)*100:.1f}%)")
        else:
            print("  No missing data in required columns")
        
        # Score distribution
        print(f"  Score range: {games['home_score'].min()}-{games['home_score'].max()}")
        print(f"  Average score: {games[['home_score', 'away_score']].mean().mean():.1f}")
        
        print("✅ Data quality check completed")
        
    except Exception as e:
        print(f"❌ Error validating data: {e}")


if __name__ == "__main__":
    app()
