#!/usr/bin/env python3
"""
Calculate proper ELO ratings with accurate season-specific data.
This script correctly handles 2025 season with only completed games.
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


def calculate_proper_elo_ratings(years: List[int] = [2021, 2022, 2023, 2024, 2025]) -> Dict[str, Any]:
    """
    Calculate proper ELO ratings with accurate season-specific data.
    
    Args:
        years: Years to process for ELO calculations
        
    Returns:
        Dictionary with results and team ratings
    """
    print("🏈 Calculating proper ELO ratings with accurate season data...")
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
        
        # Run comprehensive backtest to get final ratings
        print(f"\n🔄 Running comprehensive backtest...")
        result = run_backtest(completed_games, config)
        
        if 'final_ratings' not in result:
            print("❌ No final ratings in backtest result!")
            return {'success': False, 'error': 'No final ratings calculated'}
        
        team_ratings = result['final_ratings']
        print(f"✅ Calculated ratings for {len(team_ratings)} teams")
        
        # Calculate proper season-specific statistics
        print(f"\n📈 Calculating proper season-specific statistics...")
        team_stats = calculate_proper_season_stats(completed_games, team_ratings, years)
        
        # Store proper results in database
        print(f"\n💾 Storing proper results in database...")
        store_proper_elo_results(team_ratings, team_stats, years, result)
        
        # Display results
        print(f"\n🏆 Top 10 ELO Ratings (proper season data):")
        sorted_teams = sorted(team_ratings.items(), key=lambda x: x[1], reverse=True)
        for i, (team, rating) in enumerate(sorted_teams[:10], 1):
            stats = team_stats.get(team, {})
            print(f"{i:2d}. {team}: {rating:.1f} (Overall: {stats.get('total_wins', 0)}-{stats.get('total_losses', 0)})")
            
            # Show 2025 specific data if available
            if 2025 in stats.get('seasons', {}):
                season_2025 = stats['seasons'][2025]
                print(f"    2025: {season_2025['wins']}-{season_2025['losses']} [Δ{season_2025['change']:+.1f}]")
        
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
        print(f"❌ Error calculating proper ELO ratings: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def calculate_proper_season_stats(games: pd.DataFrame, team_ratings: Dict[str, float], years: List[int]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate proper season-specific statistics.
    
    Args:
        games: DataFrame with game data
        team_ratings: Current team ratings
        years: Years processed
        
    Returns:
        Dictionary with proper season-specific team statistics
    """
    team_stats = {}
    
    # Get all unique teams
    all_teams = set(games['home_team'].unique()) | set(games['away_team'].unique())
    
    for team in all_teams:
        if pd.isna(team):
            continue
        
        # Initialize team stats
        team_stats[team] = {
            'total_wins': 0,
            'total_losses': 0,
            'total_games': 0,
            'total_points_for': 0,
            'total_points_against': 0,
            'seasons': {}
        }
        
        # Process each season separately
        for year in years:
            year_games = games[games['season'] == year]
            team_year_games = year_games[
                (year_games['home_team'] == team) | (year_games['away_team'] == team)
            ].copy()
            
            if len(team_year_games) == 0:
                # No games for this team in this year
                team_stats[team]['seasons'][year] = {
                    'wins': 0,
                    'losses': 0,
                    'games': 0,
                    'change': 0.0,
                    'points_for': 0,
                    'points_against': 0
                }
                continue
            
            # Calculate season-specific stats
            year_wins = 0
            year_losses = 0
            year_points_for = 0
            year_points_against = 0
            year_rating_change = 0.0
            
            for _, game in team_year_games.iterrows():
                if pd.isna(game['home_score']) or pd.isna(game['away_score']):
                    continue
                
                # Determine if team won or lost
                if game['home_team'] == team:
                    # Team is home
                    team_score = game['home_score']
                    opp_score = game['away_score']
                    won = team_score > opp_score
                else:
                    # Team is away
                    team_score = game['away_score']
                    opp_score = game['home_score']
                    won = team_score > opp_score
                
                if won:
                    year_wins += 1
                    year_rating_change += 20.0  # Simplified: +20 for win
                else:
                    year_losses += 1
                    year_rating_change -= 15.0  # Simplified: -15 for loss
                
                year_points_for += team_score
                year_points_against += opp_score
            
            # Store season-specific stats
            team_stats[team]['seasons'][year] = {
                'wins': year_wins,
                'losses': year_losses,
                'games': year_wins + year_losses,
                'change': year_rating_change,
                'points_for': year_points_for,
                'points_against': year_points_against
            }
            
            # Add to total stats
            team_stats[team]['total_wins'] += year_wins
            team_stats[team]['total_losses'] += year_losses
            team_stats[team]['total_games'] += year_wins + year_losses
            team_stats[team]['total_points_for'] += year_points_for
            team_stats[team]['total_points_against'] += year_points_against
        
        # Calculate overall stats
        team_stats[team]['total_win_pct'] = (
            team_stats[team]['total_wins'] / team_stats[team]['total_games'] 
            if team_stats[team]['total_games'] > 0 else 0.0
        )
        team_stats[team]['current_rating'] = team_ratings.get(team, 1500.0)
    
    return team_stats


def store_proper_elo_results(team_ratings: Dict[str, float], team_stats: Dict[str, Dict], 
                           years: List[int], backtest_result: Dict) -> None:
    """
    Store proper ELO results in the database.
    
    Args:
        team_ratings: Final team ratings
        team_stats: Team statistics with proper season data
        years: Years processed
        backtest_result: Backtest results
    """
    db_path = Path("sportsedge_unified.db")
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
    
    # Insert proper ratings for each year
    for year in years:
        for team, rating in team_ratings.items():
            stats = team_stats.get(team, {})
            season_stats = stats.get('seasons', {}).get(year, {})
            
            # Use season-specific stats
            wins = season_stats.get('wins', 0)
            losses = season_stats.get('losses', 0)
            games = season_stats.get('games', 0)
            change = season_stats.get('change', 0.0)
            points_for = season_stats.get('points_for', 0)
            points_against = season_stats.get('points_against', 0)
            
            win_pct = wins / games if games > 0 else 0.0
            point_differential = points_for - points_against
            avg_points_for = points_for / games if games > 0 else 0.0
            avg_points_against = points_against / games if games > 0 else 0.0
            
            cursor.execute('''
                INSERT OR REPLACE INTO team_ratings 
                (team, rating, season, config_name, wins, losses, win_pct, rating_change,
                 points_for, points_against, point_differential, avg_points_for, 
                 avg_points_against, total_games)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                team, rating, year, 'comprehensive',
                wins, losses, win_pct, change,
                points_for, points_against, point_differential,
                avg_points_for, avg_points_against, games
            ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Proper ELO results stored in database")


if __name__ == "__main__":
    print("🏈 PROPER ELO RATING SYSTEM")
    print("="*80)
    
    # Calculate proper ELO ratings
    years = [2021, 2022, 2023, 2024, 2025]
    result = calculate_proper_elo_ratings(years)
    
    if result['success']:
        print(f"\n🎉 Proper ELO ratings calculation completed successfully!")
        print(f"Processed {result['games_processed']} games")
        print(f"Calculated ratings for {len(result['team_ratings'])} teams")
    else:
        print(f"\n💥 Proper ELO ratings calculation failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)
