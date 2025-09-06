#!/usr/bin/env python3
"""
Database Optimization Script
Implements comprehensive database optimizations with testing.
"""

import sqlite3
import time
import json
import os
from typing import Dict, List, Any, Tuple
from contextlib import contextmanager
import statistics

class DatabaseOptimizer:
    def __init__(self, db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        self.db_path = db_path
        self.optimization_results = {}
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def analyze_current_performance(self) -> Dict[str, Any]:
        """Analyze current database performance with correct schema."""
        print("🔍 ANALYZING CURRENT DATABASE PERFORMANCE")
        print("=" * 50)
        
        queries = {
            "elo_ratings_current": """
                SELECT team, rating, wins, losses, rating_change 
                FROM team_ratings 
                WHERE season = 2025 AND config_name = 'comprehensive'
                ORDER BY rating DESC
            """,
            "elo_ratings_historical": """
                SELECT team, rating, wins, losses, rating_change, season
                FROM team_ratings 
                WHERE season IN (2022, 2023, 2024) AND config_name = 'comprehensive'
                ORDER BY season DESC, rating DESC
            """,
            "team_comparison": """
                SELECT t1.team, t1.rating, t1.wins, t1.losses, t1.rating_change,
                       t2.team, t2.rating, t2.wins, t2.losses, t2.rating_change
                FROM team_ratings t1
                JOIN team_ratings t2 ON t1.season = t2.season AND t1.config_name = t2.config_name
                WHERE t1.season = 2025 AND t1.config_name = 'comprehensive'
                AND t1.team IN ('PHI', 'DAL') AND t2.team IN ('PHI', 'DAL')
            """,
            "action_network_picks": """
                SELECT expert, pick, confidence, game_date
                FROM action_network_picks 
                WHERE game_date >= date('now', '-7 days')
                ORDER BY game_date DESC, confidence DESC
            """,
            "backtest_results": """
                SELECT season, accuracy, log_loss, brier_score
                FROM backtest_results 
                ORDER BY season DESC
            """,
            "nfl_games_2025": """
                SELECT home_team, away_team, home_score, away_score, week
                FROM nfl_games_2025 
                WHERE week <= 1
                ORDER BY week DESC
            """
        }
        
        results = {}
        
        with self.get_connection() as conn:
            for query_name, query in queries.items():
                print(f"\n📊 Testing: {query_name}")
                
                # Run query multiple times for accurate timing
                times = []
                for i in range(10):
                    start_time = time.time()
                    try:
                        cursor = conn.execute(query)
                        rows = cursor.fetchall()
                        end_time = time.time()
                        times.append(end_time - start_time)
                    except Exception as e:
                        print(f"   ❌ Query failed: {e}")
                        times.append(float('inf'))
                
                if times and all(t != float('inf') for t in times):
                    avg_time = statistics.mean(times)
                    min_time = min(times)
                    max_time = max(times)
                    row_count = len(rows) if 'rows' in locals() else 0
                    
                    results[query_name] = {
                        'avg_time_ms': round(avg_time * 1000, 2),
                        'min_time_ms': round(min_time * 1000, 2),
                        'max_time_ms': round(max_time * 1000, 2),
                        'row_count': row_count,
                        'status': 'success'
                    }
                    
                    print(f"   ✅ Avg: {avg_time*1000:.2f}ms, Min: {min_time*1000:.2f}ms, Max: {max_time*1000:.2f}ms, Rows: {row_count}")
                else:
                    results[query_name] = {
                        'status': 'failed',
                        'error': 'Query execution failed'
                    }
                    print(f"   ❌ Query failed")
        
        return results
    
    def create_optimization_indexes(self) -> Dict[str, Any]:
        """Create additional indexes for better performance."""
        print(f"\n🏗️ CREATING OPTIMIZATION INDEXES")
        print("=" * 50)
        
        indexes = [
            # Team ratings optimizations
            ("idx_team_ratings_rating_desc", "team_ratings", "(rating DESC)"),
            ("idx_team_ratings_team_rating", "team_ratings", "(team, rating DESC)"),
            ("idx_team_ratings_season_rating", "team_ratings", "(season, rating DESC)"),
            
            # Action Network optimizations
            ("idx_action_network_picks_date", "action_network_picks", "(game_date DESC)"),
            ("idx_action_network_picks_expert", "action_network_picks", "(expert)"),
            ("idx_action_network_picks_confidence", "action_network_picks", "(confidence DESC)"),
            
            # Games optimizations
            ("idx_nfl_games_2025_week", "nfl_games_2025", "(week)"),
            ("idx_nfl_games_2025_teams", "nfl_games_2025", "(home_team, away_team)"),
            
            # Backtest optimizations
            ("idx_backtest_results_season", "backtest_results", "(season DESC)"),
            ("idx_backtest_results_accuracy", "backtest_results", "(accuracy DESC)"),
        ]
        
        results = {}
        
        with self.get_connection() as conn:
            for index_name, table_name, columns in indexes:
                print(f"📊 Creating index: {index_name}")
                
                try:
                    # Check if index already exists
                    check_query = f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'"
                    existing = conn.execute(check_query).fetchone()
                    
                    if existing:
                        print(f"   ⚠️  Index already exists: {index_name}")
                        results[index_name] = {'status': 'exists', 'table': table_name}
                    else:
                        # Create index
                        create_query = f"CREATE INDEX {index_name} ON {table_name} {columns}"
                        start_time = time.time()
                        conn.execute(create_query)
                        end_time = time.time()
                        
                        creation_time = (end_time - start_time) * 1000
                        print(f"   ✅ Created in {creation_time:.2f}ms")
                        results[index_name] = {
                            'status': 'created',
                            'table': table_name,
                            'creation_time_ms': round(creation_time, 2)
                        }
                        
                except Exception as e:
                    print(f"   ❌ Failed to create index: {e}")
                    results[index_name] = {
                        'status': 'failed',
                        'table': table_name,
                        'error': str(e)
                    }
            
            # Commit all changes
            conn.commit()
        
        return results
    
    def optimize_database_settings(self) -> Dict[str, Any]:
        """Apply database optimization settings."""
        print(f"\n⚙️ APPLYING DATABASE OPTIMIZATIONS")
        print("=" * 50)
        
        optimizations = [
            ("journal_mode", "WAL", "Write-Ahead Logging for better concurrency"),
            ("cache_size", "-10000", "10MB cache size"),
            ("temp_store", "MEMORY", "Store temporary tables in memory"),
            ("synchronous", "NORMAL", "Balanced safety and performance"),
            ("mmap_size", "268435456", "256MB memory-mapped I/O"),
            ("page_size", "4096", "4KB page size"),
            ("auto_vacuum", "INCREMENTAL", "Incremental vacuum for maintenance")
        ]
        
        results = {}
        
        with self.get_connection() as conn:
            for setting, value, description in optimizations:
                print(f"🔧 Setting {setting} = {value}")
                
                try:
                    # Get current value
                    current_query = f"PRAGMA {setting}"
                    current_result = conn.execute(current_query).fetchone()
                    current_value = current_result[0] if current_result else "Unknown"
                    
                    # Set new value
                    set_query = f"PRAGMA {setting} = {value}"
                    conn.execute(set_query)
                    
                    # Verify new value
                    verify_result = conn.execute(current_query).fetchone()
                    new_value = verify_result[0] if verify_result else "Unknown"
                    
                    print(f"   ✅ {setting}: {current_value} → {new_value}")
                    results[setting] = {
                        'status': 'success',
                        'old_value': current_value,
                        'new_value': new_value,
                        'description': description
                    }
                    
                except Exception as e:
                    print(f"   ❌ Failed to set {setting}: {e}")
                    results[setting] = {
                        'status': 'failed',
                        'error': str(e),
                        'description': description
                    }
        
        return results
    
    def run_query_optimization_tests(self) -> Dict[str, Any]:
        """Run tests to verify optimization improvements."""
        print(f"\n🧪 RUNNING OPTIMIZATION TESTS")
        print("=" * 50)
        
        # Test queries that should benefit from new indexes
        test_queries = {
            "team_ratings_by_rating": """
                SELECT team, rating FROM team_ratings 
                WHERE season = 2025 AND config_name = 'comprehensive'
                ORDER BY rating DESC LIMIT 10
            """,
            "recent_picks": """
                SELECT expert, pick, confidence FROM action_network_picks 
                ORDER BY game_date DESC LIMIT 20
            """,
            "games_by_week": """
                SELECT home_team, away_team, week FROM nfl_games_2025 
                WHERE week = 1 ORDER BY home_team
            """,
            "backtest_accuracy": """
                SELECT season, accuracy FROM backtest_results 
                ORDER BY accuracy DESC LIMIT 5
            """
        }
        
        results = {}
        
        with self.get_connection() as conn:
            for query_name, query in test_queries.items():
                print(f"🧪 Testing: {query_name}")
                
                # Run query multiple times
                times = []
                for i in range(20):  # More iterations for better accuracy
                    start_time = time.time()
                    try:
                        cursor = conn.execute(query)
                        rows = cursor.fetchall()
                        end_time = time.time()
                        times.append(end_time - start_time)
                    except Exception as e:
                        print(f"   ❌ Query failed: {e}")
                        times.append(float('inf'))
                
                if times and all(t != float('inf') for t in times):
                    avg_time = statistics.mean(times)
                    min_time = min(times)
                    max_time = max(times)
                    std_dev = statistics.stdev(times) if len(times) > 1 else 0
                    row_count = len(rows) if 'rows' in locals() else 0
                    
                    results[query_name] = {
                        'avg_time_ms': round(avg_time * 1000, 2),
                        'min_time_ms': round(min_time * 1000, 2),
                        'max_time_ms': round(max_time * 1000, 2),
                        'std_dev_ms': round(std_dev * 1000, 2),
                        'row_count': row_count,
                        'status': 'success'
                    }
                    
                    print(f"   ✅ Avg: {avg_time*1000:.2f}ms (±{std_dev*1000:.2f}ms), Rows: {row_count}")
                else:
                    results[query_name] = {
                        'status': 'failed',
                        'error': 'Query execution failed'
                    }
                    print(f"   ❌ Query failed")
        
        return results
    
    def generate_performance_report(self, before_results: Dict, after_results: Dict, index_results: Dict, settings_results: Dict) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        print(f"\n📊 GENERATING PERFORMANCE REPORT")
        print("=" * 50)
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'optimization_summary': {
                'indexes_created': len([r for r in index_results.values() if r.get('status') == 'created']),
                'indexes_existing': len([r for r in index_results.values() if r.get('status') == 'exists']),
                'indexes_failed': len([r for r in index_results.values() if r.get('status') == 'failed']),
                'settings_applied': len([r for r in settings_results.values() if r.get('status') == 'success']),
                'settings_failed': len([r for r in settings_results.values() if r.get('status') == 'failed'])
            },
            'performance_comparison': {},
            'recommendations': []
        }
        
        # Compare performance before and after
        for query_name in before_results:
            if query_name in after_results:
                before_time = before_results[query_name].get('avg_time_ms', 0)
                after_time = after_results[query_name].get('avg_time_ms', 0)
                
                if before_time > 0 and after_time > 0:
                    improvement = ((before_time - after_time) / before_time) * 100
                    report['performance_comparison'][query_name] = {
                        'before_ms': before_time,
                        'after_ms': after_time,
                        'improvement_pct': round(improvement, 2),
                        'faster': improvement > 0
                    }
        
        # Generate recommendations
        slow_queries = [name for name, data in after_results.items() 
                       if data.get('avg_time_ms', 0) > 50]  # >50ms threshold
        
        if slow_queries:
            report['recommendations'].append({
                'type': 'query_optimization',
                'priority': 'high',
                'description': f'Found {len(slow_queries)} queries still >50ms',
                'queries': slow_queries,
                'action': 'Consider query restructuring or additional indexes'
            })
        
        # Check for successful optimizations
        successful_improvements = [name for name, data in report['performance_comparison'].items() 
                                 if data.get('faster', False)]
        
        if successful_improvements:
            report['recommendations'].append({
                'type': 'success',
                'priority': 'info',
                'description': f'Successfully optimized {len(successful_improvements)} queries',
                'queries': successful_improvements,
                'action': 'Continue monitoring performance'
            })
        
        return report
    
    def run_full_optimization(self) -> Dict[str, Any]:
        """Run complete database optimization process."""
        print("🚀 STARTING DATABASE OPTIMIZATION")
        print("=" * 60)
        
        # Check if database exists
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return {'error': 'Database not found'}
        
        # Step 1: Analyze current performance
        print("\n📊 STEP 1: ANALYZING CURRENT PERFORMANCE")
        before_results = self.analyze_current_performance()
        
        # Step 2: Create optimization indexes
        print("\n🏗️ STEP 2: CREATING OPTIMIZATION INDEXES")
        index_results = self.create_optimization_indexes()
        
        # Step 3: Apply database settings
        print("\n⚙️ STEP 3: APPLYING DATABASE SETTINGS")
        settings_results = self.optimize_database_settings()
        
        # Step 4: Test optimized performance
        print("\n🧪 STEP 4: TESTING OPTIMIZED PERFORMANCE")
        after_results = self.run_query_optimization_tests()
        
        # Step 5: Generate report
        print("\n📊 STEP 5: GENERATING PERFORMANCE REPORT")
        report = self.generate_performance_report(before_results, after_results, index_results, settings_results)
        
        # Compile final results
        optimization_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'database_path': self.db_path,
            'before_optimization': before_results,
            'after_optimization': after_results,
            'index_creation': index_results,
            'settings_optimization': settings_results,
            'performance_report': report
        }
        
        # Save results
        results_file = f"artifacts/database_optimization_{int(time.time())}.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(optimization_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Print summary
        print(f"\n📊 OPTIMIZATION SUMMARY")
        print("=" * 30)
        print(f"Indexes created: {report['optimization_summary']['indexes_created']}")
        print(f"Indexes existing: {report['optimization_summary']['indexes_existing']}")
        print(f"Settings applied: {report['optimization_summary']['settings_applied']}")
        print(f"Queries improved: {len([q for q in report['performance_comparison'].values() if q.get('faster', False)])}")
        
        return optimization_results

if __name__ == "__main__":
    optimizer = DatabaseOptimizer()
    results = optimizer.run_full_optimization()
