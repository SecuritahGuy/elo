import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ELORankings from '../ELORankings';
import apiService from '../../services/api';

// Mock the API service
jest.mock('../../services/api', () => ({
  getEloSeasons: jest.fn(),
  getEloRatings: jest.fn(),
  recalculateEloRatings: jest.fn(),
}));

const mockSeasons = [2024, 2025, 2023];

const mockEloData = [
  {
    team: { abbreviation: 'PHI', name: 'Philadelphia Eagles' },
    rating: 1703.7,
    rating_change: 4.7,
    record: { wins: 10, losses: 2, ties: 0 },
    stats: { points_for: 350, points_against: 280 }
  },
  {
    team: { abbreviation: 'BUF', name: 'Buffalo Bills' },
    rating: 1667.1,
    rating_change: 0.0,
    record: { wins: 8, losses: 4, ties: 0 },
    stats: { points_for: 320, points_against: 300 }
  },
  {
    team: { abbreviation: 'SF', name: 'San Francisco 49ers' },
    rating: 1650.3,
    rating_change: -2.1,
    record: { wins: 7, losses: 5, ties: 0 },
    stats: { points_for: 310, points_against: 290 }
  },
  {
    team: { abbreviation: 'KC', name: 'Kansas City Chiefs' },
    rating: 1620.5,
    rating_change: -23.0,
    record: { wins: 6, losses: 6, ties: 0 },
    stats: { points_for: 300, points_against: 320 }
  }
];

