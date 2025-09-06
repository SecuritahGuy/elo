import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  ChevronLeft, 
  ChevronRight, 
  Clock, 
  MapPin, 
  TrendingUp, 
  TrendingDown,
  RefreshCw
} from 'lucide-react';
import apiService from '../services/api';

const NFLSchedule = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [availableWeeks, setAvailableWeeks] = useState([]);
  const [scheduleData, setScheduleData] = useState([]);
  const [eloData, setEloData] = useState([]);
  const [teamEloMap, setTeamEloMap] = useState({});
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedWeek) {
      loadScheduleData(selectedWeek);
    }
  }, [selectedWeek]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      
      // Load available weeks (1-18 for regular season)
      const weeks = Array.from({ length: 18 }, (_, i) => i + 1);
      setAvailableWeeks(weeks);
      
      // Load current ELO data for team comparisons
      const eloResponse = await apiService.getEloRatings(2025);
      if (eloResponse.data && eloResponse.data.ratings) {
        setEloData(eloResponse.data.ratings);
        
        // Create a map for quick ELO lookups
        const eloMap = {};
        eloResponse.data.ratings.forEach(team => {
          const teamAbbr = team.team?.abbreviation;
          if (teamAbbr) {
            eloMap[teamAbbr] = {
              rating: team.rating,
              change: team.rating_change,
              record: team.record
            };
          }
        });
        setTeamEloMap(eloMap);
      }
      
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError('Failed to load schedule data');
    } finally {
      setLoading(false);
    }
  };

  const loadScheduleData = async (week) => {
    try {
      setRefreshing(true);
      
      // Load schedule for specific week
      const response = await apiService.getNFLSchedule(week, 2025);
      if (response.data && response.data.games) {
        setScheduleData(response.data.games);
      }
      
    } catch (err) {
      console.error(`Error loading schedule for week ${week}:`, err);
      setError(`Failed to load schedule for week ${week}`);
    } finally {
      setRefreshing(false);
    }
  };

  const handleWeekChange = (week) => {
    setSelectedWeek(week);
  };

  const handlePreviousWeek = () => {
    if (selectedWeek > 1) {
      setSelectedWeek(selectedWeek - 1);
    }
  };

  const handleNextWeek = () => {
    if (selectedWeek < 18) {
      setSelectedWeek(selectedWeek + 1);
    }
  };

  const getTeamElo = (teamAbbr) => {
    return teamEloMap[teamAbbr] || { rating: 1500, change: 0, record: { wins: 0, losses: 0 } };
  };

  const formatGameTime = (gameTime) => {
    if (!gameTime) return 'TBD';
    const date = new Date(gameTime);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      timeZoneName: 'short'
    });
  };

  const getGameStatus = (game) => {
    if (game.status === 'completed') return 'Final';
    if (game.status === 'in_progress') return 'Live';
    if (game.status === 'scheduled') return 'Scheduled';
    return game.status || 'Scheduled';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Final': return 'text-gray-600';
      case 'Live': return 'text-red-600 font-semibold';
      case 'Scheduled': return 'text-blue-600';
      default: return 'text-gray-500';
    }
  };

  const getELOChangeIcon = (change) => {
    if (change > 0) return <TrendingUp className="h-3 w-3 text-green-600" />;
    if (change < 0) return <TrendingDown className="h-3 w-3 text-red-600" />;
    return <div className="h-3 w-3" />;
  };

  const getELOChangeColor = (change) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-nfl-primary" data-testid="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">{error}</p>
        <button 
          onClick={loadInitialData}
          className="px-4 py-2 bg-nfl-primary text-white rounded hover:bg-nfl-secondary"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <Calendar className="h-8 w-8 text-nfl-primary mr-3" />
              NFL Schedule
            </h1>
            <p className="text-gray-600 mt-1">
              Week-by-week game schedule with ELO ratings comparison
            </p>
          </div>
          <button
            onClick={() => loadScheduleData(selectedWeek)}
            disabled={refreshing}
            className="flex items-center px-4 py-2 bg-nfl-primary text-white rounded-lg hover:bg-nfl-secondary transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Week Navigation */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Week {selectedWeek}</h2>
          <div className="flex items-center space-x-4">
            <button
              onClick={handlePreviousWeek}
              disabled={selectedWeek <= 1}
              className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            
            <select
              value={selectedWeek}
              onChange={(e) => handleWeekChange(parseInt(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
            >
              {availableWeeks.map(week => (
                <option key={week} value={week}>
                  Week {week}
                </option>
              ))}
            </select>
            
            <button
              onClick={handleNextWeek}
              disabled={selectedWeek >= 18}
              className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Schedule Grid */}
      <div className="space-y-4">
        {scheduleData.length > 0 ? (
          scheduleData.map((game, index) => {
            const homeElo = getTeamElo(game.home_team?.abbreviation || game.home_team);
            const awayElo = getTeamElo(game.away_team?.abbreviation || game.away_team);
            const gameStatus = getGameStatus(game);
            const eloDifference = Math.abs(homeElo.rating - awayElo.rating);
            const favorite = homeElo.rating > awayElo.rating ? 'home' : 'away';
            
            return (
              <div key={game.id || index} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <Clock className="h-5 w-5 text-gray-400" />
                    <span className="text-sm text-gray-600">
                      {formatGameTime(game.game_time || game.date)}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4">
                    {game.venue && (
                      <div className="flex items-center text-sm text-gray-600">
                        <MapPin className="h-4 w-4 mr-1" />
                        {game.venue.name || game.venue}
                      </div>
                    )}
                    <span className={`text-sm font-medium ${getStatusColor(gameStatus)}`}>
                      {gameStatus}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Away Team */}
                  <div className={`p-4 rounded-lg border-2 ${favorite === 'away' ? 'border-nfl-primary bg-blue-50' : 'border-gray-200'}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                          <span className="text-sm font-bold text-gray-700">
                            {game.away_team?.abbreviation || game.away_team}
                          </span>
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">
                            {game.away_team?.name || game.away_team}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {awayElo.record.wins}-{awayElo.record.losses}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center space-x-2">
                          <span className="text-2xl font-bold text-gray-900">
                            {awayElo.rating.toFixed(1)}
                          </span>
                          {getELOChangeIcon(awayElo.change)}
                        </div>
                        <div className={`text-sm ${getELOChangeColor(awayElo.change)}`}>
                          {awayElo.change > 0 ? '+' : ''}{awayElo.change.toFixed(1)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Home Team */}
                  <div className={`p-4 rounded-lg border-2 ${favorite === 'home' ? 'border-nfl-primary bg-blue-50' : 'border-gray-200'}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                          <span className="text-sm font-bold text-gray-700">
                            {game.home_team?.abbreviation || game.home_team}
                          </span>
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">
                            {game.home_team?.name || game.home_team}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {homeElo.record.wins}-{homeElo.record.losses}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center space-x-2">
                          <span className="text-2xl font-bold text-gray-900">
                            {homeElo.rating.toFixed(1)}
                          </span>
                          {getELOChangeIcon(homeElo.change)}
                        </div>
                        <div className={`text-sm ${getELOChangeColor(homeElo.change)}`}>
                          {homeElo.change > 0 ? '+' : ''}{homeElo.change.toFixed(1)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Game Details */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>ELO Difference: {eloDifference.toFixed(1)}</span>
                    <span>
                      {favorite === 'home' ? game.home_team?.abbreviation || game.home_team : game.away_team?.abbreviation || game.away_team} 
                      {' '}favorite by {eloDifference.toFixed(1)} points
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-12">
            <Calendar className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Games Scheduled</h3>
            <p className="text-gray-600">
              No games found for Week {selectedWeek}. Try selecting a different week.
            </p>
          </div>
        )}
      </div>

      {/* ELO Legend */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">ELO Rating Guide</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-4 w-4 text-green-600" />
            <span>Green: Recent ELO increase</span>
          </div>
          <div className="flex items-center space-x-2">
            <TrendingDown className="h-4 w-4 text-red-600" />
            <span>Red: Recent ELO decrease</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 border-2 border-nfl-primary bg-blue-50 rounded"></div>
            <span>Blue border: ELO favorite</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NFLSchedule;
