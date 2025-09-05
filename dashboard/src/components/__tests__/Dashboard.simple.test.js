import React from 'react';
import { render, screen } from '@testing-library/react';
import Dashboard from '../Dashboard';
import { apiService } from '../../services/api';

// Mock the API service
jest.mock('../../services/api');

describe('Dashboard Component - Simple Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders dashboard title', async () => {
    apiService.getTeamRankings.mockResolvedValue({ data: [] });
    apiService.getWeekPredictions.mockResolvedValue({ data: [] });
    apiService.getPerformanceMetrics.mockResolvedValue({ data: null });

    render(<Dashboard />);
    
    // Wait for loading to complete
    await screen.findByText('NFL Analytics Dashboard');
    expect(screen.getByText('NFL Analytics Dashboard')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    apiService.getTeamRankings.mockResolvedValue({ data: [] });
    apiService.getWeekPredictions.mockResolvedValue({ data: [] });
    apiService.getPerformanceMetrics.mockResolvedValue({ data: null });

    render(<Dashboard />);
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  it('calls API services on mount', async () => {
    apiService.getTeamRankings.mockResolvedValue({ data: [] });
    apiService.getWeekPredictions.mockResolvedValue({ data: [] });
    apiService.getPerformanceMetrics.mockResolvedValue({ data: null });

    render(<Dashboard />);
    
    // Wait for API calls to be made
    await screen.findByText('NFL Analytics Dashboard');
    
    expect(apiService.getTeamRankings).toHaveBeenCalled();
    expect(apiService.getWeekPredictions).toHaveBeenCalled();
    expect(apiService.getPerformanceMetrics).toHaveBeenCalled();
  });
});
