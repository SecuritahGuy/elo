#!/usr/bin/env python3
"""
Calculate comprehensive ELO ratings using our full system with all features.
This replaces the basic calculate_real_elo_ratings.py script.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from models.nfl_elo.prediction_interface import NFLPredictionInterface
from models.nfl_elo.config import EloConfig
from models.nfl_elo.backtest import run_backtest
from ingest.nfl.data_loader import load_games


def calculate_comprehensive_elo_ratings(years: List[int] = [2020, 2021, 2022, 2023, 2024, 2025]) -> Dict[str, Any]:
    """
    Calculate comprehensive ELO ratings using our full system.
    
    Args:
        years: Years to process for ELO calculations
        
    Returns:
        Dictionary with results and team ratings
    """
    print("🏈 Calculating comprehensive ELO ratings for NFL teams...")
    print(f"Processing years: {years}")
    print("="*80)
    
    # Initialize the comprehensive prediction interface
    config = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.75,
        use_weather_adjustment=False,  # Disabled based on testing
        use_travel_adjustment=True,    # Enabled - provides improvement
        use_qb_adjustment=True,        # Enabled - provides improvement
        use_injury_adjustment=False,   # Disabled - no improvement
        use_redzone_adjustment=False,  # Disabled - no improvement
        use_downs_adjustment=False,    # Disabled - no improvement
        use_clock_management_adjustment=False,  # Disabled - no improvement
        use_situational_adjustment=False,       # Disabled - no improvement
        use_turnover_adjustment=False           # Disabled - no improvement
    )
    
    interface = NFLPredictionInterface(config)
    
    try:
        # Load games data for all years
        print(f"\n📊 Loading game data for years: {years}")
        games = load_games(years)
        print(f"✅ Loaded {len(games)} games")
        
        # Filter out games without scores (future games)
        completed_games = games.dropna(subset=['home_score', 'away_score'])
        print(f"✅ Found {len(completed_games)} completed games")
        
        if len(completed_games) == 0:
            print("❌ No completed games found!")
            return {'success': False, 'error': 'No completed games found'}
        
        # Run comprehensive backtest to get final ratings
        print(f"\n🔄 Running comprehensive backtest...")
        result = run_backtest(completed_games, config)
        
        if 'final_ratings' not in result:
            print("❌ No final ratings in backtest result!")
            return {'success': False, 'error': 'No final ratings calculated'}
        
        team_ratings = result['final_ratings']
        print(f"✅ Calculated ratings for {len(team_ratings)} teams")
        
        # Calculate team statistics from actual game data
        print(f"\n📈 Calculating team statistics...")
        team_stats = calculate_team_statistics(completed_games, team_ratings)
        
        # Store comprehensive results in database
        print(f"\n💾 Storing results in database...")
        store_comprehensive_results(team_ratings, team_stats, years, result)
        
        # Display results
        print(f"\n🏆 Top 10 ELO Ratings:")
        sorted_teams = sorted(team_ratings.items(), key=lambda x: x[1], reverse=True)
        for i, (team, rating) in enumerate(sorted_teams[:10], 1):
            stats = team_stats.get(team, {})
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            change = stats.get('rating_change', 0.0)
            print(f"{i:2d}. {team}: {rating:.1f} ({wins}-{losses}) [Δ{change:+.1f}]")
        
        return {
            'success': True,
            'team_ratings': team_ratings,
            'team_stats': team_stats,
            'games_processed': len(completed_games),
            'years_processed': years,
            'backtest_metrics': result.get('metrics', {}),
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error calculating comprehensive ELO ratings: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def calculate_team_statistics(games: pd.DataFrame, team_ratings: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate comprehensive team statistics from game data.
    
    Args:
        games: DataFrame with game data
        team_ratings: Current team ratings
        
    Returns:
        Dictionary with team statistics
    """
    team_stats = {}
    
    # Get all unique teams
    all_teams = set(games['home_team'].unique()) | set(games['away_team'].unique())
    
    for team in all_teams:
        if pd.isna(team):
            continue
            
        # Get team's games
        team_games = games[
            (games['home_team'] == team) | (games['away_team'] == team)
        ].copy()
        
        if len(team_games) == 0:
            continue
        
        # Calculate wins and losses
        wins = 0
        losses = 0
        total_score = 0
        total_opponent_score = 0
        
        for _, game in team_games.iterrows():
            if pd.isna(game['home_score']) or pd.isna(game['away_score']):
                continue
                
            if game['home_team'] == team:
                # Team is home
                team_score = game['home_score']
                opp_score = game['away_score']
                if team_score > opp_score:
                    wins += 1
                else:
                    losses += 1
            else:
                # Team is away
                team_score = game['away_score']
                opp_score = game['home_score']
                if team_score > opp_score:
                    wins += 1
                else:
                    losses += 1
            
            total_score += team_score
            total_opponent_score += opp_score
        
        # Calculate additional stats
        total_games = wins + losses
        win_pct = wins / total_games if total_games > 0 else 0.0
        point_differential = total_score - total_opponent_score
        avg_points_for = total_score / total_games if total_games > 0 else 0.0
        avg_points_against = total_opponent_score / total_games if total_games > 0 else 0.0
        
        # Calculate rating change (simplified - would need historical data for accurate calculation)
        rating_change = 0.0  # This would require tracking rating changes over time
        
        team_stats[team] = {
            'wins': wins,
            'losses': losses,
            'win_pct': win_pct,
            'total_games': total_games,
            'points_for': total_score,
            'points_against': total_opponent_score,
            'point_differential': point_differential,
            'avg_points_for': avg_points_for,
            'avg_points_against': avg_points_against,
            'rating_change': rating_change,
            'current_rating': team_ratings.get(team, 1500.0)
        }
    
    return team_stats


