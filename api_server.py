"""Enhanced API server with Action Network expert picks integration."""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Import Action Network components
from ingest.action_network.analysis_tools import ActionNetworkAnalyzer
from ingest.action_network.team_mapper import ActionNetworkTeamMapper

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize analyzers
analyzer = ActionNetworkAnalyzer()
team_mapper = ActionNetworkTeamMapper()

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

@app.route('/api/metrics/performance', methods=['GET'])
def get_performance_metrics():
    """Legacy endpoint for performance metrics."""
    return jsonify({
        'metrics': {},
        'message': 'Use Action Network analytics endpoint for performance data'
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