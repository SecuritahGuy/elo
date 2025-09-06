/**
 * Historical Analysis Service
 * Provides season comparison tools and trend analysis
 */

import apiService from './api';

class HistoricalAnalysisService {
  constructor() {
    this.cache = new Map();
    this.cacheTimeout = 10 * 60 * 1000; // 10 minutes
  }

  /**
   * Compare multiple seasons
   */
  async compareSeasons(seasons = [2021, 2022, 2023, 2024, 2025]) {
    const cacheKey = `seasons:${seasons.join(',')}`;
    
    // Check cache first
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const comparisons = await Promise.all(
        seasons.map(season => this.analyzeSeason(season))
      );

      const comparison = {
        seasons: seasons.map((season, index) => ({
          year: season,
          data: comparisons[index]
        })),
        summary: this.generateSeasonSummary(comparisons, seasons),
        trends: this.analyzeSeasonTrends(comparisons, seasons),
        generatedAt: new Date().toISOString()
      };

      // Cache the results
      this.cache.set(cacheKey, {
        data: comparison,
        timestamp: Date.now()
      });

      return comparison;
    } catch (error) {
      console.error('Error comparing seasons:', error);
      throw error;
    }
  }

  /**
   * Analyze a single season
   */
  async analyzeSeason(season) {
    try {
      const [eloRatings, seasonSummary] = await Promise.all([
        apiService.getEloRatings(season, 'comprehensive'),
        apiService.getEloSeasonSummary(season)
      ]);

      return {
        season,
        totalGames: seasonSummary?.totalGames || 0,
        totalTeams: eloRatings?.teams?.length || 0,
        averageRating: this.calculateAverageRating(eloRatings),
        ratingSpread: this.calculateRatingSpread(eloRatings),
        topTeam: this.getTopTeam(eloRatings),
        bottomTeam: this.getBottomTeam(eloRatings),
        competitiveBalance: this.calculateCompetitiveBalance(eloRatings),
        ratingDistribution: this.calculateRatingDistribution(eloRatings),
        teamRankings: this.generateTeamRankings(eloRatings),
        seasonStats: seasonSummary
      };
    } catch (error) {
      console.error(`Error analyzing season ${season}:`, error);
      return {
        season,
        error: error.message,
        totalGames: 0,
        totalTeams: 0,
        averageRating: 0,
        ratingSpread: 0,
        topTeam: null,
        bottomTeam: null,
        competitiveBalance: 0,
        ratingDistribution: {},
        teamRankings: [],
        seasonStats: null
      };
    }
  }

  /**
   * Calculate average rating for a season
   */
  calculateAverageRating(eloRatings) {
    if (!eloRatings?.teams || eloRatings.teams.length === 0) return 0;
    
    const totalRating = eloRatings.teams.reduce((sum, team) => sum + team.rating, 0);
    return Math.round(totalRating / eloRatings.teams.length);
  }

  /**
   * Calculate rating spread (max - min)
   */
  calculateRatingSpread(eloRatings) {
    if (!eloRatings?.teams || eloRatings.teams.length === 0) return 0;
    
    const ratings = eloRatings.teams.map(team => team.rating);
    const maxRating = Math.max(...ratings);
    const minRating = Math.min(...ratings);
    
    return Math.round(maxRating - minRating);
  }

  /**
   * Get top team by rating
   */
  getTopTeam(eloRatings) {
    if (!eloRatings?.teams || eloRatings.teams.length === 0) return null;
    
    return eloRatings.teams.reduce((top, team) => 
      team.rating > top.rating ? team : top
    );
  }

  /**
   * Get bottom team by rating
   */
  getBottomTeam(eloRatings) {
    if (!eloRatings?.teams || eloRatings.teams.length === 0) return null;
    
    return eloRatings.teams.reduce((bottom, team) => 
      team.rating < bottom.rating ? team : bottom
    );
  }

  /**
   * Calculate competitive balance (lower = more balanced)
   */
  calculateCompetitiveBalance(eloRatings) {
    if (!eloRatings?.teams || eloRatings.teams.length === 0) return 0;
    
    const ratings = eloRatings.teams.map(team => team.rating);
    const mean = ratings.reduce((sum, rating) => sum + rating, 0) / ratings.length;
    const variance = ratings.reduce((sum, rating) => sum + Math.pow(rating - mean, 2), 0) / ratings.length;
    const standardDeviation = Math.sqrt(variance);
    
    // Normalize to 0-100 scale (lower is more balanced)
    return Math.round(Math.min(100, (standardDeviation / 200) * 100));
  }

  /**
   * Calculate rating distribution
   */
  calculateRatingDistribution(eloRatings) {
    if (!eloRatings?.teams || eloRatings.teams.length === 0) return {};
    
    const distribution = {
      '1400-1500': 0,
      '1500-1600': 0,
      '1600-1700': 0,
      '1700-1800': 0,
      '1800+': 0
    };
    
    eloRatings.teams.forEach(team => {
      if (team.rating < 1500) distribution['1400-1500']++;
      else if (team.rating < 1600) distribution['1500-1600']++;
      else if (team.rating < 1700) distribution['1600-1700']++;
      else if (team.rating < 1800) distribution['1700-1800']++;
      else distribution['1800+']++;
    });
    
    return distribution;
  }

  /**
   * Generate team rankings
   */
  generateTeamRankings(eloRatings) {
    if (!eloRatings?.teams || eloRatings.teams.length === 0) return [];
    
    return eloRatings.teams
      .sort((a, b) => b.rating - a.rating)
      .map((team, index) => ({
        rank: index + 1,
        team: team.team,
        rating: Math.round(team.rating),
        wins: team.wins || 0,
        losses: team.losses || 0,
        winPct: team.winPct || 0,
        change: team.ratingChange || 0
      }));
  }

  /**
   * Generate season summary
   */
  generateSeasonSummary(comparisons, seasons) {
    const validSeasons = comparisons.filter(comp => !comp.error);
    
    if (validSeasons.length === 0) {
      return {
        totalSeasons: 0,
        averageGames: 0,
        averageTeams: 0,
        averageRating: 0,
        averageSpread: 0,
        mostCompetitive: null,
        leastCompetitive: null,
        topTeamOverall: null,
        bottomTeamOverall: null
      };
    }

    const totalGames = validSeasons.reduce((sum, comp) => sum + comp.totalGames, 0);
    const totalTeams = validSeasons.reduce((sum, comp) => sum + comp.totalTeams, 0);
    const averageRating = validSeasons.reduce((sum, comp) => sum + comp.averageRating, 0) / validSeasons.length;
    const averageSpread = validSeasons.reduce((sum, comp) => sum + comp.ratingSpread, 0) / validSeasons.length;

    // Find most/least competitive seasons
    const mostCompetitive = validSeasons.reduce((min, comp) => 
      comp.competitiveBalance < min.competitiveBalance ? comp : min
    );
    const leastCompetitive = validSeasons.reduce((max, comp) => 
      comp.competitiveBalance > max.competitiveBalance ? comp : max
    );

    // Find overall top/bottom teams
    const allTeams = validSeasons.flatMap(comp => comp.teamRankings);
    const topTeamOverall = allTeams.reduce((top, team) => 
      team.rating > top.rating ? team : top
    );
    const bottomTeamOverall = allTeams.reduce((bottom, team) => 
      team.rating < bottom.rating ? team : bottom
    );

    return {
      totalSeasons: validSeasons.length,
      averageGames: Math.round(totalGames / validSeasons.length),
      averageTeams: Math.round(totalTeams / validSeasons.length),
      averageRating: Math.round(averageRating),
      averageSpread: Math.round(averageSpread),
      mostCompetitive: {
        season: mostCompetitive.season,
        balance: mostCompetitive.competitiveBalance
      },
      leastCompetitive: {
        season: leastCompetitive.season,
        balance: leastCompetitive.competitiveBalance
      },
      topTeamOverall: {
        team: topTeamOverall.team,
        rating: topTeamOverall.rating,
        season: this.findTeamSeason(topTeamOverall.team, validSeasons)
      },
      bottomTeamOverall: {
        team: bottomTeamOverall.team,
        rating: bottomTeamOverall.rating,
        season: this.findTeamSeason(bottomTeamOverall.team, validSeasons)
      }
    };
  }

  /**
   * Find which season a team appeared in
   */
  findTeamSeason(team, seasons) {
    const season = seasons.find(comp => 
      comp.teamRankings.some(ranking => ranking.team === team)
    );
    return season ? season.season : null;
  }

  /**
   * Analyze season trends
   */
  analyzeSeasonTrends(comparisons, seasons) {
    const validSeasons = comparisons.filter(comp => !comp.error);
    
    if (validSeasons.length < 2) {
      return {
        ratingTrend: 'insufficient_data',
        competitiveTrend: 'insufficient_data',
        gameTrend: 'insufficient_data',
        teamTrend: 'insufficient_data'
      };
    }

    // Sort by season year
    const sortedSeasons = validSeasons.sort((a, b) => a.season - b.season);
    
    // Calculate trends
    const ratingTrend = this.calculateTrend(
      sortedSeasons.map(comp => comp.averageRating)
    );
    const competitiveTrend = this.calculateTrend(
      sortedSeasons.map(comp => comp.competitiveBalance)
    );
    const gameTrend = this.calculateTrend(
      sortedSeasons.map(comp => comp.totalGames)
    );
    const teamTrend = this.calculateTrend(
      sortedSeasons.map(comp => comp.totalTeams)
    );

    return {
      ratingTrend,
      competitiveTrend,
      gameTrend,
      teamTrend,
      trendData: sortedSeasons.map(comp => ({
        season: comp.season,
        averageRating: comp.averageRating,
        competitiveBalance: comp.competitiveBalance,
        totalGames: comp.totalGames,
        totalTeams: comp.totalTeams
      }))
    };
  }

  /**
   * Calculate trend direction
   */
  calculateTrend(values) {
    if (values.length < 2) return 'insufficient_data';
    
    const firstHalf = values.slice(0, Math.ceil(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));
    
    const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;
    
    const change = ((secondAvg - firstAvg) / firstAvg) * 100;
    
    if (Math.abs(change) < 5) return 'stable';
    return change > 0 ? 'increasing' : 'decreasing';
  }

  /**
   * Get team historical performance
   */
  async getTeamHistory(team, seasons = [2021, 2022, 2023, 2024, 2025]) {
    const cacheKey = `team:${team}:${seasons.join(',')}`;
    
    // Check cache first
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const teamHistory = [];
      
      for (const season of seasons) {
        try {
          const eloRatings = await apiService.getEloRatings(season, 'comprehensive');
          const teamData = eloRatings?.teams?.find(t => t.team === team);
          
          if (teamData) {
            teamHistory.push({
              season,
              rating: Math.round(teamData.rating),
              wins: teamData.wins || 0,
              losses: teamData.losses || 0,
              winPct: teamData.winPct || 0,
              change: teamData.ratingChange || 0,
              rank: this.getTeamRank(team, eloRatings)
            });
          }
        } catch (error) {
          console.warn(`Error getting team data for ${team} in ${season}:`, error);
        }
      }

      const history = {
        team,
        seasons: teamHistory,
        summary: this.generateTeamSummary(teamHistory),
        trends: this.analyzeTeamTrends(teamHistory),
        generatedAt: new Date().toISOString()
      };

      // Cache the results
      this.cache.set(cacheKey, {
        data: history,
        timestamp: Date.now()
      });

      return history;
    } catch (error) {
      console.error(`Error getting team history for ${team}:`, error);
      throw error;
    }
  }

  /**
   * Get team rank in a season
   */
  getTeamRank(team, eloRatings) {
    if (!eloRatings?.teams) return null;
    
    const sortedTeams = eloRatings.teams.sort((a, b) => b.rating - a.rating);
    const rank = sortedTeams.findIndex(t => t.team === team);
    return rank >= 0 ? rank + 1 : null;
  }

  /**
   * Generate team summary
   */
  generateTeamSummary(teamHistory) {
    if (teamHistory.length === 0) {
      return {
        totalSeasons: 0,
        averageRating: 0,
        highestRating: 0,
        lowestRating: 0,
        averageWins: 0,
        averageLosses: 0,
        averageWinPct: 0,
        bestSeason: null,
        worstSeason: null
      };
    }

    const ratings = teamHistory.map(h => h.rating);
    const wins = teamHistory.map(h => h.wins);
    const losses = teamHistory.map(h => h.losses);
    const winPcts = teamHistory.map(h => h.winPct);

    const bestSeason = teamHistory.reduce((best, season) => 
      season.rating > best.rating ? season : best
    );
    const worstSeason = teamHistory.reduce((worst, season) => 
      season.rating < worst.rating ? season : worst
    );

    return {
      totalSeasons: teamHistory.length,
      averageRating: Math.round(ratings.reduce((sum, r) => sum + r, 0) / ratings.length),
      highestRating: Math.max(...ratings),
      lowestRating: Math.min(...ratings),
      averageWins: Math.round(wins.reduce((sum, w) => sum + w, 0) / wins.length),
      averageLosses: Math.round(losses.reduce((sum, l) => sum + l, 0) / losses.length),
      averageWinPct: Math.round(winPcts.reduce((sum, w) => sum + w, 0) / winPcts.length),
      bestSeason: {
        season: bestSeason.season,
        rating: bestSeason.rating,
        rank: bestSeason.rank
      },
      worstSeason: {
        season: worstSeason.season,
        rating: worstSeason.rating,
        rank: worstSeason.rank
      }
    };
  }

  /**
   * Analyze team trends
   */
  analyzeTeamTrends(teamHistory) {
    if (teamHistory.length < 2) {
      return {
        ratingTrend: 'insufficient_data',
        performanceTrend: 'insufficient_data',
        consistency: 'insufficient_data'
      };
    }

    const sortedHistory = teamHistory.sort((a, b) => a.season - b.season);
    
    const ratingTrend = this.calculateTrend(
      sortedHistory.map(h => h.rating)
    );
    const performanceTrend = this.calculateTrend(
      sortedHistory.map(h => h.winPct)
    );
    
    // Calculate consistency (lower variance = more consistent)
    const ratings = sortedHistory.map(h => h.rating);
    const mean = ratings.reduce((sum, r) => sum + r, 0) / ratings.length;
    const variance = ratings.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / ratings.length;
    const standardDeviation = Math.sqrt(variance);
    
    let consistency;
    if (standardDeviation < 50) consistency = 'very_consistent';
    else if (standardDeviation < 100) consistency = 'consistent';
    else if (standardDeviation < 150) consistency = 'inconsistent';
    else consistency = 'very_inconsistent';

    return {
      ratingTrend,
      performanceTrend,
      consistency,
      ratingVariance: Math.round(standardDeviation)
    };
  }

  /**
   * Get league evolution analysis
   */
  async getLeagueEvolution(seasons = [2021, 2022, 2023, 2024, 2025]) {
    const cacheKey = `evolution:${seasons.join(',')}`;
    
    // Check cache first
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }

    try {
      const seasonComparisons = await this.compareSeasons(seasons);
      const validSeasons = seasonComparisons.seasons.filter(s => !s.data.error);
      
      if (validSeasons.length < 2) {
        return {
          error: 'Insufficient data for evolution analysis',
          generatedAt: new Date().toISOString()
        };
      }

      const evolution = {
        timeSpan: {
          start: Math.min(...seasons),
          end: Math.max(...seasons),
          years: seasons.length
        },
        leagueMetrics: this.analyzeLeagueMetrics(validSeasons),
        teamEvolution: await this.analyzeTeamEvolution(validSeasons),
        competitiveEvolution: this.analyzeCompetitiveEvolution(validSeasons),
        generatedAt: new Date().toISOString()
      };

      // Cache the results
      this.cache.set(cacheKey, {
        data: evolution,
        timestamp: Date.now()
      });

      return evolution;
    } catch (error) {
      console.error('Error analyzing league evolution:', error);
      throw error;
    }
  }

  /**
   * Analyze league-wide metrics over time
   */
  analyzeLeagueMetrics(validSeasons) {
    const metrics = validSeasons.map(season => ({
      year: season.year,
      averageRating: season.data.averageRating,
      ratingSpread: season.data.ratingSpread,
      competitiveBalance: season.data.competitiveBalance,
      totalGames: season.data.totalGames,
      totalTeams: season.data.totalTeams
    }));

    return {
      metrics,
      trends: {
        averageRating: this.calculateTrend(metrics.map(m => m.averageRating)),
        ratingSpread: this.calculateTrend(metrics.map(m => m.ratingSpread)),
        competitiveBalance: this.calculateTrend(metrics.map(m => m.competitiveBalance)),
        totalGames: this.calculateTrend(metrics.map(m => m.totalGames)),
        totalTeams: this.calculateTrend(metrics.map(m => m.totalTeams))
      }
    };
  }

  /**
   * Analyze team evolution over time
   */
  async analyzeTeamEvolution(validSeasons) {
    const allTeams = new Set();
    validSeasons.forEach(season => {
      season.data.teamRankings.forEach(team => {
        allTeams.add(team.team);
      });
    });

    const teamEvolutions = [];
    
    for (const team of allTeams) {
      try {
        const teamHistory = await this.getTeamHistory(team, validSeasons.map(s => s.year));
        teamEvolutions.push({
          team,
          history: teamHistory.seasons,
          summary: teamHistory.summary,
          trends: teamHistory.trends
        });
      } catch (error) {
        console.warn(`Error analyzing evolution for team ${team}:`, error);
      }
    }

    return teamEvolutions;
  }

  /**
   * Analyze competitive evolution
   */
  analyzeCompetitiveEvolution(validSeasons) {
    const competitiveData = validSeasons.map(season => ({
      year: season.year,
      balance: season.data.competitiveBalance,
      spread: season.data.ratingSpread,
      topTeam: season.data.topTeam,
      bottomTeam: season.data.bottomTeam
    }));

    return {
      data: competitiveData,
      trends: {
        balance: this.calculateTrend(competitiveData.map(d => d.balance)),
        spread: this.calculateTrend(competitiveData.map(d => d.spread))
      },
      analysis: this.generateCompetitiveAnalysis(competitiveData)
    };
  }

  /**
   * Generate competitive analysis
   */
  generateCompetitiveAnalysis(competitiveData) {
    const balanceTrend = this.calculateTrend(competitiveData.map(d => d.balance));
    const spreadTrend = this.calculateTrend(competitiveData.map(d => d.spread));
    
    let analysis = [];
    
    if (balanceTrend === 'decreasing') {
      analysis.push('The league has become more competitive over time');
    } else if (balanceTrend === 'increasing') {
      analysis.push('The league has become less competitive over time');
    } else {
      analysis.push('The league has maintained consistent competitiveness');
    }
    
    if (spreadTrend === 'decreasing') {
      analysis.push('The gap between top and bottom teams has narrowed');
    } else if (spreadTrend === 'increasing') {
      analysis.push('The gap between top and bottom teams has widened');
    } else {
      analysis.push('The gap between top and bottom teams has remained stable');
    }
    
    return analysis;
  }

  /**
   * Clear cache
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
      timeout: this.cacheTimeout
    };
  }
}

// Create singleton instance
const historicalAnalysisService = new HistoricalAnalysisService();

export default historicalAnalysisService;
