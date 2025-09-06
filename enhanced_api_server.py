#!/usr/bin/env python3
"""
Enhanced API Server with Multi-Sport Support
Updated API endpoints to work with unified database and support multiple sports
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class MultiSportAPIServer:
    """Enhanced API server with multi-sport support."""
    
    def __init__(self, db_path: str = "sportsedge_unified.db"):
        self.db_path = db_path
        self.supported_sports = ['nfl', 'nba', 'mlb', 'nhl', 'ncaaf', 'ncaab']
    
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def validate_sport(self, sport: str) -> bool:
        """Validate sport parameter."""
        return sport.lower() in self.supported_sports
    
    def get_sport_id(self, sport: str) -> Optional[int]:
        """Get sport ID from sport code."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM sports WHERE sport_code = ?", (sport.lower(),))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            conn.close()

# Initialize API server
api_server = MultiSportAPIServer()

# ============================================================================
# SPORTS AND LEAGUES ENDPOINTS
# ============================================================================

@app.route('/api/sports', methods=['GET'])
def get_sports():
    """Get all supported sports."""
    try:
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, sport_code, sport_name, sport_type, season_structure
            FROM sports
            ORDER BY sport_name
        ''')
        
        sports = []
        for row in cursor.fetchall():
            sports.append({
                'id': row['id'],
                'code': row['sport_code'],
                'name': row['sport_name'],
                'type': row['sport_type'],
                'season_structure': row['season_structure']
            })
        
        conn.close()
        return jsonify({'sports': sports})
        
    except Exception as e:
        logger.error(f"Error getting sports: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sports/<sport>/leagues', methods=['GET'])
def get_sport_leagues(sport):
    """Get leagues for a specific sport."""
    try:
        if not api_server.validate_sport(sport):
            return jsonify({'error': f'Unsupported sport: {sport}'}), 400
        
        sport_id = api_server.get_sport_id(sport)
        if not sport_id:
            return jsonify({'error': f'Sport not found: {sport}'}), 404
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, league_code, league_name, conference, division, level
            FROM leagues
            WHERE sport_id = ?
            ORDER BY league_name
        ''', (sport_id,))
        
        leagues = []
        for row in cursor.fetchall():
            leagues.append({
                'id': row['id'],
                'code': row['league_code'],
                'name': row['league_name'],
                'conference': row['conference'],
                'division': row['division'],
                'level': row['level']
            })
        
        conn.close()
        return jsonify({'sport': sport, 'leagues': leagues})
        
    except Exception as e:
        logger.error(f"Error getting leagues for {sport}: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# TEAMS ENDPOINTS
# ============================================================================

@app.route('/api/sports/<sport>/teams', methods=['GET'])
def get_sport_teams(sport):
    """Get teams for a specific sport."""
    try:
        if not api_server.validate_sport(sport):
            return jsonify({'error': f'Unsupported sport: {sport}'}), 400
        
        sport_id = api_server.get_sport_id(sport)
        if not sport_id:
            return jsonify({'error': f'Sport not found: {sport}'}), 404
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get query parameters
        league_id = request.args.get('league_id', type=int)
        conference = request.args.get('conference')
        division = request.args.get('division')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        # Build query
        query = '''
            SELECT t.id, t.team_code, t.team_name, t.city, t.mascot, t.abbreviation,
                   t.conference, t.division, t.home_venue, t.venue_surface, t.venue_dome,
                   t.timezone, t.colors, t.logo_url, t.active, l.league_name
            FROM teams t
            LEFT JOIN leagues l ON t.league_id = l.id
            WHERE t.sport_id = ?
        '''
        params = [sport_id]
        
        if league_id:
            query += ' AND t.league_id = ?'
            params.append(league_id)
        
        if conference:
            query += ' AND t.conference = ?'
            params.append(conference)
        
        if division:
            query += ' AND t.division = ?'
            params.append(division)
        
        if active_only:
            query += ' AND t.active = 1'
        
        query += ' ORDER BY t.team_name'
        
        cursor.execute(query, params)
        
        teams = []
        for row in cursor.fetchall():
            teams.append({
                'id': row['id'],
                'code': row['team_code'],
                'name': row['team_name'],
                'city': row['city'],
                'mascot': row['mascot'],
                'abbreviation': row['abbreviation'],
                'conference': row['conference'],
                'division': row['division'],
                'venue': {
                    'name': row['home_venue'],
                    'surface': row['venue_surface'],
                    'dome': bool(row['venue_dome'])
                },
                'timezone': row['timezone'],
                'colors': json.loads(row['colors']) if row['colors'] else None,
                'logo_url': row['logo_url'],
                'active': bool(row['active']),
                'league': row['league_name']
            })
        
        conn.close()
        return jsonify({'sport': sport, 'teams': teams})
        
    except Exception as e:
        logger.error(f"Error getting teams for {sport}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sports/<sport>/teams/<int:team_id>', methods=['GET'])
def get_team_details(sport, team_id):
    """Get detailed information for a specific team."""
    try:
        if not api_server.validate_sport(sport):
            return jsonify({'error': f'Unsupported sport: {sport}'}), 400
        
        sport_id = api_server.get_sport_id(sport)
        if not sport_id:
            return jsonify({'error': f'Sport not found: {sport}'}), 404
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get team details
        cursor.execute('''
            SELECT t.*, l.league_name, s.sport_name
            FROM teams t
            LEFT JOIN leagues l ON t.league_id = l.id
            LEFT JOIN sports s ON t.sport_id = s.id
            WHERE t.id = ? AND t.sport_id = ?
        ''', (team_id, sport_id))
        
        team_row = cursor.fetchone()
        if not team_row:
            return jsonify({'error': 'Team not found'}), 404
        
        # Get recent games
        cursor.execute('''
            SELECT g.id, g.game_date, g.game_status, g.home_score, g.away_score,
                   ht.team_name as home_team, at.team_name as away_team,
                   CASE WHEN g.home_team_id = ? THEN 'home' ELSE 'away' END as team_side
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            WHERE (g.home_team_id = ? OR g.away_team_id = ?)
            ORDER BY g.game_date DESC
            LIMIT 10
        ''', (team_id, team_id, team_id))
        
        recent_games = []
        for row in cursor.fetchall():
            recent_games.append({
                'id': row['id'],
                'date': row['game_date'],
                'status': row['game_status'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_score': row['home_score'],
                'away_score': row['away_score'],
                'team_side': row['team_side']
            })
        
        # Get current season stats
        cursor.execute('''
            SELECT season_id, week, rating, wins, losses, ties, win_percentage,
                   points_for, points_against, point_differential
            FROM team_ratings
            WHERE team_id = ?
            ORDER BY season_id DESC, week DESC
            LIMIT 1
        ''', (team_id,))
        
        current_stats = None
        stats_row = cursor.fetchone()
        if stats_row:
            current_stats = {
                'season_id': stats_row['season_id'],
                'week': stats_row['week'],
                'rating': stats_row['rating'],
                'record': f"{stats_row['wins']}-{stats_row['losses']}-{stats_row['ties']}",
                'win_percentage': stats_row['win_percentage'],
                'points_for': stats_row['points_for'],
                'points_against': stats_row['points_against'],
                'point_differential': stats_row['point_differential']
            }
        
        team_data = {
            'id': team_row['id'],
            'code': team_row['team_code'],
            'name': team_row['team_name'],
            'city': team_row['city'],
            'mascot': team_row['mascot'],
            'abbreviation': team_row['abbreviation'],
            'conference': team_row['conference'],
            'division': team_row['division'],
            'venue': {
                'name': team_row['home_venue'],
                'surface': team_row['venue_surface'],
                'dome': bool(team_row['venue_dome']),
                'capacity': team_row['venue_capacity']
            },
            'timezone': team_row['timezone'],
            'colors': json.loads(team_row['colors']) if team_row['colors'] else None,
            'logo_url': team_row['logo_url'],
            'website_url': team_row['website_url'],
            'active': bool(team_row['active']),
            'league': team_row['league_name'],
            'sport': team_row['sport_name'],
            'recent_games': recent_games,
            'current_stats': current_stats
        }
        
        conn.close()
        return jsonify({'team': team_data})
        
    except Exception as e:
        logger.error(f"Error getting team details: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# GAMES ENDPOINTS
# ============================================================================

@app.route('/api/sports/<sport>/games', methods=['GET'])
def get_sport_games(sport):
    """Get games for a specific sport."""
    try:
        if not api_server.validate_sport(sport):
            return jsonify({'error': f'Unsupported sport: {sport}'}), 400
        
        sport_id = api_server.get_sport_id(sport)
        if not sport_id:
            return jsonify({'error': f'Sport not found: {sport}'}), 404
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get query parameters
        season = request.args.get('season', type=int)
        week = request.args.get('week', type=int)
        game_type = request.args.get('game_type', 'regular')
        status = request.args.get('status')
        team_id = request.args.get('team_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = '''
            SELECT g.id, g.external_game_id, g.game_type, g.round, g.week,
                   g.game_date, g.game_time_local, g.game_status, g.quarter,
                   g.time_remaining, g.possession, g.down, g.distance, g.yard_line,
                   g.red_zone, g.weather_condition, g.temperature, g.wind_speed,
                   g.attendance, g.home_score, g.away_score, g.home_win,
                   g.home_rest_days, g.away_rest_days, g.home_win_prob, g.away_win_prob,
                   ht.team_name as home_team, ht.team_code as home_team_code,
                   at.team_name as away_team, at.team_code as away_team_code,
                   s.season_year, l.league_name
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            JOIN seasons s ON g.season_id = s.id
            LEFT JOIN leagues l ON g.league_id = l.id
            WHERE g.sport_id = ?
        '''
        params = [sport_id]
        
        if season:
            query += ' AND s.season_year = ?'
            params.append(season)
        
        if week:
            query += ' AND g.week = ?'
            params.append(week)
        
        if game_type:
            query += ' AND g.game_type = ?'
            params.append(game_type)
        
        if status:
            query += ' AND g.game_status = ?'
            params.append(status)
        
        if team_id:
            query += ' AND (g.home_team_id = ? OR g.away_team_id = ?)'
            params.extend([team_id, team_id])
        
        query += ' ORDER BY g.game_date DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        games = []
        for row in cursor.fetchall():
            games.append({
                'id': row['id'],
                'external_id': row['external_game_id'],
                'type': row['game_type'],
                'round': row['round'],
                'week': row['week'],
                'date': row['game_date'],
                'time_local': row['game_time_local'],
                'status': row['game_status'],
                'quarter': row['quarter'],
                'time_remaining': row['time_remaining'],
                'possession': row['possession'],
                'down': row['down'],
                'distance': row['distance'],
                'yard_line': row['yard_line'],
                'red_zone': bool(row['red_zone']),
                'weather': {
                    'condition': row['weather_condition'],
                    'temperature': row['temperature'],
                    'wind_speed': row['wind_speed']
                },
                'attendance': row['attendance'],
                'home_team': {
                    'name': row['home_team'],
                    'code': row['home_team_code'],
                    'score': row['home_score'],
                    'rest_days': row['home_rest_days'],
                    'win_prob': row['home_win_prob']
                },
                'away_team': {
                    'name': row['away_team'],
                    'code': row['away_team_code'],
                    'score': row['away_score'],
                    'rest_days': row['away_rest_days'],
                    'win_prob': row['away_win_prob']
                },
                'home_win': row['home_win'],
                'season': row['season_year'],
                'league': row['league_name']
            })
        
        conn.close()
        return jsonify({'sport': sport, 'games': games})
        
    except Exception as e:
        logger.error(f"Error getting games for {sport}: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ODDS ENDPOINTS
# ============================================================================

@app.route('/api/sports/<sport>/odds', methods=['GET'])
def get_sport_odds(sport):
    """Get odds for a specific sport."""
    try:
        if not api_server.validate_sport(sport):
            return jsonify({'error': f'Unsupported sport: {sport}'}), 400
        
        sport_id = api_server.get_sport_id(sport)
        if not sport_id:
            return jsonify({'error': f'Sport not found: {sport}'}), 404
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get query parameters
        game_id = request.args.get('game_id', type=int)
        sportsbook = request.args.get('sportsbook')
        odds_type = request.args.get('odds_type')
        limit = request.args.get('limit', 100, type=int)
        
        # Build query
        query = '''
            SELECT o.id, o.game_id, o.sportsbook, o.odds_type,
                   o.home_value, o.away_value, o.total_value,
                   o.home_odds, o.away_odds, o.over_odds, o.under_odds,
                   o.prop_name, o.prop_value, o.prop_odds, o.timestamp,
                   g.game_date, ht.team_name as home_team, at.team_name as away_team
            FROM odds o
            JOIN games g ON o.game_id = g.id
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            WHERE g.sport_id = ?
        '''
        params = [sport_id]
        
        if game_id:
            query += ' AND o.game_id = ?'
            params.append(game_id)
        
        if sportsbook:
            query += ' AND o.sportsbook = ?'
            params.append(sportsbook)
        
        if odds_type:
            query += ' AND o.odds_type = ?'
            params.append(odds_type)
        
        query += ' ORDER BY o.timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        odds = []
        for row in cursor.fetchall():
            odds.append({
                'id': row['id'],
                'game_id': row['game_id'],
                'sportsbook': row['sportsbook'],
                'odds_type': row['odds_type'],
                'values': {
                    'home': row['home_value'],
                    'away': row['away_value'],
                    'total': row['total_value']
                },
                'odds': {
                    'home': row['home_odds'],
                    'away': row['away_odds'],
                    'over': row['over_odds'],
                    'under': row['under_odds']
                },
                'prop': {
                    'name': row['prop_name'],
                    'value': row['prop_value'],
                    'odds': row['prop_odds']
                },
                'timestamp': row['timestamp'],
                'game': {
                    'date': row['game_date'],
                    'home_team': row['home_team'],
                    'away_team': row['away_team']
                }
            })
        
        conn.close()
        return jsonify({'sport': sport, 'odds': odds})
        
    except Exception as e:
        logger.error(f"Error getting odds for {sport}: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# EXPERT PICKS ENDPOINTS
# ============================================================================

@app.route('/api/sports/<sport>/expert-picks', methods=['GET'])
def get_sport_expert_picks(sport):
    """Get expert picks for a specific sport."""
    try:
        if not api_server.validate_sport(sport):
            return jsonify({'error': f'Unsupported sport: {sport}'}), 400
        
        sport_id = api_server.get_sport_id(sport)
        if not sport_id:
            return jsonify({'error': f'Sport not found: {sport}'}), 404
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get query parameters
        expert_id = request.args.get('expert_id', type=int)
        game_id = request.args.get('game_id', type=int)
        pick_type = request.args.get('pick_type')
        result = request.args.get('result')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = '''
            SELECT p.id, p.external_pick_id, p.pick_type, p.play_description,
                   p.value, p.odds, p.units, p.units_net, p.money, p.money_net,
                   p.result, p.confidence_level, p.reasoning, p.pick_created_at,
                   p.starts_at, p.ends_at, p.settled_at, p.trend,
                   p.social_likes, p.social_copies, p.verified,
                   e.name as expert_name, e.username, e.is_verified as expert_verified,
                   g.game_date, ht.team_name as home_team, at.team_name as away_team
            FROM expert_picks p
            JOIN experts e ON p.expert_id = e.id
            LEFT JOIN games g ON p.game_id = g.id
            LEFT JOIN teams ht ON g.home_team_id = ht.id
            LEFT JOIN teams at ON g.away_team_id = at.id
            WHERE p.sport_id = ?
        '''
        params = [sport_id]
        
        if expert_id:
            query += ' AND p.expert_id = ?'
            params.append(expert_id)
        
        if game_id:
            query += ' AND p.game_id = ?'
            params.append(game_id)
        
        if pick_type:
            query += ' AND p.pick_type = ?'
            params.append(pick_type)
        
        if result:
            query += ' AND p.result = ?'
            params.append(result)
        
        query += ' ORDER BY p.pick_created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        picks = []
        for row in cursor.fetchall():
            picks.append({
                'id': row['id'],
                'external_id': row['external_pick_id'],
                'pick_type': row['pick_type'],
                'description': row['play_description'],
                'value': row['value'],
                'odds': row['odds'],
                'units': row['units'],
                'units_net': row['units_net'],
                'money': row['money'],
                'money_net': row['money_net'],
                'result': row['result'],
                'confidence_level': row['confidence_level'],
                'reasoning': row['reasoning'],
                'timestamps': {
                    'created': row['pick_created_at'],
                    'starts': row['starts_at'],
                    'ends': row['ends_at'],
                    'settled': row['settled_at']
                },
                'trend': row['trend'],
                'social': {
                    'likes': row['social_likes'],
                    'copies': row['social_copies']
                },
                'verified': bool(row['verified']),
                'expert': {
                    'name': row['expert_name'],
                    'username': row['username'],
                    'verified': bool(row['expert_verified'])
                },
                'game': {
                    'date': row['game_date'],
                    'home_team': row['home_team'],
                    'away_team': row['away_team']
                } if row['game_date'] else None
            })
        
        # Always return experts along with picks
        cursor.execute('''
            SELECT e.id, e.name, e.username, e.is_verified, e.avatar_url,
                   e.bio, e.followers, e.social_media, e.specialties,
                   e.created_at
            FROM experts e
            ORDER BY e.followers DESC
            LIMIT ?
        ''', (limit,))
        
        experts = []
        for row in cursor.fetchall():
            experts.append({
                'id': row['id'],
                'name': row['name'],
                'username': row['username'],
                'verified': bool(row['is_verified']),
                'avatar_url': row['avatar_url'],
                'bio': row['bio'],
                'followers': row['followers'] or 0,
                'social_media': row['social_media'],
                'specialties': row['specialties'],
                'created_at': row['created_at']
            })
        
        conn.close()
        return jsonify({
            'sport': sport, 
            'picks': picks,
            'experts': experts
        })
        
    except Exception as e:
        logger.error(f"Error getting expert picks for {sport}: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ELO RATINGS ENDPOINTS
# ============================================================================

@app.route('/api/elo/seasons', methods=['GET'])
def get_elo_seasons():
    """Get available ELO seasons."""
    try:
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT s.season_year as season
            FROM seasons s
            JOIN team_ratings tr ON s.id = tr.season_id
            ORDER BY s.season_year DESC
        ''')
        
        seasons = [{'season': row['season']} for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'seasons': seasons})
        
    except Exception as e:
        logger.error(f"Error getting ELO seasons: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elo/ratings', methods=['GET'])
def get_elo_ratings():
    """Get ELO ratings for a specific season."""
    try:
        season = request.args.get('season', 2024, type=int)
        config = request.args.get('config', 'comprehensive')
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get season ID
        cursor.execute('SELECT id FROM seasons WHERE season_year = ?', (season,))
        season_row = cursor.fetchone()
        if not season_row:
            return jsonify({'error': f'Season {season} not found'}), 404
        
        season_id = season_row['id']
        
        # Get latest ratings for each team in the season (only the most recent entry per team)
        cursor.execute('''
            SELECT t.team_name, t.abbreviation, t.city, t.conference, t.division,
                   tr.rating, tr.rating_change, tr.wins, tr.losses, tr.ties,
                   tr.win_percentage, tr.points_for, tr.points_against,
                   tr.point_differential, tr.strength_of_schedule
            FROM team_ratings tr
            JOIN teams t ON tr.team_id = t.id
            WHERE tr.season_id = ?
            AND tr.id IN (
                SELECT MAX(tr2.id) 
                FROM team_ratings tr2 
                WHERE tr2.team_id = tr.team_id 
                AND tr2.season_id = ?
            )
            ORDER BY tr.rating DESC
        ''', (season_id, season_id))
        
        ratings = []
        for row in cursor.fetchall():
            ratings.append({
                'team': {
                    'name': row['team_name'],
                    'abbreviation': row['abbreviation'],
                    'city': row['city'],
                    'conference': row['conference'],
                    'division': row['division']
                },
                'rating': row['rating'],
                'rating_change': row['rating_change'],
                'record': {
                    'wins': row['wins'],
                    'losses': row['losses'],
                    'ties': row['ties'],
                    'win_percentage': row['win_percentage']
                },
                'stats': {
                    'points_for': row['points_for'],
                    'points_against': row['points_against'],
                    'point_differential': row['point_differential'],
                    'strength_of_schedule': row['strength_of_schedule']
                }
            })
        
        conn.close()
        return jsonify({'season': season, 'ratings': ratings})
        
    except Exception as e:
        logger.error(f"Error getting ELO ratings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elo/teams/<team>/history', methods=['GET'])
def get_team_elo_history(team):
    """Get ELO history for a specific team."""
    try:
        seasons = request.args.getlist('seasons', type=int)
        if not seasons:
            seasons = [2024]  # Default to current season
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get team ID
        cursor.execute('SELECT id FROM teams WHERE abbreviation = ? OR team_name = ?', (team, team))
        team_row = cursor.fetchone()
        if not team_row:
            return jsonify({'error': f'Team {team} not found'}), 404
        
        team_id = team_row['id']
        
        # Get season IDs
        placeholders = ','.join(['?' for _ in seasons])
        cursor.execute(f'SELECT id, season_year FROM seasons WHERE season_year IN ({placeholders})', seasons)
        season_data = {row['season_year']: row['id'] for row in cursor.fetchall()}
        
        history = []
        for season in seasons:
            if season not in season_data:
                continue
                
            season_id = season_data[season]
            cursor.execute('''
                SELECT week, rating, rating_change, wins, losses, ties, win_percentage
                FROM team_ratings
                WHERE team_id = ? AND season_id = ?
                ORDER BY week
            ''', (team_id, season_id))
            
            season_history = []
            for row in cursor.fetchall():
                season_history.append({
                    'week': row['week'],
                    'rating': row['rating'],
                    'rating_change': row['rating_change'],
                    'record': {
                        'wins': row['wins'],
                        'losses': row['losses'],
                        'ties': row['ties'],
                        'win_percentage': row['win_percentage']
                    }
                })
            
            if season_history:
                history.append({
                    'season': season,
                    'data': season_history
                })
        
        conn.close()
        return jsonify({'team': team, 'history': history})
        
    except Exception as e:
        logger.error(f"Error getting team ELO history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elo/recalculate', methods=['POST'])
def recalculate_elo_ratings():
    """Recalculate ELO ratings for all teams."""
    try:
        # This would trigger the ELO calculation process
        # For now, just return a success message
        return jsonify({
            'message': 'ELO recalculation triggered',
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error recalculating ELO ratings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elo/season-summary', methods=['GET'])
def get_elo_season_summary():
    """Get ELO season summary statistics."""
    try:
        season = request.args.get('season', 2024, type=int)
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get season ID
        cursor.execute('SELECT id FROM seasons WHERE season_year = ?', (season,))
        season_row = cursor.fetchone()
        if not season_row:
            return jsonify({'error': f'Season {season} not found'}), 404
        
        season_id = season_row['id']
        
        # Get basic season statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_teams,
                AVG(rating) as avg_rating,
                MIN(rating) as min_rating,
                MAX(rating) as max_rating,
                SUM(wins) as total_wins,
                SUM(losses) as total_losses,
                SUM(ties) as total_ties
            FROM team_ratings tr
            WHERE tr.season_id = ?
        ''', (season_id,))
        
        stats = cursor.fetchone()
        
        # Get rating distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN rating >= 1800 THEN 'Elite'
                    WHEN rating >= 1600 THEN 'Good'
                    WHEN rating >= 1400 THEN 'Average'
                    ELSE 'Below Average'
                END as tier,
                COUNT(*) as count
            FROM team_ratings tr
            WHERE tr.season_id = ?
            GROUP BY tier
            ORDER BY AVG(rating) DESC
        ''', (season_id,))
        
        distribution = [{'tier': row['tier'], 'count': row['count']} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'season': season,
            'summary': {
                'total_teams': stats['total_teams'],
                'avg_rating': round(stats['avg_rating'], 2),
                'min_rating': stats['min_rating'],
                'max_rating': stats['max_rating'],
                'total_games': stats['total_wins'] + stats['total_losses'] + stats['total_ties'],
                'rating_distribution': distribution
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting ELO season summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elo/projections/<int:season>/<int:week>', methods=['GET'])
def get_elo_projections(season, week):
    """Get ELO projections for a specific season and week."""
    try:
        # For now, return empty projections since we don't have projection data
        # This endpoint can be implemented later when projection data is available
        return jsonify({
            'season': season,
            'week': week,
            'projections': [],
            'message': 'Projections not yet implemented'
        })
        
    except Exception as e:
        logger.error(f"Error getting ELO projections: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/elo/compare', methods=['GET'])
def get_elo_team_comparison():
    """Compare ELO ratings between multiple teams."""
    try:
        teams = request.args.getlist('teams')
        season = request.args.get('season', 2024, type=int)
        
        if not teams:
            return jsonify({'error': 'No teams specified'}), 400
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get season ID
        cursor.execute('SELECT id FROM seasons WHERE season_year = ?', (season,))
        season_row = cursor.fetchone()
        if not season_row:
            return jsonify({'error': f'Season {season} not found'}), 404
        
        season_id = season_row['id']
        
        # Get ratings for specified teams
        placeholders = ','.join(['?' for _ in teams])
        cursor.execute(f'''
            SELECT t.team_name, t.abbreviation, t.city, t.conference, t.division,
                   tr.rating, tr.rating_change, tr.wins, tr.losses, tr.ties,
                   tr.win_percentage, tr.points_for, tr.points_against,
                   tr.point_differential, tr.strength_of_schedule
            FROM team_ratings tr
            JOIN teams t ON tr.team_id = t.id
            WHERE tr.season_id = ? AND t.abbreviation IN ({placeholders})
            ORDER BY tr.rating DESC
        ''', [season_id] + teams)
        
        teams_data = []
        for row in cursor.fetchall():
            teams_data.append({
                'team': {
                    'name': row['team_name'],
                    'abbreviation': row['abbreviation'],
                    'city': row['city'],
                    'conference': row['conference'],
                    'division': row['division']
                },
                'rating': row['rating'],
                'rating_change': row['rating_change'],
                'record': {
                    'wins': row['wins'],
                    'losses': row['losses'],
                    'ties': row['ties'],
                    'win_percentage': row['win_percentage']
                },
                'stats': {
                    'points_for': row['points_for'],
                    'points_against': row['points_against'],
                    'point_differential': row['point_differential'],
                    'strength_of_schedule': row['strength_of_schedule']
                }
            })
        
        conn.close()
        
        return jsonify({
            'season': season,
            'teams': teams_data,
            'comparison': {
                'highest_rated': max(teams_data, key=lambda x: x['rating']) if teams_data else None,
                'lowest_rated': min(teams_data, key=lambda x: x['rating']) if teams_data else None,
                'rating_spread': max([t['rating'] for t in teams_data]) - min([t['rating'] for t in teams_data]) if teams_data else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting ELO team comparison: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# DASHBOARD AND ANALYTICS ENDPOINTS
# ============================================================================

@app.route('/api/sports/<sport>/dashboard', methods=['GET'])
def get_sport_dashboard(sport):
    """Get dashboard data for a specific sport."""
    try:
        if not api_server.validate_sport(sport):
            return jsonify({'error': f'Unsupported sport: {sport}'}), 400
        
        sport_id = api_server.get_sport_id(sport)
        if not sport_id:
            return jsonify({'error': f'Sport not found: {sport}'}), 404
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get live games
        cursor.execute('''
            SELECT g.id, g.game_status, g.quarter, g.time_remaining,
                   g.home_score, g.away_score, g.home_win_prob, g.away_win_prob,
                   ht.team_name as home_team, at.team_name as away_team
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            WHERE g.sport_id = ? AND g.game_status = 'in_progress'
            ORDER BY g.game_date
        ''', (sport_id,))
        
        live_games = []
        for row in cursor.fetchall():
            live_games.append({
                'id': row['id'],
                'status': row['game_status'],
                'quarter': row['quarter'],
                'time_remaining': row['time_remaining'],
                'home_team': {
                    'name': row['home_team'],
                    'score': row['home_score'],
                    'win_prob': row['home_win_prob']
                },
                'away_team': {
                    'name': row['away_team'],
                    'score': row['away_score'],
                    'win_prob': row['away_win_prob']
                }
            })
        
        # Get upcoming games
        cursor.execute('''
            SELECT g.id, g.game_date, g.game_time_local, g.home_win_prob, g.away_win_prob,
                   ht.team_name as home_team, at.team_name as away_team
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            WHERE g.sport_id = ? AND g.game_status = 'scheduled'
            ORDER BY g.game_date
            LIMIT 10
        ''', (sport_id,))
        
        upcoming_games = []
        for row in cursor.fetchall():
            upcoming_games.append({
                'id': row['id'],
                'date': row['game_date'],
                'time_local': row['game_time_local'],
                'home_team': {
                    'name': row['home_team'],
                    'win_prob': row['home_win_prob']
                },
                'away_team': {
                    'name': row['away_team'],
                    'win_prob': row['away_win_prob']
                }
            })
        
        # Get top experts
        cursor.execute('''
            SELECT e.id, e.name, e.username, e.is_verified,
                   COUNT(p.id) as total_picks,
                   SUM(CASE WHEN p.result = 'win' THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN p.result = 'loss' THEN 1 ELSE 0 END) as losses,
                   AVG(p.units_net) as avg_units
            FROM experts e
            JOIN expert_picks p ON e.id = p.expert_id
            WHERE p.sport_id = ? AND p.result IN ('win', 'loss')
            GROUP BY e.id, e.name, e.username, e.is_verified
            HAVING total_picks >= 5
            ORDER BY (wins * 1.0 / (wins + losses)) DESC, total_picks DESC
            LIMIT 10
        ''', (sport_id,))
        
        top_experts = []
        for row in cursor.fetchall():
            win_rate = (row['wins'] * 1.0 / (row['wins'] + row['losses'])) if (row['wins'] + row['losses']) > 0 else 0
            top_experts.append({
                'id': row['id'],
                'name': row['name'],
                'username': row['username'],
                'verified': bool(row['is_verified']),
                'stats': {
                    'total_picks': row['total_picks'],
                    'wins': row['wins'],
                    'losses': row['losses'],
                    'win_rate': round(win_rate * 100, 1),
                    'avg_units': round(row['avg_units'] or 0, 2)
                }
            })
        
        dashboard_data = {
            'sport': sport,
            'live_games': live_games,
            'upcoming_games': upcoming_games,
            'top_experts': top_experts,
            'timestamp': datetime.now().isoformat()
        }
        
        conn.close()
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard for {sport}: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HEALTH AND STATUS ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Check database connectivity
        cursor.execute("SELECT COUNT(*) FROM sports")
        sports_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM teams")
        teams_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM games")
        games_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'stats': {
                'sports': sports_count,
                'teams': teams_count,
                'games': games_count
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/sports/<sport>/standings', methods=['GET'])
def get_standings(sport):
    """Get team standings for a specific sport."""
    try:
        if not api_server.validate_sport(sport):
            return jsonify({'error': f'Unsupported sport: {sport}'}), 400
        
        sport_id = api_server.get_sport_id(sport)
        if not sport_id:
            return jsonify({'error': f'Sport not found: {sport}'}), 404
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get teams with their win/loss records
        cursor.execute('''
            SELECT 
                t.id,
                t.team_name,
                t.abbreviation,
                t.conference,
                t.division,
                t.city,
                COALESCE(SUM(CASE 
                    WHEN g.home_team_id = t.id AND g.home_score > g.away_score THEN 1
                    WHEN g.away_team_id = t.id AND g.away_score > g.home_score THEN 1
                    ELSE 0
                END), 0) as wins,
                COALESCE(SUM(CASE 
                    WHEN g.home_team_id = t.id AND g.home_score < g.away_score THEN 1
                    WHEN g.away_team_id = t.id AND g.away_score < g.home_score THEN 1
                    ELSE 0
                END), 0) as losses,
                COALESCE(SUM(CASE 
                    WHEN g.home_team_id = t.id AND g.home_score = g.away_score THEN 1
                    WHEN g.away_team_id = t.id AND g.away_score = g.home_score THEN 1
                    ELSE 0
                END), 0) as ties
            FROM teams t
            LEFT JOIN games g ON (g.home_team_id = t.id OR g.away_team_id = t.id) 
                AND g.sport_id = t.sport_id 
                AND g.game_status = 'final'
            WHERE t.sport_id = ? AND t.active = 1
            GROUP BY t.id, t.team_name, t.abbreviation, t.conference, t.division, t.city
            ORDER BY wins DESC, losses ASC, ties ASC
        ''', (sport_id,))
        
        teams = []
        for row in cursor.fetchall():
            wins = row['wins'] or 0
            losses = row['losses'] or 0
            ties = row['ties'] or 0
            total_games = wins + losses + ties
            win_percentage = (wins + ties * 0.5) / total_games if total_games > 0 else 0
            
            teams.append({
                'id': row['id'],
                'team_name': row['team_name'],
                'abbreviation': row['abbreviation'],
                'city': row['city'],
                'conference': row['conference'],
                'division': row['division'],
                'wins': wins,
                'losses': losses,
                'ties': ties,
                'win_percentage': round(win_percentage, 3),
                'total_games': total_games
            })
        
        conn.close()
        return jsonify({'sport': sport, 'standings': teams})
        
    except Exception as e:
        logger.error(f"Error getting standings for {sport}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sports/<sport>/schedule', methods=['GET'])
def get_sport_schedule(sport):
    """Get schedule for a specific sport with week filtering."""
    try:
        if not api_server.validate_sport(sport):
            return jsonify({'error': f'Unsupported sport: {sport}'}), 400
        
        sport_id = api_server.get_sport_id(sport)
        if not sport_id:
            return jsonify({'error': f'Sport not found: {sport}'}), 404
        
        # Get query parameters
        week = request.args.get('week', type=int)
        season = request.args.get('season', 2025, type=int)
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get season ID
        cursor.execute("SELECT id FROM seasons WHERE sport_id = ? AND season_year = ?", (sport_id, season))
        season_result = cursor.fetchone()
        if not season_result:
            return jsonify({'error': f'Season {season} not found for {sport}'}), 404
        
        season_id = season_result[0]
        
        # Build query with optional week filter
        # Filter by both season_id and actual game date year to ensure we get the right season
        base_query = '''
            SELECT g.id, g.external_game_id, g.game_date, g.game_time_local, g.game_status,
                   g.home_score, g.away_score, g.quarter, g.time_remaining,
                   g.home_win_prob, g.away_win_prob, g.week,
                   ht.id as home_team_id, ht.team_name as home_team_name, ht.abbreviation as home_team_abbr,
                   at.id as away_team_id, at.team_name as away_team_name, at.abbreviation as away_team_abbr,
                   g.venue as venue_name, g.venue_city, g.venue_state
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            WHERE g.sport_id = ? AND g.season_id = ? AND strftime('%Y', g.game_date) = ?
        '''
        
        params = [sport_id, season_id, str(season)]
        
        if week:
            base_query += ' AND g.week = ?'
            params.append(week)
        
        base_query += ' ORDER BY g.game_date, g.game_time_local'
        
        cursor.execute(base_query, params)
        
        games = []
        for row in cursor.fetchall():
            games.append({
                'id': row['id'],
                'external_id': row['external_game_id'],
                'week': row['week'],
                'date': row['game_date'],
                'time_local': row['game_time_local'],
                'status': row['game_status'],
                'home_team': {
                    'id': row['home_team_id'],
                    'name': row['home_team_name'],
                    'abbreviation': row['home_team_abbr']
                },
                'away_team': {
                    'id': row['away_team_id'],
                    'name': row['away_team_name'],
                    'abbreviation': row['away_team_abbr']
                },
                'home_score': row['home_score'],
                'away_score': row['away_score'],
                'quarter': row['quarter'],
                'time_remaining': row['time_remaining'],
                'home_win_prob': row['home_win_prob'],
                'away_win_prob': row['away_win_prob'],
                'venue': {
                    'name': row['venue_name'],
                    'city': row['venue_city'],
                    'state': row['venue_state']
                } if row['venue_name'] else None
            })
        
        conn.close()
        return jsonify({
            'sport': sport,
            'season': season,
            'week': week,
            'games': games,
            'total_games': len(games)
        })
        
    except Exception as e:
        logger.error(f"Error getting schedule for {sport}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sports/<sport>/schedule-with-picks', methods=['GET'])
def get_sport_schedule_with_picks(sport):
    """Get schedule for a specific sport with expert picks included."""
    try:
        if not api_server.validate_sport(sport):
            return jsonify({'error': f'Unsupported sport: {sport}'}), 400
        
        sport_id = api_server.get_sport_id(sport)
        if not sport_id:
            return jsonify({'error': f'Sport not found: {sport}'}), 404
        
        # Get query parameters
        week = request.args.get('week', type=int)
        season = request.args.get('season', 2025, type=int)
        
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get season ID
        cursor.execute("SELECT id FROM seasons WHERE sport_id = ? AND season_year = ?", (sport_id, season))
        season_result = cursor.fetchone()
        if not season_result:
            return jsonify({'error': f'Season {season} not found for {sport}'}), 404
        
        season_id = season_result[0]
        
        # Build query for games
        base_query = '''
            SELECT g.id, g.external_game_id, g.game_date, g.game_time_local, g.game_status,
                   g.home_score, g.away_score, g.quarter, g.time_remaining,
                   g.home_win_prob, g.away_win_prob, g.week,
                   ht.id as home_team_id, ht.team_name as home_team_name, ht.abbreviation as home_team_abbr,
                   at.id as away_team_id, at.team_name as away_team_name, at.abbreviation as away_team_abbr,
                   g.venue as venue_name, g.venue_city, g.venue_state
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            WHERE g.sport_id = ? AND g.season_id = ? AND strftime('%Y', g.game_date) = ?
        '''
        
        params = [sport_id, season_id, str(season)]
        
        if week:
            base_query += ' AND g.week = ?'
            params.append(week)
        
        base_query += ' ORDER BY g.game_date, g.game_time_local'
        
        cursor.execute(base_query, params)
        
        games = []
        for row in cursor.fetchall():
            game_data = {
                'id': row['id'],
                'external_id': row['external_game_id'],
                'week': row['week'],
                'date': row['game_date'],
                'time_local': row['game_time_local'],
                'status': row['game_status'],
                'home_team': {
                    'id': row['home_team_id'],
                    'name': row['home_team_name'],
                    'abbreviation': row['home_team_abbr']
                },
                'away_team': {
                    'id': row['away_team_id'],
                    'name': row['away_team_name'],
                    'abbreviation': row['away_team_abbr']
                },
                'home_score': row['home_score'],
                'away_score': row['away_score'],
                'quarter': row['quarter'],
                'time_remaining': row['time_remaining'],
                'home_win_prob': row['home_win_prob'],
                'away_win_prob': row['away_win_prob'],
                'venue': {
                    'name': row['venue_name'],
                    'city': row['venue_city'],
                    'state': row['venue_state']
                } if row['venue_name'] else None,
                'expert_picks': []
            }
            
            # Get expert picks for this game (by team names or external game ID)
            cursor.execute('''
                SELECT p.id, p.play_description, p.pick_type, p.value, p.odds, p.units, p.confidence_level,
                       p.reasoning, p.result, p.verified,
                       e.name as expert_name, e.username as expert_username, e.is_verified as expert_verified
                FROM expert_picks p
                JOIN experts e ON p.expert_id = e.id
                WHERE p.sport_id = ? AND p.result = 'pending'
                AND (p.play_description LIKE ? OR p.play_description LIKE ? OR p.play_description LIKE ?)
                ORDER BY p.created_at DESC
                LIMIT 5
            ''', (
                sport_id,
                f"%{row['home_team_abbr']}%",
                f"%{row['away_team_abbr']}%",
                f"%{row['home_team_name']}%"
            ))
            
            picks = []
            for pick_row in cursor.fetchall():
                picks.append({
                    'id': pick_row['id'],
                    'description': pick_row['play_description'],
                    'pick_type': pick_row['pick_type'],
                    'value': pick_row['value'],
                    'odds': pick_row['odds'],
                    'units': pick_row['units'],
                    'confidence_level': pick_row['confidence_level'],
                    'reasoning': pick_row['reasoning'],
                    'result': pick_row['result'],
                    'verified': pick_row['verified'],
                    'expert': {
                        'name': pick_row['expert_name'],
                        'username': pick_row['expert_username'],
                        'verified': pick_row['expert_verified']
                    }
                })
            
            game_data['expert_picks'] = picks
            games.append(game_data)
        
        conn.close()
        return jsonify({
            'sport': sport,
            'season': season,
            'week': week,
            'games': games,
            'total_games': len(games)
        })
        
    except Exception as e:
        logger.error(f"Error getting schedule with picks for {sport}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status and statistics."""
    try:
        conn = api_server.get_connection()
        cursor = conn.cursor()
        
        # Get overall statistics
        cursor.execute("SELECT sport_code, sport_name FROM sports")
        sports = [{'code': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        stats = {}
        for sport in sports:
            sport_id = api_server.get_sport_id(sport['code'])
            if sport_id:
                cursor.execute("SELECT COUNT(*) FROM teams WHERE sport_id = ?", (sport_id,))
                teams_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM games WHERE sport_id = ?", (sport_id,))
                games_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM expert_picks WHERE sport_id = ?", (sport_id,))
                picks_count = cursor.fetchone()[0]
                
                stats[sport['code']] = {
                    'teams': teams_count,
                    'games': games_count,
                    'picks': picks_count
                }
        
        conn.close()
        
        return jsonify({
            'sports': sports,
            'statistics': stats,
            'supported_sports': api_server.supported_sports,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Enhanced Multi-Sport API Server...")
    print(f"📊 Database: {api_server.db_path}")
    print(f"🏆 Supported Sports: {', '.join(api_server.supported_sports)}")
    print("🌐 Server running on http://localhost:5001")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