describe('ELORankings', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiService.getEloSeasons.mockResolvedValue({
      data: { seasons: mockSeasons }
    });
    apiService.getEloRatings.mockResolvedValue({
      data: { ratings: mockEloData }
    });
    apiService.recalculateEloRatings.mockResolvedValue({
      data: { message: 'ELO ratings recalculated successfully' }
    });
  });

  describe('Initial Load', () => {
    it('should render loading state initially', () => {
      render(<ELORankings />);
      expect(screen.getByText('Loading ELO rankings...')).toBeInTheDocument();
    });

    it('should load seasons and ELO data on mount', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        expect(apiService.getEloSeasons).toHaveBeenCalled();
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2025); // Default to latest season
      });
    });

    it('should display ELO rankings table after loading', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        expect(screen.getByText('All NFL ELO Rankings')).toBeInTheDocument();
        expect(screen.getByText('Rank')).toBeInTheDocument();
        expect(screen.getByText('Team')).toBeInTheDocument();
        expect(screen.getByText('ELO Rating')).toBeInTheDocument();
        expect(screen.getByText('Change')).toBeInTheDocument();
        expect(screen.getByText('Record (W-L-T)')).toBeInTheDocument();
        expect(screen.getByText('Points (For-Against)')).toBeInTheDocument();
      });
    });
  });

  describe('Data Display', () => {
    it('should display team data correctly', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        // Check first team (PHI)
        expect(screen.getByText('1')).toBeInTheDocument(); // Rank
        expect(screen.getByText('PHI')).toBeInTheDocument(); // Team abbreviation
        expect(screen.getByText('Philadelphia Eagles')).toBeInTheDocument(); // Team name
        expect(screen.getByText('1703.7')).toBeInTheDocument(); // Rating
        expect(screen.getByText('+4.7')).toBeInTheDocument(); // Change
        expect(screen.getByText('10-2-0')).toBeInTheDocument(); // Record
        expect(screen.getByText('350-280')).toBeInTheDocument(); // Points
      });
    });

    it('should display rating changes with correct colors', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        // Positive change (green)
        const positiveChange = screen.getByText('+4.7');
        expect(positiveChange).toHaveClass('text-green-600');

        // No change (gray)
        const noChange = screen.getByText('0.0');
        expect(noChange).toHaveClass('text-gray-500');

        // Negative change (red)
        const negativeChange = screen.getByText('-2.1');
        expect(negativeChange).toHaveClass('text-red-600');
      });
    });

    it('should display trending icons for rating changes', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        // Should have trending up and down icons
        const trendingIcons = screen.getAllByTestId('trending-icon');
        expect(trendingIcons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Season Selection', () => {
    it('should render season selector', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        const seasonSelect = screen.getByDisplayValue('2025');
        expect(seasonSelect).toBeInTheDocument();
      });
    });

    it('should load data for selected season', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        const seasonSelect = screen.getByDisplayValue('2025');
        fireEvent.change(seasonSelect, { target: { value: '2024' } });
      });

      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2024);
      });
    });

    it('should show all available seasons in dropdown', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        expect(screen.getByText('2025')).toBeInTheDocument();
        expect(screen.getByText('2024')).toBeInTheDocument();
        expect(screen.getByText('2023')).toBeInTheDocument();
      });
    });
  });

  describe('Recalculate Functionality', () => {
    it('should render recalculate button', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        expect(screen.getByText('Recalculate ELO')).toBeInTheDocument();
      });
    });

    it('should call recalculate API when button is clicked', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        const recalculateButton = screen.getByText('Recalculate ELO');
        fireEvent.click(recalculateButton);
      });

      await waitFor(() => {
        expect(apiService.recalculateEloRatings).toHaveBeenCalled();
      });
    });

    it('should show loading state during recalculation', async () => {
      // Mock a delayed response
      apiService.recalculateEloRatings.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: { message: 'Success' } }), 100))
      );

      render(<ELORankings />);
      
      await waitFor(() => {
        const recalculateButton = screen.getByText('Recalculate ELO');
        fireEvent.click(recalculateButton);
      });

      expect(screen.getByText('Recalculating...')).toBeInTheDocument();
    });

    it('should reload data after successful recalculation', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        const recalculateButton = screen.getByText('Recalculate ELO');
        fireEvent.click(recalculateButton);
      });

      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledTimes(2); // Once on mount, once after recalculation
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle seasons API error', async () => {
      apiService.getEloSeasons.mockRejectedValue(new Error('Seasons API Error'));

      render(<ELORankings />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load initial ELO data.')).toBeInTheDocument();
      });
    });

    it('should handle ELO ratings API error', async () => {
      apiService.getEloRatings.mockRejectedValue(new Error('ELO API Error'));

      render(<ELORankings />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load ELO rankings for season 2025.')).toBeInTheDocument();
      });
    });

    it('should handle recalculation error', async () => {
      apiService.recalculateEloRatings.mockRejectedValue(new Error('Recalculation Error'));

      render(<ELORankings />);
      
      await waitFor(() => {
        const recalculateButton = screen.getByText('Recalculate ELO');
        fireEvent.click(recalculateButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Failed to recalculate ELO ratings.')).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('should handle empty ELO data', async () => {
      apiService.getEloRatings.mockResolvedValue({
        data: { ratings: [] }
      });

      render(<ELORankings />);
      
      await waitFor(() => {
        expect(screen.getByText('No ELO rankings available for this season.')).toBeInTheDocument();
      });
    });

    it('should handle missing seasons data', async () => {
      apiService.getEloSeasons.mockResolvedValue({
        data: { seasons: [] }
      });

      render(<ELORankings />);
      
      await waitFor(() => {
        expect(screen.getByText('All NFL ELO Rankings')).toBeInTheDocument();
        // Should still render the component even with no seasons
      });
    });
  });

  describe('Data Formatting', () => {
    it('should format ratings to one decimal place', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        expect(screen.getAllByText('1703.7')).toHaveLength(2); // Table + summary
        expect(screen.getAllByText('1667.1')).toHaveLength(2); // Table + summary
      });
    });

    it('should format rating changes with appropriate signs', async () => {
      render(<ELORankings />);
      
      await waitFor(() => {
        expect(screen.getAllByText('+4.7')).toHaveLength(2); // Table + summary
        expect(screen.getAllByText('0.0')).toHaveLength(2); // Table + summary
        expect(screen.getAllByText('-2.1')).toHaveLength(2); // Table + summary
        expect(screen.getAllByText('-23.0')).toHaveLength(2); // Table + summary
      });
    });

    it('should handle missing team data gracefully', async () => {
      const incompleteData = [
        {
          team: null,
          rating: 1500.0,
          rating_change: 0.0,
          record: null,
          stats: null
        }
      ];

      apiService.getEloRatings.mockResolvedValue({
        data: { ratings: incompleteData }
      });

      render(<ELORankings />);
      
      await waitFor(() => {
        expect(screen.getByText('UNK')).toBeInTheDocument(); // Unknown team abbreviation
        expect(screen.getByText('Unknown Team')).toBeInTheDocument(); // Unknown team name
        expect(screen.getByText('0 - 0')).toBeInTheDocument(); // Default record (with spaces)
        expect(screen.getByText('0 - 0')).toBeInTheDocument(); // Default points (with spaces)
      });
    });
  });
});
