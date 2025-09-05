"""Automated data collection system for Action Network and NFL stats."""

import schedule
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sqlite3
import pandas as pd

from ingest.action_network.data_collector import ActionNetworkCollector
from ingest.action_network.analysis_tools import ActionNetworkAnalyzer
from ingest.nfl.data_loader import load_games, load_team_reference
from ingest.nfl.epa_data_loader import load_epa_data
from ingest.nfl.ngs_calculator import NGSCalculator
from ingest.nfl.weather_loader import load_weather_for_games
from ingest.nfl.enhanced_epa_loader import load_travel_data_for_games
from ingest.nfl.qb_data_loader import load_qb_performance
from ingest.nfl.turnover_calculator import TurnoverCalculator
from ingest.nfl.redzone_data_loader import add_redzone_data_to_games
from ingest.nfl.downs_data_loader import add_downs_data_to_games
from models.nfl_elo.action_network_storage import ActionNetworkStorage


class AutomatedDataCollector:
    """Automated data collection system for both Action Network and NFL stats."""
    
    def __init__(self, config_file: str = "configs/automated_collection.json"):
        """
        Initialize automated data collector.
        
        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.setup_logging()
        
        # Initialize collectors
        self.action_network_collector = ActionNetworkCollector()
        self.action_network_storage = ActionNetworkStorage()
        self.ngs_calculator = NGSCalculator()
        self.turnover_calculator = TurnoverCalculator()
        
        # Create artifacts directory
        Path("artifacts").mkdir(exist_ok=True)
        Path("artifacts/automated_collection").mkdir(exist_ok=True)
        
        self.logger.info("Automated data collector initialized")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file."""
        default_config = {
            "action_network": {
                "enabled": True,
                "expert_picks_interval_minutes": 15,
                "all_picks_interval_minutes": 5,
                "max_retries": 3,
                "retry_delay_seconds": 30
            },
            "nfl_stats": {
                "enabled": True,
                "collection_interval_hours": 6,
                "years": [2025],
                "include_weather": True,
                "include_travel": True,
                "include_ngs": True,
                "include_epa": True,
                "include_qb_stats": True,
                "include_turnover_stats": True,
                "include_redzone_stats": True,
                "include_downs_stats": True
            },
            "database": {
                "path": "artifacts/stats/nfl_elo_stats.db",
                "backup_enabled": True,
                "backup_interval_hours": 24
            },
            "logging": {
                "level": "INFO",
                "file": "artifacts/automated_collection/collection.log",
                "max_size_mb": 100,
                "backup_count": 5
            }
        }
        
        if Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    for key, value in user_config.items():
                        if key in default_config and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                print(f"Error loading config file {config_file}: {e}")
                print("Using default configuration")
        
        return default_config
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config['logging']
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Setup file handler
        file_handler = logging.FileHandler(log_config['file'])
        file_handler.setFormatter(formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Setup logger
        self.logger = logging.getLogger('AutomatedDataCollector')
        self.logger.setLevel(getattr(logging, log_config['level']))
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def collect_action_network_data(self) -> Dict[str, Any]:
        """Collect Action Network data."""
        if not self.config['action_network']['enabled']:
            return {'skipped': True, 'reason': 'Action Network collection disabled'}
        
        self.logger.info("Starting Action Network data collection...")
        
        try:
            # Collect expert picks
            expert_results = self.action_network_collector.collect_expert_picks()
            
            # Collect all picks
            all_picks_results = self.action_network_collector.collect_all_picks()
            
            # Collect for yesterday as well to catch any missed data
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            yesterday_results = self.action_network_collector.collect_all_picks(yesterday)
            
            results = {
                'expert_picks': expert_results,
                'all_picks': all_picks_results,
                'yesterday_picks': yesterday_results,
                'timestamp': datetime.now().isoformat(),
                'success': all([
                    expert_results.get('success', False),
                    all_picks_results.get('success', False)
                ])
            }
            
            # Log results
            if results['success']:
                self.logger.info(f"Action Network collection successful: "
                               f"{expert_results.get('experts_processed', 0)} experts, "
                               f"{expert_results.get('picks_processed', 0)} picks")
            else:
                self.logger.warning("Action Network collection had errors")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in Action Network collection: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def collect_nfl_stats_data(self) -> Dict[str, Any]:
        """Collect comprehensive NFL stats data for 2025 season."""
        if not self.config['nfl_stats']['enabled']:
            return {'skipped': True, 'reason': 'NFL stats collection disabled'}
        
        self.logger.info("Starting NFL stats data collection...")
        
        try:
            years = self.config['nfl_stats']['years']
            results = {
                'timestamp': datetime.now().isoformat(),
                'years': years,
                'collections': {}
            }
            
            # Load basic game data
            self.logger.info("Loading NFL game schedules...")
            games_df = load_games(years)
            results['collections']['games'] = {
                'count': len(games_df),
                'success': True
            }
            
            # Load team reference data
            self.logger.info("Loading team reference data...")
            teams_df = load_team_reference()
            results['collections']['teams'] = {
                'count': len(teams_df),
                'success': True
            }
            
            # Load EPA data if enabled
            if self.config['nfl_stats']['include_epa']:
                self.logger.info("Loading EPA data...")
                try:
                    epa_df = load_epa_data(years)
                    results['collections']['epa'] = {
                        'count': len(epa_df),
                        'success': True
                    }
                except Exception as e:
                    self.logger.warning(f"Error loading EPA data: {e}")
                    results['collections']['epa'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Load NGS data if enabled
            if self.config['nfl_stats']['include_ngs']:
                self.logger.info("Loading NGS data...")
                try:
                    ngs_data = self.ngs_calculator.load_ngs_data(years)
                    results['collections']['ngs'] = {
                        'types': list(ngs_data.keys()),
                        'counts': {k: len(v) for k, v in ngs_data.items()},
                        'success': True
                    }
                except Exception as e:
                    self.logger.warning(f"Error loading NGS data: {e}")
                    results['collections']['ngs'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Load weather data if enabled
            if self.config['nfl_stats']['include_weather']:
                self.logger.info("Loading weather data...")
                try:
                    weather_df = load_weather_for_games(games_df)
                    results['collections']['weather'] = {
                        'count': len(weather_df),
                        'success': True
                    }
                except Exception as e:
                    self.logger.warning(f"Error loading weather data: {e}")
                    results['collections']['weather'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Load travel data if enabled
            if self.config['nfl_stats']['include_travel']:
                self.logger.info("Loading travel data...")
                try:
                    travel_df = load_travel_data_for_games(games_df)
                    results['collections']['travel'] = {
                        'count': len(travel_df),
                        'success': True
                    }
                except Exception as e:
                    self.logger.warning(f"Error loading travel data: {e}")
                    results['collections']['travel'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Load QB performance data if enabled
            if self.config['nfl_stats']['include_qb_stats']:
                self.logger.info("Loading QB performance data...")
                try:
                    qb_df = load_qb_performance(years)
                    results['collections']['qb_performance'] = {
                        'count': len(qb_df),
                        'success': True
                    }
                except Exception as e:
                    self.logger.warning(f"Error loading QB performance data: {e}")
                    results['collections']['qb_performance'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Load turnover data if enabled
            if self.config['nfl_stats']['include_turnover_stats']:
                self.logger.info("Loading turnover data...")
                try:
                    turnover_data = self.turnover_calculator.load_turnover_data(years)
                    results['collections']['turnover'] = {
                        'count': len(turnover_data),
                        'success': True
                    }
                except Exception as e:
                    # Check if it's a future year issue
                    if "2025" in str(e) or any(str(year) in str(e) for year in years if year > 2024):
                        self.logger.info(f"Turnover data not available for future years - this is expected: {e}")
                    else:
                        self.logger.warning(f"Error loading turnover data: {e}")
                    results['collections']['turnover'] = {
                        'success': False,
                        'error': str(e),
                        'note': 'Future year data not available yet' if "2025" in str(e) else 'Data loading error'
                    }
            
            # Load redzone data if enabled
            if self.config['nfl_stats']['include_redzone_stats']:
                self.logger.info("Loading redzone data...")
                try:
                    games_with_redzone = add_redzone_data_to_games(games_df, years)
                    results['collections']['redzone'] = {
                        'count': len(games_with_redzone),
                        'success': True
                    }
                except Exception as e:
                    # Check if it's a future year issue
                    if "2025" in str(e) or any(str(year) in str(e) for year in years if year > 2024):
                        self.logger.info(f"Redzone data not available for future years - this is expected: {e}")
                    else:
                        self.logger.warning(f"Error loading redzone data: {e}")
                    results['collections']['redzone'] = {
                        'success': False,
                        'error': str(e),
                        'note': 'Future year data not available yet' if "2025" in str(e) else 'Data loading error'
                    }
            
            # Load downs data if enabled
            if self.config['nfl_stats']['include_downs_stats']:
                self.logger.info("Loading downs data...")
                try:
                    games_with_downs = add_downs_data_to_games(games_df, years)
                    results['collections']['downs'] = {
                        'count': len(games_with_downs),
                        'success': True
                    }
                except Exception as e:
                    # Check if it's a future year issue
                    if "2025" in str(e) or any(str(year) in str(e) for year in years if year > 2024):
                        self.logger.info(f"Downs data not available for future years - this is expected: {e}")
                    else:
                        self.logger.warning(f"Error loading downs data: {e}")
                    results['collections']['downs'] = {
                        'success': False,
                        'error': str(e),
                        'note': 'Future year data not available yet' if "2025" in str(e) else 'Data loading error'
                    }
            
            # Store data in database
            self._store_nfl_data_in_database(games_df, teams_df, results)
            
            # Calculate overall success
            successful_collections = sum(1 for col in results['collections'].values() 
                                       if col.get('success', False))
            total_collections = len(results['collections'])
            results['success'] = successful_collections >= (total_collections * 0.8)  # 80% success rate
            
            self.logger.info(f"NFL stats collection completed: {successful_collections}/{total_collections} successful")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in NFL stats collection: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _store_nfl_data_in_database(self, games_df: pd.DataFrame, teams_df: pd.DataFrame, 
                                   results: Dict[str, Any]) -> None:
        """Store NFL data in the database."""
        try:
            conn = sqlite3.connect(self.config['database']['path'])
            
            # Store games data
            games_df.to_sql('nfl_games_2025', conn, if_exists='replace', index=False)
            
            # Store teams data
            teams_df.to_sql('nfl_teams_2025', conn, if_exists='replace', index=False)
            
            # Store collection results
            results_df = pd.DataFrame([{
                'timestamp': results['timestamp'],
                'years': str(results['years']),
                'collections': json.dumps(results['collections']),
                'success': results.get('success', False)
            }])
            results_df.to_sql('nfl_collection_log', conn, if_exists='append', index=False)
            
            conn.commit()
            conn.close()
            
            self.logger.info("NFL data stored in database successfully")
            
        except Exception as e:
            self.logger.error(f"Error storing NFL data in database: {e}")
    
    def run_collection_cycle(self) -> Dict[str, Any]:
        """Run a complete collection cycle."""
        self.logger.info("Starting automated collection cycle...")
        
        cycle_results = {
            'timestamp': datetime.now().isoformat(),
            'action_network': {},
            'nfl_stats': {},
            'overall_success': False
        }
        
        try:
            # Collect Action Network data
            cycle_results['action_network'] = self.collect_action_network_data()
            
            # Collect NFL stats data
            cycle_results['nfl_stats'] = self.collect_nfl_stats_data()
            
            # Determine overall success
            an_success = cycle_results['action_network'].get('success', False)
            nfl_success = cycle_results['nfl_stats'].get('success', False)
            cycle_results['overall_success'] = an_success and nfl_success
            
            # Save cycle results
            self._save_cycle_results(cycle_results)
            
            if cycle_results['overall_success']:
                self.logger.info("Collection cycle completed successfully")
            else:
                self.logger.warning("Collection cycle completed with errors")
            
            return cycle_results
            
        except Exception as e:
            self.logger.error(f"Error in collection cycle: {e}")
            cycle_results['error'] = str(e)
            return cycle_results
    
    def _save_cycle_results(self, results: Dict[str, Any]) -> None:
        """Save collection cycle results."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"artifacts/automated_collection/cycle_results_{timestamp}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.logger.info(f"Cycle results saved to {results_file}")
        except Exception as e:
            self.logger.error(f"Error saving cycle results: {e}")
    
    def setup_scheduling(self) -> None:
        """Setup automated scheduling."""
        an_config = self.config['action_network']
        nfl_config = self.config['nfl_stats']
        
        # Schedule Action Network collections
        if an_config['enabled']:
            # Expert picks every 15 minutes
            schedule.every(an_config['expert_picks_interval_minutes']).minutes.do(
                self.collect_action_network_data
            )
            
            # All picks every 5 minutes
            schedule.every(an_config['all_picks_interval_minutes']).minutes.do(
                self.collect_action_network_data
            )
        
        # Schedule NFL stats collection
        if nfl_config['enabled']:
            schedule.every(nfl_config['collection_interval_hours']).hours.do(
                self.collect_nfl_stats_data
            )
        
        # Schedule full collection cycle daily
        schedule.every().day.at("02:00").do(self.run_collection_cycle)
        
        self.logger.info("Scheduling setup completed")
    
    def run_scheduler(self) -> None:
        """Run the scheduler continuously."""
        self.logger.info("Starting automated data collection scheduler...")
        self.setup_scheduling()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
    
    def run_single_cycle(self) -> Dict[str, Any]:
        """Run a single collection cycle and return results."""
        return self.run_collection_cycle()


def main():
    """Main function for running the automated collector."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Data Collector')
    parser.add_argument('--mode', choices=['single', 'scheduler'], default='single',
                       help='Run mode: single cycle or continuous scheduler')
    parser.add_argument('--config', default='configs/automated_collection.json',
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    collector = AutomatedDataCollector(args.config)
    
    if args.mode == 'single':
        results = collector.run_single_cycle()
        print(json.dumps(results, indent=2, default=str))
    else:
        collector.run_scheduler()


if __name__ == "__main__":
    main()
