#!/usr/bin/env python3
"""
Update ELO ratings in the unified database with latest 2025 season data.
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
from models.nfl_elo.backtest import run_backtest, analyze_rating_trajectories
from ingest.nfl.data_loader import load_games


def update_unified_elo_ratings(years: List[int] = [2021, 2022, 2023, 2024, 2025]) -> Dict[str, Any]:
    """
    Update ELO ratings in the unified database with latest data.
    
    Args:
        years: Years to process for ELO calculations
        
    Returns:
        Dictionary with results and team ratings
    """
    print("🏈 Updating ELO ratings in unified database...")
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
        use_qb_adjustment=True,
        start_season=min(years),
        end_season=max(years)
    )
    
    try:
        # Load games data for all years
        print(f"📊 Loading game data for years: {years}")
        games_df = load_games(years)
        print(f"✅ Loaded {len(games_df)} games")
        
        # Filter to completed games only
        completed_games = games_df.dropna(subset=['home_score', 'away_score'])
        print(f"✅ Found {len(completed_games)} completed games")
        
        # Run backtest to calculate ELO ratings
        print("🔄 Running comprehensive backtest...")
        backtest_result = run_backtest(
            games=completed_games,
            cfg=config
        )
        
        team_ratings = backtest_result['final_ratings']
        print(f"✅ Calculated ratings for {len(team_ratings)} teams")
        
        # Calculate rating trajectories for accurate rating changes
        print("📈 Calculating rating trajectories...")
        trajectories = analyze_rating_trajectories(backtest_result)
        backtest_result['trajectories'] = trajectories
        
        # Calculate team statistics
        print("📈 Calculating team statistics...")
        team_stats = calculate_team_statistics(completed_games, team_ratings, years)
        
        # Update unified database
        print("💾 Updating unified database...")
        update_unified_database(team_ratings, team_stats, years, backtest_result)
        
        # Display results
        print("\n🏆 Top 10 ELO Ratings (updated):")
        sorted_teams = sorted(team_ratings.items(), key=lambda x: x[1], reverse=True)
        for i, (team, rating) in enumerate(sorted_teams[:10], 1):
            stats = team_stats.get(team, {})
            overall_wins = stats.get('overall_wins', 0)
            overall_losses = stats.get('overall_losses', 0)
            season_2025 = stats.get('seasons', {}).get(2025, {})
            wins_2025 = season_2025.get('wins', 0)
            losses_2025 = season_2025.get('losses', 0)
            change_2025 = season_2025.get('change', 0.0)
            
            print(f"{i:2d}. {team}: {rating:.1f} (Overall: {overall_wins}-{overall_losses})")
            print(f"    2025: {wins_2025}-{losses_2025} [Δ{change_2025:+.1f}]")
        
        print(f"\n🎉 ELO ratings update completed successfully!")
        print(f"Processed {len(completed_games)} games")
        print(f"Calculated ratings for {len(team_ratings)} teams")
        
        return {
            'team_ratings': team_ratings,
            'team_stats': team_stats,
            'years': years,
            'backtest_result': backtest_result
        }
        
    except Exception as e:
        print(f"❌ Error updating ELO ratings: {e}")
        raise


def calculate_team_statistics(games_df: pd.DataFrame, team_ratings: Dict[str, float], years: List[int]) -> Dict[str, Any]:
    """Calculate comprehensive team statistics."""
    team_stats = {}
    
    for team in team_ratings.keys():
        # Overall stats
        team_games = games_df[
            (games_df['home_team'] == team) | (games_df['away_team'] == team)
        ]
        
        wins = 0
        losses = 0
        points_for = 0
        points_against = 0
        
        for _, game in team_games.iterrows():
            if pd.isna(game['home_score']) or pd.isna(game['away_score']):
                continue
                
            if game['home_team'] == team:
                team_score = game['home_score']
                opp_score = game['away_score']
                if team_score > opp_score:
                    wins += 1
                else:
                    losses += 1
            else:
                team_score = game['away_score']
                opp_score = game['home_score']
                if team_score > opp_score:
                    wins += 1
                else:
                    losses += 1
            
            points_for += team_score
            points_against += opp_score
        
        # Season-specific stats
        seasons = {}
        for year in years:
            year_games = team_games[team_games['season'] == year]
            year_wins = 0
            year_losses = 0
            year_points_for = 0
            year_points_against = 0
            
            for _, game in year_games.iterrows():
                if pd.isna(game['home_score']) or pd.isna(game['away_score']):
                    continue
                    
                if game['home_team'] == team:
                    team_score = game['home_score']
                    opp_score = game['away_score']
                    if team_score > opp_score:
                        year_wins += 1
                    else:
                        year_losses += 1
                else:
                    team_score = game['away_score']
                    opp_score = game['home_score']
                    if team_score > opp_score:
                        year_wins += 1
                    else:
                        year_losses += 1
                
                year_points_for += team_score
                year_points_against += opp_score
            
            seasons[year] = {
                'wins': year_wins,
                'losses': year_losses,
                'games': year_wins + year_losses,
                'points_for': year_points_for,
                'points_against': year_points_against,
                'change': 0.0  # Will be calculated separately
            }
        
        team_stats[team] = {
            'overall_wins': wins,
            'overall_losses': losses,
            'overall_points_for': points_for,
            'overall_points_against': points_against,
            'seasons': seasons
        }
    
    return team_stats


def update_unified_database(team_ratings: Dict[str, float], team_stats: Dict[str, Any], 
                          years: List[int], backtest_result: Dict[str, Any]):
    """Update the unified database with new ELO ratings."""
    db_path = Path("sportsedge_unified.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get sport and season IDs
    cursor.execute("SELECT id FROM sports WHERE sport_code = 'nfl'")
    sport_result = cursor.fetchone()
    if not sport_result:
        print("❌ NFL sport not found in database")
        return
    sport_id = sport_result[0]
    
    # Get team mappings
    cursor.execute("SELECT id, abbreviation FROM teams WHERE sport_id = ?", (sport_id,))
    team_mapping = {abbr: team_id for team_id, abbr in cursor.fetchall()}
    
    # Get season mappings
    cursor.execute("SELECT id, season_year FROM seasons WHERE season_year IN ({})".format(','.join('?' * len(years))), years)
    season_mapping = {year: season_id for season_id, year in cursor.fetchall()}
    
    # Clear existing ELO ratings for 2025
    if 2025 in season_mapping:
        season_id_2025 = season_mapping[2025]
        cursor.execute("DELETE FROM team_ratings WHERE season_id = ? AND sport_id = ?", (season_id_2025, sport_id))
        print(f"✅ Cleared existing 2025 ELO ratings")
    
    # Insert new ELO ratings
    for team_abbr, rating in team_ratings.items():
        if team_abbr not in team_mapping:
            print(f"⚠️  Team {team_abbr} not found in database")
            continue
            
        team_id = team_mapping[team_abbr]
        stats = team_stats.get(team_abbr, {})
        
        # Insert for each year
        for year in years:
            if year not in season_mapping:
                continue
                
            season_id = season_mapping[year]
            season_stats = stats.get('seasons', {}).get(year, {})
            
            wins = season_stats.get('wins', 0)
            losses = season_stats.get('losses', 0)
            ties = 0  # NFL doesn't have ties in recent years
            games = wins + losses + ties
            win_pct = wins / games if games > 0 else 0.0
            
            points_for = season_stats.get('points_for', 0)
            points_against = season_stats.get('points_against', 0)
            point_diff = points_for - points_against
            
            # Calculate rating change from backtest trajectories
            rating_change = 0.0
            if year == 2025 and games > 0:
                # Get actual rating changes from backtest trajectories
                if 'trajectories' in backtest_result:
                    team_trajectories = backtest_result['trajectories']
                    if len(team_trajectories) > 0:
                        # Filter by team and season
                        team_changes = team_trajectories[
                            (team_trajectories['team'] == team_abbr) & 
                            (team_trajectories['season'] == year)
                        ]
                        if len(team_changes) > 0:
                            # Sum all rating changes for this team in this specific season
                            rating_change = team_changes['rating_change'].sum()
                else:
                    # Fallback: calculate change from base rating (simplified)
                    base_rating = 1500.0
                    rating_change = rating - base_rating
            
            cursor.execute('''
                INSERT INTO team_ratings 
                (team_id, sport_id, season_id, week, rating, rating_change, wins, losses, ties, 
                 win_percentage, points_for, points_against, point_differential, 
                 home_record, away_record, division_record, conference_record, 
                 strength_of_schedule, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                team_id, sport_id, season_id, None, rating, rating_change, wins, losses, ties,
                win_pct, points_for, points_against, point_diff,
                None, None, None, None, 0.0, datetime.now(), datetime.now()
            ))
    
    conn.commit()
    conn.close()
    print("✅ Updated unified database with new ELO ratings")


if __name__ == "__main__":
    result = update_unified_elo_ratings()
    print("\n🎉 ELO ratings update completed!")
