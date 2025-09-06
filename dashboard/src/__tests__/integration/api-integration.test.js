/**
 * Comprehensive API Integration Tests
 * Tests the complete frontend-backend integration flow
 */

import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import { apiService } from '../../services/api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock components that make API calls
const TestComponent = () => {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.getEloRatings(2025, 'comprehensive');
      setData(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={fetchData}>Fetch Data</button>
      {loading && <div>Loading...</div>}
      {error && <div>Error: {error}</div>}
      {data && <div>Data loaded: {data.ratings?.length || 0} items</div>}
    </div>
  );
};

describe('API Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('ELO Ratings API', () => {
    it('should successfully fetch ELO ratings', async () => {
      const mockResponse = {
        data: {
          ratings: [
            { team: 'KC', rating: 1500, rank: 1 },
            { team: 'BUF', rating: 1490, rank: 2 }
          ],
          season: 2025,
          config: 'comprehensive'
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      render(
        <BrowserRouter>
          <TestComponent />
        </BrowserRouter>
      );

      fireEvent.click(screen.getByText('Fetch Data'));

      await waitFor(() => {
        expect(screen.getByText('Data loaded: 2 items')).toBeInTheDocument();
      });

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/elo/ratings?season=2025&config=comprehensive'
      );
    });

    it('should handle API errors gracefully', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'));

      render(
        <BrowserRouter>
          <TestComponent />
        </BrowserRouter>
      );

      fireEvent.click(screen.getByText('Fetch Data'));

      await waitFor(() => {
        expect(screen.getByText('Error: Network error')).toBeInTheDocument();
      });
    });

    it('should show loading state during API calls', async () => {
      mockedAxios.get.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      render(
        <BrowserRouter>
          <TestComponent />
        </BrowserRouter>
      );

      fireEvent.click(screen.getByText('Fetch Data'));

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('Live Games API', () => {
    it('should fetch live games data', async () => {
      const mockResponse = {
        data: {
          games: [
            {
              id: 'game1',
              home_team: 'KC',
              away_team: 'BUF',
              home_score: 21,
              away_score: 14,
              status: 'in_progress',
              quarter: 4,
              time_remaining: '2:30'
            }
          ],
          total_games: 1,
          live_games: 1
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getLiveGames();
      
      expect(response.data.games).toHaveLength(1);
      expect(response.data.games[0].home_team).toBe('KC');
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/live/games');
    });
  });

  describe('ELO Projections API', () => {
    it('should fetch projected ELO ratings for future weeks', async () => {
      const mockResponse = {
        data: {
          projections: [
            { team: 'KC', projected_rating: 1515, confidence_score: 0.8, rank: 1 },
            { team: 'BUF', projected_rating: 1506, confidence_score: 0.7, rank: 2 }
          ],
          season: 2025,
          week: 2,
          count: 2
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getEloProjections(2025, 2);
      
      expect(response.data.projections).toHaveLength(2);
      expect(response.data.week).toBe(2);
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/elo/projections/2025/2');
    });
  });

  describe('Error Handling', () => {
    it('should handle 404 errors', async () => {
      const error = {
        response: {
          status: 404,
          data: { error: 'Not found' }
        }
      };
      mockedAxios.get.mockRejectedValue(error);

      try {
        await apiService.getEloRatings(2025);
      } catch (err) {
        expect(err.response.status).toBe(404);
      }
    });

    it('should handle network timeouts', async () => {
      const error = {
        code: 'ECONNABORTED',
        message: 'timeout of 10000ms exceeded'
      };
      mockedAxios.get.mockRejectedValue(error);

      try {
        await apiService.getEloRatings(2025);
      } catch (err) {
        expect(err.code).toBe('ECONNABORTED');
      }
    });

    it('should handle malformed responses', async () => {
      const mockResponse = {
        data: null // Malformed response
      };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const response = await apiService.getEloRatings(2025);
      expect(response.data).toBeNull();
    });
  });

  describe('API Service Configuration', () => {
    it('should use correct base URL', () => {
      expect(apiService.defaults.baseURL).toBe('http://localhost:8000');
    });

    it('should have correct timeout configuration', () => {
      expect(apiService.defaults.timeout).toBe(10000);
    });

    it('should have correct headers', () => {
      expect(apiService.defaults.headers['Content-Type']).toBe('application/json');
    });
  });
});
