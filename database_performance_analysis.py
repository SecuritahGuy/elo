#!/usr/bin/env python3
"""
Database Performance Analysis and Optimization
Analyzes current database performance and identifies optimization opportunities.
"""

import sqlite3
import time
import json
import os
from typing import Dict, List, Any, Tuple
from contextlib import contextmanager
import statistics

class DatabasePerformanceAnalyzer:
    def __init__(self, db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        self.db_path = db_path
        self.results = {}
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze performance of common queries."""
        print("🔍 DATABASE PERFORMANCE ANALYSIS")
        print("=" * 50)
        
        queries = {
            "elo_ratings_current": """
                SELECT team, rating, wins, losses, change 
                FROM team_ratings 
                WHERE season = 2025 AND config = 'comprehensive'
                ORDER BY rating DESC
            """,
            "elo_ratings_historical": """
                SELECT team, rating, wins, losses, change, season
                FROM team_ratings 
                WHERE season IN (2022, 2023, 2024) AND config = 'comprehensive'
                ORDER BY season DESC, rating DESC
            """,
            "team_comparison": """
                SELECT t1.team, t1.rating, t1.wins, t1.losses, t1.change,
                       t2.team, t2.rating, t2.wins, t2.losses, t2.change
                FROM team_ratings t1
                JOIN team_ratings t2 ON t1.season = t2.season AND t1.config = t2.config
                WHERE t1.season = 2025 AND t1.config = 'comprehensive'
                AND t1.team IN ('PHI', 'DAL') AND t2.team IN ('PHI', 'DAL')
            """,
            "injury_data_summary": """
                SELECT team, COUNT(*) as injury_count, 
                       AVG(severity_score) as avg_severity
                FROM injury_data 
                WHERE season = 2025 AND week = 1
                GROUP BY team
                ORDER BY injury_count DESC
            """,
            "expert_picks_recent": """
                SELECT expert, pick, confidence, game_date
                FROM expert_picks 
                WHERE game_date >= date('now', '-7 days')
                ORDER BY game_date DESC, confidence DESC
            """,
            "system_health": """
                SELECT component, status, last_updated, error_count
                FROM system_health 
                WHERE last_updated >= date('now', '-1 day')
                ORDER BY last_updated DESC
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
    
    def analyze_database_structure(self) -> Dict[str, Any]:
        """Analyze database structure and identify optimization opportunities."""
        print(f"\n🏗️ DATABASE STRUCTURE ANALYSIS")
        print("=" * 50)
        
        structure_info = {}
        
        with self.get_connection() as conn:
            # Get table information
            tables_query = """
                SELECT name, sql FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
            tables = conn.execute(tables_query).fetchall()
            
            structure_info['tables'] = {}
            for table_name, sql in tables:
                # Get row count
                count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                row_count = conn.execute(count_query).fetchone()['count']
                
                # Get index information
                indexes_query = f"PRAGMA index_list({table_name})"
                indexes = conn.execute(indexes_query).fetchall()
                
                structure_info['tables'][table_name] = {
                    'row_count': row_count,
                    'indexes': len(indexes),
                    'index_details': [dict(idx) for idx in indexes]
                }
                
                print(f"📋 {table_name}: {row_count} rows, {len(indexes)} indexes")
            
            # Check for missing indexes
            print(f"\n🔍 INDEX ANALYSIS")
            missing_indexes = self._identify_missing_indexes(conn)
            structure_info['missing_indexes'] = missing_indexes
            
            for idx in missing_indexes:
                print(f"   ⚠️  Missing index: {idx['table']}.{idx['column']} ({idx['reason']})")
        
        return structure_info
    
    def _identify_missing_indexes(self, conn) -> List[Dict[str, str]]:
        """Identify potentially missing indexes based on query patterns."""
        missing_indexes = []
        
        # Common patterns that benefit from indexes
        patterns = [
            ("team_ratings", "season", "Filtering by season"),
            ("team_ratings", "config", "Filtering by configuration"),
            ("team_ratings", "team", "Filtering by team"),
            ("injury_data", "season", "Filtering injury data by season"),
            ("injury_data", "team", "Filtering injury data by team"),
            ("injury_data", "week", "Filtering injury data by week"),
            ("expert_picks", "game_date", "Filtering picks by date"),
            ("expert_picks", "expert", "Filtering picks by expert"),
            ("system_health", "last_updated", "Filtering health data by date"),
            ("system_health", "component", "Filtering health data by component")
        ]
        
        for table, column, reason in patterns:
            # Check if index exists
            index_query = f"""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='{table}' 
                AND sql LIKE '%{column}%'
            """
            existing_indexes = conn.execute(index_query).fetchall()
            
            if not existing_indexes:
                missing_indexes.append({
                    'table': table,
                    'column': column,
                    'reason': reason
                })
        
        return missing_indexes
    
    def generate_optimization_recommendations(self, query_results: Dict, structure_info: Dict) -> List[Dict[str, Any]]:
        """Generate specific optimization recommendations."""
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS")
        print("=" * 50)
        
        recommendations = []
        
        # Analyze slow queries
        slow_queries = {k: v for k, v in query_results.items() 
                       if v.get('avg_time_ms', 0) > 100}  # >100ms threshold
        
        if slow_queries:
            recommendations.append({
                'type': 'slow_queries',
                'priority': 'high',
                'description': f'Found {len(slow_queries)} slow queries (>100ms)',
                'queries': slow_queries,
                'action': 'Add indexes and optimize query structure'
            })
            print(f"🚨 {len(slow_queries)} slow queries detected")
        
        # Analyze missing indexes
        missing_indexes = structure_info.get('missing_indexes', [])
        if missing_indexes:
            recommendations.append({
                'type': 'missing_indexes',
                'priority': 'high',
                'description': f'Found {len(missing_indexes)} missing indexes',
                'indexes': missing_indexes,
                'action': 'Create indexes for frequently queried columns'
            })
            print(f"📊 {len(missing_indexes)} missing indexes identified")
        
        # Analyze table sizes
        large_tables = {name: info for name, info in structure_info.get('tables', {}).items() 
                       if info.get('row_count', 0) > 10000}
        
        if large_tables:
            recommendations.append({
                'type': 'large_tables',
                'priority': 'medium',
                'description': f'Found {len(large_tables)} large tables (>10k rows)',
                'tables': large_tables,
                'action': 'Consider partitioning or archiving old data'
            })
            print(f"📈 {len(large_tables)} large tables identified")
        
        # General recommendations
        recommendations.extend([
            {
                'type': 'general',
                'priority': 'medium',
                'description': 'Enable WAL mode for better concurrency',
                'action': 'PRAGMA journal_mode=WAL;'
            },
            {
                'type': 'general',
                'priority': 'low',
                'description': 'Set optimal cache size',
                'action': 'PRAGMA cache_size=10000;'
            },
            {
                'type': 'general',
                'priority': 'low',
                'description': 'Enable query optimization',
                'action': 'PRAGMA optimize;'
            }
        ])
        
        return recommendations
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete database performance analysis."""
        print("🚀 STARTING DATABASE PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        # Check if database exists
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return {'error': 'Database not found'}
        
        # Run analysis
        query_results = self.analyze_query_performance()
        structure_info = self.analyze_database_structure()
        recommendations = self.generate_optimization_recommendations(query_results, structure_info)
        
        # Compile results
        analysis_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'database_path': self.db_path,
            'query_performance': query_results,
            'database_structure': structure_info,
            'recommendations': recommendations,
            'summary': {
                'total_queries_tested': len(query_results),
                'slow_queries': len([q for q in query_results.values() if q.get('avg_time_ms', 0) > 100]),
                'missing_indexes': len(structure_info.get('missing_indexes', [])),
                'total_tables': len(structure_info.get('tables', {})),
                'total_rows': sum(info.get('row_count', 0) for info in structure_info.get('tables', {}).values())
            }
        }
        
        # Save results
        results_file = f"artifacts/database_performance_analysis_{int(time.time())}.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Print summary
        print(f"\n📊 ANALYSIS SUMMARY")
        print("=" * 30)
        print(f"Queries tested: {analysis_results['summary']['total_queries_tested']}")
        print(f"Slow queries: {analysis_results['summary']['slow_queries']}")
        print(f"Missing indexes: {analysis_results['summary']['missing_indexes']}")
        print(f"Total tables: {analysis_results['summary']['total_tables']}")
        print(f"Total rows: {analysis_results['summary']['total_rows']:,}")
        
        return analysis_results

if __name__ == "__main__":
    analyzer = DatabasePerformanceAnalyzer()
    results = analyzer.run_full_analysis()

