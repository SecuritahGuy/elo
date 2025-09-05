import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import TeamRankings from '../TeamRankings';
import { apiService } from '../../services/api';

// Mock the API service
jest.mock('../../services/api');

// Helper function to render component with Router context
const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('TeamRankings Component', () => {
  const mockRankings = [
    { team: 'PHI', rating: 1765.2, rank: 1, wins: 0, losses: 0, win_pct: 0.0, change: 0.0 },
    { team: 'BUF', rating: 1724.3, rank: 2, wins: 0, losses: 0, win_pct: 0.0, change: 0.0 },
    { team: 'BAL', rating: 1722.3, rank: 3, wins: 0, losses: 0, win_pct: 0.0, change: 0.0 }
  ];

  const mockSeasons = [2024, 2025];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders team rankings title', () => {
    renderWithRouter(<TeamRankings />);
    expect(screen.getByText('Team Rankings')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    renderWithRouter(<TeamRankings />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays team rankings when data is loaded', async () => {
    apiService.getEloSeasons.mockResolvedValue({ data: { seasons: mockSeasons } });
    apiService.getEloRatings.mockResolvedValue({ data: { ratings: mockRankings } });
    apiService.getEloSeasonSummary.mockResolvedValue({ data: { summary: {} } });

    renderWithRouter(<TeamRankings />);

    await waitFor(() => {
      expect(screen.getByText('PHI')).toBeInTheDocument();
      expect(screen.getByText('BUF')).toBeInTheDocument();
      expect(screen.getByText('BAL')).toBeInTheDocument();
    });
  });

  it('displays team ratings correctly', async () => {
    apiService.getEloSeasons.mockResolvedValue({ data: { seasons: mockSeasons } });
    apiService.getEloRatings.mockResolvedValue({ data: { ratings: mockRankings } });
    apiService.getEloSeasonSummary.mockResolvedValue({ data: { summary: {} } });

    renderWithRouter(<TeamRankings />);

    await waitFor(() => {
      expect(screen.getByText('1765.2')).toBeInTheDocument();
      expect(screen.getByText('1724.3')).toBeInTheDocument();
      expect(screen.getByText('1722.3')).toBeInTheDocument();
    });
  });

  it('displays win/loss records', async () => {
    apiService.getEloSeasons.mockResolvedValue({ data: { seasons: mockSeasons } });
    apiService.getEloRatings.mockResolvedValue({ data: { ratings: mockRankings } });
    apiService.getEloSeasonSummary.mockResolvedValue({ data: { summary: {} } });

    renderWithRouter(<TeamRankings />);

    await waitFor(() => {
      expect(screen.getByText('0-0')).toBeInTheDocument();
    });
  });

  it('displays rating changes', async () => {
    apiService.getEloSeasons.mockResolvedValue({ data: { seasons: mockSeasons } });
    apiService.getEloRatings.mockResolvedValue({ data: { ratings: mockRankings } });
    apiService.getEloSeasonSummary.mockResolvedValue({ data: { summary: {} } });

    renderWithRouter(<TeamRankings />);

    await waitFor(() => {
      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });

  it('handles season selection', async () => {
    apiService.getEloSeasons.mockResolvedValue({ data: { seasons: mockSeasons } });
    apiService.getEloRatings.mockResolvedValue({ data: { ratings: mockRankings } });
    apiService.getEloSeasonSummary.mockResolvedValue({ data: { summary: {} } });

    renderWithRouter(<TeamRankings />);

    await waitFor(() => {
      const seasonSelect = screen.getByDisplayValue('2024');
      expect(seasonSelect).toBeInTheDocument();
    });

    // Change season
    const seasonSelect = screen.getByDisplayValue('2024');
    fireEvent.change(seasonSelect, { target: { value: '2025' } });

    await waitFor(() => {
      expect(apiService.getEloRatings).toHaveBeenCalledWith(2025, 'baseline');
    });
  });

  it('handles configuration selection', async () => {
    apiService.getEloSeasons.mockResolvedValue({ data: { seasons: mockSeasons } });
    apiService.getEloRatings.mockResolvedValue({ data: { ratings: mockRankings } });
    apiService.getEloSeasonSummary.mockResolvedValue({ data: { summary: {} } });

    renderWithRouter(<TeamRankings />);

    await waitFor(() => {
      const configSelect = screen.getByDisplayValue('baseline');
      expect(configSelect).toBeInTheDocument();
    });

    // Change configuration
    const configSelect = screen.getByDisplayValue('baseline');
    fireEvent.change(configSelect, { target: { value: 'weather_only' } });

    await waitFor(() => {
      expect(apiService.getEloRatings).toHaveBeenCalledWith(2024, 'weather_only');
    });
  });

  it('displays error message when API fails', async () => {
    apiService.getEloSeasons.mockRejectedValue(new Error('API Error'));

    renderWithRouter(<TeamRankings />);

    await waitFor(() => {
      expect(screen.getByText('Error loading rankings')).toBeInTheDocument();
    });
  });

  it('displays empty state when no data', async () => {
    apiService.getEloSeasons.mockResolvedValue({ data: { seasons: mockSeasons } });
    apiService.getEloRatings.mockResolvedValue({ data: { ratings: [] } });
    apiService.getEloSeasonSummary.mockResolvedValue({ data: { summary: {} } });

    renderWithRouter(<TeamRankings />);

    await waitFor(() => {
      expect(screen.getByText('No rankings available')).toBeInTheDocument();
    });
  });
});
