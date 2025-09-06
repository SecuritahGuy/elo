import React, { useState, useEffect } from 'react';
import { 
  Trophy, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  RefreshCw,
  ArrowUp,
  ArrowDown,
  Minus as MinusIcon
} from 'lucide-react';
import apiService from '../services/api';

const ELORankings = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [eloData, setEloData] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState(2025);
  const [availableSeasons, setAvailableSeasons] = useState([]);
  const [recalculating, setRecalculating] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedSeason) {
      loadELORankings();
    }
  }, [selectedSeason]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      
      // Load available seasons
      const seasonsResponse = await apiService.getEloSeasons();
      const seasons = seasonsResponse.data.seasons?.map(s => s.season || s) || [2020, 2021, 2022, 2023, 2024, 2025];
      setAvailableSeasons(seasons);
      
    } catch (error) {
      console.error('Error loading initial data:', error);
      setError('Failed to load initial data');
    } finally {
      setLoading(false);
    }
  };

  const loadELORankings = async () => {
    try {
      setLoading(true);
      const response = await apiService.getEloRatings(selectedSeason);
      
      if (response.data && response.data.ratings) {
        setEloData(response.data.ratings);
      } else {
        setError('No ELO data available');
      }
    } catch (error) {
      console.error('Error loading ELO rankings:', error);
      setError('Failed to load ELO rankings');
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    try {
      setRecalculating(true);
      const response = await apiService.recalculateEloRatings();
      
      if (response.data.status === 'success') {
        // Reload data after recalculation
        await loadELORankings();
      } else {
        setError('Failed to recalculate ELO ratings');
      }
    } catch (error) {
      console.error('Error recalculating ELO ratings:', error);
      setError('Failed to recalculate ELO ratings');
    } finally {
      setRecalculating(false);
    }
  };

  const getChangeIcon = (change) => {
    if (change > 0) return <ArrowUp className="h-4 w-4 text-green-600" />;
    if (change < 0) return <ArrowDown className="h-4 w-4 text-red-600" />;
    return <MinusIcon className="h-4 w-4 text-gray-400" />;
  };

  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-500';
  };

  const formatChange = (change) => {
    if (change > 0) return `+${change.toFixed(1)}`;
    if (change < 0) return change.toFixed(1);
    return '0.0';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 text-nfl-primary animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading ELO rankings...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 mb-4">
            <Trophy className="h-12 w-12 mx-auto mb-2" />
            <p className="text-lg font-semibold">Error Loading Rankings</p>
            <p className="text-sm">{error}</p>
          </div>
          <button
            onClick={loadELORankings}
            className="bg-nfl-primary text-white px-4 py-2 rounded-lg hover:bg-nfl-secondary transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <Trophy className="h-8 w-8 text-nfl-primary mr-3" />
                NFL ELO Rankings
              </h1>
              <p className="text-gray-600 mt-2">
                Complete team rankings based on ELO rating system
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Season Selector */}
              <select
                value={selectedSeason}
                onChange={(e) => setSelectedSeason(parseInt(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
              >
                {availableSeasons.map(season => (
                  <option key={season} value={season}>{season}</option>
                ))}
              </select>
              
              {/* Recalculate Button */}
              <button
                onClick={handleRecalculate}
                disabled={recalculating}
                className="bg-nfl-primary text-white px-4 py-2 rounded-lg hover:bg-nfl-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {recalculating ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                {recalculating ? 'Recalculating...' : 'Recalculate'}
              </button>
            </div>
          </div>
        </div>

        {/* Rankings Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              Team Rankings - {selectedSeason} Season
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {eloData.length} teams ranked by ELO rating
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Team
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ELO Rating
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Change
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Record
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Points
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {eloData.map((team, index) => {
                  const teamName = team.team?.name || 'Unknown Team';
                  const teamAbbr = team.team?.abbreviation || 'UNK';
                  const teamCity = team.team?.city || '';
                  const rating = team.rating?.toFixed(1) || '0.0';
                  const change = team.rating_change || 0;
                  const wins = team.record?.wins || 0;
                  const losses = team.record?.losses || 0;
                  const ties = team.record?.ties || 0;
                  const pointsFor = team.stats?.points_for || 0;
                  const pointsAgainst = team.stats?.points_against || 0;
                  
                  return (
                    <tr key={teamAbbr} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-nfl-primary text-white rounded-full flex items-center justify-center text-sm font-bold">
                            {index + 1}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center">
                              <span className="text-sm font-bold text-gray-700">{teamAbbr}</span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{teamName}</div>
                            <div className="text-sm text-gray-500">{teamCity}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-gray-900">{rating}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`flex items-center text-sm font-medium ${getChangeColor(change)}`}>
                          {getChangeIcon(change)}
                          <span className="ml-1">{formatChange(change)}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {wins}-{losses}{ties > 0 ? `-${ties}` : ''}
                        </div>
                        <div className="text-xs text-gray-500">
                          {wins + losses + ties > 0 ? 
                            `${((wins / (wins + losses + ties)) * 100).toFixed(1)}%` : 
                            '0.0%'
                          }
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {pointsFor}-{pointsAgainst}
                        </div>
                        <div className="text-xs text-gray-500">
                          {pointsFor - pointsAgainst > 0 ? '+' : ''}{pointsFor - pointsAgainst}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Trophy className="h-8 w-8 text-yellow-500 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-500">Highest Rating</p>
                <p className="text-2xl font-bold text-gray-900">
                  {eloData.length > 0 ? eloData[0].rating?.toFixed(1) : '0.0'}
                </p>
                <p className="text-sm text-gray-600">
                  {eloData.length > 0 ? eloData[0].team?.abbreviation : 'N/A'}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-500 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-500">Biggest Gain</p>
                <p className="text-2xl font-bold text-gray-900">
                  {eloData.length > 0 ? 
                    Math.max(...eloData.map(t => t.rating_change || 0)).toFixed(1) : 
                    '0.0'
                  }
                </p>
                <p className="text-sm text-gray-600">
                  {eloData.length > 0 ? 
                    eloData.find(t => t.rating_change === Math.max(...eloData.map(t => t.rating_change || 0)))?.team?.abbreviation || 'N/A' : 
                    'N/A'
                  }
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <TrendingDown className="h-8 w-8 text-red-500 mr-3" />
              <div>
                <p className="text-sm font-medium text-gray-500">Biggest Drop</p>
                <p className="text-2xl font-bold text-gray-900">
                  {eloData.length > 0 ? 
                    Math.min(...eloData.map(t => t.rating_change || 0)).toFixed(1) : 
                    '0.0'
                  }
                </p>
                <p className="text-sm text-gray-600">
                  {eloData.length > 0 ? 
                    eloData.find(t => t.rating_change === Math.min(...eloData.map(t => t.rating_change || 0)))?.team?.abbreviation || 'N/A' : 
                    'N/A'
                  }
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ELORankings;
