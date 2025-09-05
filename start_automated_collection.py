#!/usr/bin/env python3
"""Startup script for automated data collection system."""

import sys
import os
import signal
import time
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from automated_data_collector import AutomatedDataCollector
from monitoring.health_check import DataCollectionHealthCheck


class AutomatedCollectionManager:
    """Manager for automated data collection system."""
    
    def __init__(self, config_file: str = "configs/automated_collection.json"):
        """Initialize the collection manager."""
        self.collector = AutomatedDataCollector(config_file)
        self.health_check = DataCollectionHealthCheck()
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def run_health_check(self) -> bool:
        """Run health check before starting collection."""
        print("Running health check...")
        health = self.health_check.get_overall_health()
        
        print(f"Overall Status: {health['overall_status'].upper()}")
        
        if health['overall_status'] == 'critical':
            print("❌ Critical issues found. Please resolve before starting collection.")
            for issue in health['all_issues']:
                print(f"  - {issue}")
            return False
        elif health['overall_status'] == 'warning':
            print("⚠️  Warning issues found:")
            for issue in health['all_issues']:
                print(f"  - {issue}")
            print("Continuing with collection...")
        else:
            print("✅ System healthy. Starting collection...")
        
        return True
    
    def run_initial_collection(self) -> bool:
        """Run initial data collection."""
        print("\nRunning initial data collection...")
        
        try:
            results = self.collector.run_single_cycle()
            
            if results.get('overall_success', False):
                print("✅ Initial collection successful")
                return True
            else:
                print("❌ Initial collection failed")
                print("Action Network:", results.get('action_network', {}).get('success', False))
                print("NFL Stats:", results.get('nfl_stats', {}).get('success', False))
                return False
                
        except Exception as e:
            print(f"❌ Error in initial collection: {e}")
            return False
    
    def start_scheduler(self) -> None:
        """Start the automated scheduler."""
        print("\nStarting automated data collection scheduler...")
        print("Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                # Run scheduled tasks
                self.collector.run_collection_cycle()
                
                # Wait before next cycle
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\nScheduler stopped by user")
        except Exception as e:
            print(f"❌ Scheduler error: {e}")
        finally:
            self.running = False
            print("Scheduler stopped")
    
    def run_single_cycle(self) -> None:
        """Run a single collection cycle."""
        print("Running single collection cycle...")
        
        try:
            results = self.collector.run_single_cycle()
            
            if results.get('overall_success', False):
                print("✅ Collection cycle successful")
            else:
                print("❌ Collection cycle failed")
                print("Action Network:", results.get('action_network', {}).get('success', False))
                print("NFL Stats:", results.get('nfl_stats', {}).get('success', False))
            
            # Print summary
            an_data = results.get('action_network', {})
            nfl_data = results.get('nfl_stats', {})
            
            print(f"\nAction Network: {an_data.get('experts_processed', 0)} experts, {an_data.get('picks_processed', 0)} picks")
            print(f"NFL Stats: {nfl_data.get('collections', {}).get('games', {}).get('count', 0)} games")
            
        except Exception as e:
            print(f"❌ Error in collection cycle: {e}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Data Collection Manager')
    parser.add_argument('--mode', choices=['single', 'scheduler', 'health'], 
                       default='scheduler', help='Run mode')
    parser.add_argument('--config', default='configs/automated_collection.json',
                       help='Configuration file path')
    parser.add_argument('--skip-health-check', action='store_true',
                       help='Skip health check before starting')
    parser.add_argument('--skip-initial-collection', action='store_true',
                       help='Skip initial collection when starting scheduler')
    
    args = parser.parse_args()
    
    # Create artifacts directory
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/automated_collection").mkdir(exist_ok=True)
    
    # Initialize manager
    manager = AutomatedCollectionManager(args.config)
    
    if args.mode == 'health':
        # Just run health check
        health = manager.health_check.get_overall_health()
        print(manager.health_check.generate_health_report())
        return
    
    # Run health check unless skipped
    if not args.skip_health_check:
        if not manager.run_health_check():
            print("Exiting due to health check failures")
            return
    
    if args.mode == 'single':
        # Run single collection cycle
        manager.run_single_cycle()
        
    elif args.mode == 'scheduler':
        # Run initial collection unless skipped
        if not args.skip_initial_collection:
            if not manager.run_initial_collection():
                print("Initial collection failed. Starting scheduler anyway...")
        
        # Start scheduler
        manager.start_scheduler()


if __name__ == "__main__":
    main()
