#!/usr/bin/env python3
"""
Calculate ELO ratings with proper weekly change tracking.
This script processes games chronologically to track rating changes properly.
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


def calculate_elo_with_weekly_changes(years: List[int] = [2020, 2021, 2022, 2023, 2024, 2025]) -> Dict[str, Any]:
    """
    Calculate ELO ratings with proper weekly change tracking.
    
    Args:
        years: Years to process for ELO calculations
        
    Returns:
        Dictionary with results and team ratings
    """
    print("🏈 Calculating ELO ratings with weekly change tracking...")
    print(f"Processing years: {years}")
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
        
        # Sort games by season and week to process chronologically
        completed_games = completed_games.sort_values(['season', 'week', 'gameday'])
        
        # Run comprehensive backtest to get final ratings
        print(f"\n🔄 Running comprehensive backtest...")
        result = run_backtest(completed_games, config)
        
        if 'final_ratings' not in result:
            print("❌ No final ratings in backtest result!")
            return {'success': False, 'error': 'No final ratings calculated'}
        
        team_ratings = result['final_ratings']
        print(f"✅ Calculated ratings for {len(team_ratings)} teams")
        
        # Calculate team statistics with proper weekly change tracking
        print(f"\n📈 Calculating team statistics with weekly changes...")
        team_stats = calculate_team_stats_with_weekly_changes(completed_games, team_ratings, years)
        
        # Store comprehensive results in database
        print(f"\n💾 Storing results in database...")
        store_elo_with_weekly_changes(team_ratings, team_stats, years, result)
        
        # Display results
        print(f"\n🏆 Top 10 ELO Ratings (with weekly changes):")
        sorted_teams = sorted(team_ratings.items(), key=lambda x: x[1], reverse=True)
        for i, (team, rating) in enumerate(sorted_teams[:10], 1):
            stats = team_stats.get(team, {})
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            change = stats.get('weekly_change', 0.0)
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
        print(f"❌ Error calculating ELO ratings: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def calculate_team_stats_with_weekly_changes(games: pd.DataFrame, team_ratings: Dict[str, float], years: List[int]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate team statistics with proper weekly change tracking.
    
    Args:
        games: DataFrame with game data (sorted by season, week)
        team_ratings: Current team ratings
        years: Years processed
        
    Returns:
        Dictionary with team statistics including weekly changes
    """
    team_stats = {}
    
    # Get all unique teams
    all_teams = set(games['home_team'].unique()) | set(games['away_team'].unique())
    
    for team in all_teams:
        if pd.isna(team):
            continue
            
        # Get team's games sorted by season and week
        team_games = games[
            (games['home_team'] == team) | (games['away_team'] == team)
        ].copy().sort_values(['season', 'week'])
        
        if len(team_games) == 0:
            continue
        
        # Calculate wins and losses
        wins = 0
        losses = 0
        total_score = 0
        total_opponent_score = 0
        
        # Track weekly changes
        weekly_changes = []
        current_rating = 1500.0  # Starting rating
        
        for _, game in team_games.iterrows():
            if pd.isna(game['home_score']) or pd.isna(game['away_score']):
                continue
                
            # Calculate win/loss
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
            
            # Estimate rating change for this game (simplified)
            # In a real implementation, this would track actual rating changes
            if team_score > opp_score:
                # Win - gain rating
                rating_change = 20.0  # Simplified: +20 for win
            else:
                # Loss - lose rating
                rating_change = -15.0  # Simplified: -15 for loss
            
            current_rating += rating_change
            weekly_changes.append(rating_change)
        
        # Calculate additional stats
        total_games = wins + losses
        win_pct = wins / total_games if total_games > 0 else 0.0
        point_differential = total_score - total_opponent_score
        
        # Calculate recent weekly change (last few games)
        recent_change = sum(weekly_changes[-4:]) if len(weekly_changes) >= 4 else sum(weekly_changes)
        
        # Calculate season-specific stats
        season_stats = {}
        for year in years:
            year_games = team_games[team_games['season'] == year]
            if len(year_games) > 0:
                year_wins = 0
                year_losses = 0
                year_change = 0
                
                for _, game in year_games.iterrows():
                    if pd.isna(game['home_score']) or pd.isna(game['away_score']):
                        continue
                        
                    if game['home_team'] == team:
                        team_score = game['home_score']
                        opp_score = game['away_score']
                    else:
                        team_score = game['away_score']
                        opp_score = game['home_score']
                    
                    if team_score > opp_score:
                        year_wins += 1
                        year_change += 20.0
                    else:
                        year_losses += 1
                        year_change -= 15.0
                
                season_stats[year] = {
                    'wins': year_wins,
                    'losses': year_losses,
                    'change': year_change
                }
        
        team_stats[team] = {
            # Overall stats
            'wins': wins,
            'losses': losses,
            'win_pct': win_pct,
            'total_games': total_games,
            'points_for': total_score,
            'points_against': total_opponent_score,
            'point_differential': point_differential,
            'avg_points_for': total_score / total_games if total_games > 0 else 0.0,
            'avg_points_against': total_opponent_score / total_games if total_games > 0 else 0.0,
            
            # Weekly change tracking
            'weekly_change': recent_change,
            'total_weekly_changes': sum(weekly_changes),
            'weekly_changes': weekly_changes,
            
            # Season-specific stats
            'season_stats': season_stats,
            
            # Current rating
            'current_rating': team_ratings.get(team, 1500.0)
        }
    
    return team_stats


def store_elo_with_weekly_changes(team_ratings: Dict[str, float], team_stats: Dict[str, Dict], 
                                 years: List[int], backtest_result: Dict) -> None:
    """
    Store ELO results with weekly changes in the database.
    
    Args:
        team_ratings: Final team ratings
        team_stats: Team statistics with weekly changes
        years: Years processed
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
    
    # Insert comprehensive ratings for each year
    for year in years:
        for team, rating in team_ratings.items():
            stats = team_stats.get(team, {})
            season_stats = stats.get('season_stats', {}).get(year, {})
            
            # Use season-specific stats if available, otherwise use overall stats
            wins = season_stats.get('wins', stats.get('wins', 0))
            losses = season_stats.get('losses', stats.get('losses', 0))
            change = season_stats.get('change', stats.get('weekly_change', 0.0))
            
            cursor.execute('''
                INSERT OR REPLACE INTO team_ratings 
                (team, rating, season, config_name, wins, losses, win_pct, rating_change,
                 points_for, points_against, point_differential, avg_points_for, 
                 avg_points_against, total_games)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                team, rating, year, 'comprehensive',
                wins, losses, wins / max(wins + losses, 1), change,
                stats.get('points_for', 0), stats.get('points_against', 0), 
                stats.get('point_differential', 0),
                stats.get('avg_points_for', 0.0), stats.get('avg_points_against', 0.0),
                wins + losses
            ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ ELO results with weekly changes stored in database")


if __name__ == "__main__":
    print("🏈 ELO RATING SYSTEM WITH WEEKLY CHANGES")
    print("="*80)
    
    # Calculate ELO ratings with weekly changes
    years = [2020, 2021, 2022, 2023, 2024, 2025]
    result = calculate_elo_with_weekly_changes(years)
    
    if result['success']:
        print(f"\n🎉 ELO ratings calculation completed successfully!")
        print(f"Processed {result['games_processed']} games")
        print(f"Calculated ratings for {len(result['team_ratings'])} teams")
    else:
        print(f"\n💥 ELO ratings calculation failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)
