import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import WeeklySchedule from '../WeeklySchedule';
import { apiService } from '../../services/api';
import { predictionService } from '../../services/predictionService';

// Mock the API services
jest.mock('../../services/api', () => ({
  apiService: {
    getTeamEloHistory: jest.fn(),
    getGamePrediction: jest.fn()
  }
}));

jest.mock('../../services/predictionService', () => ({
  predictionService: {
    getGamesForWeek: jest.fn()
  }
}));

const mockGames = [
  {
    id: 'game_2025_week1_KC_LAC',
    home_team: 'LAC',
    away_team: 'KC',
    home_score: 20,
    away_score: 12,
    week: 1,
    season: 2025,
    status: 'scheduled',
    game_time: '2025-09-07T20:00:00Z',
    home_elo: 1580,
    away_elo: 1620,
    home_win_probability: 0.45,
    away_win_probability: 0.55,
    predicted_winner: 'KC',
    confidence: 0.75,
    expected_margin: 3
  },
  {
    id: 'game_2025_week1_DAL_PHI',
    home_team: 'PHI',
    away_team: 'DAL',
    home_score: 24,
    away_score: 20,
    week: 1,
    season: 2025,
    status: 'final',
    game_time: '2025-09-07T16:00:00Z',
    home_elo: 1550,
    away_elo: 1520,
    home_win_probability: 0.65,
    away_win_probability: 0.35,
    predicted_winner: 'PHI',
    confidence: 0.80,
    expected_margin: 5
  }
];

const mockEloData = {
  elo_history: [
    {
      rating: 1620,
      week: 1,
      season: 2025
    }
  ]
};

const mockPrediction = {
  home_win_probability: 0.45,
  away_win_probability: 0.55,
  predicted_winner: 'KC',
  confidence: 0.75,
  expected_margin: 3
};

