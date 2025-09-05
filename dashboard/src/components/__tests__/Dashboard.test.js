import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import Dashboard from '../Dashboard';
import { apiService } from '../../services/api';

// Mock the API service
jest.mock('../../services/api');

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders dashboard title', () => {
    render(<Dashboard />);
    expect(screen.getByText('NFL ELO Dashboard')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    render(<Dashboard />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays team rankings when data is loaded', async () => {
    const mockRankings = [
      { team: 'PHI', rating: 1768.4, rank: 1, wins: 12, losses: 5 },
      { team: 'BUF', rating: 1750.2, rank: 2, wins: 11, losses: 6 }
    ];

    apiService.getTeamRankings.mockResolvedValue({ data: mockRankings });
    apiService.getWeekPredictions.mockResolvedValue({ data: [] });
    apiService.getPerformanceMetrics.mockResolvedValue({ data: null });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Team Rankings')).toBeInTheDocument();
      expect(screen.getByText('PHI')).toBeInTheDocument();
      expect(screen.getByText('BUF')).toBeInTheDocument();
    });
  });

  it('displays error message when API fails', async () => {
    apiService.getTeamRankings.mockRejectedValue(new Error('API Error'));

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Error loading dashboard data')).toBeInTheDocument();
    });
  });

  it('displays performance metrics when available', async () => {
    const mockMetrics = {
      accuracy: 62.6,
      brier_score: 0.2278,
      total_games: 1406
    };

    apiService.getTeamRankings.mockResolvedValue({ data: [] });
    apiService.getWeekPredictions.mockResolvedValue({ data: [] });
    apiService.getPerformanceMetrics.mockResolvedValue({ data: mockMetrics });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
      expect(screen.getByText('62.6%')).toBeInTheDocument();
    });
  });
});
