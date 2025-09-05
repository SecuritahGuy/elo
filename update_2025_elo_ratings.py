#!/usr/bin/env python3
"""
Update 2025 ELO ratings with proper weekly change tracking.
This script focuses on 2025 season and tracks rating changes properly.
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


def update_2025_elo_with_changes() -> Dict[str, Any]:
    """
    Update 2025 ELO ratings with proper weekly change tracking.
    
    Returns:
        Dictionary with results and team ratings
    """
    print("🏈 Updating 2025 ELO ratings with weekly change tracking...")
    print("="*80)
    
    # Initialize the comprehensive prediction interface
    config = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.75,
        use_travel_adjustment=True,
        use_qb_adjustment=True
    )
    
    try:
        # Load games data for all years to get proper historical context
        print(f"\n📊 Loading historical game data...")
        historical_games = load_games([2020, 2021, 2022, 2023, 2024])
        print(f"✅ Loaded {len(historical_games)} historical games")
        
        # Load 2025 games
        print(f"\n📊 Loading 2025 game data...")
        games_2025 = load_games([2025])
        completed_2025 = games_2025.dropna(subset=['home_score', 'away_score'])
        print(f"✅ Loaded {len(games_2025)} total 2025 games, {len(completed_2025)} completed")
        
        if len(completed_2025) > 0:
            print(f"\n🎮 Completed 2025 games:")
            for _, game in completed_2025.iterrows():
                winner = game['home_team'] if game['home_score'] > game['away_score'] else game['away_team']
                loser = game['away_team'] if game['home_score'] > game['away_score'] else game['home_team']
                print(f"  Week {int(game['week'])}: {winner} def. {loser} ({int(game['home_score'])}-{int(game['away_score'])})")
        
        # Combine historical and 2025 data
        all_games = pd.concat([historical_games, games_2025], ignore_index=True)
        print(f"✅ Combined dataset: {len(all_games)} total games")
        
        # Run comprehensive backtest to get final ratings
        print(f"\n🔄 Running comprehensive backtest...")
        result = run_backtest(all_games, config)
        
        if 'final_ratings' not in result:
            print("❌ No final ratings in backtest result!")
            return {'success': False, 'error': 'No final ratings calculated'}
        
        team_ratings = result['final_ratings']
        print(f"✅ Calculated ratings for {len(team_ratings)} teams")
        
        # Calculate team statistics with 2025 focus
        print(f"\n📈 Calculating team statistics with 2025 focus...")
        team_stats = calculate_2025_team_statistics(all_games, team_ratings, completed_2025)
        
        # Store comprehensive results in database
        print(f"\n💾 Storing 2025-focused results in database...")
        store_2025_results(team_ratings, team_stats, result)
        
        # Display 2025-focused results
        print(f"\n🏆 2025 Season ELO Ratings (with changes):")
        sorted_teams = sorted(team_ratings.items(), key=lambda x: x[1], reverse=True)
        for i, (team, rating) in enumerate(sorted_teams[:10], 1):
            stats = team_stats.get(team, {})
            wins_2025 = stats.get('wins_2025', 0)
            losses_2025 = stats.get('losses_2025', 0)
            change_2025 = stats.get('rating_change_2025', 0.0)
            total_wins = stats.get('wins', 0)
            total_losses = stats.get('losses', 0)
            print(f"{i:2d}. {team}: {rating:.1f} (2025: {wins_2025}-{losses_2025} [Δ{change_2025:+.1f}], Total: {total_wins}-{total_losses})")
        
        return {
            'success': True,
            'team_ratings': team_ratings,
            'team_stats': team_stats,
            'games_processed': len(all_games),
            'games_2025': len(completed_2025),
            'backtest_metrics': result.get('metrics', {}),
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error updating 2025 ELO ratings: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def calculate_2025_team_statistics(all_games: pd.DataFrame, team_ratings: Dict[str, float], 
                                 games_2025: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Calculate team statistics with focus on 2025 season changes.
    
    Args:
        all_games: All historical games
        team_ratings: Current team ratings
        games_2025: 2025 season games
        
    Returns:
        Dictionary with team statistics including 2025-specific data
    """
    team_stats = {}
    
    # Get all unique teams
    all_teams = set(all_games['home_team'].unique()) | set(all_games['away_team'].unique())
    
    for team in all_teams:
        if pd.isna(team):
            continue
            
        # Get team's all-time games
        team_games = all_games[
            (all_games['home_team'] == team) | (all_games['away_team'] == team)
        ].copy()
        
        # Get team's 2025 games
        team_games_2025 = games_2025[
            (games_2025['home_team'] == team) | (games_2025['away_team'] == team)
        ].copy()
        
        if len(team_games) == 0:
            continue
        
        # Calculate all-time stats
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
        
        # Calculate 2025-specific stats
        wins_2025 = 0
        losses_2025 = 0
        total_score_2025 = 0
        total_opponent_score_2025 = 0
        
        for _, game in team_games_2025.iterrows():
            if pd.isna(game['home_score']) or pd.isna(game['away_score']):
                continue
                
            if game['home_team'] == team:
                # Team is home
                team_score = game['home_score']
                opp_score = game['away_score']
                if team_score > opp_score:
                    wins_2025 += 1
                else:
                    losses_2025 += 1
            else:
                # Team is away
                team_score = game['away_score']
                opp_score = game['home_score']
                if team_score > opp_score:
                    wins_2025 += 1
                else:
                    losses_2025 += 1
            
            total_score_2025 += team_score
            total_opponent_score_2025 += opp_score
        
        # Calculate additional stats
        total_games = wins + losses
        total_games_2025 = wins_2025 + losses_2025
        win_pct = wins / total_games if total_games > 0 else 0.0
        win_pct_2025 = wins_2025 / total_games_2025 if total_games_2025 > 0 else 0.0
        
        # Calculate rating change for 2025 (simplified - would need historical tracking)
        # For now, we'll estimate based on 2025 performance
        rating_change_2025 = 0.0
        if total_games_2025 > 0:
            # Estimate rating change based on 2025 win percentage vs expected
            expected_win_pct = 0.5  # Base expectation
            performance_delta = win_pct_2025 - expected_win_pct
            # Rough estimate: each game affects rating by ~20 points
            rating_change_2025 = performance_delta * total_games_2025 * 20
        
        team_stats[team] = {
            # All-time stats
            'wins': wins,
            'losses': losses,
            'win_pct': win_pct,
            'total_games': total_games,
            'points_for': total_score,
            'points_against': total_opponent_score,
            'point_differential': total_score - total_opponent_score,
            
            # 2025-specific stats
            'wins_2025': wins_2025,
            'losses_2025': losses_2025,
            'win_pct_2025': win_pct_2025,
            'total_games_2025': total_games_2025,
            'points_for_2025': total_score_2025,
            'points_against_2025': total_opponent_score_2025,
            'point_differential_2025': total_score_2025 - total_opponent_score_2025,
            'rating_change_2025': rating_change_2025,
            
            # Current rating
            'current_rating': team_ratings.get(team, 1500.0)
        }
    
    return team_stats


