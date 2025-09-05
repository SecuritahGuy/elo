import { apiService } from '../api';

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  })),
}));

// Import the mocked axios
import axios from 'axios';
const mockedAxios = axios.create();

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('System Status', () => {
    it('should get system status', async () => {
      const mockResponse = { data: { status: 'healthy' } };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getSystemStatus();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/system/status');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Team Data', () => {
    it('should get team rankings', async () => {
      const mockResponse = { data: [{ team: 'PHI', rating: 1768.4 }] };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getTeamRankings();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/teams/rankings');
      expect(result).toEqual(mockResponse);
    });

    it('should get team details', async () => {
      const mockResponse = { data: { team: 'PHI', rating: 1768.4 } };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getTeamDetails('PHI');

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/teams/PHI');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('ELO Ratings', () => {
    it('should get ELO seasons', async () => {
      const mockResponse = { data: [2024, 2025] };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getEloSeasons();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/elo/seasons');
      expect(result).toEqual(mockResponse);
    });

    it('should get ELO ratings with default parameters', async () => {
      const mockResponse = { data: [{ team: 'PHI', rating: 1768.4 }] };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getEloRatings();

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/elo/ratings?season=2024&config=baseline');
      expect(result).toEqual(mockResponse);
    });

    it('should get ELO ratings with custom parameters', async () => {
      const mockResponse = { data: [{ team: 'PHI', rating: 1768.4 }] };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getEloRatings(2025, 'weather_only');

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/elo/ratings?season=2025&config=weather_only');
      expect(result).toEqual(mockResponse);
    });

    it('should get team ELO history', async () => {
      const mockResponse = { data: [{ season: 2024, rating: 1768.4 }] };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getTeamEloHistory('PHI', [2024, 2025]);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/elo/team/PHI?seasons=2024&seasons=2025');
      expect(result).toEqual(mockResponse);
    });

    it('should get team comparison', async () => {
      const mockResponse = { data: [{ team: 'PHI', rating: 1768.4 }] };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getTeamComparison(['PHI', 'DAL'], 2024);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/elo/compare?teams=PHI&teams=DAL&season=2024');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Injury Data', () => {
    it('should get team injuries', async () => {
      const mockResponse = { data: { teams: [] } };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getTeamInjuries(2024, 1);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/injuries/teams?season=2024&week=1');
      expect(result).toEqual(mockResponse);
    });

    it('should get team injury history', async () => {
      const mockResponse = { data: { weeks: [] } };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getTeamInjuryHistory('PHI', 2024);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/injuries/team/PHI?season=2024');
      expect(result).toEqual(mockResponse);
    });

    it('should get player injuries', async () => {
      const mockResponse = { data: { players: [] } };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getPlayerInjuries(2024, 1, 'PHI');

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/injuries/players?season=2024&week=1&team=PHI');
      expect(result).toEqual(mockResponse);
    });

    it('should get injury summary', async () => {
      const mockResponse = { data: { summary: { total_injuries: 100 } } };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getInjurySummary(2024);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/injuries/summary?season=2024');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Action Network', () => {
    it('should get Action Network experts', async () => {
      const mockResponse = { data: [{ name: 'Expert 1' }] };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getActionNetworkExperts('nfl', 50);

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/action-network/experts?league=nfl&limit=50');
      expect(result).toEqual(mockResponse);
    });

    it('should get Action Network picks', async () => {
      const mockResponse = { data: [{ pick: 'test' }] };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await apiService.getActionNetworkPicks('nfl', 100, 1, 'win');

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/action-network/picks?league=nfl&limit=100&expert_id=1&result=win');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const error = new Error('Network Error');
      mockedAxios.get.mockRejectedValue(error);

      await expect(apiService.getSystemStatus()).rejects.toThrow('Network Error');
    });
  });
});
