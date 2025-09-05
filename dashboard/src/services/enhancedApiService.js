import axios from 'axios';
import cacheService from './cacheService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
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

// Enhanced API service with caching
export const enhancedApiService = {
  // System status
  getSystemStatus: () => {
    const cacheKey = cacheService.generateKey('system', 'status');
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: system status');
      return Promise.resolve({ data: cached });
    }

    return api.get('/api/system/status').then(response => {
      cacheService.set(cacheKey, response.data, 2 * 60 * 1000); // 2 minutes
      return response;
    });
  },

  // Team data with caching
  getTeamRankings: () => {
    const cacheKey = cacheService.generateKey('teams', 'rankings');
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: team rankings');
      return Promise.resolve({ data: cached });
    }

    return api.get('/api/teams/rankings').then(response => {
      cacheService.set(cacheKey, response.data, 5 * 60 * 1000); // 5 minutes
      return response;
    });
  },

  getTeamDetails: (teamId) => {
    const cacheKey = cacheService.generateKey('team', 'details', teamId);
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: team details', teamId);
      return Promise.resolve({ data: cached });
    }

    return api.get(`/api/teams/${teamId}`).then(response => {
      cacheService.set(cacheKey, response.data, 10 * 60 * 1000); // 10 minutes
      return response;
    });
  },

  // ELO Ratings with intelligent caching
  getEloSeasons: () => {
    const cacheKey = cacheService.generateKey('elo', 'seasons');
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: ELO seasons');
      return Promise.resolve({ data: cached });
    }

    return api.get('/api/elo/seasons').then(response => {
      cacheService.set(cacheKey, response.data, 30 * 60 * 1000); // 30 minutes
      return response;
    });
  },

  getEloRatings: (season = 2024, config = 'baseline') => {
    const cacheKey = cacheService.generateKey('elo', 'ratings', season, config);
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: ELO ratings', season, config);
      return Promise.resolve({ data: cached });
    }

    return api.get(`/api/elo/ratings?season=${season}&config=${config}`).then(response => {
      cacheService.set(cacheKey, response.data, 5 * 60 * 1000); // 5 minutes
      return response;
    });
  },

  getTeamEloHistory: (team, seasons) => {
    const cacheKey = cacheService.generateKey('elo', 'team-history', team, seasons.join(','));
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: team ELO history', team);
      return Promise.resolve({ data: cached });
    }

    const seasonParams = seasons.map(s => `seasons=${s}`).join('&');
    return api.get(`/api/elo/team/${team}?${seasonParams}`).then(response => {
      cacheService.set(cacheKey, response.data, 10 * 60 * 1000); // 10 minutes
      return response;
    });
  },

  getTeamComparison: (teams, season = 2024) => {
    const cacheKey = cacheService.generateKey('elo', 'comparison', teams.join(','), season);
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: team comparison', teams);
      return Promise.resolve({ data: cached });
    }

    const teamParams = teams.map(t => `teams=${t}`).join('&');
    return api.get(`/api/elo/compare?${teamParams}&season=${season}`).then(response => {
      cacheService.set(cacheKey, response.data, 5 * 60 * 1000); // 5 minutes
      return response;
    });
  },

  // Injury Data with caching
  getTeamInjuries: (season = 2025, week = 1) => {
    const cacheKey = cacheService.generateKey('injuries', 'teams', season, week);
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: team injuries', season, week);
      return Promise.resolve({ data: cached });
    }

    return api.get(`/api/injuries/teams?season=${season}&week=${week}`).then(response => {
      cacheService.set(cacheKey, response.data, 2 * 60 * 1000); // 2 minutes
      return response;
    });
  },

  getInjurySummary: (season = 2025) => {
    const cacheKey = cacheService.generateKey('injuries', 'summary', season);
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: injury summary', season);
      return Promise.resolve({ data: cached });
    }

    return api.get(`/api/injuries/summary?season=${season}`).then(response => {
      cacheService.set(cacheKey, response.data, 5 * 60 * 1000); // 5 minutes
      return response;
    });
  },

  // Team Detail APIs with caching
  getTeamRoster: (team, season = 2024) => {
    const cacheKey = cacheService.generateKey('team', 'roster', team, season);
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: team roster', team, season);
      return Promise.resolve({ data: cached });
    }

    return api.get(`/api/teams/${team}/roster?season=${season}`).then(response => {
      cacheService.set(cacheKey, response.data, 15 * 60 * 1000); // 15 minutes
      return response;
    });
  },

  getTeamGames: (team, season = 2024, week = null) => {
    const cacheKey = cacheService.generateKey('team', 'games', team, season, week);
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: team games', team, season, week);
      return Promise.resolve({ data: cached });
    }

    const params = new URLSearchParams({ season });
    if (week) params.append('week', week);
    return api.get(`/api/teams/${team}/games?${params}`).then(response => {
      cacheService.set(cacheKey, response.data, 10 * 60 * 1000); // 10 minutes
      return response;
    });
  },

  getTeamAnalysis: (team, season = 2024) => {
    const cacheKey = cacheService.generateKey('team', 'analysis', team, season);
    const cached = cacheService.get(cacheKey);
    
    if (cached) {
      console.log('Cache hit: team analysis', team, season);
      return Promise.resolve({ data: cached });
    }

    return api.get(`/api/teams/${team}/analysis?season=${season}`).then(response => {
      cacheService.set(cacheKey, response.data, 20 * 60 * 1000); // 20 minutes
      return response;
    });
  },

  // Cache management
  clearCache: () => {
    cacheService.clear();
    console.log('Cache cleared');
  },

  getCacheStats: () => {
    return cacheService.getStats();
  },

  // Force refresh (bypass cache)
  forceRefresh: (apiCall) => {
    return apiCall();
  }
};

export default enhancedApiService;
