import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ELOVisualizations from '../ELOVisualizations';
import apiService from '../../services/api';

// Mock the API service
jest.mock('../../services/api', () => ({
  getEloSeasons: jest.fn(),
  getEloRatings: jest.fn(),
  getTeamEloHistory: jest.fn(),
}));

// Mock Recharts components
jest.mock('recharts', () => ({
  LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
  Line: ({ dataKey }) => <div data-testid={`line-${dataKey}`}>Line: {dataKey}</div>,
  XAxis: ({ dataKey }) => <div data-testid={`x-axis-${dataKey}`}>XAxis: {dataKey}</div>,
  YAxis: () => <div data-testid="y-axis">YAxis</div>,
  CartesianGrid: () => <div data-testid="cartesian-grid">CartesianGrid</div>,
  Tooltip: () => <div data-testid="tooltip">Tooltip</div>,
  Legend: () => <div data-testid="legend">Legend</div>,
  ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }) => <div data-testid="bar-chart">{children}</div>,
  Bar: ({ dataKey }) => <div data-testid={`bar-${dataKey}`}>Bar: {dataKey}</div>,
}));

const mockEloData = [
  {
    team: { abbreviation: 'PHI' },
    rating: 1703.7,
    rating_change: 4.7,
    record: { wins: 10, losses: 2 }
  },
  {
    team: { abbreviation: 'BUF' },
    rating: 1667.1,
    rating_change: 0.0,
    record: { wins: 8, losses: 4 }
  },
  {
    team: { abbreviation: 'SF' },
    rating: 1650.3,
    rating_change: -2.1,
    record: { wins: 7, losses: 5 }
  }
];

const mockTeamHistory = [
  { week: 1, rating: 1650.0, change: 0.0 },
  { week: 2, rating: 1665.0, change: 15.0 },
  { week: 3, rating: 1670.0, change: 5.0 },
  { week: 4, rating: 1703.7, change: 33.7 }
];

