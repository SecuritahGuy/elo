"""Health check and monitoring system for automated data collection."""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging


class DataCollectionHealthCheck:
    """Health check system for automated data collection."""
    
    def __init__(self, db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        """
        Initialize health check system.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
    
    def check_action_network_health(self) -> Dict[str, Any]:
        """Check Action Network data collection health."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check expert data
            cursor.execute('SELECT COUNT(*) FROM action_network_experts')
            expert_count = cursor.fetchone()[0]
            
            # Check picks data
            cursor.execute('SELECT COUNT(*) FROM action_network_picks')
            picks_count = cursor.fetchone()[0]
            
            # Check recent picks (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM action_network_picks 
                WHERE DATE(created_at) >= ?
            ''', (yesterday,))
            recent_picks = cursor.fetchone()[0]
            
            # Check NFL picks specifically
            cursor.execute('''
                SELECT COUNT(*) FROM action_network_picks 
                WHERE league_name = 'nfl'
            ''')
            nfl_picks = cursor.fetchone()[0]
            
            # Check data freshness
            cursor.execute('''
                SELECT MAX(created_at) FROM action_network_picks
            ''')
            latest_pick = cursor.fetchone()[0]
            
            conn.close()
            
            # Determine health status
            health_status = "healthy"
            issues = []
            
            if expert_count == 0:
                health_status = "critical"
                issues.append("No expert data found")
            elif expert_count < 50:
                health_status = "warning"
                issues.append(f"Low expert count: {expert_count}")
            
            if picks_count == 0:
                health_status = "critical"
                issues.append("No picks data found")
            elif recent_picks == 0:
                health_status = "warning"
                issues.append("No recent picks in last 24 hours")
            
            if nfl_picks == 0:
                health_status = "warning"
                issues.append("No NFL picks found")
            
            return {
                'status': health_status,
                'expert_count': expert_count,
                'picks_count': picks_count,
                'recent_picks': recent_picks,
                'nfl_picks': nfl_picks,
                'latest_pick': latest_pick,
                'issues': issues,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_nfl_stats_health(self) -> Dict[str, Any]:
        """Check NFL stats data collection health."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if NFL tables exist
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'nfl_%'
            ''')
            nfl_tables = [row[0] for row in cursor.fetchall()]
            
            # Check games data
            games_count = 0
            if 'nfl_games_2025' in nfl_tables:
                cursor.execute('SELECT COUNT(*) FROM nfl_games_2025')
                games_count = cursor.fetchone()[0]
            
            # Check teams data
            teams_count = 0
            if 'nfl_teams_2025' in nfl_tables:
                cursor.execute('SELECT COUNT(*) FROM nfl_teams_2025')
                teams_count = cursor.fetchone()[0]
            
            # Check collection log
            cursor.execute('''
                SELECT COUNT(*), MAX(timestamp) FROM nfl_collection_log
            ''')
            log_count, latest_collection = cursor.fetchone()
            
            conn.close()
            
            # Determine health status
            health_status = "healthy"
            issues = []
            
            if not nfl_tables:
                health_status = "critical"
                issues.append("No NFL tables found")
            elif games_count == 0:
                health_status = "warning"
                issues.append("No games data found")
            
            if teams_count == 0:
                health_status = "warning"
                issues.append("No teams data found")
            
            if log_count == 0:
                health_status = "warning"
                issues.append("No collection logs found")
            
            return {
                'status': health_status,
                'nfl_tables': nfl_tables,
                'games_count': games_count,
                'teams_count': teams_count,
                'log_count': log_count,
                'latest_collection': latest_collection,
                'issues': issues,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health and performance."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check database size
            db_size = Path(self.db_path).stat().st_size / (1024 * 1024)  # MB
            
            # Check table counts
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ''')
            tables = [row[0] for row in cursor.fetchall()]
            
            table_counts = {}
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                table_counts[table] = cursor.fetchone()[0]
            
            # Check for recent activity
            cursor.execute('''
                SELECT MAX(created_at) FROM action_network_picks
                WHERE created_at IS NOT NULL
            ''')
            latest_activity = cursor.fetchone()[0]
            
            conn.close()
            
            # Determine health status
            health_status = "healthy"
            issues = []
            
            if db_size > 1000:  # > 1GB
                health_status = "warning"
                issues.append(f"Large database size: {db_size:.1f}MB")
            
            if not latest_activity:
                health_status = "warning"
                issues.append("No recent activity found")
            else:
                try:
                    # Handle different timestamp formats
                    if 'Z' in str(latest_activity):
                        latest_dt = datetime.fromisoformat(str(latest_activity).replace('Z', '+00:00'))
                    else:
                        latest_dt = datetime.fromisoformat(str(latest_activity))
                    
                    # Make both datetimes timezone-aware for comparison
                    from datetime import timezone
                    if latest_dt.tzinfo is None:
                        latest_dt = latest_dt.replace(tzinfo=timezone.utc)
                    
                    now_utc = datetime.now(timezone.utc)
                    if (now_utc - latest_dt).days > 1:
                        health_status = "warning"
                        issues.append("Stale data - no activity in last 24 hours")
                except Exception as e:
                    health_status = "warning"
                    issues.append(f"Error parsing latest activity timestamp: {e}")
            
            return {
                'status': health_status,
                'db_size_mb': db_size,
                'table_count': len(tables),
                'table_counts': table_counts,
                'latest_activity': latest_activity,
                'issues': issues,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        an_health = self.check_action_network_health()
        nfl_health = self.check_nfl_stats_health()
        db_health = self.check_database_health()
        
        # Determine overall status
        statuses = [an_health['status'], nfl_health['status'], db_health['status']]
        
        if 'critical' in statuses or 'error' in statuses:
            overall_status = 'critical'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        # Collect all issues
        all_issues = []
        for health in [an_health, nfl_health, db_health]:
            if 'issues' in health:
                all_issues.extend(health['issues'])
        
        return {
            'overall_status': overall_status,
            'action_network': an_health,
            'nfl_stats': nfl_health,
            'database': db_health,
            'all_issues': all_issues,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_health_report(self) -> str:
        """Generate a human-readable health report."""
        health = self.get_overall_health()
        
        report = f"""
Data Collection Health Report
============================
Generated: {health['timestamp']}
Overall Status: {health['overall_status'].upper()}

Action Network Data:
  Status: {health['action_network']['status']}
  Experts: {health['action_network'].get('expert_count', 'N/A')}
  Total Picks: {health['action_network'].get('picks_count', 'N/A')}
  Recent Picks (24h): {health['action_network'].get('recent_picks', 'N/A')}
  NFL Picks: {health['action_network'].get('nfl_picks', 'N/A')}

NFL Stats Data:
  Status: {health['nfl_stats']['status']}
  Games: {health['nfl_stats'].get('games_count', 'N/A')}
  Teams: {health['nfl_stats'].get('teams_count', 'N/A')}
  Collection Logs: {health['nfl_stats'].get('log_count', 'N/A')}

Database:
  Status: {health['database']['status']}
  Size: {health['database'].get('db_size_mb', 0):.1f} MB
  Tables: {health['database'].get('table_count', 'N/A')}

Issues:
"""
        
        if health['all_issues']:
            for issue in health['all_issues']:
                report += f"  - {issue}\n"
        else:
            report += "  None\n"
        
        return report
    
    def save_health_report(self, output_file: str = None) -> str:
        """Save health report to file."""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"artifacts/automated_collection/health_report_{timestamp}.txt"
        
        report = self.generate_health_report()
        
        with open(output_file, 'w') as f:
            f.write(report)
        
        return output_file


def main():
    """Main function for running health check."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Data Collection Health Check')
    parser.add_argument('--output', help='Output file for health report')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    
    args = parser.parse_args()
    
    health_check = DataCollectionHealthCheck()
    
    if args.json:
        health = health_check.get_overall_health()
        print(json.dumps(health, indent=2, default=str))
    else:
        report = health_check.generate_health_report()
        print(report)
        
        if args.output:
            health_check.save_health_report(args.output)
            print(f"\nHealth report saved to: {args.output}")


if __name__ == "__main__":
    main()
