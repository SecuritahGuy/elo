#!/usr/bin/env python3
"""
Database Optimization Script
Creates indexes and optimizes queries for better performance.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Optimizes database performance by creating indexes and analyzing queries."""
    
    def __init__(self, db_path: str = "artifacts/stats/nfl_elo_stats.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
    
    def create_indexes(self) -> Dict[str, bool]:
        """Create performance indexes for common queries."""
        indexes = {
            "team_ratings_season_config": False,
            "team_ratings_team_season": False,
            "action_network_picks_expert": False,
            "action_network_picks_league": False,
            "action_network_picks_created": False,
            "action_network_games_season": False,
            "action_network_games_teams": False,
            "action_network_expert_performance_expert": False,
            "action_network_expert_performance_recorded": False
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Create indexes for team_ratings table
            logger.info("Creating indexes for team_ratings table...")
            
            # Index for season and config queries (most common)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_team_ratings_season_config 
                ON team_ratings(season, config_name, rating DESC)
            """)
            indexes["team_ratings_season_config"] = True
            
            # Index for team-specific queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_team_ratings_team_season 
                ON team_ratings(team, season, config_name)
            """)
            indexes["team_ratings_team_season"] = True
            
            # Create indexes for action_network_picks table
            logger.info("Creating indexes for action_network_picks table...")
            
            # Index for expert-specific picks
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_picks_expert_created 
                ON action_network_picks(expert_id, created_at DESC)
            """)
            indexes["action_network_picks_expert"] = True
            
            # Index for league filtering
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_picks_league_created 
                ON action_network_picks(league_name, created_at DESC)
            """)
            indexes["action_network_picks_league"] = True
            
            # Index for result filtering
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_picks_result_created 
                ON action_network_picks(result, created_at DESC)
            """)
            indexes["action_network_picks_created"] = True
            
            # Create indexes for action_network_games table
            logger.info("Creating indexes for action_network_games table...")
            
            # Index for season queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_games_season_start 
                ON action_network_games(season, start_time)
            """)
            indexes["action_network_games_season"] = True
            
            # Index for team queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_games_teams 
                ON action_network_games(home_team_id, away_team_id)
            """)
            indexes["action_network_games_teams"] = True
            
            # Create indexes for action_network_expert_performance table
            logger.info("Creating indexes for action_network_expert_performance table...")
            
            # Index for expert performance queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_performance_expert_recorded 
                ON action_network_expert_performance(expert_id, recorded_at DESC)
            """)
            indexes["action_network_expert_performance_expert"] = True
            
            # Index for performance by date
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_performance_recorded 
                ON action_network_expert_performance(recorded_at DESC)
            """)
            indexes["action_network_expert_performance_recorded"] = True
            
            # Analyze the database to update statistics
            logger.info("Analyzing database for query optimization...")
            cursor.execute("ANALYZE")
            
            conn.commit()
            conn.close()
            
            logger.info("Database optimization completed successfully!")
            return indexes
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return indexes
    
    def analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze query performance and suggest optimizations."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table statistics
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            stats = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                stats[table] = {
                    "row_count": count,
                    "columns": len(columns),
                    "column_names": [col[1] for col in columns]
                }
            
            # Get index information
            cursor.execute("""
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            indexes = cursor.fetchall()
            
            conn.close()
            
            return {
                "tables": stats,
                "indexes": [{"name": idx[0], "table": idx[1], "sql": idx[2]} for idx in indexes],
                "optimization_date": str(datetime.now())
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            return {}
    
    def optimize_queries(self) -> List[str]:
        """Suggest query optimizations based on common patterns."""
        optimizations = [
            "✅ Use prepared statements to prevent SQL injection and improve performance",
            "✅ Add LIMIT clauses to prevent large result sets",
            "✅ Use specific column names instead of SELECT *",
            "✅ Consider pagination for large datasets",
            "✅ Use connection pooling for high-traffic applications",
            "✅ Implement query result caching for frequently accessed data",
            "✅ Use EXPLAIN QUERY PLAN to analyze query execution",
            "✅ Consider denormalization for frequently joined tables",
            "✅ Use batch operations for multiple inserts/updates",
            "✅ Monitor slow queries and optimize them individually"
        ]
        
        return optimizations
    
    def create_optimized_queries(self) -> Dict[str, str]:
        """Create optimized versions of common queries."""
        optimized_queries = {
            "team_ratings_optimized": """
                SELECT team, rating, wins, losses, win_pct, rating_change
                FROM team_ratings
                WHERE season = ? AND config_name = ?
                ORDER BY rating DESC
                LIMIT 32
            """,
            
            "expert_picks_optimized": """
                SELECT p.an_pick_id, e.name as expert_name, p.play_description,
                       p.pick_type, p.value, p.odds, p.units, p.units_net,
                       p.result, p.created_at, p.trend, p.social_likes, p.social_copies
                FROM action_network_picks p
                INNER JOIN action_network_experts e ON p.expert_id = e.id
                WHERE p.league_name = ? AND p.created_at >= datetime('now', '-30 days')
                ORDER BY p.created_at DESC
                LIMIT ?
            """,
            
            "team_comparison_optimized": """
                SELECT team, rating, wins, losses, win_pct, rating_change
                FROM team_ratings
                WHERE season = ? AND config_name = ? AND team IN ({})
                ORDER BY rating DESC
            """.format(','.join(['?' for _ in range(10)])),  # Support up to 10 teams
            
            "expert_performance_optimized": """
                SELECT window_period, wins, losses, pushes, total_picks, 
                       units_net, roi, win_streak_type, win_streak_value
                FROM action_network_expert_performance
                WHERE expert_id = ? AND recorded_at >= datetime('now', '-90 days')
                ORDER BY recorded_at DESC
                LIMIT 10
            """
        }
        
        return optimized_queries

def main():
    """Main function to run database optimization."""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='Optimize database performance')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze, do not create indexes')
    parser.add_argument('--db-path', default='artifacts/stats/nfl_elo_stats.db', help='Database path')
    
    args = parser.parse_args()
    
    try:
        optimizer = DatabaseOptimizer(args.db_path)
        
        if not args.analyze_only:
            logger.info("Starting database optimization...")
            indexes = optimizer.create_indexes()
            
            logger.info("Index creation results:")
            for index_name, success in indexes.items():
                status = "✅ Created" if success else "❌ Failed"
                logger.info(f"  {index_name}: {status}")
        
        # Analyze performance
        logger.info("Analyzing database performance...")
        stats = optimizer.analyze_query_performance()
        
        logger.info("Database statistics:")
        for table, info in stats.get('tables', {}).items():
            logger.info(f"  {table}: {info['row_count']} rows, {info['columns']} columns")
        
        logger.info(f"Total indexes: {len(stats.get('indexes', []))}")
        
        # Show optimization suggestions
        logger.info("Query optimization suggestions:")
        optimizations = optimizer.optimize_queries()
        for suggestion in optimizations:
            logger.info(f"  {suggestion}")
        
        logger.info("Database optimization completed!")
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
