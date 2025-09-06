/**
 * Historical Analysis Component
 * Displays season comparison tools and trend analysis
 */

import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, Calendar, Target, Award, Activity } from 'lucide-react';
import historicalAnalysisService from '../services/historicalAnalysisService';

const HistoricalAnalysis = () => {
  const [comparison, setComparison] = useState(null);
  const [teamHistory, setTeamHistory] = useState(null);
  const [leagueEvolution, setLeagueEvolution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeasons, setSelectedSeasons] = useState([2021, 2022, 2023, 2024, 2025]);
  const [selectedTeam, setSelectedTeam] = useState('PHI');
  const [viewMode, setViewMode] = useState('overview'); // 'overview', 'teams', 'evolution'

  useEffect(() => {
    loadHistoricalData();
  }, [selectedSeasons, selectedTeam]);

  const loadHistoricalData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [comparisonData, teamHistoryData, leagueEvolutionData] = await Promise.all([
        historicalAnalysisService.compareSeasons(selectedSeasons),
        historicalAnalysisService.getTeamHistory(selectedTeam, selectedSeasons),
        historicalAnalysisService.getLeagueEvolution(selectedSeasons)
      ]);
      
      setComparison(comparisonData);
      setTeamHistory(teamHistoryData);
      setLeagueEvolution(leagueEvolutionData);
    } catch (err) {
      setError('Failed to load historical data');
      console.error('Error loading historical data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'increasing': return '📈';
      case 'decreasing': return '📉';
      case 'stable': return '➡️';
      default: return '❓';
    }
  };

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'increasing': return 'text-green-600';
      case 'decreasing': return 'text-red-600';
      case 'stable': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      {comparison && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="dashboard-card">
            <div className="flex items-center">
              <Calendar className="w-8 h-8 text-nfl-primary mr-3" />
              <div>
                <p className="text-sm text-gray-600">Seasons Analyzed</p>
                <p className="text-2xl font-bold text-gray-900">
                  {comparison.summary.totalSeasons}
                </p>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <BarChart3 className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Average Rating</p>
                <p className="text-2xl font-bold text-gray-900">
                  {comparison.summary.averageRating}
                </p>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <Users className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Average Teams</p>
                <p className="text-2xl font-bold text-gray-900">
                  {comparison.summary.averageTeams}
                </p>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <Target className="w-8 h-8 text-purple-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Rating Spread</p>
                <p className="text-2xl font-bold text-gray-900">
                  {comparison.summary.averageSpread}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Season Comparison Table */}
      {comparison && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4">Season Comparison</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2">Season</th>
                  <th className="text-right py-2">Games</th>
                  <th className="text-right py-2">Teams</th>
                  <th className="text-right py-2">Avg Rating</th>
                  <th className="text-right py-2">Spread</th>
                  <th className="text-right py-2">Balance</th>
                  <th className="text-left py-2">Top Team</th>
                </tr>
              </thead>
              <tbody>
                {comparison.seasons.map((season) => (
                  <tr key={season.year} className="border-b border-gray-100">
                    <td className="py-2 font-medium">{season.year}</td>
                    <td className="py-2 text-right">{season.data.totalGames}</td>
                    <td className="py-2 text-right">{season.data.totalTeams}</td>
                    <td className="py-2 text-right">{season.data.averageRating}</td>
                    <td className="py-2 text-right">{season.data.ratingSpread}</td>
                    <td className="py-2 text-right">
                      <span className={`px-2 py-1 rounded text-xs ${
                        season.data.competitiveBalance < 30 ? 'bg-green-100 text-green-800' :
                        season.data.competitiveBalance < 50 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {season.data.competitiveBalance}%
                      </span>
                    </td>
                    <td className="py-2 text-left">
                      {season.data.topTeam ? (
                        <div className="flex items-center">
                          <span className="font-medium">{season.data.topTeam.team}</span>
                          <span className="ml-2 text-sm text-gray-500">
                            ({Math.round(season.data.topTeam.rating)})
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-500">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Trends Analysis */}
      {comparison && comparison.trends && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4">Trend Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">{getTrendIcon(comparison.trends.ratingTrend)}</div>
              <div className="text-sm text-gray-600">Rating Trend</div>
              <div className={`font-semibold ${getTrendColor(comparison.trends.ratingTrend)}`}>
                {comparison.trends.ratingTrend}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">{getTrendIcon(comparison.trends.competitiveTrend)}</div>
              <div className="text-sm text-gray-600">Competitive Trend</div>
              <div className={`font-semibold ${getTrendColor(comparison.trends.competitiveTrend)}`}>
                {comparison.trends.competitiveTrend}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">{getTrendIcon(comparison.trends.gameTrend)}</div>
              <div className="text-sm text-gray-600">Game Trend</div>
              <div className={`font-semibold ${getTrendColor(comparison.trends.gameTrend)}`}>
                {comparison.trends.gameTrend}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">{getTrendIcon(comparison.trends.teamTrend)}</div>
              <div className="text-sm text-gray-600">Team Trend</div>
              <div className={`font-semibold ${getTrendColor(comparison.trends.teamTrend)}`}>
                {comparison.trends.teamTrend}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderTeams = () => (
    <div className="space-y-6">
      {/* Team Selector */}
      <div className="dashboard-card">
        <h3 className="text-lg font-semibold mb-4">Team Analysis</h3>
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Select Team:</label>
          <select
            value={selectedTeam}
            onChange={(e) => setSelectedTeam(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
          >
            <option value="PHI">Philadelphia Eagles</option>
            <option value="DAL">Dallas Cowboys</option>
            <option value="SF">San Francisco 49ers</option>
            <option value="BUF">Buffalo Bills</option>
            <option value="BAL">Baltimore Ravens</option>
            <option value="KC">Kansas City Chiefs</option>
            <option value="GB">Green Bay Packers</option>
            <option value="MIN">Minnesota Vikings</option>
          </select>
        </div>
      </div>

      {/* Team Summary */}
      {teamHistory && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="dashboard-card">
            <div className="flex items-center">
              <Award className="w-8 h-8 text-nfl-primary mr-3" />
              <div>
                <p className="text-sm text-gray-600">Average Rating</p>
                <p className="text-2xl font-bold text-gray-900">
                  {teamHistory.summary.averageRating}
                </p>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <Target className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Highest Rating</p>
                <p className="text-2xl font-bold text-gray-900">
                  {teamHistory.summary.highestRating}
                </p>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <TrendingUp className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Average Wins</p>
                <p className="text-2xl font-bold text-gray-900">
                  {teamHistory.summary.averageWins}
                </p>
              </div>
            </div>
          </div>
          
          <div className="dashboard-card">
            <div className="flex items-center">
              <Activity className="w-8 h-8 text-purple-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Consistency</p>
                <p className="text-2xl font-bold text-gray-900">
                  {teamHistory.trends.consistency.replace('_', ' ')}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Team History Table */}
      {teamHistory && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4">{selectedTeam} Season History</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2">Season</th>
                  <th className="text-right py-2">Rating</th>
                  <th className="text-right py-2">Rank</th>
                  <th className="text-right py-2">Wins</th>
                  <th className="text-right py-2">Losses</th>
                  <th className="text-right py-2">Win %</th>
                  <th className="text-right py-2">Change</th>
                </tr>
              </thead>
              <tbody>
                {teamHistory.seasons.map((season) => (
                  <tr key={season.season} className="border-b border-gray-100">
                    <td className="py-2 font-medium">{season.season}</td>
                    <td className="py-2 text-right">{season.rating}</td>
                    <td className="py-2 text-right">
                      <span className="px-2 py-1 rounded text-xs bg-gray-100">
                        #{season.rank}
                      </span>
                    </td>
                    <td className="py-2 text-right">{season.wins}</td>
                    <td className="py-2 text-right">{season.losses}</td>
                    <td className="py-2 text-right">{season.winPct}%</td>
                    <td className="py-2 text-right">
                      <span className={`px-2 py-1 rounded text-xs ${
                        season.change > 0 ? 'bg-green-100 text-green-800' :
                        season.change < 0 ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {season.change > 0 ? '+' : ''}{season.change}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Team Trends */}
      {teamHistory && teamHistory.trends && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold mb-4">Team Trends</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">{getTrendIcon(teamHistory.trends.ratingTrend)}</div>
              <div className="text-sm text-gray-600">Rating Trend</div>
              <div className={`font-semibold ${getTrendColor(teamHistory.trends.ratingTrend)}`}>
                {teamHistory.trends.ratingTrend}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">{getTrendIcon(teamHistory.trends.performanceTrend)}</div>
              <div className="text-sm text-gray-600">Performance Trend</div>
              <div className={`font-semibold ${getTrendColor(teamHistory.trends.performanceTrend)}`}>
                {teamHistory.trends.performanceTrend}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">📊</div>
              <div className="text-sm text-gray-600">Rating Variance</div>
              <div className="font-semibold text-gray-900">
                {teamHistory.trends.ratingVariance}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderEvolution = () => (
    <div className="space-y-6">
      {leagueEvolution && !leagueEvolution.error && (
        <>
          {/* League Metrics */}
          <div className="dashboard-card">
            <h3 className="text-lg font-semibold mb-4">League Evolution Metrics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-2">{getTrendIcon(leagueEvolution.leagueMetrics.trends.averageRating)}</div>
                <div className="text-sm text-gray-600">Rating Trend</div>
                <div className={`font-semibold ${getTrendColor(leagueEvolution.leagueMetrics.trends.averageRating)}`}>
                  {leagueEvolution.leagueMetrics.trends.averageRating}
                </div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-2">{getTrendIcon(leagueEvolution.leagueMetrics.trends.competitiveBalance)}</div>
                <div className="text-sm text-gray-600">Balance Trend</div>
                <div className={`font-semibold ${getTrendColor(leagueEvolution.leagueMetrics.trends.competitiveBalance)}`}>
                  {leagueEvolution.leagueMetrics.trends.competitiveBalance}
                </div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-2">{getTrendIcon(leagueEvolution.leagueMetrics.trends.ratingSpread)}</div>
                <div className="text-sm text-gray-600">Spread Trend</div>
                <div className={`font-semibold ${getTrendColor(leagueEvolution.leagueMetrics.trends.ratingSpread)}`}>
                  {leagueEvolution.leagueMetrics.trends.ratingSpread}
                </div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-2">{getTrendIcon(leagueEvolution.leagueMetrics.trends.totalGames)}</div>
                <div className="text-sm text-gray-600">Games Trend</div>
                <div className={`font-semibold ${getTrendColor(leagueEvolution.leagueMetrics.trends.totalGames)}`}>
                  {leagueEvolution.leagueMetrics.trends.totalGames}
                </div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-2">{getTrendIcon(leagueEvolution.leagueMetrics.trends.totalTeams)}</div>
                <div className="text-sm text-gray-600">Teams Trend</div>
                <div className={`font-semibold ${getTrendColor(leagueEvolution.leagueMetrics.trends.totalTeams)}`}>
                  {leagueEvolution.leagueMetrics.trends.totalTeams}
                </div>
              </div>
            </div>
          </div>

          {/* Competitive Analysis */}
          {leagueEvolution.competitiveEvolution && (
            <div className="dashboard-card">
              <h3 className="text-lg font-semibold mb-4">Competitive Analysis</h3>
              <div className="space-y-3">
                {leagueEvolution.competitiveEvolution.analysis.map((analysis, index) => (
                  <div key={index} className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-blue-800">{analysis}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Team Evolution Summary */}
          {leagueEvolution.teamEvolution && (
            <div className="dashboard-card">
              <h3 className="text-lg font-semibold mb-4">Team Evolution Summary</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2">Team</th>
                      <th className="text-right py-2">Avg Rating</th>
                      <th className="text-right py-2">Rating Trend</th>
                      <th className="text-right py-2">Performance Trend</th>
                      <th className="text-right py-2">Consistency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leagueEvolution.teamEvolution.slice(0, 10).map((team) => (
                      <tr key={team.team} className="border-b border-gray-100">
                        <td className="py-2 font-medium">{team.team}</td>
                        <td className="py-2 text-right">{team.summary.averageRating}</td>
                        <td className="py-2 text-right">
                          <span className={`px-2 py-1 rounded text-xs ${
                            team.trends.ratingTrend === 'increasing' ? 'bg-green-100 text-green-800' :
                            team.trends.ratingTrend === 'decreasing' ? 'bg-red-100 text-red-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {team.trends.ratingTrend}
                          </span>
                        </td>
                        <td className="py-2 text-right">
                          <span className={`px-2 py-1 rounded text-xs ${
                            team.trends.performanceTrend === 'increasing' ? 'bg-green-100 text-green-800' :
                            team.trends.performanceTrend === 'decreasing' ? 'bg-red-100 text-red-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {team.trends.performanceTrend}
                          </span>
                        </td>
                        <td className="py-2 text-right">
                          <span className="px-2 py-1 rounded text-xs bg-gray-100">
                            {team.trends.consistency.replace('_', ' ')}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nfl-primary mx-auto mb-4"></div>
          <p className="text-gray-600">Loading historical analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={loadHistoricalData}
          className="px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-primary-dark transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Historical Analysis</h1>
          <p className="text-gray-600">Season comparison tools and trend analysis</p>
        </div>
        
        <div className="flex items-center space-x-4 mt-4 sm:mt-0">
          {/* Season Selector */}
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Seasons:</label>
            <select
              value={selectedSeasons.join(',')}
              onChange={(e) => setSelectedSeasons(e.target.value.split(',').map(s => parseInt(s.trim())))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
            >
              <option value="2021,2022,2023,2024,2025">2021-2025</option>
              <option value="2022,2023,2024,2025">2022-2025</option>
              <option value="2023,2024,2025">2023-2025</option>
              <option value="2024,2025">2024-2025</option>
            </select>
          </div>
        </div>
      </div>

      {/* View Mode Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'teams', label: 'Teams', icon: Users },
            { id: 'evolution', label: 'Evolution', icon: TrendingUp }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setViewMode(id)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                viewMode === id
                  ? 'border-nfl-primary text-nfl-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {viewMode === 'overview' && renderOverview()}
      {viewMode === 'teams' && renderTeams()}
      {viewMode === 'evolution' && renderEvolution()}
    </div>
  );
};

export default HistoricalAnalysis;
