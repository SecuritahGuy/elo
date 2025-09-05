import React, { useState, useEffect } from 'react';
import { Trophy, Search, RefreshCw, TrendingUp, TrendingDown } from 'lucide-react';
import { apiService } from '../services/api';

const TeamRankings = () => {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('rank');

  const loadTeamRankings = async () => {
    try {
      setLoading(true);
      const response = await apiService.getTeamRankings();
      setTeams(response.data.teams);
    } catch (error) {
      console.error('Failed to load team rankings:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTeamRankings();
  }, []);

  const filteredTeams = teams.filter(team =>
    team.team.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedTeams = [...filteredTeams].sort((a, b) => {
    switch (sortBy) {
      case 'rating':
        return b.rating - a.rating;
      case 'team':
        return a.team.localeCompare(b.team);
      default:
        return a.rank - b.rank;
    }
  });

  const getRatingColor = (rating) => {
    if (rating >= 1700) return 'text-green-600';
    if (rating >= 1600) return 'text-blue-600';
    if (rating >= 1500) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRatingBarWidth = (rating) => {
    const minRating = 1200;
    const maxRating = 1800;
    return Math.max(0, Math.min(100, ((rating - minRating) / (maxRating - minRating)) * 100));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner w-8 h-8"></div>
        <span className="ml-2 text-gray-600">Loading team rankings...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Team Rankings</h1>
          <p className="text-gray-600">Current NFL team Elo ratings and rankings</p>
        </div>
        <button
          onClick={loadTeamRankings}
          className="flex items-center px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Controls */}
      <div className="dashboard-card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search teams..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
            >
              <option value="rank">Sort by Rank</option>
              <option value="rating">Sort by Rating</option>
              <option value="team">Sort by Team</option>
            </select>
          </div>
        </div>
      </div>

      {/* Team Rankings Table */}
      <div className="dashboard-card">
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
                  Rating
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rating Bar
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Updated
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedTeams.map((team, index) => (
                <tr key={team.team} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-nfl-primary text-white rounded-full flex items-center justify-center text-sm font-bold">
                        {team.rank}
                      </div>
                      {index < 3 && (
                        <Trophy className="w-4 h-4 text-nfl-accent ml-2" />
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="team-logo team-{team.team.toLowerCase()}">
                        {team.team}
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900">
                          {team.team}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm font-bold ${getRatingColor(team.rating)}`}>
                      {team.rating.toFixed(1)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-nfl-primary h-2 rounded-full transition-all duration-300"
                        style={{ width: `${getRatingBarWidth(team.rating)}%` }}
                      ></div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(team.last_updated).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="dashboard-card text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Highest Rated</h3>
          <p className="text-2xl font-bold text-nfl-primary">
            {teams.length > 0 ? teams[0].team : 'N/A'}
          </p>
          <p className="text-sm text-gray-500">
            {teams.length > 0 ? teams[0].rating.toFixed(1) : 'N/A'}
          </p>
        </div>
        <div className="dashboard-card text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Average Rating</h3>
          <p className="text-2xl font-bold text-nfl-secondary">
            {teams.length > 0 ? (teams.reduce((sum, team) => sum + team.rating, 0) / teams.length).toFixed(1) : 'N/A'}
          </p>
        </div>
        <div className="dashboard-card text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Teams</h3>
          <p className="text-2xl font-bold text-nfl-accent">
            {teams.length}
          </p>
        </div>
      </div>
    </div>
  );
};

export default TeamRankings;
