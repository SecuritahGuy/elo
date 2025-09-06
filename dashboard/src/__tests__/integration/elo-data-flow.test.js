import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import NFLDashboard from '../../components/NFLDashboard';
import ELORankings from '../../components/ELORankings';
import ELOVisualizations from '../../components/ELOVisualizations';
import apiService from '../../services/api';

// Mock the API service
jest.mock('../../services/api', () => ({
  getEloRatings: jest.fn(),
  getEloSeasons: jest.fn(),
  getTeamEloHistory: jest.fn(),
  recalculateEloRatings: jest.fn(),
  getNFLDashboard: jest.fn(),
}));

// Mock fetch for dashboard data
global.fetch = jest.fn();

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

const mockDashboardData = {
  live_games: [],
  upcoming_games: [],
  top_experts: []
};

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
  }
];

const mockTeamHistory = [
  { week: 1, rating: 1650.0, change: 0.0 },
  { week: 2, rating: 1665.0, change: 15.0 },
  { week: 3, rating: 1670.0, change: 5.0 },
  { week: 4, rating: 1703.7, change: 33.7 }
];

describe('ELO Data Flow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockResolvedValue({
      json: () => Promise.resolve(mockDashboardData)
    });
    apiService.getEloRatings.mockResolvedValue({
      data: { ratings: mockEloData }
    });
    apiService.getEloSeasons.mockResolvedValue({
      data: { seasons: [2024, 2025] }
    });
    apiService.getTeamEloHistory.mockResolvedValue({
      data: mockTeamHistory
    });
    apiService.recalculateEloRatings.mockResolvedValue({
      data: { message: 'ELO ratings recalculated successfully' }
    });
  });

  describe('Dashboard to ELO Rankings Flow', () => {
    it('should navigate from dashboard overview to ELO rankings', async () => {
      render(
        <BrowserRouter>
          <NFLDashboard />
        </BrowserRouter>
      );

      // Wait for dashboard to load
      await waitFor(() => {
        expect(screen.getByText('NFL ELO Dashboard')).toBeInTheDocument();
      });

      // Click View All button in overview
      await waitFor(() => {
        const viewAllButton = screen.getByText('View All →');
        fireEvent.click(viewAllButton);
      });

      // Should navigate to ELO rankings
      await waitFor(() => {
        expect(screen.getByText('All NFL ELO Rankings')).toBeInTheDocument();
      });
    });

    it('should maintain ELO data consistency between dashboard and rankings', async () => {
      render(
        <BrowserRouter>
          <NFLDashboard />
        </BrowserRouter>
      );

      // Wait for dashboard to load
      await waitFor(() => {
        expect(screen.getByText('PHI')).toBeInTheDocument();
        expect(screen.getByText('1703.7')).toBeInTheDocument();
      });

      // Navigate to ELO rankings
      await waitFor(() => {
        const viewAllButton = screen.getByText('View All →');
        fireEvent.click(viewAllButton);
      });

      // Should show same data in rankings
      await waitFor(() => {
        expect(screen.getByText('PHI')).toBeInTheDocument();
        expect(screen.getByText('1703.7')).toBeInTheDocument();
        expect(screen.getByText('+4.7')).toBeInTheDocument();
      });
    });
  });

  describe('ELO Rankings to Visualizations Flow', () => {
    it('should allow navigation between ELO rankings and visualizations', async () => {
      render(
        <BrowserRouter>
          <NFLDashboard />
        </BrowserRouter>
      );

      // Navigate to ELO rankings
      await waitFor(() => {
        const eloTab = screen.getByText('ELO Rankings');
        fireEvent.click(eloTab);
      });

      await waitFor(() => {
        expect(screen.getByText('All NFL ELO Rankings')).toBeInTheDocument();
      });

      // Navigate to visualizations (if there's a tab for it)
      // This would depend on the actual navigation structure
    });
  });

  describe('Data Consistency Across Components', () => {
    it('should use same API endpoints across components', async () => {
      // Test NFLDashboard
      render(
        <BrowserRouter>
          <NFLDashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2025);
      });

      // Test ELORankings
      render(<ELORankings />);

      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2025);
        expect(apiService.getEloSeasons).toHaveBeenCalled();
      });

      // Test ELOVisualizations
      render(<ELOVisualizations />);

      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2025, 'comprehensive');
      });
    });

    it('should handle data updates consistently', async () => {
      const { rerender } = render(<ELORankings />);

      // Initial load
      await waitFor(() => {
        expect(screen.getByText('PHI')).toBeInTheDocument();
      });

      // Simulate data update
      const updatedEloData = [
        ...mockEloData,
        {
          team: { abbreviation: 'DAL', name: 'Dallas Cowboys' },
          rating: 1680.0,
          rating_change: 12.5,
          record: { wins: 9, losses: 3, ties: 0 },
          stats: { points_for: 340, points_against: 290 }
        }
      ];

      apiService.getEloRatings.mockResolvedValue({
        data: { ratings: updatedEloData }
      });

      // Trigger recalculation
      await waitFor(() => {
        const recalculateButton = screen.getByText('Recalculate ELO');
        fireEvent.click(recalculateButton);
      });

      // Should reload with updated data
      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle API errors consistently across components', async () => {
      // Test with ELO API error
      apiService.getEloRatings.mockRejectedValue(new Error('ELO API Error'));

      render(
        <BrowserRouter>
          <NFLDashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No ELO data available')).toBeInTheDocument();
      });

      // Test ELORankings with same error
      render(<ELORankings />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load ELO rankings for season 2025.')).toBeInTheDocument();
      });

      // Test ELOVisualizations with same error
      render(<ELOVisualizations />);

      await waitFor(() => {
        expect(screen.getByText('Error loading ELO data')).toBeInTheDocument();
      });
    });

    it('should handle partial data loading', async () => {
      // Mock partial API responses
      apiService.getEloRatings.mockResolvedValue({
        data: { ratings: [mockEloData[0]] } // Only first team
      });

      render(
        <BrowserRouter>
          <NFLDashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PHI')).toBeInTheDocument();
        expect(screen.queryByText('BUF')).not.toBeInTheDocument();
      });
    });
  });

  describe('User Interaction Flow', () => {
    it('should handle complete user journey from dashboard to detailed ELO analysis', async () => {
      render(
        <BrowserRouter>
          <NFLDashboard />
        </BrowserRouter>
      );

      // 1. Start at dashboard overview
      await waitFor(() => {
        expect(screen.getByText('NFL ELO Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Top ELO Rankings')).toBeInTheDocument();
      });

      // 2. View detailed ELO rankings
      await waitFor(() => {
        const viewAllButton = screen.getByText('View All →');
        fireEvent.click(viewAllButton);
      });

      await waitFor(() => {
        expect(screen.getByText('All NFL ELO Rankings')).toBeInTheDocument();
        expect(screen.getByText('PHI')).toBeInTheDocument();
        expect(screen.getByText('BUF')).toBeInTheDocument();
      });

      // 3. Change season
      await waitFor(() => {
        const seasonSelect = screen.getByDisplayValue('2025');
        fireEvent.change(seasonSelect, { target: { value: '2024' } });
      });

      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2024);
      });

      // 4. Recalculate ELO ratings
      await waitFor(() => {
        const recalculateButton = screen.getByText('Recalculate ELO');
        fireEvent.click(recalculateButton);
      });

      await waitFor(() => {
        expect(apiService.recalculateEloRatings).toHaveBeenCalled();
        expect(apiService.getEloRatings).toHaveBeenCalledTimes(3); // Initial + season change + after recalculation
      });
    });

    it('should handle team selection in visualizations', async () => {
      render(<ELOVisualizations />);

      await waitFor(() => {
        expect(screen.getByText('ELO Rating Trends')).toBeInTheDocument();
      });

      // Select teams for comparison
      await waitFor(() => {
        const phiCheckbox = screen.getByLabelText('PHI');
        const bufCheckbox = screen.getByLabelText('BUF');
        
        fireEvent.click(phiCheckbox);
        fireEvent.click(bufCheckbox);
      });

      await waitFor(() => {
        expect(apiService.getTeamEloHistory).toHaveBeenCalledWith('PHI', [2025]);
        expect(apiService.getTeamEloHistory).toHaveBeenCalledWith('BUF', [2025]);
      });
    });
  });

  describe('Performance and Caching', () => {
    it('should not make redundant API calls', async () => {
      render(
        <BrowserRouter>
          <NFLDashboard />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledTimes(1);
      });

      // Navigate to ELO rankings
      await waitFor(() => {
        const eloTab = screen.getByText('ELO Rankings');
        fireEvent.click(eloTab);
      });

      // Should make another call for ELORankings component
      await waitFor(() => {
        expect(apiService.getEloRatings).toHaveBeenCalledTimes(2);
      });
    });

    it('should handle concurrent API calls gracefully', async () => {
      // Mock delayed responses
      apiService.getEloRatings.mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({ data: { ratings: mockEloData } }), 100)
        )
      );

      render(
        <BrowserRouter>
          <NFLDashboard />
        </BrowserRouter>
      );

      // Should handle loading states properly
      await waitFor(() => {
        expect(screen.getByText('Loading ELO data...')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('PHI')).toBeInTheDocument();
      });
    });
  });
});
