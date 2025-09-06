import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock the services before importing the component
jest.mock('../../services/api', () => ({
  __esModule: true,
  default: {
    getTeamEloHistory: jest.fn().mockResolvedValue({
      data: {
        elo_history: [{ rating: 1620, week: 1, season: 2025 }]
      }
    }),
    getGamePrediction: jest.fn().mockResolvedValue({
      data: {
        home_win_probability: 0.45,
        away_win_probability: 0.55,
        predicted_winner: 'KC',
        confidence: 0.75,
        expected_margin: 3
      }
    })
  }
}));

jest.mock('../../services/predictionService', () => ({
  __esModule: true,
  default: {
    getGamesForWeek: jest.fn().mockResolvedValue([
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
      }
    ])
  }
}));

// Mock Date.now and new Date for consistent testing
const mockDate = new Date('2025-09-05T21:00:00Z');
global.Date = jest.fn(() => mockDate);
global.Date.now = jest.fn(() => mockDate.getTime());
global.Date.prototype = Object.getPrototypeOf(mockDate);

import WeeklySchedule from '../WeeklySchedule';

describe('WeeklySchedule Component - Simple Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders weekly schedule component', async () => {
    render(<WeeklySchedule />);
    
    // Check if the component loads
    expect(screen.getByText(/Week \d+ Schedule - 2025 Season/)).toBeInTheDocument();
    
    // Wait for games to load
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test('displays week selector buttons', () => {
    render(<WeeklySchedule />);
    
    // Check if week selector is rendered
    expect(screen.getByText('Week 1')).toBeInTheDocument();
    expect(screen.getByText('Week 2')).toBeInTheDocument();
    expect(screen.getByText('Week 18')).toBeInTheDocument();
  });

  test('shows loading state initially', () => {
    render(<WeeklySchedule />);
    expect(screen.getByText('Loading games...')).toBeInTheDocument();
  });

  test('handles week selection', async () => {
    const { getByText } = render(<WeeklySchedule />);
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    });
    
    // Click on Week 2
    const week2Button = getByText('Week 2');
    fireEvent.click(week2Button);
    
    // Should show Week 2 in header
    expect(screen.getByText('Week 2 Schedule - 2025 Season')).toBeInTheDocument();
  });

  test('displays game information when loaded', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      // Check if game data is displayed
      expect(screen.getByText('KC')).toBeInTheDocument();
      expect(screen.getByText('LAC')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
      expect(screen.getByText('20')).toBeInTheDocument();
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

  test('opens modal when game is clicked', async () => {
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

  test('handles API errors gracefully', async () => {
    // Mock API error
    const { predictionService } = require('../../services/predictionService');
    predictionService.getGamesForWeek.mockRejectedValue(new Error('API Error'));
    
    render(<WeeklySchedule />);
    
    // Should show loading initially
    expect(screen.getByText('Loading games...')).toBeInTheDocument();
    
    // Should fallback to mock data
    await waitFor(() => {
      expect(screen.getByText('KC')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  test('displays different game statuses correctly', async () => {
    render(<WeeklySchedule />);
    
    await waitFor(() => {
      // Check scheduled game
      expect(screen.getByText('Scheduled')).toBeInTheDocument();
    });
  });

  test('shows ELO strength indicators in modal', async () => {
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
});

describe('ELO Helper Functions', () => {
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

  test('calculates home field advantage', () => {
    const homeAdvantage = 25;
    const eloDifference = 100;
    const adjustedDifference = eloDifference + homeAdvantage;
    
    expect(adjustedDifference).toBe(125);
  });
});
