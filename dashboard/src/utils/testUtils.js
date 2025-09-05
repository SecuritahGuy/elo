import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Custom render function that includes providers
export const renderWithRouter = (ui, { route = '/' } = {}) => {
  window.history.pushState({}, 'Test page', route);
  return render(ui, { wrapper: BrowserRouter });
};

// Mock API responses
export const mockApiResponses = {
  eloSeasons: [2024, 2025],
  eloRatings: {
    ratings: [
      { team: 'PHI', rating: 1768.4, rank: 1, wins: 12, losses: 5, win_pct: 0.706, change: 3.2 },
      { team: 'BUF', rating: 1750.2, rank: 2, wins: 11, losses: 6, win_pct: 0.647, change: -1.5 },
      { team: 'BAL', rating: 1745.8, rank: 3, wins: 10, losses: 7, win_pct: 0.588, change: 2.1 }
    ]
  },
  injurySummary: {
    summary: {
      total_injuries: 5954,
      unique_players: 1433,
      teams_affected: 32
    },
    common_injuries: {
      'Knee': 506,
      'Ankle': 411,
      'Hamstring': 294
    },
    common_statuses: {
      'Out': 1091,
      'Questionable': 1464,
      'Doubtful': 190
    }
  },
  teamInjuries: {
    teams: [
      { team: 'PHI', total_injuries: 176, players_out: 3, players_questionable: 5 },
      { team: 'DAL', total_injuries: 223, players_out: 2, players_questionable: 7 }
    ]
  },
  systemStatus: {
    status: 'healthy',
    timestamp: '2024-01-01T00:00:00Z'
  }
};

// Helper to wait for async operations
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));
