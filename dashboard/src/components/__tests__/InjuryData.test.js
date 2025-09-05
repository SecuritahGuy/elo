import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import InjuryData from '../InjuryData';
import { apiService } from '../../services/api';

// Mock the API service
jest.mock('../../services/api');

describe('InjuryData Component', () => {
  const mockInjurySummary = {
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
  };

  const mockTeamInjuries = [
    { team: 'PHI', total_injuries: 176, players_out: 3, players_questionable: 5 },
    { team: 'DAL', total_injuries: 223, players_out: 2, players_questionable: 7 }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders injury data title', () => {
    render(<InjuryData />);
    expect(screen.getByText('Injury Data')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    render(<InjuryData />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays injury summary when data is loaded', async () => {
    apiService.getInjurySummary.mockResolvedValue({ data: mockInjurySummary });
    apiService.getTeamInjuries.mockResolvedValue({ data: { teams: mockTeamInjuries } });

    render(<InjuryData />);

    await waitFor(() => {
      expect(screen.getByText('5954')).toBeInTheDocument();
      expect(screen.getByText('1433')).toBeInTheDocument();
      expect(screen.getByText('32')).toBeInTheDocument();
    });
  });

  it('displays team injuries', async () => {
    apiService.getInjurySummary.mockResolvedValue({ data: mockInjurySummary });
    apiService.getTeamInjuries.mockResolvedValue({ data: { teams: mockTeamInjuries } });

    render(<InjuryData />);

    await waitFor(() => {
      expect(screen.getByText('PHI')).toBeInTheDocument();
      expect(screen.getByText('DAL')).toBeInTheDocument();
      expect(screen.getByText('176')).toBeInTheDocument();
      expect(screen.getByText('223')).toBeInTheDocument();
    });
  });

  it('handles season selection', async () => {
    apiService.getInjurySummary.mockResolvedValue({ data: mockInjurySummary });
    apiService.getTeamInjuries.mockResolvedValue({ data: { teams: mockTeamInjuries } });

    render(<InjuryData />);

    await waitFor(() => {
      const seasonSelect = screen.getByDisplayValue('2025');
      expect(seasonSelect).toBeInTheDocument();
    });

    // Change season
    const seasonSelect = screen.getByDisplayValue('2025');
    fireEvent.change(seasonSelect, { target: { value: '2024' } });

    await waitFor(() => {
      expect(apiService.getInjurySummary).toHaveBeenCalledWith(2024);
      expect(apiService.getTeamInjuries).toHaveBeenCalledWith(2024, 1);
    });
  });

  it('handles week selection', async () => {
    apiService.getInjurySummary.mockResolvedValue({ data: mockInjurySummary });
    apiService.getTeamInjuries.mockResolvedValue({ data: { teams: mockTeamInjuries } });

    render(<InjuryData />);

    await waitFor(() => {
      const weekSelect = screen.getByDisplayValue('1');
      expect(weekSelect).toBeInTheDocument();
    });

    // Change week
    const weekSelect = screen.getByDisplayValue('1');
    fireEvent.change(weekSelect, { target: { value: '5' } });

    await waitFor(() => {
      expect(apiService.getTeamInjuries).toHaveBeenCalledWith(2025, 5);
    });
  });

  it('handles team selection', async () => {
    apiService.getInjurySummary.mockResolvedValue({ data: mockInjurySummary });
    apiService.getTeamInjuries.mockResolvedValue({ data: { teams: mockTeamInjuries } });
    apiService.getTeamInjuryHistory.mockResolvedValue({ data: { weeks: [] } });
    apiService.getPlayerInjuries.mockResolvedValue({ data: { players: [] } });

    render(<InjuryData />);

    await waitFor(() => {
      const teamSelect = screen.getByDisplayValue('All Teams');
      expect(teamSelect).toBeInTheDocument();
    });

    // Select a team
    const teamSelect = screen.getByDisplayValue('All Teams');
    fireEvent.change(teamSelect, { target: { value: 'PHI' } });

    await waitFor(() => {
      expect(apiService.getTeamInjuryHistory).toHaveBeenCalledWith('PHI', 2025);
      expect(apiService.getPlayerInjuries).toHaveBeenCalledWith(2025, 1, 'PHI');
    });
  });

  it('displays error message when no data available', async () => {
    const emptySummary = {
      summary: {
        total_injuries: 0,
        unique_players: 0,
        teams_affected: 0
      },
      message: 'No injury data available for 2025'
    };

    apiService.getInjurySummary.mockResolvedValue({ data: emptySummary });

    render(<InjuryData />);

    await waitFor(() => {
      expect(screen.getByText(/No injury data available for 2025/)).toBeInTheDocument();
    });
  });

  it('displays error message when API fails', async () => {
    apiService.getInjurySummary.mockRejectedValue(new Error('API Error'));

    render(<InjuryData />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load injury data. Please try a different season.')).toBeInTheDocument();
    });
  });

  it('displays debug information when available', async () => {
    apiService.getInjurySummary.mockResolvedValue({ data: mockInjurySummary });
    apiService.getTeamInjuries.mockResolvedValue({ data: { teams: mockTeamInjuries } });

    render(<InjuryData />);

    await waitFor(() => {
      expect(screen.getByText(/Current selectedSeason: 2025/)).toBeInTheDocument();
      expect(screen.getByText(/Total Injuries: 5954/)).toBeInTheDocument();
    });
  });
});
