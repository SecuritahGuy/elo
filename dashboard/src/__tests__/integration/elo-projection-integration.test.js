/**
 * ELO Projection Integration Tests
 * Tests the integration between frontend and ELO projection backend
 */

import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import WeeklySchedule from '../../components/WeeklySchedule';
import { apiService } from '../../services/api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock the API service
jest.mock('../services/api', () => ({
  apiService: {
    getLiveGames: jest.fn(),
    getEloRatings: jest.fn(),
    getEloProjections: jest.fn(),
    getTeamEloHistory: jest.fn(),
    getGamePrediction: jest.fn()
  }
}));

// Mock Date
const mockDate = new Date('2025-09-05T21:00:00Z');
global.Date = jest.fn(() => mockDate);
global.Date.now = jest.fn(() => mockDate.getTime());

describe('ELO Projection Integration Tests', () => {
  const mockCurrentEloRatings = {
    data: {
      ratings: [
        { team: 'KC', rating: 1500, rank: 1 },
        { team: 'BUF', rating: 1490, rank: 2 },
        { team: 'PHI', rating: 1480, rank: 3 },
        { team: 'DAL', rating: 1470, rank: 4 }
      ]
    }
  };

  const mockProjectedEloRatings = {
    data: {
      projections: [
        { team: 'KC', projected_rating: 1515, confidence_score: 0.8, rank: 1 },
        { team: 'BUF', projected_rating: 1506, confidence_score: 0.7, rank: 2 },
        { team: 'PHI', projected_rating: 1495, confidence_score: 0.75, rank: 3 },
        { team: 'DAL', projected_rating: 1485, confidence_score: 0.72, rank: 4 }
      ]
    }
  };

  const mockLiveGames = {
    data: {
      games: [
        {
          id: 'game1',
          home_team: 'KC',
          away_team: 'BUF',
          home_score: 0,
          away_score: 0,
          status: 'scheduled',
          quarter: 0,
          time_remaining: '0:00',
          last_update: '2025-09-05T21:00:00Z'
        }
      ]
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default mocks
    apiService.getLiveGames.mockResolvedValue(mockLiveGames);
    apiService.getEloRatings.mockResolvedValue(mockCurrentEloRatings);
    apiService.getEloProjections.mockResolvedValue(mockProjectedEloRatings);
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

  describe('Current Week ELO Integration', () => {
    it('should use current ELO ratings for current week', async () => {
      renderWeeklySchedule();

      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2025, 'comprehensive');
        expect(apiService.getEloProjections).not.toHaveBeenCalled();
      });
    });

    it('should display current ELO ratings without projection indicator', async () => {
      renderWeeklySchedule();

      await waitFor(() => {
        expect(screen.getByText('ELO: 1500')).toBeInTheDocument();
        expect(screen.queryByText('(Projected)')).not.toBeInTheDocument();
      });
    });
  });

  describe('Future Week ELO Integration', () => {
    it('should use projected ELO ratings for future weeks', async () => {
      renderWeeklySchedule();

      // Click on week 2 button
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        expect(apiService.getEloProjections).toHaveBeenCalledWith(2025, 2);
        expect(apiService.getEloRatings).toHaveBeenCalledTimes(1); // Only called once on mount
      });
    });

    it('should display projected ELO ratings with projection indicator', async () => {
      renderWeeklySchedule();

      // Click on week 2 button
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        expect(screen.getByText('ELO: 1515')).toBeInTheDocument();
        expect(screen.getByText('(Projected)')).toBeInTheDocument();
      });
    });

    it('should fallback to current ELO if projections fail', async () => {
      apiService.getEloProjections.mockRejectedValue(new Error('Projection API Error'));

      renderWeeklySchedule();

      // Click on week 2 button
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledTimes(2); // Called again as fallback
        expect(screen.getByText('ELO: 1500')).toBeInTheDocument();
      });
    });
  });

  describe('ELO Projection Data Processing', () => {
    it('should correctly convert projection data format', async () => {
      renderWeeklySchedule();

      // Click on week 2 button
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        // Check that projected ratings are displayed
        expect(screen.getByText('ELO: 1515')).toBeInTheDocument();
        expect(screen.getByText('ELO: 1506')).toBeInTheDocument();
      });
    });

    it('should maintain ELO ranking order from projections', async () => {
      renderWeeklySchedule();

      // Click on week 2 button
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        // KC should have highest rating (1515)
        const kcElo = screen.getByText('ELO: 1515');
        expect(kcElo).toBeInTheDocument();
      });
    });
  });

  describe('ELO Projection Confidence Integration', () => {
    it('should use confidence scores from projections', async () => {
      renderWeeklySchedule();

      // Click on week 2 button
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        // The confidence should be used in prediction calculations
        expect(screen.getByText(/Confidence:/)).toBeInTheDocument();
      });
    });
  });

  describe('ELO Projection Error Handling', () => {
    it('should handle projection API errors gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      apiService.getEloProjections.mockRejectedValue(new Error('Projection API Error'));

      renderWeeklySchedule();

      // Click on week 2 button
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Projected ELOs not available, using current ratings:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });

    it('should handle malformed projection data', async () => {
      const malformedResponse = {
        data: {
          projections: null
        }
      };
      apiService.getEloProjections.mockResolvedValue(malformedResponse);

      renderWeeklySchedule();

      // Click on week 2 button
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        // Should fallback to current ELO
        expect(apiService.getEloRatings).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('ELO Projection Performance', () => {
    it('should cache projection data to avoid repeated API calls', async () => {
      renderWeeklySchedule();

      // Click on week 2 button multiple times
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);
      fireEvent.click(week2Button);
      fireEvent.click(week2Button);

      await waitFor(() => {
        // Should only call the API once per week
        expect(apiService.getEloProjections).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('ELO Projection Week Navigation', () => {
    it('should load different projections for different weeks', async () => {
      renderWeeklySchedule();

      // Click on week 2
      const week2Button = screen.getByText('Week 2');
      fireEvent.click(week2Button);

      await waitFor(() => {
        expect(apiService.getEloProjections).toHaveBeenCalledWith(2025, 2);
      });

      // Click on week 3
      const week3Button = screen.getByText('Week 3');
      fireEvent.click(week3Button);

      await waitFor(() => {
        expect(apiService.getEloProjections).toHaveBeenCalledWith(2025, 3);
      });
    });
  });
});
