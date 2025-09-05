#!/usr/bin/env python3
"""
Daily Injury Data Updater
Updates injury data for the current NFL season.
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.nfl_elo.injury_integration import InjuryImpactCalculator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('artifacts/automated_collection/injury_updates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def update_injury_data(season=None, dry_run=False):
    """
    Update injury data for the specified season.
    
    Args:
        season: NFL season year (defaults to current year)
        dry_run: If True, only log what would be done without making changes
    """
    if season is None:
        season = datetime.now().year
    
    logger.info(f"Starting injury data update for season {season}")
    
    try:
        # Create injury calculator
        calculator = InjuryImpactCalculator()
        
        # Load injury data to verify it's available
        logger.info(f"Loading injury data for season {season}...")
        injuries = calculator.load_injury_data([season])
        
        if injuries.empty:
            logger.warning(f"No injury data available for season {season}")
            return False
        
        # Log summary statistics
        total_injuries = len(injuries)
        unique_players = injuries['gsis_id'].nunique()
        teams_affected = injuries['team'].nunique()
        
        logger.info(f"Injury data summary for {season}:")
        logger.info(f"  Total injuries: {total_injuries}")
        logger.info(f"  Unique players: {unique_players}")
        logger.info(f"  Teams affected: {teams_affected}")
        
        if dry_run:
            logger.info("DRY RUN: No data was actually updated")
            return True
        
        # For now, we're just verifying data availability
        # In the future, this could update a database or cache
        logger.info("Injury data verification completed successfully")
        
        # Create a status file to track last successful update
        status_file = f"artifacts/automated_collection/injury_status_{season}.txt"
        os.makedirs(os.path.dirname(status_file), exist_ok=True)
        
        with open(status_file, 'w') as f:
            f.write(f"last_update: {datetime.now().isoformat()}\n")
            f.write(f"season: {season}\n")
            f.write(f"total_injuries: {total_injuries}\n")
            f.write(f"unique_players: {unique_players}\n")
            f.write(f"teams_affected: {teams_affected}\n")
        
        logger.info(f"Status file updated: {status_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating injury data for season {season}: {e}")
        return False

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Update NFL injury data')
    parser.add_argument('--season', type=int, help='NFL season year (defaults to current year)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--summary', action='store_true', help='Show summary of recent updates')
    
    args = parser.parse_args()
    
    if args.summary:
        show_update_summary()
        return
    
    success = update_injury_data(season=args.season, dry_run=args.dry_run)
    
    if success:
        logger.info("Injury data update completed successfully")
        sys.exit(0)
    else:
        logger.error("Injury data update failed")
        sys.exit(1)

def show_update_summary():
    """Show summary of recent injury data updates."""
    logger.info("Recent injury data update summary:")
    
    # Look for status files
    status_dir = "artifacts/automated_collection"
    if os.path.exists(status_dir):
        status_files = [f for f in os.listdir(status_dir) if f.startswith('injury_status_')]
        
        if not status_files:
            logger.info("No injury data updates found")
            return
        
        for status_file in sorted(status_files):
            file_path = os.path.join(status_dir, status_file)
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    logger.info(f"\n{status_file}:")
                    logger.info(content)
            except Exception as e:
                logger.error(f"Error reading {status_file}: {e}")
    else:
        logger.info("No status directory found")

if __name__ == "__main__":
    main()
