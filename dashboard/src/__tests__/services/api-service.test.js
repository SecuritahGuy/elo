/**
 * Comprehensive API Service Tests
 * Tests all API endpoints and error handling
 */

import '@testing-library/jest-dom';
import axios from 'axios';
import { apiService } from '../../services/api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

describe('API Service Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('ELO Ratings API', () => {
    it('should fetch ELO ratings with default parameters', async () => {
      const mockResponse = {
        data: {
          ratings: [
            { team: 'KC', rating: 1500, rank: 1 },
            { team: 'BUF', rating: 1490, rank: 2 }
          ],
          season: 2024,
          config: 'comprehensive'
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getEloRatings();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/elo/ratings?season=2024&config=comprehensive');
      expect(response.data.ratings).toHaveLength(2);
    });

    it('should fetch ELO ratings with custom parameters', async () => {
      const mockResponse = { data: { ratings: [] } };
      mockedAxios.get.mockResolvedValue(mockResponse);

      await apiService.getEloRatings(2025, 'baseline');

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/elo/ratings?season=2025&config=baseline');
    });

    it('should handle ELO ratings API errors', async () => {
      const error = new Error('API Error');
      mockedAxios.get.mockRejectedValue(error);

      await expect(apiService.getEloRatings()).rejects.toThrow('API Error');
    });
  });

  describe('Team ELO History API', () => {
    it('should fetch team ELO history', async () => {
      const mockResponse = {
        data: {
          elo_history: [
            { week: 1, rating: 1500, change: 0 },
            { week: 2, rating: 1510, change: 10 }
          ]
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getTeamEloHistory('KC', [2024, 2025]);

      expect(mockedAxios.get).toHaveBeenCalledWith(expect.stringMatching(/\/api\/elo\/teams\/KC\/history\?seasons=2024&seasons=2025&_t=\d+/));
      expect(response.data.elo_history).toHaveLength(2);
    });

    it('should use default seasons if none provided', async () => {
      mockedAxios.get.mockResolvedValue({ data: { elo_history: [] } });

      await apiService.getTeamEloHistory('KC');

      expect(mockedAxios.get).toHaveBeenCalledWith(expect.stringMatching(/\/api\/elo\/teams\/KC\/history\?seasons=2020&seasons=2021&seasons=2022&seasons=2023&seasons=2024&_t=\d+/));
    });
  });

  describe('Live Games API', () => {
    it('should fetch live games', async () => {
      const mockResponse = {
        data: {
          games: [
            {
              id: 'game1',
              home_team: 'KC',
              away_team: 'BUF',
              home_score: 21,
              away_score: 14,
              status: 'in_progress'
            }
          ],
          total_games: 1,
          live_games: 1
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getLiveGames();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/live/games');
      expect(response.data.games).toHaveLength(1);
    });
  });

  describe('ELO Projections API', () => {
    it('should fetch ELO projections for specific week', async () => {
      const mockResponse = {
        data: {
          projections: [
            { team: 'KC', projected_rating: 1515, confidence_score: 0.8 }
          ],
          season: 2025,
          week: 2
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getEloProjections(2025, 2);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/elo/projections/2025/2');
      expect(response.data.projections).toHaveLength(1);
    });

    it('should fetch team ELO projections', async () => {
      const mockResponse = {
        data: {
          projections: [
            { week: 2, projected_rating: 1515, confidence_score: 0.8 },
            { week: 3, projected_rating: 1520, confidence_score: 0.75 }
          ]
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getTeamEloProjections('KC', 2025);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/elo/projections/team/KC/2025');
      expect(response.data.projections).toHaveLength(2);
    });

    it('should generate ELO projections', async () => {
      const mockResponse = {
        data: {
          message: 'ELO projections generated for season 2025',
          season: 2025
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const response = await apiService.generateEloProjections(2025, 1);

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/elo/projections/generate', {
        season: 2025,
        current_week: 1
      });
      expect(response.data.message).toContain('ELO projections generated');
    });
  });

  describe('Game Predictions API', () => {
    it('should fetch game prediction', async () => {
      const mockResponse = {
        data: {
          home_team: 'KC',
          away_team: 'BUF',
          home_win_probability: 0.6,
          away_win_probability: 0.4,
          predicted_winner: 'KC',
          confidence: 0.6,
          expected_margin: 3
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getGamePrediction('KC', 'BUF');

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/predictions/game/KC/BUF');
      expect(response.data.predicted_winner).toBe('KC');
    });

    it('should fetch week predictions', async () => {
      const mockResponse = {
        data: {
          predictions: [
            {
              home_team: 'KC',
              away_team: 'BUF',
              predicted_winner: 'KC'
            }
          ],
          week: 1
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getWeekPredictions(1);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/predictions/week/1');
      expect(response.data.predictions).toHaveLength(1);
    });
  });

  describe('System Status API', () => {
    it('should fetch system status', async () => {
      const mockResponse = {
        data: {
          status: 'healthy',
          timestamp: '2025-09-05T21:00:00Z',
          services: {
            api: 'healthy',
            database: 'healthy'
          }
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getSystemStatus();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/system/status');
      expect(response.data.status).toBe('healthy');
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      mockedAxios.get.mockRejectedValue(networkError);

      await expect(apiService.getEloRatings()).rejects.toThrow('Network Error');
    });

    it('should handle HTTP errors', async () => {
      const httpError = {
        response: {
          status: 500,
          data: { error: 'Internal Server Error' }
        }
      };
      mockedAxios.get.mockRejectedValue(httpError);

      await expect(apiService.getEloRatings()).rejects.toEqual(httpError);
    });

    it('should handle timeout errors', async () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 10000ms exceeded'
      };
      mockedAxios.get.mockRejectedValue(timeoutError);

      await expect(apiService.getEloRatings()).rejects.toEqual(timeoutError);
    });
  });

  describe('Request/Response Interceptors', () => {
    it('should log API requests', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      // Trigger a request
      mockedAxios.get.mockResolvedValue({ data: {} });
      apiService.getEloRatings();

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('API Request:')
      );

      consoleSpy.mockRestore();
    });

    it('should log API response errors', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      // Trigger an error
      mockedAxios.get.mockRejectedValue(new Error('Test Error'));
      apiService.getEloRatings().catch(() => {});

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('API Response Error:')
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Configuration', () => {
    it('should have correct base URL', () => {
      expect(apiService.defaults.baseURL).toBe('http://localhost:8000');
    });

    it('should have correct timeout', () => {
      expect(apiService.defaults.timeout).toBe(10000);
    });

    it('should have correct headers', () => {
      expect(apiService.defaults.headers['Content-Type']).toBe('application/json');
    });
  });
});
