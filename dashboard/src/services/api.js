import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
  // System status
  getSystemStatus: () => api.get('/api/system/status'),
  
  // Team data
  getTeamRankings: () => api.get('/api/teams/rankings'),
  getTeamDetails: (teamId) => api.get(`/api/teams/${teamId}`),
  
  // Predictions
  getGamePrediction: (homeTeam, awayTeam) => 
    api.get(`/api/predictions/game/${homeTeam}/${awayTeam}`),
  getWeekPredictions: (week) => api.get(`/api/predictions/week/${week}`),
  
  // Performance metrics
  getPerformanceMetrics: () => api.get('/api/metrics/performance'),
  getSystemHealth: () => api.get('/api/system/health'),
  
  // Historical data
  getHistoricalData: (startDate, endDate) => 
    api.get(`/api/historical?start=${startDate}&end=${endDate}`),
  getTeamHistory: (teamId) => api.get(`/api/teams/${teamId}/history`),
  
  // Configuration
  getConfiguration: () => api.get('/api/config'),
  updateConfiguration: (config) => api.put('/api/config', config),
  
  // Action Network endpoints
  getActionNetworkExperts: (league = 'nfl', limit = 50) => 
    api.get(`/api/action-network/experts?league=${league}&limit=${limit}`),
  getActionNetworkExpertDetails: (expertId) => 
    api.get(`/api/action-network/experts/${expertId}`),
  getActionNetworkPicks: (league = 'nfl', limit = 100, expertId = null, result = 'all') => {
    let url = `/api/action-network/picks?league=${league}&limit=${limit}`;
    if (expertId) url += `&expert_id=${expertId}`;
    if (result !== 'all') url += `&result=${result}`;
    return api.get(url);
  },
  getActionNetworkAnalytics: (league = 'nfl') => 
    api.get(`/api/action-network/analytics?league=${league}`),
  getActionNetworkTeams: () => 
    api.get('/api/action-network/teams'),
  
  // System monitoring
  getCronStatus: () => 
    api.get('/api/system/cron-status'),

  // ELO Ratings endpoints
  getEloSeasons: () => api.get('/api/elo/seasons'),
  getEloRatings: (season = 2024, config = 'baseline') =>
    api.get(`/api/elo/ratings?season=${season}&config=${config}`),
  getTeamEloHistory: (team, seasons = [2020, 2021, 2022, 2023, 2024]) => {
    const seasonParams = seasons.map(s => `seasons=${s}`).join('&');
    return api.get(`/api/elo/team/${team}?${seasonParams}`);
  },
  getEloSeasonSummary: (season = 2024) =>
    api.get(`/api/elo/season-summary?season=${season}`),
  getEloTeamComparison: (teams, season = 2024) => {
    const teamParams = teams.map(t => `teams=${t}`).join('&');
    return api.get(`/api/elo/compare?${teamParams}&season=${season}`);
  },
};

export default api;
