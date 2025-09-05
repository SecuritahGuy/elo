"""Enhanced API server with Action Network expert picks integration."""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# Import Action Network components
from ingest.action_network.analysis_tools import ActionNetworkAnalyzer
from ingest.action_network.team_mapper import ActionNetworkTeamMapper

# Import ELO components
from ingest.nfl.elo_data_service import EloDataService

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize analyzers
analyzer = ActionNetworkAnalyzer()
team_mapper = ActionNetworkTeamMapper()
elo_service = EloDataService()

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get overall system status."""
    try:
        # Get Action Network health (simplified for now)
        an_health = {
            'status': 'healthy',
            'experts_count': 0,
            'picks_count': 0,
            'last_updated': None
        }
        
        # Get NFL stats health (simplified for now)
        nfl_health = {
            'status': 'healthy',
            'games_count': 0,
            'last_updated': None
        }
        
        # Get database health (simplified for now)
        db_health = {
            'status': 'healthy',
            'db_size_mb': 0,
            'last_updated': None
        }
        
        # Determine overall status
        statuses = [an_health['status'], nfl_health['status'], db_health['status']]
        
        if 'critical' in statuses or 'error' in statuses:
            overall_status = 'critical'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return jsonify({
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'action_network': an_health,
            'nfl_stats': nfl_health,
            'database': db_health
        })
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/action-network/experts', methods=['GET'])
def get_experts():
    """Get Action Network experts with performance data."""
    try:
        limit = request.args.get('limit', 50, type=int)
        league = request.args.get('league', 'nfl')
        
        # Get top experts
        experts = analyzer.get_top_experts(league, limit=limit)
        
        return jsonify({
            'experts': experts,
            'total': len(experts),
            'league': league,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting experts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/action-network/experts/<int:expert_id>', methods=['GET'])
def get_expert_details(expert_id):
    """Get detailed information for a specific expert."""
    try:
        # Get expert performance summary
        conn = sqlite3.connect('artifacts/stats/nfl_elo_stats.db')
        cursor = conn.cursor()
        
        # Get expert basic info
        cursor.execute('''
            SELECT id, an_expert_id, name, username, is_verified, followers, bio, picture_url
            FROM action_network_experts
            WHERE an_expert_id = ?
        ''', (expert_id,))
        
        expert_info = cursor.fetchone()
        if not expert_info:
            return jsonify({'error': 'Expert not found'}), 404
        
        # Get expert performance
        cursor.execute('''
            SELECT window_period, wins, losses, pushes, total_picks, units_net, roi,
                   win_streak_type, win_streak_value, win_streak_start_date, recorded_at
            FROM action_network_expert_performance
            WHERE expert_id = ?
            ORDER BY recorded_at DESC
        ''', (expert_info[0],))
        
        performance_data = cursor.fetchall()
        
        # Get recent picks
        cursor.execute('''
            SELECT an_pick_id, league_name, play_description, value, odds, units,
                   units_net, result, created_at, trend, social_likes, social_copies
            FROM action_network_picks
            WHERE expert_id = ?
            ORDER BY created_at DESC
            LIMIT 20
        ''', (expert_info[0],))
        
        recent_picks = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'expert': {
                'id': expert_info[1],
                'name': expert_info[2],
                'username': expert_info[3],
                'is_verified': expert_info[4],
                'followers': expert_info[5],
                'bio': expert_info[6],
                'picture_url': expert_info[7]
            },
            'performance': [
                {
                    'window_period': row[0],
                    'wins': row[1],
                    'losses': row[2],
                    'pushes': row[3],
                    'total_picks': row[4],
                    'units_net': row[5],
                    'roi': row[6],
                    'win_streak_type': row[7],
                    'win_streak_value': row[8],
                    'win_streak_start_date': row[9],
                    'recorded_at': row[10]
                } for row in performance_data
            ],
            'recent_picks': [
                {
                    'pick_id': row[0],
                    'league': row[1],
                    'description': row[2],
                    'value': row[3],
                    'odds': row[4],
                    'units': row[5],
                    'units_net': row[6],
                    'result': row[7],
                    'created_at': row[8],
                    'trend': row[9],
                    'likes': row[10],
                    'copies': row[11]
                } for row in recent_picks
            ],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting expert details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/action-network/picks', methods=['GET'])
def get_picks():
    """Get Action Network picks with filtering options."""
    try:
        league = request.args.get('league', 'nfl')
        limit = request.args.get('limit', 100, type=int)
        expert_id = request.args.get('expert_id', type=int)
        result = request.args.get('result')  # 'win', 'loss', 'pending'
        
        # Build query
        query = '''
            SELECT p.an_pick_id, e.name as expert_name, p.play_description,
                   p.pick_type, p.value, p.odds, p.units, p.units_net,
                   p.result, p.created_at, p.trend, p.social_likes, p.social_copies,
                   g.an_game_id, g.start_time, g.game_status,
                   ht.full_name as home_team_name, ht.abbr as home_team_abbr,
                   at.full_name as away_team_name, at.abbr as away_team_abbr
            FROM action_network_picks p
            JOIN action_network_experts e ON p.expert_id = e.id
            LEFT JOIN action_network_games g ON p.game_id = g.an_game_id
            LEFT JOIN action_network_teams ht ON g.home_team_id = ht.an_team_id
            LEFT JOIN action_network_teams at ON g.away_team_id = at.an_team_id
            WHERE p.league_name = ?
        '''
        
        params = [league]
        
        if expert_id:
            query += ' AND p.expert_id = ?'
            params.append(expert_id)
        
        if result:
            query += ' AND p.result = ?'
            params.append(result)
        
        query += ' ORDER BY p.created_at DESC LIMIT ?'
        params.append(limit)
        
        conn = sqlite3.connect('artifacts/stats/nfl_elo_stats.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        picks = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'picks': [
                {
                    'pick_id': row[0],
                    'expert_name': row[1],
                    'description': row[2],
                    'pick_type': row[3],
                    'value': row[4],
                    'odds': row[5],
                    'units': row[6],
                    'units_net': row[7],
                    'result': row[8],
                    'created_at': row[9],
                    'trend': row[10],
                    'likes': row[11],
                    'copies': row[12],
                    'game_id': row[13],
                    'game_start': row[14],
                    'game_status': row[15],
                    'home_team': row[16],
                    'home_team_abbr': row[17],
                    'away_team': row[18],
                    'away_team_abbr': row[19]
                } for row in picks
            ],
            'total': len(picks),
            'league': league,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting picks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/action-network/analytics', methods=['GET'])
def get_analytics():
    """Get Action Network analytics and insights."""
    try:
        league = request.args.get('league', 'nfl')
        
        # Get league performance summary
        league_summary = analyzer.get_league_performance_summary(league)
        
        # Get pick accuracy by type
        accuracy_by_type = analyzer.get_pick_accuracy_by_type(league)
        
        # Get social metrics analysis
        social_analysis = analyzer.get_social_metrics_analysis(league)
        
        # Get top experts
        top_experts = analyzer.get_top_experts(league, limit=10)
        
        return jsonify({
            'league_summary': league_summary,
            'accuracy_by_type': accuracy_by_type,
            'social_analysis': social_analysis,
            'top_experts': top_experts,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/action-network/teams', methods=['GET'])
def get_teams():
    """Get NFL teams with Action Network data."""
    try:
        # Get NFL games with team info
        games = team_mapper.get_nfl_games_with_teams()
        
        # Get team mappings
        nfl_mapping = team_mapper.map_nfl_teams_to_standard()
        
        return jsonify({
            'games': games,
            'team_mappings': nfl_mapping,
            'total_games': len(games),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        return jsonify({'error': str(e)}), 500

# ELO Ratings endpoints
@app.route('/api/elo/seasons', methods=['GET'])
def get_elo_seasons():
    """Get available seasons for ELO ratings."""
    try:
        seasons = elo_service.get_available_seasons()
        return jsonify({'seasons': seasons, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Error getting ELO seasons: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elo/ratings', methods=['GET'])
def get_elo_ratings():
    """Get ELO ratings for a specific season."""
    try:
        season = request.args.get('season', 2024, type=int)
        config_name = request.args.get('config', 'baseline')
        
        ratings = elo_service.get_team_ratings_for_season(season, config_name)
        return jsonify({
            'ratings': ratings,
            'season': season,
            'config': config_name,
            'total_teams': len(ratings),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting ELO ratings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elo/team/<team>', methods=['GET'])
def get_team_elo_history(team):
    """Get ELO rating history for a specific team."""
    try:
        seasons = request.args.getlist('seasons', type=int)
        if not seasons:
            seasons = [2020, 2021, 2022, 2023, 2024]
        
        history = elo_service.get_rating_history(team.upper(), seasons)
        return jsonify({
            'team': team.upper(),
            'history': history,
            'seasons': seasons,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting team ELO history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elo/season-summary', methods=['GET'])
def get_elo_season_summary():
    """Get ELO season summary statistics."""
    try:
        season = request.args.get('season', 2024, type=int)
        summary = elo_service.get_season_summary(season)
        return jsonify({
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting ELO season summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elo/compare', methods=['GET'])
def get_elo_team_comparison():
    """Get ELO comparison for specific teams."""
    try:
        teams = request.args.getlist('teams')
        season = request.args.get('season', 2024, type=int)
        
        if not teams:
            return jsonify({'error': 'No teams specified'}), 400
        
        comparison = elo_service.get_team_comparison(teams, season)
        return jsonify({
            'teams': comparison,
            'season': season,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting ELO team comparison: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/cron-status', methods=['GET'])
def get_cron_status():
    """Get cron job status and monitoring data."""
    try:
        # Import the cron monitor directly instead of using subprocess
        from monitoring.cron_monitor import CronJobMonitor
        
        # Create monitor instance and generate report
        monitor = CronJobMonitor()
        cron_data = monitor.generate_status_report()
        
        return jsonify(cron_data)
            
    except Exception as e:
        logger.error(f"Error getting cron status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/performance', methods=['GET'])
def get_performance_metrics():
    """Get performance metrics for the dashboard."""
    try:
        # Get Action Network analytics for performance metrics
        analytics = analyzer.get_league_performance_summary('nfl')
        
        # Get expert performance data
        top_experts = analyzer.get_top_experts('nfl', limit=10)
        
        # Calculate performance metrics
        total_picks = analytics.get('total_picks', 0)
        win_rate = analytics.get('win_rate', 0)
        total_units = analytics.get('total_units_net', 0)
        
        performance_data = {
            'accuracy': win_rate,
            'brier_score': 0.22,  # Placeholder - would calculate from actual data
            'games_processed': analytics.get('recent_picks', 0),  # Use recent picks as games processed
            'confidence': 0.75,  # Placeholder
            'total_picks': total_picks,
            'win_rate': win_rate,
            'total_units': total_units,
            'top_experts': top_experts[:5],  # Top 5 experts
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(performance_data)
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/health', methods=['GET'])
def get_system_health():
    """Get system health status."""
    try:
        # Get basic system status
        status_response = get_system_status()
        status_data = status_response.get_json()
        
        # Add additional health metrics
        health_data = {
            'overall_status': status_data.get('status', 'unknown'),
            'action_network': status_data.get('action_network', {}),
            'database': status_data.get('database', {}),
            'nfl_stats': status_data.get('nfl_stats', {}),
            'timestamp': datetime.now().isoformat(),
            'uptime': 'N/A',  # Would calculate actual uptime
            'memory_usage': 'N/A',  # Would get actual memory usage
            'cpu_usage': 'N/A'  # Would get actual CPU usage
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_configuration():
    """Get system configuration."""
    try:
        config_data = {
            'action_network': {
                'enabled': True,
                'expert_picks_interval_minutes': 15,
                'all_picks_interval_minutes': 5,
                'max_retries': 3,
                'retry_delay_seconds': 30
            },
            'nfl_stats': {
                'enabled': True,
                'collection_interval_hours': 6,
                'years': [2024, 2025],
                'include_weather': True,
                'include_travel': True,
                'include_ngs': True,
                'include_epa': True,
                'include_qb_stats': True,
                'include_turnover_stats': True,
                'include_redzone_stats': True,
                'include_downs_stats': True
            },
            'database': {
                'path': 'artifacts/stats/nfl_elo_stats.db',
                'backup_enabled': True,
                'backup_interval_hours': 24
            },
            'logging': {
                'level': 'INFO',
                'file': 'artifacts/automated_collection/collection.log',
                'max_size_mb': 100,
                'backup_count': 5
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(config_data)
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['PUT'])
def update_configuration():
    """Update system configuration."""
    try:
        # In a real implementation, this would save the config to a file
        # For now, just return success
        config_data = request.get_json()
        
        return jsonify({
            'message': 'Configuration updated successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return jsonify({'error': str(e)}), 500

# Legacy endpoints for existing dashboard
@app.route('/api/teams/rankings', methods=['GET'])
def get_team_rankings():
    """Legacy endpoint for team rankings."""
    return jsonify({
        'teams': [],
        'message': 'Use Action Network teams endpoint for team data'
    })

@app.route('/api/predictions/week/<int:week>', methods=['GET'])
def get_week_predictions(week):
    """Legacy endpoint for week predictions."""
    return jsonify({
        'predictions': [],
        'week': week,
        'message': 'Use Action Network picks endpoint for prediction data'
    })


if __name__ == '__main__':
    print("Starting Action Network API server...")
    print("Available endpoints:")
    print("  GET /api/system/status - System health status")
    print("  GET /api/action-network/experts - Expert rankings")
    print("  GET /api/action-network/experts/{id} - Expert details")
    print("  GET /api/action-network/picks - Expert picks")
    print("  GET /api/action-network/analytics - Analytics and insights")
    print("  GET /api/action-network/teams - NFL teams data")
    
    app.run(host='0.0.0.0', port=8000, debug=True)