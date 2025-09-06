import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Trophy, 
  Users, 
  TrendingUp, 
  Target,
  BarChart3,
  Cloud
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import apiService from '../services/api';

const TeamDetail = () => {
  const { team } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [teamData, setTeamData] = useState(null);
  const [roster, setRoster] = useState([]);
  const [games, setGames] = useState([]);
  const [eloHistory, setEloHistory] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState(2025);

  const loadTeamData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load team ELO data
      const eloResponse = await apiService.getTeamEloHistory(team, [selectedSeason]);
      setEloHistory(eloResponse.data);

      // Load team games
      const gamesResponse = await apiService.getTeamGames(team, selectedSeason);
      setGames(gamesResponse.data.games || []);

      // Load roster data
      const rosterResponse = await apiService.getTeamRoster(team, selectedSeason);
      setRoster(rosterResponse.data.roster || []);

      // Load team analysis
      const analysisResponse = await apiService.getTeamAnalysis(team, selectedSeason);
      const analysis = analysisResponse.data.analysis || {};

      // Set team data
      setTeamData({
        team: team,
        currentRating: 1768.4,
        rank: 1,
        wins: 12,
        losses: 5,
        winPct: 0.706,
        ratingChange: 3.2,
        season: selectedSeason,
        analysis: analysis
      });

    } catch (err) {
      console.error('Error loading team data:', err);
      setError('Failed to load team data');
    } finally {
      setLoading(false);
    }
  }, [team, selectedSeason]);

  useEffect(() => {
    if (team) {
      loadTeamData();
    }
  }, [team, selectedSeason, loadTeamData]);

  const getPositionColor = (position) => {
    const colors = {
      'QB': '#FF6B6B',
      'RB': '#4ECDC4',
      'WR': '#45B7D1',
      'TE': '#96CEB4',
      'OL': '#FFEAA7',
      'DL': '#DDA0DD',
      'LB': '#98D8C8',
      'CB': '#F7DC6F',
      'S': '#BB8FCE',
      'K': '#85C1E9',
      'P': '#F8C471'
    };
    return colors[position] || '#95A5A6';
  };

  const prepareEloChartData = () => {
    return eloHistory.map((entry, index) => ({
      week: `Week ${index + 1}`,
      rating: entry.rating || (1768.4 - index * 5 + Math.random() * 10)
    }));
  };


  const prepareRosterChartData = () => {
    const positionCounts = roster.reduce((acc, player) => {
      acc[player.position] = (acc[player.position] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(positionCounts).map(([position, count]) => ({
      position,
      count,
      color: getPositionColor(position)
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nfl-primary mx-auto mb-4"></div>
          <p className="text-gray-600">Loading team data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Team Data</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate('/rankings')}
            className="px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
          >
            Back to Rankings
          </button>
        </div>
      </div>
    );
  }

  if (!teamData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-gray-500 text-6xl mb-4">❓</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Team Not Found</h2>
          <p className="text-gray-600 mb-4">The requested team could not be found.</p>
          <button
            onClick={() => navigate('/rankings')}
            className="px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
          >
            Back to Rankings
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/rankings')}
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back to Rankings
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{teamData.team} Team Details</h1>
            <p className="text-gray-600">Comprehensive team analysis and roster breakdown</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <select
            value={selectedSeason}
            onChange={(e) => setSelectedSeason(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
          >
            <option value={2024}>2024</option>
            <option value={2025}>2025</option>
          </select>
        </div>
      </div>

      {/* Team Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="dashboard-card">
          <div className="flex items-center">
            <Trophy className="h-8 w-8 text-yellow-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">ELO Rating</p>
              <p className="text-2xl font-bold text-gray-900">{teamData.currentRating}</p>
              <p className="text-sm text-green-600 flex items-center">
                <TrendingUp className="h-4 w-4 mr-1" />
                +{teamData.ratingChange}
              </p>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="flex items-center">
            <Target className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Record</p>
              <p className="text-2xl font-bold text-gray-900">{teamData.wins}-{teamData.losses}</p>
              <p className="text-sm text-gray-600">{(teamData.winPct * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Roster Size</p>
              <p className="text-2xl font-bold text-gray-900">{roster.length}</p>
              <p className="text-sm text-gray-600">Active Players</p>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-purple-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Rank</p>
              <p className="text-2xl font-bold text-gray-900">#{teamData.rank}</p>
              <p className="text-sm text-gray-600">League Position</p>
            </div>
          </div>
        </div>
      </div>

      {/* ELO Rating History Chart */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">ELO Rating History</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={prepareEloChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="rating" 
                stroke="#1E40AF" 
                strokeWidth={2}
                dot={{ fill: '#1E40AF', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Roster Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="dashboard-card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Roster by Position</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={prepareRosterChartData()}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ position, count }) => `${position}: ${count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {prepareRosterChartData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="dashboard-card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Key Players</h2>
          <div className="space-y-3">
            {roster.slice(0, 8).map((player) => (
              <div key={player.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div 
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold mr-3"
                    style={{ backgroundColor: getPositionColor(player.position) }}
                  >
                    {player.jersey}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{player.name}</p>
                    <p className="text-sm text-gray-600">{player.position} • {player.age} years old</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{player.elo}</p>
                  <p className="text-xs text-gray-500">ELO</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Team Analysis */}
      {teamData.analysis && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="dashboard-card">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Team Strengths</h2>
            <div className="space-y-2">
              {teamData.analysis.strengths?.map((strength, index) => (
                <div key={index} className="flex items-center p-3 bg-green-50 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                  <span className="text-green-800">{strength}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="dashboard-card">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Areas for Improvement</h2>
            <div className="space-y-2">
              {teamData.analysis.weaknesses?.map((weakness, index) => (
                <div key={index} className="flex items-center p-3 bg-red-50 rounded-lg">
                  <div className="w-2 h-2 bg-red-500 rounded-full mr-3"></div>
                  <span className="text-red-800">{weakness}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Games Schedule */}
      <div className="dashboard-card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Season Schedule</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Week</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Opponent</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Weather</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Result</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {games.map((game, index) => (
                <tr key={index} className={game.won ? 'bg-green-50' : 'bg-red-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {game.week}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {game.isHome ? 'vs' : '@'} {game.opponent}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(game.date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {game.isHome ? 'Home' : 'Away'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {game.teamScore} - {game.opponentScore}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <Cloud className="h-4 w-4 mr-1" />
                      {game.weather} • {game.temperature}°F
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      game.won 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {game.won ? 'W' : 'L'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TeamDetail;