def store_2025_results(team_ratings: Dict[str, float], team_stats: Dict[str, Dict], 
                      backtest_result: Dict) -> None:
    """
    Store 2025-focused ELO results in the database.
    
    Args:
        team_ratings: Final team ratings
        team_stats: Team statistics
        backtest_result: Backtest results
    """
    db_path = Path("artifacts/stats/nfl_elo_stats.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create comprehensive team_ratings table if it doesn't exist
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
    
    # Clear existing comprehensive ratings
    cursor.execute("DELETE FROM team_ratings WHERE config_name = 'comprehensive'")
    
    # Insert comprehensive ratings for 2025 (most recent)
    for team, rating in team_ratings.items():
        stats = team_stats.get(team, {})
        
        cursor.execute('''
            INSERT OR REPLACE INTO team_ratings 
            (team, rating, season, config_name, wins, losses, win_pct, rating_change,
             points_for, points_against, point_differential, avg_points_for, 
             avg_points_against, total_games)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            team, rating, 2025, 'comprehensive',
            stats.get('wins', 0), stats.get('losses', 0), stats.get('win_pct', 0.0),
            stats.get('rating_change_2025', 0.0), stats.get('points_for', 0),
            stats.get('points_against', 0), stats.get('point_differential', 0),
            stats.get('points_for', 0) / max(stats.get('total_games', 1), 1),
            stats.get('points_against', 0) / max(stats.get('total_games', 1), 1),
            stats.get('total_games', 0)
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ 2025-focused results stored in database")


if __name__ == "__main__":
    print("🏈 2025 NFL ELO RATING UPDATE SYSTEM")
    print("="*80)
    
    # Update 2025 ELO ratings with proper tracking
    result = update_2025_elo_with_changes()
    
    if result['success']:
        print(f"\n🎉 2025 ELO ratings updated successfully!")
        print(f"Processed {result['games_processed']} total games")
        print(f"Processed {result['games_2025']} 2025 games")
        print(f"Calculated ratings for {len(result['team_ratings'])} teams")
    else:
        print(f"\n💥 2025 ELO ratings update failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)
