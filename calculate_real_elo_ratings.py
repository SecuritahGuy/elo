#!/usr/bin/env python3
"""
Calculate real ELO ratings for NFL teams and store them in the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.nfl_elo.prediction_interface import NFLPredictionInterface
from models.nfl_elo.config import EloConfig
import sqlite3
import json
from datetime import datetime
from pathlib import Path

def calculate_and_store_elo_ratings():
    """Calculate real ELO ratings and store them in the database."""
    
    print("🏈 Calculating real ELO ratings for NFL teams...")
    
    # Initialize the prediction interface
    config = EloConfig(
        base_rating=1500.0,
        k=20.0,
        hfa_points=55.0,
        mov_enabled=True,
        preseason_regress=0.75
    )
    
    interface = NFLPredictionInterface(config)
    
    # Load team ratings for recent years including 2025
    years = [2020, 2021, 2022, 2023, 2024, 2025]
    print(f"Loading data for years: {years}")
    
    try:
        interface.load_team_ratings(years)
        
        if not interface.team_ratings:
            print("❌ No team ratings calculated!")
            return False
            
        print(f"✅ Calculated ratings for {len(interface.team_ratings)} teams")
        
        # Store ratings in database
        db_path = Path("artifacts/stats/nfl_elo_stats.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create team_ratings table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL,
                rating REAL NOT NULL,
                season INTEGER NOT NULL,
                config_name TEXT DEFAULT 'baseline',
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                win_pct REAL DEFAULT 0.0,
                rating_change REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team, season, config_name)
            )
        ''')
        
        # Clear existing ratings for 2024 and 2025
        cursor.execute("DELETE FROM team_ratings WHERE season IN (2024, 2025) AND config_name = 'baseline'")
        
        # Insert new ratings for both 2024 and 2025
        for team, rating in interface.team_ratings.items():
            # Calculate basic stats (this is simplified - in reality you'd get this from game data)
            wins = 0  # Placeholder - would calculate from actual games
            losses = 0  # Placeholder - would calculate from actual games
            win_pct = 0.5  # Placeholder - would calculate from actual games
            rating_change = 0.0  # Placeholder - would calculate from previous week
            
            # Store for 2024
            cursor.execute('''
                INSERT OR REPLACE INTO team_ratings 
                (team, rating, season, config_name, wins, losses, win_pct, rating_change)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (team, rating, 2024, 'baseline', wins, losses, win_pct, rating_change))
            
            # Store for 2025 (same ratings for now, will be updated as games are played)
            cursor.execute('''
                INSERT OR REPLACE INTO team_ratings 
                (team, rating, season, config_name, wins, losses, win_pct, rating_change)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (team, rating, 2025, 'baseline', wins, losses, win_pct, rating_change))
        
        conn.commit()
        conn.close()
        
        print("✅ ELO ratings stored in database")
        
        # Display top 10 teams
        print("\n🏆 Top 10 ELO Ratings:")
        sorted_teams = sorted(interface.team_ratings.items(), key=lambda x: x[1], reverse=True)
        for i, (team, rating) in enumerate(sorted_teams[:10], 1):
            print(f"{i:2d}. {team}: {rating:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error calculating ELO ratings: {e}")
        return False

if __name__ == "__main__":
    success = calculate_and_store_elo_ratings()
    if success:
        print("\n🎉 ELO ratings calculation completed successfully!")
    else:
        print("\n💥 ELO ratings calculation failed!")
        sys.exit(1)
