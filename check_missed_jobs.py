#!/usr/bin/env python3
"""
Missed Jobs Checker and Failover System
Checks if scheduled jobs have been missed and runs them if needed.
"""

import sys
import os
import subprocess
import logging
from datetime import datetime, timedelta
import glob

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('artifacts/automated_collection/failover.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_job_status(job_name, status_file_pattern, max_hours_since_last_run=25):
    """
    Check if a job has run recently and return status.
    
    Args:
        job_name: Name of the job for logging
        status_file_pattern: Pattern to match status files (e.g., "injury_status_*.txt")
        max_hours_since_last_run: Maximum hours since last run before considering it missed
    
    Returns:
        dict with status information
    """
    status_dir = "artifacts/automated_collection"
    
    if not os.path.exists(status_dir):
        return {
            'status': 'no_status_dir',
            'message': f'Status directory {status_dir} does not exist',
            'should_run': True
        }
    
    # Find most recent status file
    status_files = glob.glob(os.path.join(status_dir, status_file_pattern))
    
    if not status_files:
        return {
            'status': 'no_status_files',
            'message': f'No status files found for pattern {status_file_pattern}',
            'should_run': True
        }
    
    # Get the most recent status file
    latest_file = max(status_files, key=os.path.getmtime)
    
    try:
        with open(latest_file, 'r') as f:
            content = f.read()
        
        # Parse the status file
        status_data = {}
        for line in content.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                status_data[key.strip()] = value.strip()
        
        if 'last_update' not in status_data:
            return {
                'status': 'invalid_status_file',
                'message': f'Status file {latest_file} missing last_update timestamp',
                'should_run': True
            }
        
        # Parse the timestamp
        last_update_str = status_data['last_update']
        try:
            last_update = datetime.fromisoformat(last_update_str)
        except ValueError:
            return {
                'status': 'invalid_timestamp',
                'message': f'Invalid timestamp format in {latest_file}: {last_update_str}',
                'should_run': True
            }
        
        # Check if job is overdue
        hours_since_last_run = (datetime.now() - last_update).total_seconds() / 3600
        
        if hours_since_last_run > max_hours_since_last_run:
            return {
                'status': 'overdue',
                'message': f'Job last ran {hours_since_last_run:.1f} hours ago (max: {max_hours_since_last_run})',
                'should_run': True,
                'last_update': last_update,
                'hours_since': hours_since_last_run
            }
        else:
            return {
                'status': 'recent',
                'message': f'Job ran {hours_since_last_run:.1f} hours ago (within {max_hours_since_last_run} hour limit)',
                'should_run': False,
                'last_update': last_update,
                'hours_since': hours_since_last_run
            }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error reading status file {latest_file}: {e}',
            'should_run': True
        }

def run_job(job_script, job_args=None):
    """
    Run a job script with the given arguments.
    
    Args:
        job_script: Path to the script to run
        job_args: List of arguments to pass to the script
    
    Returns:
        bool: True if job ran successfully, False otherwise
    """
    if job_args is None:
        job_args = []
    
    try:
        logger.info(f"Running job: {job_script} {' '.join(job_args)}")
        
        result = subprocess.run(
            [sys.executable, job_script] + job_args,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            logger.info(f"Job {job_script} completed successfully")
            if result.stdout:
                logger.info(f"Job output: {result.stdout}")
            return True
        else:
            logger.error(f"Job {job_script} failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Job error: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error running job {job_script}: {e}")
        return False

def check_and_run_missed_jobs():
    """Check for missed jobs and run them if needed."""
    logger.info("Starting missed jobs check")
    
    # Define jobs to check
    jobs_to_check = [
        {
            'name': 'Injury Data Update',
            'script': 'update_injury_data.py',
            'status_pattern': 'injury_status_*.txt',
            'max_hours': 25,  # Run daily, allow 1 hour buffer
            'args': ['--season', str(datetime.now().year)]
        },
        {
            'name': 'ELO Data Update',
            'script': 'automated_weekly_elo_updater.py',
            'status_pattern': 'elo_status_*.txt',
            'max_hours': 25,  # Run daily, allow 1 hour buffer
            'args': ['--season', str(datetime.now().year)]
        }
    ]
    
    jobs_run = 0
    jobs_failed = 0
    
    for job in jobs_to_check:
        logger.info(f"Checking {job['name']}...")
        
        status = check_job_status(
            job['name'],
            job['status_pattern'],
            job['max_hours']
        )
        
        logger.info(f"Status: {status['message']}")
        
        if status['should_run']:
            logger.info(f"Running missed job: {job['name']}")
            
            if run_job(job['script'], job['args']):
                jobs_run += 1
                logger.info(f"Successfully ran {job['name']}")
            else:
                jobs_failed += 1
                logger.error(f"Failed to run {job['name']}")
        else:
            logger.info(f"No action needed for {job['name']}")
    
    logger.info(f"Missed jobs check completed. Jobs run: {jobs_run}, Jobs failed: {jobs_failed}")
    return jobs_run, jobs_failed

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check for missed jobs and run them')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without running jobs')
    parser.add_argument('--check-only', action='store_true', help='Only check status, do not run jobs')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No jobs will be executed")
        # Just check status without running
        for job in [
            {'name': 'Injury Data Update', 'status_pattern': 'injury_status_*.txt', 'max_hours': 25},
            {'name': 'ELO Data Update', 'status_pattern': 'elo_status_*.txt', 'max_hours': 25}
        ]:
            status = check_job_status(job['name'], job['status_pattern'], job['max_hours'])
            logger.info(f"{job['name']}: {status['message']}")
        return
    
    if args.check_only:
        logger.info("CHECK ONLY MODE - Checking status without running jobs")
        check_and_run_missed_jobs()
        return
    
    # Run the full check and execute missed jobs
    jobs_run, jobs_failed = check_and_run_missed_jobs()
    
    if jobs_failed > 0:
        logger.error(f"Some jobs failed to run. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("All missed jobs handled successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
