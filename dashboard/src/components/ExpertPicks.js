import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Target, 
  DollarSign, 
  Calendar,
  Filter,
  Search,
  Star,
  Eye,
  Copy,
  Trophy,
  BarChart3
} from 'lucide-react';
import apiService from '../services/api';

const ExpertPicks = ({ sport = 'nfl' }) => {
  const [experts, setExperts] = useState([]);
  const [picks, setPicks] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedExpert, setSelectedExpert] = useState(null);
  const [filters, setFilters] = useState({
    result: 'all',
    limit: 50
  });

  useEffect(() => {
    loadData();
  }, [sport, filters]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load experts and picks
      const [expertsRes, picksRes] = await Promise.all([
        apiService.getActionNetworkExperts(sport, 20),
        apiService.getActionNetworkPicks(sport, filters.limit, null, filters.result)
      ]);

      setExperts(expertsRes.data.experts || []);
      setPicks(picksRes.data.picks || []);
      
      // Calculate analytics from picks data
      const picksData = picksRes.data.picks || [];
      const totalPicks = picksData.length;
      const wins = picksData.filter(pick => pick.result === 'win').length;
      const winRate = totalPicks > 0 ? (wins / totalPicks) * 100 : 0;
      const totalUnitsNet = picksData.reduce((sum, pick) => sum + (pick.units_net || 0), 0);
      
      setAnalytics({
        total_picks: totalPicks,
        win_rate: winRate,
        units_net: totalUnitsNet
      });
    } catch (err) {
      console.error('Error loading Action Network data:', err);
      console.error('Error details:', err.message, err.response?.data);
      setError(`Failed to load expert picks data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExpertClick = async (expertId) => {
    try {
      const response = await apiService.getActionNetworkExpertDetails(expertId);
      setSelectedExpert(response.data);
    } catch (err) {
      console.error('Error loading expert details:', err);
    }
  };

  const formatOdds = (odds) => {
    if (odds > 0) return `+${odds}`;
    return odds.toString();
  };

  const formatUnits = (units) => {
    return units ? units.toFixed(2) : '0.00';
  };

  const getResultColor = (result) => {
    switch (result) {
      case 'win': return 'text-green-600 bg-green-100';
      case 'loss': return 'text-red-600 bg-red-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'winning': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'losing': return <TrendingDown className="h-4 w-4 text-red-500" />;
      default: return <Target className="h-4 w-4 text-gray-500" />;
    }
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
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Expert Picks Analysis</h1>
            <p className="text-gray-600 mt-1">Action Network expert performance and picks</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="h-5 w-5 text-gray-400" />
              <select
                value={sport}
                onChange={(e) => window.location.reload()} // Simple reload for now
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="nfl">NFL</option>
                <option value="mlb">MLB</option>
                <option value="nba">NBA</option>
                <option value="nhl">NHL</option>
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={filters.result}
                onChange={(e) => setFilters({...filters, result: e.target.value})}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="all">All Results</option>
                <option value="win">Wins</option>
                <option value="loss">Losses</option>
                <option value="pending">Pending</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Summary */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Picks</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analytics.total_picks || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <Trophy className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Win Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analytics.win_rate?.toFixed(1) || 0}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <DollarSign className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Units Net</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analytics.units_net?.toFixed(2) || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <BarChart3 className="h-6 w-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Top Experts</p>
                <p className="text-2xl font-bold text-gray-900">
                  {experts.length}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Experts */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Top Experts</h2>
            <p className="text-sm text-gray-600">Ranked by performance</p>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {experts.slice(0, 10).map((expert, index) => (
                <div
                  key={expert.id || `expert-${index}`}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                  onClick={() => expert.id && handleExpertClick(expert.id)}
                >
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center justify-center w-8 h-8 bg-nfl-primary text-white rounded-full text-sm font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-medium text-gray-900">{expert.name}</h3>
                        {expert.verified && (
                          <Star className="h-4 w-4 text-blue-500" />
                        )}
                      </div>
                      <p className="text-sm text-gray-600">
                        {expert.followers?.toLocaleString()} followers
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      @{expert.username}
                    </p>
                    <p className="text-xs text-gray-600">
                      Expert
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Picks */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Picks</h2>
            <p className="text-sm text-gray-600">Latest expert picks</p>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {picks.slice(0, 10).map((pick, index) => (
                <div key={pick.pick_id || `pick-${index}`} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-medium text-gray-900">{pick.expert_name}</h4>
                        {getTrendIcon(pick.trend)}
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getResultColor(pick.result)}`}>
                          {pick.result}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{pick.description}</p>
                      <div className="flex items-center space-x-4 text-xs text-gray-600">
                        <span>Odds: {formatOdds(pick.odds)}</span>
                        <span>Units: {formatUnits(pick.units)}</span>
                        <span>Value: {pick.value}</span>
                        {pick.game_start && (
                          <span>{new Date(pick.game_start).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <div className="flex items-center space-x-1 text-xs text-gray-600">
                        <Eye className="h-3 w-3" />
                        <span>{pick.likes}</span>
                      </div>
                      <div className="flex items-center space-x-1 text-xs text-gray-600">
                        <Copy className="h-3 w-3" />
                        <span>{pick.copies}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Expert Details Modal */}
      {selectedExpert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900">{selectedExpert.expert.name}</h2>
                <button
                  onClick={() => setSelectedExpert(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <p className="text-sm text-gray-600">Followers</p>
                  <p className="text-lg font-semibold">{selectedExpert.expert.followers?.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Verified</p>
                  <p className="text-lg font-semibold">{selectedExpert.expert.is_verified ? 'Yes' : 'No'}</p>
                </div>
              </div>
              
              {selectedExpert.performance.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-4">Performance</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-green-100 rounded-lg">
                      <p className="text-2xl font-bold text-green-600">{selectedExpert.performance[0].wins}</p>
                      <p className="text-sm text-gray-600">Wins</p>
                    </div>
                    <div className="text-center p-4 bg-red-100 rounded-lg">
                      <p className="text-2xl font-bold text-red-600">{selectedExpert.performance[0].losses}</p>
                      <p className="text-sm text-gray-600">Losses</p>
                    </div>
                    <div className="text-center p-4 bg-blue-100 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">{formatUnits(selectedExpert.performance[0].units_net)}</p>
                      <p className="text-sm text-gray-600">Units Net</p>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <h3 className="text-lg font-semibold mb-4">Recent Picks</h3>
                <div className="space-y-2">
                  {selectedExpert.recent_picks.slice(0, 5).map((pick, index) => (
                    <div key={pick.pick_id || `recent-pick-${index}`} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                      <div>
                        <p className="font-medium">{pick.description}</p>
                        <p className="text-sm text-gray-600">
                          {pick.league} • {formatOdds(pick.odds)} • {formatUnits(pick.units)} units
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getResultColor(pick.result)}`}>
                        {pick.result}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExpertPicks;