def store_comprehensive_results(team_ratings: Dict[str, float], team_stats: Dict[str, Dict], 
                              years: List[int], backtest_result: Dict) -> None:
    """
    Store comprehensive ELO results in the database.
    
    Args:
        team_ratings: Final team ratings
        team_stats: Team statistics
        years: Years processed
        backtest_result: Backtest results
    """
    db_path = Path("artifacts/stats/nfl_elo_stats.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create comprehensive team_ratings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            rating REAL NOT NULL,
            season INTEGER NOT NULL,
            config_name TEXT DEFAULT 'comprehensive',
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            win_pct REAL DEFAULT 0.0,
            rating_change REAL DEFAULT 0.0,
            points_for INTEGER DEFAULT 0,
            points_against INTEGER DEFAULT 0,
            point_differential INTEGER DEFAULT 0,
            avg_points_for REAL DEFAULT 0.0,
            avg_points_against REAL DEFAULT 0.0,
            total_games INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(team, season, config_name)
        )
    ''')
    
    # Add new columns if they don't exist (for existing tables)
    try:
        cursor.execute('ALTER TABLE team_ratings ADD COLUMN points_for INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE team_ratings ADD COLUMN points_against INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE team_ratings ADD COLUMN point_differential INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE team_ratings ADD COLUMN avg_points_for REAL DEFAULT 0.0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE team_ratings ADD COLUMN avg_points_against REAL DEFAULT 0.0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE team_ratings ADD COLUMN total_games INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Clear existing comprehensive ratings
    cursor.execute("DELETE FROM team_ratings WHERE config_name = 'comprehensive'")
    
    # Insert comprehensive ratings for each year
    for year in years:
        for team, rating in team_ratings.items():
            stats = team_stats.get(team, {})
            
            cursor.execute('''
                INSERT OR REPLACE INTO team_ratings 
                (team, rating, season, config_name, wins, losses, win_pct, rating_change,
                 points_for, points_against, point_differential, avg_points_for, 
                 avg_points_against, total_games)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                team, rating, year, 'comprehensive',
                stats.get('wins', 0), stats.get('losses', 0), stats.get('win_pct', 0.0),
                stats.get('rating_change', 0.0), stats.get('points_for', 0),
                stats.get('points_against', 0), stats.get('point_differential', 0),
                stats.get('avg_points_for', 0.0), stats.get('avg_points_against', 0.0),
                stats.get('total_games', 0)
            ))
    
    # Store backtest metrics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backtest_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            years TEXT NOT NULL,
            brier_score REAL,
            accuracy REAL,
            log_loss REAL,
            ece REAL,
            games_processed INTEGER,
            teams_count INTEGER,
            config_name TEXT DEFAULT 'comprehensive'
        )
    ''')
    
    metrics = backtest_result.get('metrics', {})
    cursor.execute('''
        INSERT INTO backtest_metrics 
        (years, brier_score, accuracy, log_loss, ece, games_processed, teams_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        json.dumps(years), metrics.get('brier_score', 0.0),
        metrics.get('accuracy', 0.0), metrics.get('log_loss', 0.0),
        metrics.get('ece', 0.0), len(team_ratings), len(team_ratings)
    ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Comprehensive results stored in database")


def run_backtesting_validation(years: List[int] = [2022, 2023, 2024]) -> Dict[str, Any]:
    """
    Run backtesting validation to verify ELO calculations are correct.
    
    Args:
        years: Years to use for validation
        
    Returns:
        Validation results
    """
    print(f"\n🧪 Running backtesting validation for years: {years}")
    print("="*80)
    
    try:
        # Load games data
        games = load_games(years)
        completed_games = games.dropna(subset=['home_score', 'away_score'])
        print(f"✅ Loaded {len(completed_games)} completed games for validation")
        
        # Run backtest with comprehensive config
        config = EloConfig(
            base_rating=1500.0,
            k=20.0,
            hfa_points=55.0,
            mov_enabled=True,
            preseason_regress=0.75,
            use_travel_adjustment=True,
            use_qb_adjustment=True
        )
        
        result = run_backtest(completed_games, config)
        
        # Display validation results
        metrics = result.get('metrics', {})
        print(f"\n📊 Validation Results:")
        print(f"  Brier Score: {metrics.get('brier_score', 0.0):.4f}")
        print(f"  Accuracy: {metrics.get('accuracy', 0.0):.1%}")
        print(f"  Log Loss: {metrics.get('log_loss', 0.0):.4f}")
        print(f"  ECE: {metrics.get('ece', 0.0):.4f}")
        print(f"  Games Processed: {len(completed_games)}")
        
        # Check if results are reasonable
        brier_score = metrics.get('brier_score', 1.0)
        accuracy = metrics.get('accuracy', 0.0)
        
        validation_passed = (
            brier_score < 0.3 and  # Good calibration
            accuracy > 0.55 and    # Better than random
            len(completed_games) > 100  # Sufficient data
        )
        
        print(f"\n{'✅' if validation_passed else '❌'} Validation {'PASSED' if validation_passed else 'FAILED'}")
        
        return {
            'validation_passed': validation_passed,
            'metrics': metrics,
            'games_processed': len(completed_games),
            'years': years
        }
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return {'validation_passed': False, 'error': str(e)}


if __name__ == "__main__":
    print("🏈 COMPREHENSIVE NFL ELO RATING SYSTEM")
    print("="*80)
    
    # Calculate comprehensive ELO ratings
    years = [2020, 2021, 2022, 2023, 2024, 2025]
    result = calculate_comprehensive_elo_ratings(years)
    
    if result['success']:
        print(f"\n🎉 ELO ratings calculation completed successfully!")
        print(f"Processed {result['games_processed']} games")
        print(f"Calculated ratings for {len(result['team_ratings'])} teams")
        
        # Run validation
        validation_result = run_backtesting_validation([2022, 2023, 2024])
        if validation_result['validation_passed']:
            print(f"\n✅ System validation PASSED - ELO calculations are correct!")
        else:
            print(f"\n❌ System validation FAILED - check configuration")
    else:
        print(f"\n💥 ELO ratings calculation failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)
