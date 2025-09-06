#!/usr/bin/env python3
"""
Background process to generate ELO projections for all remaining weeks
This script can be run as a cron job or background service
"""

import sys
import os
import logging
from datetime import datetime
from elo_projection_service import ELOProjectionService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('elo_projections.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Generate ELO projections for all remaining weeks"""
    try:
        logger.info("Starting ELO projection generation process")
        
        # Initialize the projection service
        service = ELOProjectionService()
        
        # Get current season and week
        season = 2025
        current_week = 1  # You might want to determine this dynamically
        
        logger.info(f"Generating projections for season {season}, starting from week {current_week + 1}")
        
        # Generate projections for all remaining weeks
        service.project_all_weeks(season, current_week)
        
        logger.info("ELO projection generation completed successfully")
        
        # Log summary
        conn = service._init_database() if hasattr(service, '_init_database') else None
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM projected_elo_ratings 
                WHERE season = ? AND week > ?
            ''', (season, current_week))
            count = cursor.fetchone()[0]
            logger.info(f"Generated {count} total projections")
            conn.close()
        
    except Exception as e:
        logger.error(f"Error in ELO projection generation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
