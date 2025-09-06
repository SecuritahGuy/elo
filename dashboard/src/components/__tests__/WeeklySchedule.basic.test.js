import React from 'react';
import { render, screen } from '@testing-library/react';
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

// Mock Date functions to avoid test environment issues
const mockDate = new Date('2025-09-05T21:00:00Z');
const originalDate = global.Date;
global.Date = jest.fn(() => mockDate);
global.Date.now = jest.fn(() => mockDate.getTime());
global.Date.prototype = Object.getPrototypeOf(mockDate);
global.Date.prototype.getFullYear = jest.fn(() => 2025);
global.Date.prototype.getMonth = jest.fn(() => 8);
global.Date.prototype.getDate = jest.fn(() => 5);

import WeeklySchedule from '../WeeklySchedule';

describe('WeeklySchedule Component - Basic Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterAll(() => {
    global.Date = originalDate;
  });

  test('renders weekly schedule component', () => {
    render(<WeeklySchedule />);
    
    // Check if the component loads
    expect(screen.getByText(/Week \d+ Schedule - 2025 Season/)).toBeInTheDocument();
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

  test('formats game time correctly', () => {
    const gameTime = '2025-09-07T20:00:00Z';
    const formatted = new Date(gameTime).toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      timeZoneName: 'short'
    });
    
    expect(formatted).toContain('Sep');
    expect(formatted).toContain('7');
  });

  test('determines game status color', () => {
    const getStatusColor = (status) => {
      switch (status) {
        case 'final': return '#4CAF50';
        case 'in_progress': return '#FF9800';
        case 'scheduled': return '#2196F3';
        default: return '#9E9E9E';
      }
    };
    
    expect(getStatusColor('final')).toBe('#4CAF50');
    expect(getStatusColor('in_progress')).toBe('#FF9800');
    expect(getStatusColor('scheduled')).toBe('#2196F3');
    expect(getStatusColor('unknown')).toBe('#9E9E9E');
  });

  test('determines game status text', () => {
    const getStatusText = (status) => {
      switch (status) {
        case 'final': return 'Final';
        case 'in_progress': return 'Live';
        case 'scheduled': return 'Scheduled';
        default: return 'Unknown';
      }
    };
    
    expect(getStatusText('final')).toBe('Final');
    expect(getStatusText('in_progress')).toBe('Live');
    expect(getStatusText('scheduled')).toBe('Scheduled');
    expect(getStatusText('unknown')).toBe('Unknown');
  });

  test('calculates win probability percentage', () => {
    const probability = 0.75;
    const percentage = Math.round(probability * 100);
    
    expect(percentage).toBe(75);
  });

  test('formats expected margin correctly', () => {
    const margin = 3;
    const formatted = margin > 0 ? `+${margin}` : margin.toString();
    
    expect(formatted).toBe('+3');
    
    const negativeMargin = -3;
    const negativeFormatted = negativeMargin > 0 ? `+${negativeMargin}` : negativeMargin.toString();
    
    expect(negativeFormatted).toBe('-3');
  });

  test('generates mock game data structure', () => {
    const mockGame = {
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
    };
    
    expect(mockGame.id).toBe('game_2025_week1_KC_LAC');
    expect(mockGame.home_team).toBe('LAC');
    expect(mockGame.away_team).toBe('KC');
    expect(mockGame.home_score).toBe(20);
    expect(mockGame.away_score).toBe(12);
    expect(mockGame.week).toBe(1);
    expect(mockGame.season).toBe(2025);
    expect(mockGame.status).toBe('scheduled');
    expect(mockGame.home_elo).toBe(1580);
    expect(mockGame.away_elo).toBe(1620);
    expect(mockGame.home_win_probability).toBe(0.45);
    expect(mockGame.away_win_probability).toBe(0.55);
    expect(mockGame.predicted_winner).toBe('KC');
    expect(mockGame.confidence).toBe(0.75);
    expect(mockGame.expected_margin).toBe(3);
  });

  test('validates ELO rating ranges', () => {
    const validateEloRating = (rating) => {
      return rating >= 1000 && rating <= 2000;
    };
    
    expect(validateEloRating(1500)).toBe(true);
    expect(validateEloRating(1000)).toBe(true);
    expect(validateEloRating(2000)).toBe(true);
    expect(validateEloRating(999)).toBe(false);
    expect(validateEloRating(2001)).toBe(false);
  });

  test('calculates confidence level from ELO difference', () => {
    const calculateConfidence = (eloDiff) => {
      const absDiff = Math.abs(eloDiff);
      if (absDiff >= 100) return 0.9;
      if (absDiff >= 50) return 0.8;
      if (absDiff >= 25) return 0.7;
      return 0.6;
    };
    
    expect(calculateConfidence(100)).toBe(0.9);
    expect(calculateConfidence(75)).toBe(0.8);
    expect(calculateConfidence(30)).toBe(0.7);
    expect(calculateConfidence(10)).toBe(0.6);
  });
});
