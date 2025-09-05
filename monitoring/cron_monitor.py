#!/usr/bin/env python3
"""
Cron Job Monitor for SportsEdge Automated Data Collection
Monitors cron job execution, runtimes, and health status.
"""

import os
import sys
import json
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CronJobMonitor:
    """Monitor cron job execution and performance."""
    
    def __init__(self, project_root="/Users/tim/Code/Personal/SportsEdge"):
        self.project_root = Path(project_root)
        self.logs_dir = self.project_root / "artifacts" / "automated_collection"
        self.db_path = self.project_root / "artifacts" / "stats" / "nfl_elo_stats.db"
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cron_jobs(self):
        """Get current cron jobs."""
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            else:
                logger.error(f"Failed to get cron jobs: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"Error getting cron jobs: {e}")
            return []
    
    def get_recent_logs(self, hours=24):
        """Get recent log files from the last N hours."""
        if not self.logs_dir.exists():
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_logs = []
        
        for log_file in self.logs_dir.glob("*.log"):
            if log_file.stat().st_mtime > cutoff_time.timestamp():
                recent_logs.append(log_file)
        
        return sorted(recent_logs, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def parse_log_file(self, log_file):
        """Parse a log file to extract execution information."""
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Extract key information
            lines = content.split('\n')
            
            # Look for start/end times
            start_time = None
            end_time = None
            status = "unknown"
            errors = []
            
            for line in lines:
                if "Starting automated collection cycle" in line:
                    # Extract timestamp
                    try:
                        timestamp_str = line.split(' - ')[0]
                        start_time = datetime.fromisoformat(timestamp_str)
                    except:
                        pass
                
                elif "Collection cycle completed successfully" in line:
                    status = "success"
                    try:
                        timestamp_str = line.split(' - ')[0]
                        end_time = datetime.fromisoformat(timestamp_str)
                    except:
                        pass
                
                elif "ERROR" in line or "Error" in line:
                    errors.append(line.strip())
                    if status == "unknown":
                        status = "error"
            
            # Calculate runtime
            runtime = None
            if start_time and end_time:
                runtime = (end_time - start_time).total_seconds()
            elif start_time:
                runtime = (datetime.now() - start_time).total_seconds()
            
            return {
                'file': str(log_file),
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None,
                'runtime_seconds': runtime,
                'status': status,
                'errors': errors[:5],  # First 5 errors
                'file_size': log_file.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Error parsing log file {log_file}: {e}")
            return {
                'file': str(log_file),
                'error': str(e),
                'status': 'parse_error'
            }
    
    def get_database_status(self):
        """Get database status and recent activity."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table counts
            tables = ['action_network_experts', 'action_network_picks', 'action_network_games']
            table_counts = {}
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                except:
                    table_counts[table] = 0
            
            # Get latest activity
            latest_activity = None
            try:
                cursor.execute("""
                    SELECT MAX(created_at) FROM action_network_picks 
                    WHERE created_at IS NOT NULL
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    latest_activity = result[0]
            except:
                pass
            
            conn.close()
            
            return {
                'table_counts': table_counts,
                'latest_activity': latest_activity,
                'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting database status: {e}")
            return {'error': str(e)}
    
    def generate_status_report(self):
        """Generate a comprehensive status report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'cron_jobs': self.get_cron_jobs(),
            'recent_logs': [],
            'database_status': self.get_database_status(),
            'summary': {}
        }
        
        # Parse recent logs
        recent_logs = self.get_recent_logs(24)
        for log_file in recent_logs:
            log_info = self.parse_log_file(log_file)
            report['recent_logs'].append(log_info)
        
        # Generate summary
        successful_runs = len([log for log in report['recent_logs'] if log.get('status') == 'success'])
        failed_runs = len([log for log in report['recent_logs'] if log.get('status') == 'error'])
        total_runs = len(report['recent_logs'])
        
        avg_runtime = 0
        if report['recent_logs']:
            runtimes = [log.get('runtime_seconds', 0) for log in report['recent_logs'] if log.get('runtime_seconds')]
            if runtimes:
                avg_runtime = sum(runtimes) / len(runtimes)
        
        report['summary'] = {
            'total_runs_24h': total_runs,
            'successful_runs': successful_runs,
            'failed_runs': failed_runs,
            'success_rate': (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            'avg_runtime_seconds': avg_runtime,
            'last_run': report['recent_logs'][0]['start_time'] if report['recent_logs'] else None
        }
        
        return report
    
    def print_status_report(self):
        """Print a formatted status report."""
        report = self.generate_status_report()
        
        print("=" * 80)
        print("🏈 SPORTSEDGE CRON JOB MONITOR")
        print("=" * 80)
        print(f"📅 Report Generated: {report['timestamp']}")
        print()
        
        # Cron Jobs
        print("⏰ CRON JOBS:")
        for i, job in enumerate(report['cron_jobs'], 1):
            if job.strip():
                print(f"  {i}. {job}")
        print()
        
        # Summary
        summary = report['summary']
        print("📊 24-HOUR SUMMARY:")
        print(f"  • Total Runs: {summary['total_runs_24h']}")
        print(f"  • Successful: {summary['successful_runs']} ({summary['success_rate']:.1f}%)")
        print(f"  • Failed: {summary['failed_runs']}")
        print(f"  • Avg Runtime: {summary['avg_runtime_seconds']:.1f} seconds")
        print(f"  • Last Run: {summary['last_run'] or 'Never'}")
        print()
        
        # Database Status
        db_status = report['database_status']
        if 'error' not in db_status:
            print("🗄️ DATABASE STATUS:")
            print(f"  • Size: {db_status['database_size_mb']:.1f} MB")
            print(f"  • Latest Activity: {db_status['latest_activity'] or 'None'}")
            print("  • Table Counts:")
            for table, count in db_status['table_counts'].items():
                print(f"    - {table}: {count:,}")
            print()
        
        # Recent Runs
        print("📋 RECENT RUNS (Last 10):")
        for i, log in enumerate(report['recent_logs'][:10], 1):
            status_emoji = "✅" if log.get('status') == 'success' else "❌" if log.get('status') == 'error' else "⏳"
            runtime = f"{log.get('runtime_seconds', 0):.1f}s" if log.get('runtime_seconds') else "N/A"
            start_time = log.get('start_time', 'Unknown')
            
            print(f"  {i}. {status_emoji} {start_time} - {runtime}")
            
            if log.get('errors'):
                print(f"     Errors: {len(log['errors'])}")
                for error in log['errors'][:2]:  # Show first 2 errors
                    print(f"       • {error[:100]}...")
        print()
        
        # Health Assessment
        print("🏥 HEALTH ASSESSMENT:")
        if summary['success_rate'] >= 90:
            print("  ✅ EXCELLENT - Cron jobs running smoothly")
        elif summary['success_rate'] >= 70:
            print("  ⚠️  GOOD - Some issues detected")
        else:
            print("  ❌ POOR - Multiple failures detected")
        
        if summary['avg_runtime_seconds'] > 300:  # 5 minutes
            print("  ⚠️  WARNING - Average runtime is high")
        
        print("=" * 80)

def main():
    """Main function to run the cron monitor."""
    monitor = CronJobMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        # Output JSON for programmatic use
        report = monitor.generate_status_report()
        print(json.dumps(report, indent=2))
    else:
        # Output formatted report
        monitor.print_status_report()

if __name__ == "__main__":
    main()
