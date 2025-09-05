#!/usr/bin/env python3
"""
Automated Daily ELO Updater - Runs daily to update ELO ratings.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from update_weekly_elo import WeeklyEloUpdater
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('artifacts/automated_collection/elo_updates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedEloUpdater:
    """Automated system for weekly ELO updates."""
    
    def __init__(self):
        self.updater = WeeklyEloUpdater()
    
    def get_current_week(self, season: int) -> int:
        """Determine the current week based on available games."""
        try:
            # Get the highest week with completed games
            import sqlite3
            conn = sqlite3.connect(self.updater.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT MAX(week) as max_week
                FROM nfl_games_2025
                WHERE season = ? 
                AND home_score IS NOT NULL 
                AND away_score IS NOT NULL
            ''', (season,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result[0] else 1
            
        except Exception as e:
            logger.error(f"Error getting current week: {e}")
            return 1
    
    def update_all_weeks(self, season: int, start_week: int = 1) -> Dict[str, any]:
        """Update ELO ratings for all weeks from start_week to current."""
        try:
            current_week = self.get_current_week(season)
            logger.info(f"Current week for {season}: {current_week}")
            
            results = {}
            
            for week in range(start_week, current_week + 1):
                logger.info(f"Processing Week {week}...")
                
                result = self.updater.update_ratings_for_week(season, week)
                if result:
                    results[f"week_{week}"] = result
                    logger.info(f"✅ Week {week} completed: {result['games_processed']} games processed")
                else:
                    logger.warning(f"⚠️ Week {week} failed or no games found")
            
            return results
            
        except Exception as e:
            logger.error(f"Error updating all weeks: {e}")
            return {}
    
    def get_weekly_summary(self, season: int) -> Dict[str, any]:
        """Get a summary of weekly ELO changes."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.updater.db_path)
            cursor = conn.cursor()
            
            # Get current ratings with changes
            cursor.execute('''
                SELECT team, rating, rating_change, wins, losses, win_pct
                FROM team_ratings
                WHERE season = ?
                ORDER BY rating DESC
            ''', (season,))
            
            teams = []
            for row in cursor.fetchall():
                team, rating, change, wins, losses, win_pct = row
                teams.append({
                    'team': team,
                    'rating': round(rating, 1),
                    'change': round(change, 1),
                    'wins': wins,
                    'losses': losses,
                    'win_pct': round(win_pct, 3)
                })
            
            conn.close()
            
            return {
                'season': season,
                'teams': teams,
                'total_teams': len(teams),
                'updated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting weekly summary: {e}")
            return {}

def main():
    """Main function for automated ELO updates."""
    parser = argparse.ArgumentParser(description='Automated Weekly ELO Updater')
    parser.add_argument('--season', type=int, default=2025, help='Season year')
    parser.add_argument('--week', type=int, help='Specific week to update (if not provided, updates all weeks)')
    parser.add_argument('--summary', action='store_true', help='Show weekly summary')
    
    args = parser.parse_args()
    
    updater = AutomatedEloUpdater()
    
    if args.summary:
        # Show summary
        summary = updater.get_weekly_summary(args.season)
        if summary:
            print(f"\n📊 ELO Summary for {args.season} Season:")
            print(f"Total Teams: {summary['total_teams']}")
            print(f"Updated: {summary['updated_at']}")
            print(f"\n🏆 Top 10 Teams:")
            for i, team in enumerate(summary['teams'][:10], 1):
                print(f"{i:2d}. {team['team']}: {team['rating']} ({team['change']:+.1f}) - {team['wins']}-{team['losses']}")
        else:
            print("❌ Failed to get summary")
            sys.exit(1)
    
    elif args.week:
        # Update specific week
        logger.info(f"Updating {args.season} Week {args.week}")
        result = updater.updater.update_ratings_for_week(args.season, args.week)
        if result:
            print(f"✅ Successfully updated Week {args.week}")
        else:
            print(f"❌ Failed to update Week {args.week}")
            sys.exit(1)
    
    else:
        # Update all weeks
        logger.info(f"Updating all weeks for {args.season}")
        results = updater.update_all_weeks(args.season)
        if results:
            print(f"✅ Successfully updated {len(results)} weeks")
        else:
            print("❌ Failed to update weeks")
            sys.exit(1)

if __name__ == "__main__":
    main()
