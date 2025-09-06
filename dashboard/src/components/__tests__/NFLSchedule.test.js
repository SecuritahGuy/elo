import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NFLSchedule from '../NFLSchedule';
import apiService from '../../services/api';

// Mock the API service
jest.mock('../../services/api', () => ({
  getNFLSchedule: jest.fn(),
  getEloRatings: jest.fn(),
}));

// Mock Lucide React icons
jest.mock('lucide-react', () => ({
  Calendar: () => <div data-testid="calendar-icon">Calendar</div>,
  ChevronLeft: () => <div data-testid="chevron-left">Left</div>,
  ChevronRight: () => <div data-testid="chevron-right">Right</div>,
  Clock: () => <div data-testid="clock-icon">Clock</div>,
  MapPin: () => <div data-testid="map-pin">MapPin</div>,
  TrendingUp: () => <div data-testid="trending-up">TrendingUp</div>,
  TrendingDown: () => <div data-testid="trending-down">TrendingDown</div>,
  RefreshCw: () => <div data-testid="refresh-icon">Refresh</div>,
}));

const mockScheduleData = [
  {
    id: 1,
    week: 1,
    date: '2025-01-05',
    time_local: '13:00:00',
    status: 'scheduled',
    home_team: {
      id: 1,
      name: 'Philadelphia Eagles',
      abbreviation: 'PHI'
    },
    away_team: {
      id: 2,
      name: 'Dallas Cowboys',
      abbreviation: 'DAL'
    },
    home_score: null,
    away_score: null,
    venue: {
      name: 'Lincoln Financial Field',
      city: 'Philadelphia',
      state: 'PA'
    }
  },
  {
    id: 2,
    week: 1,
    date: '2025-01-05',
    time_local: '16:25:00',
    status: 'scheduled',
    home_team: {
      id: 3,
      name: 'Buffalo Bills',
      abbreviation: 'BUF'
    },
    away_team: {
      id: 4,
      name: 'Miami Dolphins',
      abbreviation: 'MIA'
    },
    home_score: null,
    away_score: null,
    venue: {
      name: 'Highmark Stadium',
      city: 'Orchard Park',
      state: 'NY'
    }
  }
];

const mockEloData = [
  {
    team: { abbreviation: 'PHI' },
    rating: 1650.5,
    rating_change: 12.3,
    record: { wins: 12, losses: 5 }
  },
  {
    team: { abbreviation: 'DAL' },
    rating: 1580.2,
    rating_change: -8.7,
    record: { wins: 11, losses: 6 }
  },
  {
    team: { abbreviation: 'BUF' },
    rating: 1620.8,
    rating_change: 5.1,
    record: { wins: 13, losses: 4 }
  },
  {
    team: { abbreviation: 'MIA' },
    rating: 1540.3,
    rating_change: -3.2,
    record: { wins: 9, losses: 8 }
  }
];

describe('NFLSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful API responses
    apiService.getNFLSchedule.mockResolvedValue({
      data: { games: mockScheduleData }
    });
    
    apiService.getEloRatings.mockResolvedValue({
      data: { ratings: mockEloData }
    });
  });

  describe('Initial Load', () => {
    it('should render loading state initially', () => {
      render(<NFLSchedule />);
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('should load schedule and ELO data on mount', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(apiService.getNFLSchedule).toHaveBeenCalledWith(1, 2025);
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2025);
      });
    });

    it('should display schedule header', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(screen.getByText('NFL Schedule')).toBeInTheDocument();
        expect(screen.getByText('Week-by-week game schedule with ELO ratings comparison')).toBeInTheDocument();
      });
    });
  });

  describe('Week Navigation', () => {
    it('should render week selector', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(screen.getByText('Week 1')).toBeInTheDocument();
        expect(screen.getByDisplayValue('1')).toBeInTheDocument();
      });
    });

    it('should allow week selection', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(screen.getByDisplayValue('1')).toBeInTheDocument();
      });
      
      const weekSelector = screen.getByDisplayValue('1');
      fireEvent.change(weekSelector, { target: { value: '2' } });
      
      expect(apiService.getNFLSchedule).toHaveBeenCalledWith(2, 2025);
    });

    it('should navigate to previous week', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        const prevButton = screen.getByTestId('chevron-left');
        fireEvent.click(prevButton);
      });
      
      // Should not change from week 1 (minimum)
      expect(apiService.getNFLSchedule).toHaveBeenCalledWith(1, 2025);
    });

    it('should navigate to next week', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        const nextButton = screen.getByTestId('chevron-right');
        fireEvent.click(nextButton);
      });
      
      expect(apiService.getNFLSchedule).toHaveBeenCalledWith(2, 2025);
    });
  });

  describe('Game Display', () => {
    it('should display games for selected week', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(screen.getByText('Philadelphia Eagles')).toBeInTheDocument();
        expect(screen.getByText('Dallas Cowboys')).toBeInTheDocument();
        expect(screen.getByText('Buffalo Bills')).toBeInTheDocument();
        expect(screen.getByText('Miami Dolphins')).toBeInTheDocument();
      });
    });

    it('should display ELO ratings for teams', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(screen.getByText('1650.5')).toBeInTheDocument(); // PHI rating
        expect(screen.getByText('1580.2')).toBeInTheDocument(); // DAL rating
        expect(screen.getByText('+12.3')).toBeInTheDocument(); // PHI change
        expect(screen.getByText('-8.7')).toBeInTheDocument(); // DAL change
      });
    });

    it('should display team records', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(screen.getByText('12-5')).toBeInTheDocument(); // PHI record
        expect(screen.getByText('11-6')).toBeInTheDocument(); // DAL record
      });
    });

    it('should display game times and venues', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(screen.getByText('Lincoln Financial Field')).toBeInTheDocument();
        expect(screen.getByText('Highmark Stadium')).toBeInTheDocument();
      });
    });
  });

  describe('ELO Comparison', () => {
    it('should highlight ELO favorite', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        // PHI has higher ELO (1650.5 vs 1580.2), so should be highlighted
        const phiCard = screen.getByText('Philadelphia Eagles').closest('.border-nfl-primary');
        expect(phiCard).toBeInTheDocument();
      });
    });

    it('should show ELO difference', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(screen.getByText('ELO Difference: 70.3')).toBeInTheDocument();
        expect(screen.getByText('PHI favorite by 70.3 points')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      apiService.getNFLSchedule.mockRejectedValue(new Error('API Error'));
      
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load schedule for week 1')).toBeInTheDocument();
        expect(screen.getByText('Retry')).toBeInTheDocument();
      });
    });

    it('should handle empty schedule data', async () => {
      apiService.getNFLSchedule.mockResolvedValue({
        data: { games: [] }
      });
      
      render(<NFLSchedule />);
      
      await waitFor(() => {
        expect(screen.getByText('No Games Scheduled')).toBeInTheDocument();
        expect(screen.getByText('No games found for Week 1. Try selecting a different week.')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should allow manual refresh', async () => {
      render(<NFLSchedule />);
      
      await waitFor(() => {
        const refreshButton = screen.getByText('Refresh');
        fireEvent.click(refreshButton);
      });
      
      expect(apiService.getNFLSchedule).toHaveBeenCalledTimes(2); // Initial load + refresh
    });
  });
});
