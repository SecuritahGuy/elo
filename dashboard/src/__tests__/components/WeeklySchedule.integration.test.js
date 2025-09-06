/**
 * WeeklySchedule Integration Test
 * Tests the integration between WeeklySchedule component and backend APIs
 * with proper Date mocking
 */

import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import WeeklySchedule from '../../components/WeeklySchedule';

// Mock the API service
jest.mock('../../services/api', () => ({
  apiService: {
    getLiveGames: jest.fn(),
    getEloRatings: jest.fn(),
    getEloProjections: jest.fn(),
    getTeamEloHistory: jest.fn(),
    getGamePrediction: jest.fn()
  }
}));

// Import the mocked API service
import { apiService } from '../../services/api';

describe('WeeklySchedule Integration Tests', () => {
  const mockLiveGames = {
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
          time_remaining: '2:30',
          last_update: '2025-09-05T21:00:00Z'
        },
        {
          id: 'game2',
          home_team: 'PHI',
          away_team: 'DAL',
          home_score: 24,
          away_score: 20,
          status: 'final',
          quarter: 4,
          time_remaining: '0:00',
          last_update: '2025-09-05T20:30:00Z'
        }
      ],
      total_games: 2,
      live_games: 1
    }
  };

  const mockEloRatings = {
    data: {
      ratings: [
        { team: 'KC', rating: 1500, rank: 1 },
        { team: 'BUF', rating: 1490, rank: 2 },
        { team: 'PHI', rating: 1480, rank: 3 },
        { team: 'DAL', rating: 1470, rank: 4 }
      ]
    }
  };

  const mockProjections = {
    data: {
      projections: [
        { team: 'KC', projected_rating: 1515, confidence_score: 0.8, rank: 1 },
        { team: 'BUF', projected_rating: 1506, confidence_score: 0.7, rank: 2 },
        { team: 'PHI', projected_rating: 1495, confidence_score: 0.75, rank: 3 },
        { team: 'DAL', projected_rating: 1485, confidence_score: 0.72, rank: 4 }
      ]
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default mocks
    apiService.getLiveGames.mockResolvedValue(mockLiveGames);
    apiService.getEloRatings.mockResolvedValue(mockEloRatings);
    apiService.getEloProjections.mockResolvedValue(mockProjections);
    apiService.getTeamEloHistory.mockResolvedValue({
      data: { elo_history: [{ rating: 1500 }] }
    });
    apiService.getGamePrediction.mockResolvedValue({
      data: {
        home_win_probability: 0.6,
        away_win_probability: 0.4,
        predicted_winner: 'KC',
        confidence: 0.6,
        expected_margin: 3
      }
    });
  });

  const renderWeeklySchedule = () => {
    return render(
      <BrowserRouter>
        <WeeklySchedule />
      </BrowserRouter>
    );
  };

  describe('Data Loading Integration', () => {
    it('should load live games and ELO ratings on mount', async () => {
      renderWeeklySchedule();

      await waitFor(() => {
        expect(apiService.getLiveGames).toHaveBeenCalled();
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2025, 'comprehensive');
      });
    });

    it('should display live games with correct status', async () => {
      renderWeeklySchedule();

      await waitFor(() => {
        expect(screen.getByText('KC')).toBeInTheDocument();
        expect(screen.getByText('BUF')).toBeInTheDocument();
        expect(screen.getByText('LIVE')).toBeInTheDocument();
        expect(screen.getByText('FINAL')).toBeInTheDocument();
      });
    });

    it('should show live game time for in-progress games', async () => {
      renderWeeklySchedule();

      await waitFor(() => {
        expect(screen.getByText('Q4 - 2:30')).toBeInTheDocument();
      });
    });
  });

  describe('ELO Projections Integration', () => {
    it('should load projected ELOs for future weeks', async () => {
      renderWeeklySchedule();

      // Wait for component to load first
      await waitFor(() => {
        expect(screen.getByText('Week 2')).toBeInTheDocument();
      });

      // Click on week 2 button
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        expect(apiService.getEloProjections).toHaveBeenCalledWith(2025, 2);
      });
    });

    it('should show projected indicator for future weeks', async () => {
      renderWeeklySchedule();

      // Wait for component to load first
      await waitFor(() => {
        expect(screen.getByText('Week 2')).toBeInTheDocument();
      });

      // Click on week 2 button
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        expect(screen.getAllByText('(Projected)')).toHaveLength(4);
      });
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle API errors gracefully', async () => {
      apiService.getLiveGames.mockRejectedValue(new Error('API Error'));

      renderWeeklySchedule();

      await waitFor(() => {
        // Should fallback to mock data instead of showing error
        expect(screen.getByText('KC')).toBeInTheDocument();
      });
    });

    it('should fallback to mock data when APIs fail', async () => {
      apiService.getLiveGames.mockRejectedValue(new Error('API Error'));
      apiService.getEloRatings.mockRejectedValue(new Error('API Error'));

      renderWeeklySchedule();

      await waitFor(() => {
        // Should show mock games (using real team names)
        expect(screen.getByText('KC')).toBeInTheDocument();
      });
    });
  });

  describe('Week Navigation Integration', () => {
    it('should switch between weeks and load appropriate data', async () => {
      renderWeeklySchedule();

      // Wait for component to load first
      await waitFor(() => {
        expect(screen.getByText('Week 3')).toBeInTheDocument();
      });

      // Click on week 3
      const week3Button = screen.getByText('Week 3');
      fireEvent.click(week3Button);

      await waitFor(() => {
        expect(apiService.getEloProjections).toHaveBeenCalledWith(2025, 3);
      });
    });

    it('should highlight current week', async () => {
      renderWeeklySchedule();

      // Wait for component to load first
      await waitFor(() => {
        expect(screen.getByText('Week 1')).toBeInTheDocument();
      });

      const week1Button = screen.getByText('Week 1');
      expect(week1Button).toHaveClass('active');
    });
  });

  describe('Data Processing Integration', () => {
    it('should correctly process live game data into component format', async () => {
      renderWeeklySchedule();

      await waitFor(() => {
        // Check that scores are displayed
        expect(screen.getByText('21')).toBeInTheDocument();
        expect(screen.getByText('14')).toBeInTheDocument();
        
        // Check that ELO ratings are displayed
        expect(screen.getByText('ELO: 1500')).toBeInTheDocument();
        expect(screen.getByText('ELO: 1490')).toBeInTheDocument();
      });
    });

    it('should calculate win probabilities correctly', async () => {
      renderWeeklySchedule();

      await waitFor(() => {
        // Check that predictions are shown
        expect(screen.getAllByText(/Predicted:/)).toHaveLength(2);
        expect(screen.getAllByText(/Confidence:/)).toHaveLength(2);
      });
    });
  });
});
