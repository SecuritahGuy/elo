import React, { useState, useEffect } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  AreaChart,
  Area
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Target,
  Calendar,
  BarChart3,
  LineChart as LineChartIcon
} from 'lucide-react';
import apiService from '../services/api';

const ELOVisualizations = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeason, setSelectedSeason] = useState(2025);
  const [selectedTeams, setSelectedTeams] = useState(['PHI', 'DAL', 'BUF', 'BAL']);
  const [availableSeasons, setAvailableSeasons] = useState([]);
  const [availableTeams, setAvailableTeams] = useState([]);
  const [eloHistory, setEloHistory] = useState([]);
  const [teamTrends, setTeamTrends] = useState([]);
  const [ratingDistribution, setRatingDistribution] = useState([]);
  const [weeklyChanges, setWeeklyChanges] = useState([]);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedSeason) {
      loadVisualizationData();
    }
  }, [selectedSeason, selectedTeams]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      
      // Load available seasons
      const seasonsResponse = await apiService.getEloSeasons();
      setAvailableSeasons(seasonsResponse.data.seasons || [2020, 2021, 2022, 2023, 2024, 2025]);
      
      // Load available teams
      const teamsResponse = await apiService.getEloRatings(selectedSeason);
      const teams = teamsResponse.data.ratings?.map(team => team.team) || [];
      setAvailableTeams(teams);
      
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError('Failed to load initial data');
    } finally {
      setLoading(false);
    }
  };

  const loadVisualizationData = async () => {
    try {
      setLoading(true);
      
      // Load ELO history for selected teams
      const historyPromises = selectedTeams.map(team => 
        apiService.getTeamEloHistory(team, [selectedSeason])
      );
      const historyResponses = await Promise.all(historyPromises);
      
      // Process ELO history data
      const processedHistory = processEloHistory(historyResponses);
      setEloHistory(processedHistory);
      
      // Load team trends
      const trendsData = await loadTeamTrends();
      setTeamTrends(trendsData);
      
      // Load rating distribution
      const distributionData = await loadRatingDistribution();
      setRatingDistribution(distributionData);
      
      // Load weekly changes
      const changesData = await loadWeeklyChanges();
      setWeeklyChanges(changesData);
      
    } catch (err) {
      console.error('Error loading visualization data:', err);
      setError('Failed to load visualization data');
    } finally {
      setLoading(false);
    }
  };

  const processEloHistory = (responses) => {
    const historyData = [];
    const maxWeeks = 18; // Regular season weeks
    
    for (let week = 1; week <= maxWeeks; week++) {
      const weekData = { week: `Week ${week}` };
      
      responses.forEach((response, index) => {
        const team = selectedTeams[index];
        const teamData = response.data.history?.[0] || {};
        
        // Simulate weekly progression (in real implementation, this would come from API)
        const baseRating = teamData.rating || 1500;
        const weeklyChange = (Math.random() - 0.5) * 20; // Simulate weekly changes
        const rating = baseRating + (weeklyChange * (week - 1));
        
        weekData[team] = Math.round(rating);
      });
      
      historyData.push(weekData);
    }
    
    return historyData;
  };

  const loadTeamTrends = async () => {
    // Simulate team trend data
    return [
      { team: 'PHI', trend: 'up', change: 15.2, games: 3 },
      { team: 'DAL', trend: 'down', change: -8.7, games: 3 },
      { team: 'BUF', trend: 'stable', change: 2.1, games: 2 },
      { team: 'BAL', trend: 'up', change: 12.4, games: 2 }
    ];
  };

  const loadRatingDistribution = async () => {
    // Simulate rating distribution data
    return [
      { range: '1600+', count: 8, percentage: 25 },
      { range: '1500-1599', count: 12, percentage: 37.5 },
      { range: '1400-1499', count: 8, percentage: 25 },
      { range: '1300-1399', count: 4, percentage: 12.5 }
    ];
  };

  const loadWeeklyChanges = async () => {
    // Simulate weekly changes data
    return [
      { week: 'Week 1', avgChange: 3.2, maxChange: 12.4, minChange: -8.7 },
      { week: 'Week 2', avgChange: 1.8, maxChange: 8.9, minChange: -5.2 },
      { week: 'Week 3', avgChange: 2.5, maxChange: 10.1, minChange: -6.8 }
    ];
  };

  const handleTeamSelection = (team) => {
    if (selectedTeams.includes(team)) {
      setSelectedTeams(selectedTeams.filter(t => t !== team));
    } else if (selectedTeams.length < 4) {
      setSelectedTeams([...selectedTeams, team]);
    }
  };

  const getTeamColor = (team) => {
    const colors = {
      'PHI': '#004C54',
      'DAL': '#003594',
      'BUF': '#00338D',
      'BAL': '#241773',
      'KC': '#E31837',
      'GB': '#203731',
      'SF': '#AA0000',
      'LAR': '#003594'
    };
    return colors[team] || '#6B7280';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nfl-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">{error}</p>
        <button 
          onClick={loadInitialData}
          className="px-4 py-2 bg-nfl-primary text-white rounded hover:bg-nfl-primary-dark"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ELO Visualizations</h1>
          <p className="text-gray-600">Advanced ELO rating analysis and trends</p>
        </div>
        
        {/* Season Selector */}
        <div className="mt-4 sm:mt-0">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Season
          </label>
          <select
            value={selectedSeason}
            onChange={(e) => setSelectedSeason(parseInt(e.target.value))}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-nfl-primary focus:border-nfl-primary"
          >
            {availableSeasons.map(season => (
              <option key={season} value={season}>{season}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Team Selection */}
      <div className="dashboard-card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Teams to Compare</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
          {availableTeams.map(team => (
            <button
              key={team}
              onClick={() => handleTeamSelection(team)}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedTeams.includes(team)
                  ? 'bg-nfl-primary text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {team}
            </button>
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-2">
          Selected: {selectedTeams.join(', ')} ({selectedTeams.length}/4)
        </p>
      </div>

      {/* ELO History Chart */}
      <div className="dashboard-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">ELO Rating History</h2>
          <LineChartIcon className="h-5 w-5 text-gray-400" />
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={eloHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis domain={[1300, 1800]} />
              <Tooltip 
                formatter={(value, name) => [value, name]}
                labelFormatter={(label) => `Week: ${label}`}
              />
              <Legend />
              {selectedTeams.map(team => (
                <Line
                  key={team}
                  type="monotone"
                  dataKey={team}
                  stroke={getTeamColor(team)}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  connectNulls={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Team Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Team Trend Analysis */}
        <div className="dashboard-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Team Trends</h2>
            <TrendingUp className="h-5 w-5 text-gray-400" />
          </div>
          <div className="space-y-3">
            {teamTrends.map((trend, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-nfl-primary text-white rounded-full flex items-center justify-center text-sm font-bold mr-3">
                    {trend.team}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{trend.team}</p>
                    <p className="text-sm text-gray-500">{trend.games} games</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`flex items-center ${
                    trend.trend === 'up' ? 'text-green-600' : 
                    trend.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {trend.trend === 'up' ? <TrendingUp className="h-4 w-4 mr-1" /> :
                     trend.trend === 'down' ? <TrendingDown className="h-4 w-4 mr-1" /> :
                     <Activity className="h-4 w-4 mr-1" />}
                    <span className="font-semibold">
                      {trend.change > 0 ? '+' : ''}{trend.change.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Rating Distribution */}
        <div className="dashboard-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Rating Distribution</h2>
            <BarChart3 className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ratingDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip 
                  formatter={(value, name) => [value, name === 'count' ? 'Teams' : 'Percentage']}
                />
                <Bar dataKey="count" fill="#004C54" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Weekly Changes */}
      <div className="dashboard-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Weekly Rating Changes</h2>
          <Calendar className="h-5 w-5 text-gray-400" />
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={weeklyChanges}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [value, name]}
                labelFormatter={(label) => `Week: ${label}`}
              />
              <Area 
                type="monotone" 
                dataKey="avgChange" 
                stackId="1" 
                stroke="#004C54" 
                fill="#004C54" 
                fillOpacity={0.6}
              />
              <Area 
                type="monotone" 
                dataKey="maxChange" 
                stackId="2" 
                stroke="#10B981" 
                fill="#10B981" 
                fillOpacity={0.3}
              />
              <Area 
                type="monotone" 
                dataKey="minChange" 
                stackId="3" 
                stroke="#EF4444" 
                fill="#EF4444" 
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default ELOVisualizations;
