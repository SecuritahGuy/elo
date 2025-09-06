import React, { useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';
import { TrendingUp, TrendingDown, BarChart3, Calendar, RefreshCw } from 'lucide-react';

const TeamComparison = () => {
  const [selectedTeams, setSelectedTeams] = useState([]);
  const [availableTeams] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);
  const [season, setSeason] = useState(2025);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  // NFL team options
  const nflTeams = [
    { code: 'ARI', name: 'Arizona Cardinals' },
    { code: 'ATL', name: 'Atlanta Falcons' },
    { code: 'BAL', name: 'Baltimore Ravens' },
    { code: 'BUF', name: 'Buffalo Bills' },
    { code: 'CAR', name: 'Carolina Panthers' },
    { code: 'CHI', name: 'Chicago Bears' },
    { code: 'CIN', name: 'Cincinnati Bengals' },
    { code: 'CLE', name: 'Cleveland Browns' },
    { code: 'DAL', name: 'Dallas Cowboys' },
    { code: 'DEN', name: 'Denver Broncos' },
    { code: 'DET', name: 'Detroit Lions' },
    { code: 'GB', name: 'Green Bay Packers' },
    { code: 'HOU', name: 'Houston Texans' },
    { code: 'IND', name: 'Indianapolis Colts' },
    { code: 'JAX', name: 'Jacksonville Jaguars' },
    { code: 'KC', name: 'Kansas City Chiefs' },
    { code: 'LV', name: 'Las Vegas Raiders' },
    { code: 'LAC', name: 'Los Angeles Chargers' },
    { code: 'LAR', name: 'Los Angeles Rams' },
    { code: 'MIA', name: 'Miami Dolphins' },
    { code: 'MIN', name: 'Minnesota Vikings' },
    { code: 'NE', name: 'New England Patriots' },
    { code: 'NO', name: 'New Orleans Saints' },
    { code: 'NYG', name: 'New York Giants' },
    { code: 'NYJ', name: 'New York Jets' },
    { code: 'PHI', name: 'Philadelphia Eagles' },
    { code: 'PIT', name: 'Pittsburgh Steelers' },
    { code: 'SF', name: 'San Francisco 49ers' },
    { code: 'SEA', name: 'Seattle Seahawks' },
    { code: 'TB', name: 'Tampa Bay Buccaneers' },
    { code: 'TEN', name: 'Tennessee Titans' },
    { code: 'WAS', name: 'Washington Commanders' }
  ];

  const loadComparisonData = useCallback(async () => {
    if (selectedTeams.length === 0) {
      setComparisonData([]);
      return;
    }

    try {
      setLoading(true);
      const response = await apiService.getEloTeamComparison(selectedTeams, season);
      setComparisonData(response.data.teams || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load comparison data:', error);
      setComparisonData([]);
    } finally {
      setLoading(false);
    }
  }, [selectedTeams, season]);

  useEffect(() => {
    loadComparisonData();
  }, [loadComparisonData]);

  const handleTeamToggle = (teamCode) => {
    setSelectedTeams(prev => {
      if (prev.includes(teamCode)) {
        return prev.filter(t => t !== teamCode);
      } else if (prev.length < 6) { // Limit to 6 teams for readability
        return [...prev, teamCode];
      }
      return prev;
    });
  };

  const getRatingColor = (rating) => {
    if (rating >= 1600) return 'text-green-600';
    if (rating >= 1500) return 'text-blue-600';
    if (rating >= 1400) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getChangeIcon = (change) => {
    if (change > 0) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (change < 0) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <BarChart3 className="w-4 h-4 text-gray-500" />;
  };

  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getTeamName = (teamCode) => {
    const team = nflTeams.find(t => t.code === teamCode);
    return team ? team.name : teamCode;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Team Comparison</h1>
          <p className="text-gray-600">Compare ELO ratings and performance across teams</p>
        </div>
        <div className="flex items-center space-x-4">
          {/* Season Selector */}
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <select
              value={season}
              onChange={(e) => setSeason(parseInt(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
            >
              <option value={2025}>2025</option>
              <option value={2024}>2024</option>
            </select>
          </div>
          <button
            onClick={loadComparisonData}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Team Selection */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Select Teams to Compare</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
          {nflTeams.map(team => (
            <button
              key={team.code}
              onClick={() => handleTeamToggle(team.code)}
              disabled={!selectedTeams.includes(team.code) && selectedTeams.length >= 6}
              className={`p-3 rounded-lg border-2 transition-colors text-sm font-medium ${
                selectedTeams.includes(team.code)
                  ? 'border-nfl-primary bg-nfl-primary text-white'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed'
              }`}
            >
              {team.code}
            </button>
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-2">
          {selectedTeams.length}/6 teams selected
        </p>
      </div>

      {/* Comparison Results */}
      {selectedTeams.length > 0 && (
        <div className="dashboard-card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              Team Comparison - {season} Season
            </h2>
            <div className="text-sm text-gray-500">
              {lastUpdated && `Last updated: ${lastUpdated.toLocaleTimeString()}`}
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="loading-spinner w-8 h-8"></div>
              <span className="ml-2 text-gray-600">Loading comparison data...</span>
            </div>
          ) : comparisonData.length > 0 ? (
            <div className="space-y-4">
              {/* Header Row */}
              <div className="grid grid-cols-12 gap-4 p-3 bg-gray-50 rounded-lg font-semibold text-gray-700">
                <div className="col-span-2">Team</div>
                <div className="col-span-2">ELO Rating</div>
                <div className="col-span-2">Change</div>
                <div className="col-span-2">Record</div>
                <div className="col-span-2">Win %</div>
                <div className="col-span-2">Rank</div>
              </div>

              {/* Team Rows */}
              {comparisonData.map((team, index) => (
                <div key={team.team} className="grid grid-cols-12 gap-4 p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="col-span-2 flex items-center">
                    <div className="w-8 h-8 bg-nfl-primary text-white rounded-full flex items-center justify-center text-sm font-bold mr-3">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{team.team}</p>
                      <p className="text-xs text-gray-500">{getTeamName(team.team)}</p>
                    </div>
                  </div>
                  <div className="col-span-2 flex items-center">
                    <span className={`text-lg font-bold ${getRatingColor(team.rating)}`}>
                      {team.rating}
                    </span>
                  </div>
                  <div className="col-span-2 flex items-center">
                    <div className="flex items-center space-x-1">
                      {getChangeIcon(team.change)}
                      <span className={`text-sm font-semibold ${getChangeColor(team.change)}`}>
                        {team.change > 0 ? '+' : ''}{team.change}
                      </span>
                    </div>
                  </div>
                  <div className="col-span-2 flex items-center">
                    <span className="text-sm font-medium text-gray-900">
                      {team.wins}-{team.losses}
                    </span>
                  </div>
                  <div className="col-span-2 flex items-center">
                    <span className="text-sm font-medium text-gray-900">
                      {team.win_pct ? (team.win_pct * 100).toFixed(1) : 0}%
                    </span>
                  </div>
                  <div className="col-span-2 flex items-center">
                    <span className="text-sm font-medium text-gray-600">
                      #{team.rank}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No comparison data available for selected teams
            </div>
          )}
        </div>
      )}

      {/* Quick Comparison Suggestions */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Comparisons</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <button
            onClick={() => setSelectedTeams(['PHI', 'DAL', 'NYG', 'WAS'])}
            className="p-4 border border-gray-200 rounded-lg hover:border-nfl-primary hover:bg-gray-50 transition-colors text-left"
          >
            <h3 className="font-semibold text-gray-900">NFC East</h3>
            <p className="text-sm text-gray-500">Compare division rivals</p>
          </button>
          <button
            onClick={() => setSelectedTeams(['KC', 'BUF', 'BAL', 'CIN'])}
            className="p-4 border border-gray-200 rounded-lg hover:border-nfl-primary hover:bg-gray-50 transition-colors text-left"
          >
            <h3 className="font-semibold text-gray-900">Top AFC Teams</h3>
            <p className="text-sm text-gray-500">Compare conference leaders</p>
          </button>
          <button
            onClick={() => setSelectedTeams(['SF', 'DET', 'GB', 'MIN'])}
            className="p-4 border border-gray-200 rounded-lg hover:border-nfl-primary hover:bg-gray-50 transition-colors text-left"
          >
            <h3 className="font-semibold text-gray-900">NFC North</h3>
            <p className="text-sm text-gray-500">Compare division teams</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default TeamComparison;
