import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import { 
  AlertTriangle, 
  Users, 
  Activity, 
  Calendar,
  TrendingUp,
  Shield,
  UserCheck,
  UserX
} from 'lucide-react';
import apiService from '../services/api';

const InjuryData = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeason, setSelectedSeason] = useState(2025);
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [selectedTeam, setSelectedTeam] = useState('');
  const [injurySummary, setInjurySummary] = useState(null);
  const [teamInjuries, setTeamInjuries] = useState([]);
  const [teamInjuryHistory, setTeamInjuryHistory] = useState([]);
  const [playerInjuries, setPlayerInjuries] = useState([]);

  useEffect(() => {
    loadInjuryData();
  }, [selectedSeason, selectedWeek, selectedTeam]);

  // Debug: Log when injurySummary changes
  useEffect(() => {
    if (injurySummary) {
      console.log(`injurySummary state updated for ${selectedSeason}:`, {
        total_injuries: injurySummary.summary?.total_injuries,
        unique_players: injurySummary.summary?.unique_players,
        teams_affected: injurySummary.summary?.teams_affected
      });
    }
  }, [injurySummary, selectedSeason]);

  const loadInjuryData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`Loading injury data for season: ${selectedSeason}`);
      
      // Load injury summary
      const summaryResponse = await apiService.getInjurySummary(selectedSeason);
      console.log(`Injury summary response for ${selectedSeason}:`, summaryResponse.data);
      console.log(`Total injuries for ${selectedSeason}:`, summaryResponse.data.summary.total_injuries);
      console.log(`Unique players for ${selectedSeason}:`, summaryResponse.data.summary.unique_players);
      setInjurySummary(summaryResponse.data);
      
      // Debug: Log what will be displayed in UI
      console.log(`UI will display for ${selectedSeason}:`, {
        total_injuries: summaryResponse.data.summary.total_injuries,
        unique_players: summaryResponse.data.summary.unique_players,
        teams_affected: summaryResponse.data.summary.teams_affected
      });
      
      // Check if we have data
      if (summaryResponse.data.summary.total_injuries === 0) {
        setError(`No injury data available for ${selectedSeason}. ${summaryResponse.data.message || 'Please try a different season.'}`);
        setTeamInjuries([]);
        setTeamInjuryHistory([]);
        setPlayerInjuries([]);
        return;
      }
      
      // Load team injuries for current week
      const teamResponse = await apiService.getTeamInjuries(selectedSeason, selectedWeek);
      setTeamInjuries(teamResponse.data.teams || []);
      
      // Load team injury history if team is selected
      if (selectedTeam) {
        const historyResponse = await apiService.getTeamInjuryHistory(selectedTeam, selectedSeason);
        setTeamInjuryHistory(historyResponse.data.weeks || []);
        
        // Load player injuries for selected team
        const playerResponse = await apiService.getPlayerInjuries(selectedSeason, selectedWeek, selectedTeam);
        setPlayerInjuries(playerResponse.data.players || []);
      } else {
        setTeamInjuryHistory([]);
        setPlayerInjuries([]);
      }
      
    } catch (err) {
      console.error('Error loading injury data:', err);
      setError('Failed to load injury data. Please try a different season.');
      setInjurySummary(null);
      setTeamInjuries([]);
      setTeamInjuryHistory([]);
      setPlayerInjuries([]);
    } finally {
      setLoading(false);
    }
  };

  const getInjuryStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'out':
        return '#EF4444'; // Red
      case 'doubtful':
        return '#F59E0B'; // Yellow
      case 'questionable':
        return '#F97316'; // Orange
      case 'probable':
        return '#10B981'; // Green
      default:
        return '#6B7280'; // Gray
    }
  };

  const getInjuryStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'out':
        return <UserX className="h-4 w-4" />;
      case 'doubtful':
        return <AlertTriangle className="h-4 w-4" />;
      case 'questionable':
        return <Activity className="h-4 w-4" />;
      case 'probable':
        return <UserCheck className="h-4 w-4" />;
      default:
        return <Shield className="h-4 w-4" />;
    }
  };

  const prepareInjuryChartData = () => {
    if (!injurySummary?.common_injuries) return [];
    
    return Object.entries(injurySummary.common_injuries).map(([injury, count]) => ({
      injury: injury || 'Unknown',
      count,
      percentage: ((count / injurySummary.summary.total_injuries) * 100).toFixed(1)
    }));
  };

  const prepareStatusChartData = () => {
    if (!injurySummary?.common_statuses) return [];
    
    return Object.entries(injurySummary.common_statuses).map(([status, count]) => ({
      status: status || 'Unknown',
      count,
      percentage: ((count / injurySummary.summary.total_injuries) * 100).toFixed(1)
    }));
  };

  const prepareTeamChartData = () => {
    return teamInjuries.map(team => ({
      team: team.team,
      injuries: team.total_injuries,
      out: team.status_breakdown?.Out || 0,
      doubtful: team.status_breakdown?.Doubtful || 0,
      questionable: team.status_breakdown?.Questionable || 0,
      probable: team.status_breakdown?.Probable || 0
    }));
  };

  const prepareHistoryChartData = () => {
    return teamInjuryHistory.map(week => ({
      week: `Week ${week.week}`,
      injuries: week.total_injuries
    }));
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
          onClick={loadInjuryData}
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
          <h1 className="text-2xl font-bold text-gray-900">Injury Data</h1>
          <p className="text-gray-600">NFL injury reports and analysis</p>
        </div>
        
        {/* Controls */}
        <div className="mt-4 sm:mt-0 flex flex-col sm:flex-row gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Season</label>
            <select
              value={selectedSeason}
              onChange={(e) => {
                const newSeason = parseInt(e.target.value);
                console.log(`Season selector changed from ${selectedSeason} to ${newSeason}`);
                setSelectedSeason(newSeason);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-nfl-primary focus:border-nfl-primary"
            >
              <option value={2025}>2025</option>
              <option value={2024}>2024</option>
              <option value={2023}>2023</option>
              <option value={2022}>2022</option>
              <option value={2021}>2021</option>
              <option value={2020}>2020</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Week</label>
            <select
              value={selectedWeek}
              onChange={(e) => setSelectedWeek(parseInt(e.target.value))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-nfl-primary focus:border-nfl-primary"
            >
              {Array.from({ length: 18 }, (_, i) => i + 1).map(week => (
                <option key={week} value={week}>Week {week}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Team</label>
            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-nfl-primary focus:border-nfl-primary"
            >
              <option value="">All Teams</option>
              {teamInjuries.map(team => (
                <option key={team.team} value={team.team}>{team.team}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Debug info */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
        <p className="text-sm text-yellow-800">
          <strong>Debug:</strong> Current selectedSeason: {selectedSeason} | 
          Total Injuries: {injurySummary?.summary?.total_injuries || 'Loading...'} | 
          Unique Players: {injurySummary?.summary?.unique_players || 'Loading...'}
        </p>
      </div>

      {/* Summary Cards */}
      {injurySummary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="dashboard-card">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-red-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Injuries</p>
                <p className="text-2xl font-bold text-gray-900">{injurySummary.summary.total_injuries}</p>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Players Affected</p>
                <p className="text-2xl font-bold text-gray-900">{injurySummary.summary.unique_players}</p>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Teams Affected</p>
                <p className="text-2xl font-bold text-gray-900">{injurySummary.summary.teams_affected}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Common Injuries */}
        <div className="dashboard-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Most Common Injuries</h2>
            <AlertTriangle className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={prepareInjuryChartData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="injury" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip 
                  formatter={(value, name) => [value, name === 'count' ? 'Injuries' : 'Percentage']}
                />
                <Bar dataKey="count" fill="#004C54" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Injury Status Distribution */}
        <div className="dashboard-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Injury Status Distribution</h2>
            <Activity className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={prepareStatusChartData()}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ status, percentage }) => `${status}: ${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {prepareStatusChartData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getInjuryStatusColor(entry.status)} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Team Injuries Chart */}
      <div className="dashboard-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Team Injuries by Status</h2>
          <Users className="h-5 w-5 text-gray-400" />
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={prepareTeamChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="team" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="out" stackId="a" fill="#EF4444" name="Out" />
              <Bar dataKey="doubtful" stackId="a" fill="#F59E0B" name="Doubtful" />
              <Bar dataKey="questionable" stackId="a" fill="#F97316" name="Questionable" />
              <Bar dataKey="probable" stackId="a" fill="#10B981" name="Probable" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Team Injury History */}
      {selectedTeam && teamInjuryHistory.length > 0 && (
        <div className="dashboard-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">{selectedTeam} Injury History</h2>
            <TrendingUp className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={prepareHistoryChartData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip formatter={(value, name) => [value, 'Injuries']} />
                <Line type="monotone" dataKey="injuries" stroke="#004C54" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Player Injuries Table */}
      {selectedTeam && playerInjuries.length > 0 && (
        <div className="dashboard-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">{selectedTeam} Player Injuries</h2>
            <Calendar className="h-5 w-5 text-gray-400" />
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Player</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Position</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Injury</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Practice</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {playerInjuries.map((player, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {player.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {player.position}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {player.primary_injury || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 mr-2">
                          {getInjuryStatusIcon(player.status)}
                        </div>
                        <span 
                          className="text-sm font-medium"
                          style={{ color: getInjuryStatusColor(player.status) }}
                        >
                          {player.status || 'N/A'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {player.practice_status || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Note about injury data usefulness */}
      <div className="dashboard-card bg-blue-50 border-blue-200">
        <div className="flex items-start">
          <AlertTriangle className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
          <div>
            <h3 className="text-sm font-medium text-blue-800">Note about Injury Data</h3>
            <p className="text-sm text-blue-700 mt-1">
              While injury data is available for analysis and context, our research found that injury adjustments 
              provide minimal improvement (+0.02%) to ELO prediction accuracy, which is below our 0.1% threshold 
              for useful features. This data is provided for informational purposes and user analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InjuryData;