describe('ELOVisualizations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    apiService.getEloSeasons.mockResolvedValue({
      data: { seasons: [2024, 2025] }
    });
    apiService.getEloRatings.mockResolvedValue({
      data: { ratings: mockEloData }
    });
    apiService.getTeamEloHistory.mockResolvedValue({
      data: mockTeamHistory
    });
  });

  describe('Initial Load', () => {
    it('should render loading state initially', () => {
      render(<ELOVisualizations />);
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument(); // Spinner element
    });

    it('should load ELO data on mount', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        expect(apiService.getEloSeasons).toHaveBeenCalled();
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2025);
      });
    });

    it('should render visualization content after loading', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        expect(screen.getByText('ELO Rating Trends')).toBeInTheDocument();
        expect(screen.getByText('Team Comparison')).toBeInTheDocument();
      });
    });
  });

  describe('Team Selection', () => {
    it('should render team selection dropdown', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        expect(screen.getByText('Select Teams to Compare')).toBeInTheDocument();
        expect(screen.getByText('PHI')).toBeInTheDocument();
        expect(screen.getByText('BUF')).toBeInTheDocument();
        expect(screen.getByText('SF')).toBeInTheDocument();
      });
    });

    it('should allow selecting multiple teams', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        const phiCheckbox = screen.getByLabelText('PHI');
        const bufCheckbox = screen.getByLabelText('BUF');
        
        fireEvent.click(phiCheckbox);
        fireEvent.click(bufCheckbox);
        
        expect(phiCheckbox).toBeChecked();
        expect(bufCheckbox).toBeChecked();
      });
    });

    it('should load team history when teams are selected', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        const phiCheckbox = screen.getByLabelText('PHI');
        fireEvent.click(phiCheckbox);
      });

      await waitFor(() => {
        expect(apiService.getTeamEloHistory).toHaveBeenCalledWith('PHI', [2025]);
      });
    });
  });

  describe('Rating Trends Chart', () => {
    it('should render rating trends chart', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
        expect(screen.getByTestId('line-rating')).toBeInTheDocument();
        expect(screen.getByTestId('x-axis-week')).toBeInTheDocument();
        expect(screen.getByTestId('y-axis')).toBeInTheDocument();
      });
    });

    it('should display chart with selected teams data', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        const phiCheckbox = screen.getByLabelText('PHI');
        fireEvent.click(phiCheckbox);
      });

      await waitFor(() => {
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      });
    });
  });

  describe('Team Comparison Chart', () => {
    it('should render team comparison chart', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
        expect(screen.getByTestId('bar-rating')).toBeInTheDocument();
        expect(screen.getByTestId('x-axis-team')).toBeInTheDocument();
      });
    });

    it('should display current ratings for all teams', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
        // Should show all teams' current ratings
      });
    });
  });

  describe('Data Processing', () => {
    it('should process team trends data correctly', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        const phiCheckbox = screen.getByLabelText('PHI');
        fireEvent.click(phiCheckbox);
      });

      await waitFor(() => {
        // Should process the team history data for visualization
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      });
    });

    it('should handle missing team data gracefully', async () => {
      const incompleteData = [
        {
          team: null,
          rating: 1500.0,
          rating_change: 0.0,
          record: null
        }
      ];

      apiService.getEloRatings.mockResolvedValue({
        data: { ratings: incompleteData }
      });

      render(<ELOVisualizations />);
      
      await waitFor(() => {
        expect(screen.getByText('ELO Rating Trends')).toBeInTheDocument();
        // Should handle missing team data without crashing
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle ELO ratings API error', async () => {
      apiService.getEloSeasons.mockRejectedValue(new Error('Seasons API Error'));

      render(<ELOVisualizations />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load initial data')).toBeInTheDocument();
      });
    });

    it('should handle team history API error', async () => {
      apiService.getTeamEloHistory.mockRejectedValue(new Error('History API Error'));

      render(<ELOVisualizations />);
      
      await waitFor(() => {
        const phiCheckbox = screen.getByLabelText('PHI');
        fireEvent.click(phiCheckbox);
      });

      await waitFor(() => {
        expect(screen.getByText('Failed to load visualization data')).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('should handle empty ELO data', async () => {
      apiService.getEloRatings.mockResolvedValue({
        data: { ratings: [] }
      });

      render(<ELOVisualizations />);
      
      await waitFor(() => {
        expect(screen.getByText('ELO Rating Trends')).toBeInTheDocument();
        // Should still render the component even with empty data
      });
    });

    it('should handle empty team history data', async () => {
      apiService.getTeamEloHistory.mockResolvedValue({
        data: []
      });

      render(<ELOVisualizations />);
      
      await waitFor(() => {
        const phiCheckbox = screen.getByLabelText('PHI');
        fireEvent.click(phiCheckbox);
      });

      await waitFor(() => {
        // Should handle empty history data gracefully
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      });
    });
  });

  describe('Chart Interactions', () => {
    it('should update charts when team selection changes', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        const phiCheckbox = screen.getByLabelText('PHI');
        fireEvent.click(phiCheckbox);
      });

      await waitFor(() => {
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      });

      // Select another team
      await waitFor(() => {
        const bufCheckbox = screen.getByLabelText('BUF');
        fireEvent.click(bufCheckbox);
      });

      await waitFor(() => {
        expect(apiService.getTeamEloHistory).toHaveBeenCalledWith('BUF', [2025]);
      });
    });

    it('should clear selection when teams are deselected', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        const phiCheckbox = screen.getByLabelText('PHI');
        fireEvent.click(phiCheckbox);
      });

      await waitFor(() => {
        expect(phiCheckbox).toBeChecked();
      });

      // Deselect team
      await waitFor(() => {
        fireEvent.click(phiCheckbox);
      });

      await waitFor(() => {
        expect(phiCheckbox).not.toBeChecked();
      });
    });
  });

  describe('Responsive Design', () => {
    it('should render responsive containers', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        const responsiveContainers = screen.getAllByTestId('responsive-container');
        expect(responsiveContainers.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Chart Configuration', () => {
    it('should render chart with proper tooltips and legends', async () => {
      render(<ELOVisualizations />);
      
      await waitFor(() => {
        expect(screen.getByTestId('tooltip')).toBeInTheDocument();
        expect(screen.getByTestId('legend')).toBeInTheDocument();
        expect(screen.getByTestId('cartesian-grid')).toBeInTheDocument();
      });
    });
  });
});
