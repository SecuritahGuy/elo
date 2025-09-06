import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    return Promise.reject(error);
  }
);

// API endpoints
export const apiService = {
  // NFL-specific endpoints
  getNFLTeams: () => api.get('/api/sports/nfl/teams'),
  getNFLGames: () => api.get('/api/sports/nfl/games'),
  getNFLDashboard: () => api.get('/api/sports/nfl/dashboard'),
  getNFLStandings: () => api.get('/api/sports/nfl/standings'),
  getNFLSchedule: (week = null, season = 2025) => {
    const params = new URLSearchParams();
    if (week) params.append('week', week);
    params.append('season', season);
    return api.get(`/api/sports/nfl/schedule?${params.toString()}`);
  },
  getNFLScheduleWithPicks: (week = null, season = 2025) => {
    const params = new URLSearchParams();
    if (week) params.append('week', week);
    params.append('season', season);
    return api.get(`/api/sports/nfl/schedule-with-picks?${params.toString()}`);
  },
  
  // Multi-sport endpoints (for expert picks only)
  getSports: () => api.get('/api/sports'),
  getSportExpertPicks: (sport) => api.get(`/api/sports/${sport}/expert-picks`),
  
  // System status
  getSystemStatus: () => api.get('/api/status'),
  
  // Team data
  getTeamRankings: () => api.get('/api/teams/rankings'),
  getTeamDetails: (teamId) => api.get(`/api/teams/${teamId}`),
  
  // Predictions
  getGamePrediction: (homeTeam, awayTeam) => 
    api.get(`/api/predictions/game/${homeTeam}/${awayTeam}`),
  getWeekPredictions: (week) => api.get(`/api/predictions/week/${week}`),
  
  // Performance metrics
  getPerformanceMetrics: () => api.get('/api/metrics/performance'),
  getSystemHealth: () => api.get('/api/health'),
  
  // Historical data
  getHistoricalData: (startDate, endDate) => 
    api.get(`/api/historical?start=${startDate}&end=${endDate}`),
  getTeamHistory: (teamId) => api.get(`/api/teams/${teamId}/history`),
  
  // Configuration
  getConfiguration: () => api.get('/api/config'),
  updateConfiguration: (config) => api.put('/api/config', config),
  
  // Action Network endpoints (using multi-sport API)
  getActionNetworkExperts: (sport = 'nfl', limit = 50) => 
    api.get(`/api/sports/${sport}/expert-picks?limit=${limit}`),
  getActionNetworkExpertDetails: (expertId) => 
    api.get(`/api/action-network/experts/${expertId}`),
  getActionNetworkPicks: (sport = 'nfl', limit = 100, expertId = null, result = 'all') => {
    let url = `/api/sports/${sport}/expert-picks?limit=${limit}`;
    if (expertId) url += `&expert_id=${expertId}`;
    if (result !== 'all') url += `&result=${result}`;
    return api.get(url);
  },
  getActionNetworkAnalytics: (sport = 'nfl') => 
    api.get(`/api/sports/${sport}/expert-picks?analytics=true`),
  getActionNetworkTeams: (sport = 'nfl') => 
    api.get(`/api/sports/${sport}/teams`),
  
  // System monitoring
  getCronStatus: () => 
    api.get('/api/system/cron-status'),

  // ELO Ratings endpoints
  getEloSeasons: () => {
    const timestamp = Date.now(); // Cache busting
    return api.get(`/api/elo/seasons?_t=${timestamp}`);
  },
  getEloRatings: (season = 2024, config = 'comprehensive') => {
    // Use the real API for all seasons including 2025
    const timestamp = Date.now(); // Cache busting
    return api.get(`/api/elo/ratings?season=${season}&config=${config}&_t=${timestamp}`);
  },
  getTeamEloHistory: (team, seasons = [2020, 2021, 2022, 2023, 2024]) => {
    const seasonParams = seasons.map(s => `seasons=${s}`).join('&');
    const timestamp = Date.now(); // Cache busting
    return api.get(`/api/elo/teams/${team}/history?${seasonParams}&_t=${timestamp}`);
  },
  getEloSeasonSummary: (season = 2024) => {
    return api.get(`/api/elo/season-summary?season=${season}`);
  },
  
  // ELO Projections
  getEloProjections: (season, week) => {
    return api.get(`/api/elo/projections/${season}/${week}`);
  },
  getTeamEloProjections: (team, season) => {
    return api.get(`/api/elo/projections/team/${team}/${season}`);
  },
  generateEloProjections: (season, currentWeek) => {
    return api.post('/api/elo/projections/generate', {
      season,
      current_week: currentWeek
    });
  },
  
  getEloTeamComparison: (teams, season = 2024) => {
    const teamParams = teams.map(t => `teams=${t}`).join('&');
    return api.get(`/api/elo/compare?${teamParams}&season=${season}`);
  },

  // Injury Data endpoints
  getTeamInjuries: (season = 2025, week = 1) =>
    api.get(`/api/injuries/teams?season=${season}&week=${week}`),
  getTeamInjuryHistory: (team, season = 2025, weeks = []) => {
    const weekParams = weeks.length > 0 ? weeks.map(w => `weeks=${w}`).join('&') : '';
    return api.get(`/api/injuries/team/${team}?season=${season}&${weekParams}`);
  },
  getPlayerInjuries: (season = 2025, week = 1, team = null) => {
    const params = new URLSearchParams({ season, week });
    if (team) params.append('team', team);
    return api.get(`/api/injuries/players?${params}`);
  },
  getInjurySummary: (season = 2025) =>
    api.get(`/api/injuries/summary?season=${season}`),

  // Team Detail endpoints
  getTeamRoster: (team, season = 2024) =>
    api.get(`/api/teams/${team}/roster?season=${season}`),
  getTeamGames: (team, season = 2024, week = null) => {
    const params = new URLSearchParams({ season });
    if (week) params.append('week', week);
    return api.get(`/api/teams/${team}/games?${params}`);
  },
  getTeamAnalysis: (team, season = 2024) =>
    api.get(`/api/teams/${team}/analysis?season=${season}`),

  // ELO Management endpoints
  recalculateEloRatings: () =>
    api.post('/api/elo/recalculate'),

  // Live game tracking endpoints
  getLiveGames: () => 
    api.get('/api/live/games'),
  
  getLiveGame: (gameId) => 
    api.get(`/api/live/games/${gameId}`),
  
  getLiveGameStats: (gameId) => 
    api.get(`/api/live/games/${gameId}/stats`),
  
  getLiveGamePredictions: (gameId) => 
    api.get(`/api/live/games/${gameId}/predictions`),
};

export default apiService;
