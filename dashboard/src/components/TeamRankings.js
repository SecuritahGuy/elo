import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import { Trophy, TrendingUp, TrendingDown, Calendar, BarChart3, ExternalLink } from 'lucide-react';

const TeamRankings = () => {
  const navigate = useNavigate();
  const [rankings, setRankings] = useState([]);
  const [seasons, setSeasons] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState(2024);
  const [seasonSummary, setSeasonSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadRankingsData = async (season = selectedSeason) => {
    try {
      setLoading(true);
      
      // Load ELO ratings for the selected season
      const ratingsResponse = await apiService.getEloRatings(season);
      setRankings(ratingsResponse.data.ratings || []);
      
      // Load season summary
      const summaryResponse = await apiService.getEloSeasonSummary(season);
      setSeasonSummary(summaryResponse.data.summary || {});
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load rankings data:', error);
      setRankings([]);
      setSeasonSummary(null);
    } finally {
      setLoading(false);
    }
  };

  const loadSeasons = async () => {
    try {
      const response = await apiService.getEloSeasons();
      const availableSeasons = response.data.seasons || [];
      
      // If no seasons from API, use default recent seasons
      if (availableSeasons.length === 0) {
        const currentYear = new Date().getFullYear();
        const defaultSeasons = [currentYear, currentYear - 1, currentYear - 2, currentYear - 3, currentYear - 4];
        setSeasons(defaultSeasons);
      } else {
        setSeasons(availableSeasons);
      }
    } catch (error) {
      console.error('Failed to load seasons:', error);
      // Fallback to default seasons
      const currentYear = new Date().getFullYear();
      setSeasons([currentYear, currentYear - 1, currentYear - 2, currentYear - 3, currentYear - 4]);
    }
  };

  useEffect(() => {
    loadSeasons();
  }, []);

  useEffect(() => {
    if (seasons.length > 0) {
      loadRankingsData();
    }
  }, [seasons, selectedSeason]);

  const handleSeasonChange = (season) => {
    setSelectedSeason(parseInt(season));
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
          <p className="text-gray-600">ELO Ratings & Team Performance</p>
        </div>
        <div className="flex items-center space-x-4">
          {/* Season Selector */}
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <select
              value={selectedSeason}
              onChange={(e) => handleSeasonChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
            >
              {seasons.map(season => (
                <option key={season} value={season}>{season}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Season Summary */}
      {seasonSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="dashboard-card">
            <div className="flex items-center">
              <Trophy className="w-8 h-8 text-nfl-primary mr-3" />
              <div>
                <p className="text-sm text-gray-600">Total Teams</p>
                <p className="text-2xl font-bold text-gray-900">{seasonSummary.total_teams || 0}</p>
              </div>
            </div>
          </div>
          <div className="dashboard-card">
            <div className="flex items-center">
              <BarChart3 className="w-8 h-8 text-nfl-secondary mr-3" />
              <div>
                <p className="text-sm text-gray-600">Average Rating</p>
                <p className="text-2xl font-bold text-gray-900">{seasonSummary.avg_rating || 'N/A'}</p>
              </div>
            </div>
          </div>
          <div className="dashboard-card">
            <div className="flex items-center">
              <TrendingUp className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Highest Rating</p>
                <p className="text-2xl font-bold text-gray-900">{seasonSummary.highest_rating || 'N/A'}</p>
              </div>
            </div>
          </div>
          <div className="dashboard-card">
            <div className="flex items-center">
              <TrendingDown className="w-8 h-8 text-red-600 mr-3" />
              <div>
                <p className="text-sm text-gray-600">Lowest Rating</p>
                <p className="text-2xl font-bold text-gray-900">{seasonSummary.lowest_rating || 'N/A'}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Team Rankings */}
      <div className="dashboard-card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">
            ELO Rankings - {selectedSeason} Season
          </h2>
          <div className="text-sm text-gray-500">
            {lastUpdated && `Last updated: ${lastUpdated.toLocaleTimeString()}`}
          </div>
        </div>
        
        <div className="space-y-3">
          {rankings.map((team, index) => (
            <div key={team.team} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-nfl-primary text-white rounded-full flex items-center justify-center text-sm font-bold mr-4">
                  {team.rank}
                </div>
                <div>
                  <button
                    onClick={() => navigate(`/team/${team.team}`)}
                    className="flex items-center text-left hover:text-nfl-primary transition-colors group"
                  >
                    <p className="font-semibold text-gray-900 group-hover:text-nfl-primary">{team.team}</p>
                    <ExternalLink className="h-4 w-4 ml-2 text-gray-400 group-hover:text-nfl-primary" />
                  </button>
                  <p className="text-sm text-gray-500">
                    {team.wins}-{team.losses} ({team.win_pct ? (team.win_pct * 100).toFixed(1) : 0}%)
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className={`text-lg font-bold ${getRatingColor(team.rating)}`}>
                    {team.rating}
                  </p>
                  <p className="text-xs text-gray-500">ELO Rating</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-1">
                    {getChangeIcon(team.change)}
                    <p className={`text-sm font-semibold ${getChangeColor(team.change)}`}>
                      {team.change > 0 ? '+' : ''}{team.change}
                    </p>
                  </div>
                  <p className="text-xs text-gray-500">Change</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TeamRankings;