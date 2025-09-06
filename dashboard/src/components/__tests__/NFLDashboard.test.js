import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import NFLDashboard from '../NFLDashboard';
import apiService from '../../services/api';

// Mock the API service
jest.mock('../../services/api', () => ({
  getEloRatings: jest.fn(),
  getNFLDashboard: jest.fn(),
}));

// Mock child components
jest.mock('../LiveGames', () => {
  return function MockLiveGames() {
    return <div data-testid="live-games">Live Games Component</div>;
  };
});

jest.mock('../UpcomingGames', () => {
  return function MockUpcomingGames() {
    return <div data-testid="upcoming-games">Upcoming Games Component</div>;
  };
});

jest.mock('../TeamStandings', () => {
  return function MockTeamStandings() {
    return <div data-testid="team-standings">Team Standings Component</div>;
  };
});

jest.mock('../ExpertPicks', () => {
  return function MockExpertPicks() {
    return <div data-testid="expert-picks">Expert Picks Component</div>;
  };
});

jest.mock('../SportAnalysis', () => {
  return function MockSportAnalysis() {
    return <div data-testid="sport-analysis">Sport Analysis Component</div>;
  };
});

jest.mock('../ELORankings', () => {
  return function MockELORankings() {
    return <div data-testid="elo-rankings">ELO Rankings Component</div>;
  };
});

jest.mock('../ELOVisualizations', () => {
  return function MockELOVisualizations() {
    return <div data-testid="elo-visualizations">ELO Visualizations Component</div>;
  };
});

// Mock fetch for dashboard data
global.fetch = jest.fn();

const mockDashboardData = {
  live_games: [
    { id: 1, home_team: 'PHI', away_team: 'DAL', status: 'live' }
  ],
  upcoming_games: [
    { id: 2, home_team: 'BUF', away_team: 'MIA', date: '2025-01-12' }
  ],
  top_experts: [
    { name: 'Expert 1', accuracy: 0.85 }
  ]
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
  },
  {
    team: { abbreviation: 'SF', name: 'San Francisco 49ers' },
    rating: 1650.3,
    rating_change: -2.1,
    record: { wins: 7, losses: 5, ties: 0 },
    stats: { points_for: 310, points_against: 290 }
  }
];

const renderNFLDashboard = () => {
  return render(
    <BrowserRouter>
      <NFLDashboard />
    </BrowserRouter>
  );
};

describe('NFLDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockResolvedValue({
      json: () => Promise.resolve(mockDashboardData)
    });
    apiService.getEloRatings.mockResolvedValue({
      data: { ratings: mockEloData }
    });
  });

  describe('Initial Load', () => {
    it('should render loading state initially', () => {
      renderNFLDashboard();
      // Check for skeleton loading elements
      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    });

    it('should load dashboard and ELO data on mount', async () => {
      renderNFLDashboard();
      
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/sports/nfl/dashboard');
        expect(apiService.getEloRatings).toHaveBeenCalledWith(2025);
      });
    });

    it('should render dashboard content after loading', async () => {
      renderNFLDashboard();
      
      await waitFor(() => {
        expect(screen.getByText('NFL ELO Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('should render navigation tabs', async () => {
      renderNFLDashboard();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Live Scores')).toBeInTheDocument();
        expect(screen.getByText('Schedules')).toBeInTheDocument();
        expect(screen.getByText('Standings')).toBeInTheDocument();
        expect(screen.getByText('Expert Picks')).toBeInTheDocument();
        expect(screen.getByText('Analysis')).toBeInTheDocument();
        expect(screen.getByText('ELO Rankings')).toBeInTheDocument();
      });
    });

    it('should switch sections when navigation tabs are clicked', async () => {
      renderNFLDashboard();
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      // Click on Live Scores tab
      fireEvent.click(screen.getByText('Live Scores'));
      expect(screen.getByTestId('live-games')).toBeInTheDocument();

      // Click on Schedules tab
      fireEvent.click(screen.getByText('Schedules'));
      expect(screen.getByTestId('upcoming-games')).toBeInTheDocument();

      // Click on Standings tab
      fireEvent.click(screen.getByText('Standings'));
      expect(screen.getByTestId('team-standings')).toBeInTheDocument();

      // Click on Expert Picks tab
      fireEvent.click(screen.getByText('Expert Picks'));
      expect(screen.getByTestId('expert-picks')).toBeInTheDocument();

      // Click on Analysis tab
      fireEvent.click(screen.getByText('Analysis'));
      expect(screen.getByTestId('sport-analysis')).toBeInTheDocument();

      // Click on ELO Rankings tab
      fireEvent.click(screen.getByText('ELO Rankings'));
      expect(screen.getByTestId('elo-rankings')).toBeInTheDocument();
    });
  });

  describe('Overview Section', () => {
    it('should display ELO rankings in overview', async () => {
      renderNFLDashboard();
      
      await waitFor(() => {
        expect(screen.getByText('Top ELO Rankings')).toBeInTheDocument();
        expect(screen.getByText('PHI')).toBeInTheDocument();
        expect(screen.getByText('1703.7')).toBeInTheDocument();
        expect(screen.getByText('+4.7')).toBeInTheDocument();
      });
    });

    it('should display correct number of top teams', async () => {
      renderNFLDashboard();
      
      await waitFor(() => {
        // Should show top 5 teams
        expect(screen.getByText('PHI')).toBeInTheDocument();
        expect(screen.getByText('BUF')).toBeInTheDocument();
        expect(screen.getByText('SF')).toBeInTheDocument();
      });
    });

    it('should handle missing ELO data gracefully', async () => {
      apiService.getEloRatings.mockResolvedValue({
        data: { ratings: [] }
      });

      renderNFLDashboard();
      
      await waitFor(() => {
        expect(screen.getByText('No ELO data available')).toBeInTheDocument();
      });
    });

    it('should show loading state for ELO data', async () => {
      // Delay the ELO response
      apiService.getEloRatings.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: { ratings: mockEloData } }), 100))
      );

      renderNFLDashboard();
      
      await waitFor(() => {
        expect(screen.getByText('Loading ELO data...')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      fetch.mockRejectedValue(new Error('API Error'));
      apiService.getEloRatings.mockRejectedValue(new Error('ELO API Error'));

      renderNFLDashboard();
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
      });
    });

    it('should handle partial data loading', async () => {
      fetch.mockResolvedValue({
        json: () => Promise.resolve(mockDashboardData)
      });
      apiService.getEloRatings.mockRejectedValue(new Error('ELO API Error'));

      renderNFLDashboard();
      
      await waitFor(() => {
        expect(screen.getByText('NFL ELO Dashboard')).toBeInTheDocument();
        expect(screen.getByText('No ELO data available')).toBeInTheDocument();
      });
    });
  });

  describe('View All Button', () => {
    it('should navigate to ELO rankings when View All is clicked', async () => {
      renderNFLDashboard();
      
      await waitFor(() => {
        expect(screen.getByText('View All →')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('View All →'));
      
      expect(screen.getByTestId('elo-rankings')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('should render mobile navigation on small screens', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 640,
      });

      renderNFLDashboard();
      
      await waitFor(() => {
        expect(screen.getByText('NFL ELO Dashboard')).toBeInTheDocument();
      });
    });
  });
});
