import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ExpertPicks from '../components/ExpertPicks';
import { apiService } from '../services/api';

// Mock the API service
jest.mock('../services/api', () => ({
  __esModule: true,
  default: {
    getActionNetworkExperts: jest.fn(),
    getActionNetworkPicks: jest.fn(),
    getActionNetworkAnalytics: jest.fn(),
  }
}));

describe('ExpertPicks Component', () => {
  const mockExperts = [
    {
      id: 1,
      name: 'Test Expert',
      username: 'testexpert',
      verified: true,
      followers: 1000,
      avatar_url: null,
      bio: null,
      social_media: null,
      specialties: null,
      created_at: '2025-09-06T14:07:59'
    }
  ];

  const mockPicks = [
    {
      id: 1,
      external_id: '123456',
      description: 'Test Pick',
      expert: {
        name: 'Test Expert',
        username: 'testexpert',
        verified: true
      },
      odds: -110,
      units: 1.0,
      units_net: 0.0,
      value: 10,
      result: 'pending',
      pick_type: 'spread',
      money: 100,
      money_net: 0,
      confidence_level: null,
      reasoning: null,
      timestamps: {
        created: '2025-09-06T15:11:44.121Z',
        starts: '2025-09-06T16:00:00.000Z',
        ends: '2025-09-07T06:59:59.999Z',
        settled: null
      },
      social: {
        likes: 0,
        copies: 0
      },
      trend: null,
      verified: true
    }
  ];

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Get the mocked API service
    const { default: mockedApiService } = require('../services/api');
    
    // Setup default mock responses
    mockedApiService.getActionNetworkExperts.mockResolvedValue({
      data: { experts: mockExperts }
    });
    
    mockedApiService.getActionNetworkPicks.mockResolvedValue({
      data: { picks: mockPicks }
    });
  });

  test('renders expert picks component', async () => {
    render(<ExpertPicks sport="nfl" />);
    
    // Wait for data to load and check if component renders without error
    await waitFor(() => {
      expect(screen.getByText('Expert Picks Analysis')).toBeInTheDocument();
      expect(screen.getByText('Action Network expert performance and picks')).toBeInTheDocument();
    });
  });

  test('displays expert data correctly', async () => {
    render(<ExpertPicks sport="nfl" />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Expert')).toBeInTheDocument();
      expect(screen.getByText('@testexpert')).toBeInTheDocument();
      expect(screen.getByText('1,000 followers')).toBeInTheDocument();
    });
  });

  test('displays picks data correctly', async () => {
    render(<ExpertPicks sport="nfl" />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Pick')).toBeInTheDocument();
      expect(screen.getByText('Odds: -110')).toBeInTheDocument();
      expect(screen.getByText('Units: 1.00')).toBeInTheDocument();
    });
  });

  test('calculates analytics correctly', async () => {
    const picksWithResults = [
      { ...mockPicks[0], result: 'win' },
      { ...mockPicks[0], id: 2, result: 'loss' },
      { ...mockPicks[0], id: 3, result: 'pending' }
    ];

    const { default: mockedApiService } = require('../services/api');
    mockedApiService.getActionNetworkPicks.mockResolvedValue({
      data: { picks: picksWithResults }
    });

    render(<ExpertPicks sport="nfl" />);
    
    await waitFor(() => {
      // Should show 3 total picks
      expect(screen.getByText('3')).toBeInTheDocument();
      // Should show 33.3% win rate (1 win out of 3 total)
      expect(screen.getByText('33.3%')).toBeInTheDocument();
    });
  });

  test('handles API errors gracefully', async () => {
    const { default: mockedApiService } = require('../services/api');
    mockedApiService.getActionNetworkExperts.mockRejectedValue(new Error('API Error'));
    mockedApiService.getActionNetworkPicks.mockRejectedValue(new Error('API Error'));

    render(<ExpertPicks sport="nfl" />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load expert picks data: API Error')).toBeInTheDocument();
    });
  });

  test('shows loading state initially', () => {
    // Don't set up mocks for this test to ensure loading state
    const { default: mockedApiService } = require('../services/api');
    mockedApiService.getActionNetworkExperts.mockImplementation(() => new Promise(() => {})); // Never resolves
    mockedApiService.getActionNetworkPicks.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<ExpertPicks sport="nfl" />);
    
    // Check that component renders without error (loading state)
    expect(screen.getByRole('generic')).toBeInTheDocument();
  });
});