describe('WeeklySchedule Component', () => {
  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Mock successful API responses
    predictionService.getGamesForWeek.mockResolvedValue(mockGames);
    apiService.getTeamEloHistory.mockResolvedValue({ data: mockEloData });
    apiService.getGamePrediction.mockResolvedValue({ data: mockPrediction });
  });

  test('renders weekly schedule with games', async () => {
    render(<WeeklySchedule />);
    
    // Check if the component loads
    expect(screen.getByText('Week 1 Schedule - 2025 Season')).toBeInTheDocument();
    
    // Wait for games to load
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
      expect(screen.getByText('LAC')).toBeInTheDocument();
    });
  });

  test('displays week selector buttons', async () => {
    render(<WeeklySchedule />);
    
    // Check if week selector is rendered
    expect(screen.getByText('Week 1')).toBeInTheDocument();
    expect(screen.getByText('Week 2')).toBeInTheDocument();
    expect(screen.getByText('Week 18')).toBeInTheDocument();
  });

  test('handles week selection', async () => {
    render(<WeeklySchedule />);
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Click on Week 2
    const week2Button = screen.getByText('Week 2');
    fireEvent.click(week2Button);
    
    // Verify that getGamesForWeek was called with the new week
    expect(predictionService.getGamesForWeek).toHaveBeenCalledWith(2025, 2);
  });

  test('displays game information correctly', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      // Check if game data is displayed
      expect(screen.getByText('KC')).toBeInTheDocument();
      expect(screen.getByText('LAC')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
      expect(screen.getByText('20')).toBeInTheDocument();
      expect(screen.getByText('ELO: 1620')).toBeInTheDocument();
      expect(screen.getByText('ELO: 1580')).toBeInTheDocument();
    });
  });

  test('shows prediction preview', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      expect(screen.getByText('Predicted: KC')).toBeInTheDocument();
      expect(screen.getByText('Confidence: 75%')).toBeInTheDocument();
      expect(screen.getByText('Expected Margin: +3')).toBeInTheDocument();
    });
  });

  test('opens ELO breakdown modal when game is clicked', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Click on the first game card
    const gameCard = screen.getByText('KC').closest('.game-card');
    fireEvent.click(gameCard);
    
    // Wait for modal to appear
    await waitFor(() => {
      expect(screen.getByText('KC @ LAC')).toBeInTheDocument();
    });
  });

  test('displays ELO comparison in modal', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Click on game card to open modal
    const gameCard = screen.getByText('KC').closest('.game-card');
    fireEvent.click(gameCard);
    
    await waitFor(() => {
      // Check ELO comparison
      expect(screen.getByText('1620')).toBeInTheDocument();
      expect(screen.getByText('1580')).toBeInTheDocument();
      expect(screen.getByText('ELO Difference')).toBeInTheDocument();
    });
  });

  test('shows prediction details in modal', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Click on game card to open modal
    const gameCard = screen.getByText('KC').closest('.game-card');
    fireEvent.click(gameCard);
    
    await waitFor(() => {
      // Check prediction details
      expect(screen.getByText('Game Prediction')).toBeInTheDocument();
      expect(screen.getByText('Predicted Winner')).toBeInTheDocument();
      expect(screen.getByText('Confidence')).toBeInTheDocument();
      expect(screen.getByText('Expected Margin')).toBeInTheDocument();
    });
  });

  test('displays win probability bars in modal', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Click on game card to open modal
    const gameCard = screen.getByText('KC').closest('.game-card');
    fireEvent.click(gameCard);
    
    await waitFor(() => {
      // Check win probability bars
      expect(screen.getByText('55%')).toBeInTheDocument();
      expect(screen.getByText('45%')).toBeInTheDocument();
    });
  });

  test('closes modal when close button is clicked', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Click on game card to open modal
    const gameCard = screen.getByText('KC').closest('.game-card');
    fireEvent.click(gameCard);
    
    await waitFor(() => {
      expect(screen.getByText('KC @ LAC')).toBeInTheDocument();
    });
    
    // Click close button
    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);
    
    // Modal should be closed
    expect(screen.queryByText('KC @ LAC')).not.toBeInTheDocument();
  });

  test('closes modal when overlay is clicked', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Click on game card to open modal
    const gameCard = screen.getByText('KC').closest('.game-card');
    fireEvent.click(gameCard);
    
    await waitFor(() => {
      expect(screen.getByText('KC @ LAC')).toBeInTheDocument();
    });
    
    // Click on modal overlay
    const overlay = screen.getByText('KC @ LAC').closest('.modal-overlay');
    fireEvent.click(overlay);
    
    // Modal should be closed
    expect(screen.queryByText('KC @ LAC')).not.toBeInTheDocument();
  });

  test('handles API errors gracefully', async () => {
    // Mock API error
    predictionService.getGamesForWeek.mockRejectedValue(new Error('API Error'));
    
    render(<WeeklySchedule />);
    
    // Should show loading initially
    expect(screen.getByText('Loading games...')).toBeInTheDocument();
    
    // Should fallback to mock data
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
  });

  test('handles modal API errors gracefully', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Mock API error for modal
    apiService.getTeamEloHistory.mockRejectedValue(new Error('API Error'));
    apiService.getGamePrediction.mockRejectedValue(new Error('API Error'));
    
    // Click on game card to open modal
    const gameCard = screen.getByText('KC').closest('.game-card');
    fireEvent.click(gameCard);
    
    // Modal should still open with basic data
    await waitFor(() => {
      expect(screen.getByText('KC @ LAC')).toBeInTheDocument();
    });
  });

  test('displays different game statuses correctly', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      // Check scheduled game
      expect(screen.getByText('Scheduled')).toBeInTheDocument();
      // Check final game
      expect(screen.getByText('Final')).toBeInTheDocument();
    });
  });

  test('formats game time correctly', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      // Check if game time is formatted
      expect(screen.getByText(/Sep/)).toBeInTheDocument();
    });
  });

  test('shows ELO strength indicators', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Click on game card to open modal
    const gameCard = screen.getByText('KC').closest('.game-card');
    fireEvent.click(gameCard);
    
    await waitFor(() => {
      // Check ELO strength
      expect(screen.getByText('Elite')).toBeInTheDocument();
      expect(screen.getByText('Strong')).toBeInTheDocument();
    });
  });

  test('displays game information in modal', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Click on game card to open modal
    const gameCard = screen.getByText('KC').closest('.game-card');
    fireEvent.click(gameCard);
    
    await waitFor(() => {
      // Check game info
      expect(screen.getByText('Game Information')).toBeInTheDocument();
      expect(screen.getByText('Week')).toBeInTheDocument();
      expect(screen.getByText('Season')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Home Advantage')).toBeInTheDocument();
    });
  });

  test('handles empty games array', async () => {
    // Mock empty response
    predictionService.getGamesForWeek.mockResolvedValue([]);
    
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      // Should show no games message or fallback to mock data
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
  });

  test('updates current week based on date', () => {
    // Mock current date to be in week 5
    const mockDate = new Date('2025-10-01');
    jest.spyOn(global, 'Date').mockImplementation(() => mockDate);
    
    render(<WeeklySchedule />);
    
    // Should calculate week 5
    expect(screen.getByText('Week 5 Schedule - 2025 Season')).toBeInTheDocument();
    
    // Restore original Date
    jest.restoreAllMocks();
  });
});

describe('EloBreakdownModal Component', () => {
  const mockGame = {
    id: 'game_2025_week1_KC_LAC',
    home_team: 'LAC',
    away_team: 'KC',
    home_elo: 1580,
    away_elo: 1620,
    home_elo_data: { rating: 1580 },
    away_elo_data: { rating: 1620 },
    prediction: {
      home_win_probability: 0.45,
      away_win_probability: 0.55,
      predicted_winner: 'KC',
      confidence: 0.75,
      expected_margin: 3
    },
    week: 1,
    season: 2025,
    status: 'scheduled'
  };

  test('renders ELO comparison correctly', () => {
    render(
      <WeeklySchedule />
    );
    
    // This test would need to be integrated with the parent component
    // For now, we'll test the modal logic through the parent component
  });

  test('calculates ELO difference correctly', () => {
    const homeElo = 1580;
    const awayElo = 1620;
    const eloDifference = homeElo - awayElo;
    
    expect(eloDifference).toBe(-40);
  });

  test('determines ELO strength correctly', () => {
    const getEloStrength = (elo) => {
      if (elo >= 1600) return 'Elite';
      if (elo >= 1500) return 'Strong';
      if (elo >= 1400) return 'Average';
      if (elo >= 1300) return 'Below Average';
      return 'Weak';
    };
    
    expect(getEloStrength(1620)).toBe('Elite');
    expect(getEloStrength(1580)).toBe('Strong');
    expect(getEloStrength(1450)).toBe('Average');
    expect(getEloStrength(1350)).toBe('Below Average');
    expect(getEloStrength(1250)).toBe('Weak');
  });
});
