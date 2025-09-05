import React, { useState, useEffect } from 'react';
import { Trophy, Target, BarChart3, Activity, RefreshCw } from 'lucide-react';
import { apiService } from '../services/api';

const Dashboard = () => {
  const [teamRankings, setTeamRankings] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load Action Network experts (top 10)
      const expertsResponse = await apiService.getActionNetworkExperts('nfl', 10);
      setTeamRankings(expertsResponse.data.experts || []);
      
      // Load recent picks (first 6)
      const picksResponse = await apiService.getActionNetworkPicks('nfl', 6);
      setPredictions(picksResponse.data.picks || []);
      
      // Load analytics for performance metrics
      const analyticsResponse = await apiService.getActionNetworkAnalytics('nfl');
      setPerformanceMetrics(analyticsResponse.data);
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      // Set empty data on error
      setTeamRankings([]);
      setPredictions([]);
      setPerformanceMetrics(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    
    // Refresh data every 5 minutes
    const interval = setInterval(loadDashboardData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ title, value, icon: Icon, color = 'nfl-primary' }) => (
    <div className="dashboard-card">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg bg-${color} bg-opacity-10`}>
          <Icon className={`w-6 h-6 text-${color}`} />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner w-8 h-8"></div>
        <span className="ml-2 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Action Network Dashboard</h1>
          <p className="text-gray-600">Expert Picks & Performance Analysis</p>
        </div>
        <button
          onClick={loadDashboardData}
          className="flex items-center px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Top Experts"
          value={teamRankings.length}
          icon={Trophy}
          color="nfl-primary"
        />
        <StatCard
          title="Total Picks"
          value={performanceMetrics?.league_summary?.total_picks || 'N/A'}
          icon={Target}
          color="nfl-secondary"
        />
        <StatCard
          title="Win Rate"
          value={performanceMetrics?.league_summary?.win_rate ? `${performanceMetrics.league_summary.win_rate.toFixed(1)}%` : 'N/A'}
          icon={BarChart3}
          color="nfl-accent"
        />
        <StatCard
          title="Units Net"
          value={performanceMetrics?.league_summary?.total_units_net ? performanceMetrics.league_summary.total_units_net.toFixed(2) : 'N/A'}
          icon={Activity}
          color="green-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Experts */}
        <div className="dashboard-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Top Experts</h2>
            <Trophy className="w-5 h-5 text-nfl-primary" />
          </div>
          <div className="space-y-3">
            {teamRankings.map((expert, index) => (
              <div key={expert.name || `expert-${index}`} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-nfl-primary text-white rounded-full flex items-center justify-center text-sm font-bold mr-3">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{expert.name}</p>
                    <p className="text-sm text-gray-500">{expert.total_picks} picks • {expert.win_rate?.toFixed(1) || 0}% win rate</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-green-600">
                    {expert.total_units_net?.toFixed(2) || 0} units
                  </p>
                  <p className="text-xs text-gray-500">
                    {expert.followers?.toLocaleString() || 0} followers
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Picks */}
        <div className="dashboard-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Recent Picks</h2>
            <Target className="w-5 h-5 text-nfl-secondary" />
          </div>
          <div className="space-y-3">
            {predictions.map((pick, index) => (
              <div key={pick.pick_id || `pick-${index}`} className="prediction-card">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{pick.expert_name}</p>
                    <p className="text-sm text-gray-600">{pick.description || 'No description'}</p>
                    <p className="text-xs text-gray-500">
                      {pick.home_team && pick.away_team ? `${pick.home_team} vs ${pick.away_team}` : 'NFL Pick'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-nfl-primary">
                      {pick.odds > 0 ? `+${pick.odds}` : pick.odds}
                    </p>
                    <p className="text-sm text-gray-500">
                      {pick.units} units • {pick.result || 'pending'}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="dashboard-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">System Status</h2>
          <Activity className="w-5 h-5 text-green-600" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-sm text-gray-600">Total Experts</p>
            <p className="text-2xl font-bold text-green-600">
              {performanceMetrics?.top_experts?.length || teamRankings.length}
            </p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-600">Last Updated</p>
            <p className="text-sm font-semibold text-blue-600">
              {lastUpdated ? lastUpdated.toLocaleTimeString() : 'N/A'}
            </p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="text-sm text-gray-600">System Health</p>
            <p className="text-sm font-semibold text-purple-600">Operational</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
