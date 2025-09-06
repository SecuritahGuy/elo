/**
 * Export Service
 * Provides data export and custom report generation functionality
 */

import apiService from './api';
import predictionService from './predictionService';
import confidenceService from './confidenceService';
import historicalAnalysisService from './historicalAnalysisService';

class ExportService {
  constructor() {
    this.supportedFormats = ['csv', 'json', 'xlsx', 'pdf'];
    this.reportTemplates = {
      'elo-summary': 'ELO Ratings Summary',
      'predictions': 'Game Predictions',
      'confidence-analysis': 'Confidence Analysis',
      'historical-comparison': 'Historical Season Comparison',
      'team-analysis': 'Team Performance Analysis',
      'custom': 'Custom Report'
    };
  }

  /**
   * Export ELO ratings data
   */
  async exportEloRatings(season, config = 'comprehensive', format = 'csv') {
    try {
      const eloRatings = await apiService.getEloRatings(season, config);
      const seasonSummary = await apiService.getEloSeasonSummary(season);

      const data = {
        metadata: {
          season,
          config,
          exportDate: new Date().toISOString(),
          totalTeams: eloRatings?.teams?.length || 0
        },
        summary: seasonSummary,
        teams: eloRatings?.teams?.map(team => ({
          team: team.team,
          rating: Math.round(team.rating),
          wins: team.wins || 0,
          losses: team.losses || 0,
          winPct: team.winPct || 0,
          ratingChange: team.ratingChange || 0,
          pointsFor: team.pointsFor || 0,
          pointsAgainst: team.pointsAgainst || 0,
          pointDifferential: team.pointDifferential || 0
        })) || []
      };

      return this.formatData(data, format);
    } catch (error) {
      console.error('Error exporting ELO ratings:', error);
      throw error;
    }
  }

  /**
   * Export game predictions
   */
  async exportPredictions(season, week, format = 'csv') {
    try {
      const predictions = await predictionService.getGamePredictions(season, week);
      const accuracy = await predictionService.getPredictionAccuracy(season, week);

      const data = {
        metadata: {
          season,
          week,
          exportDate: new Date().toISOString(),
          totalGames: predictions.length
        },
        accuracy,
        predictions: predictions.map(game => ({
          gameId: game.id,
          season: game.season,
          week: game.week,
          homeTeam: game.homeTeam,
          awayTeam: game.awayTeam,
          gameDate: game.gameDate,
          status: game.status,
          homeWinProbability: game.prediction?.homeWinProbability || 0,
          awayWinProbability: game.prediction?.awayWinProbability || 0,
          predictedWinner: game.prediction?.predictedWinner || '',
          confidence: game.prediction?.confidence || 0,
          predictedHomeScore: game.prediction?.predictedScore?.home || 0,
          predictedAwayScore: game.prediction?.predictedScore?.away || 0,
          ratingDifference: game.prediction?.ratingDifference || 0,
          homeFieldAdvantage: game.prediction?.homeFieldAdvantage || 0
        }))
      };

      return this.formatData(data, format);
    } catch (error) {
      console.error('Error exporting predictions:', error);
      throw error;
    }
  }

  /**
   * Export confidence analysis
   */
  async exportConfidenceAnalysis(season, format = 'csv') {
    try {
      const confidenceReport = await confidenceService.generateConfidenceReport(season);
      const trends = await confidenceService.getConfidenceTrends(season);

      const data = {
        metadata: {
          season,
          exportDate: new Date().toISOString(),
          reportType: 'confidence-analysis'
        },
        summary: confidenceReport.summary,
        bins: confidenceReport.bins,
        recommendations: confidenceReport.recommendations,
        trends: trends
      };

      return this.formatData(data, format);
    } catch (error) {
      console.error('Error exporting confidence analysis:', error);
      throw error;
    }
  }

  /**
   * Export historical comparison
   */
  async exportHistoricalComparison(seasons, format = 'csv') {
    try {
      const comparison = await historicalAnalysisService.compareSeasons(seasons);

      const data = {
        metadata: {
          seasons,
          exportDate: new Date().toISOString(),
          reportType: 'historical-comparison'
        },
        summary: comparison.summary,
        trends: comparison.trends,
        seasons: comparison.seasons.map(season => ({
          year: season.year,
          totalGames: season.data.totalGames,
          totalTeams: season.data.totalTeams,
          averageRating: season.data.averageRating,
          ratingSpread: season.data.ratingSpread,
          competitiveBalance: season.data.competitiveBalance,
          topTeam: season.data.topTeam?.team || '',
          topTeamRating: season.data.topTeam?.rating || 0,
          bottomTeam: season.data.bottomTeam?.team || '',
          bottomTeamRating: season.data.bottomTeam?.rating || 0
        }))
      };

      return this.formatData(data, format);
    } catch (error) {
      console.error('Error exporting historical comparison:', error);
      throw error;
    }
  }

  /**
   * Export team analysis
   */
  async exportTeamAnalysis(team, seasons, format = 'csv') {
    try {
      const teamHistory = await historicalAnalysisService.getTeamHistory(team, seasons);

      const data = {
        metadata: {
          team,
          seasons,
          exportDate: new Date().toISOString(),
          reportType: 'team-analysis'
        },
        summary: teamHistory.summary,
        trends: teamHistory.trends,
        seasons: teamHistory.seasons.map(season => ({
          season: season.season,
          rating: season.rating,
          rank: season.rank,
          wins: season.wins,
          losses: season.losses,
          winPct: season.winPct,
          change: season.change
        }))
      };

      return this.formatData(data, format);
    } catch (error) {
      console.error('Error exporting team analysis:', error);
      throw error;
    }
  }

  /**
   * Generate custom report
   */
  async generateCustomReport(config, format = 'pdf') {
    try {
      const reportData = {
        metadata: {
          reportType: 'custom',
          exportDate: new Date().toISOString(),
          config
        },
        sections: []
      };

      // Process each section in the config
      for (const section of config.sections) {
        let sectionData = null;

        switch (section.type) {
          case 'elo-ratings':
            sectionData = await this.exportEloRatings(section.season, section.config, 'json');
            break;
          case 'predictions':
            sectionData = await this.exportPredictions(section.season, section.week, 'json');
            break;
          case 'confidence-analysis':
            sectionData = await this.exportConfidenceAnalysis(section.season, 'json');
            break;
          case 'historical-comparison':
            sectionData = await this.exportHistoricalComparison(section.seasons, 'json');
            break;
          case 'team-analysis':
            sectionData = await this.exportTeamAnalysis(section.team, section.seasons, 'json');
            break;
          default:
            console.warn(`Unknown section type: ${section.type}`);
        }

        if (sectionData) {
          reportData.sections.push({
            title: section.title,
            type: section.type,
            data: sectionData
          });
        }
      }

      return this.formatData(reportData, format);
    } catch (error) {
      console.error('Error generating custom report:', error);
      throw error;
    }
  }

  /**
   * Format data for export
   */
  formatData(data, format) {
    switch (format.toLowerCase()) {
      case 'csv':
        return this.formatAsCSV(data);
      case 'json':
        return this.formatAsJSON(data);
      case 'xlsx':
        return this.formatAsXLSX(data);
      case 'pdf':
        return this.formatAsPDF(data);
      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  /**
   * Format data as CSV
   */
  formatAsCSV(data) {
    if (data.teams) {
      return this.convertTeamsToCSV(data);
    } else if (data.predictions) {
      return this.convertPredictionsToCSV(data);
    } else if (data.seasons) {
      return this.convertSeasonsToCSV(data);
    } else {
      return this.convertGenericToCSV(data);
    }
  }

  /**
   * Convert teams data to CSV
   */
  convertTeamsToCSV(data) {
    const headers = ['Team', 'Rating', 'Wins', 'Losses', 'Win%', 'Rating Change', 'Points For', 'Points Against', 'Point Differential'];
    const rows = data.teams.map(team => [
      team.team,
      team.rating,
      team.wins,
      team.losses,
      team.winPct,
      team.ratingChange,
      team.pointsFor,
      team.pointsAgainst,
      team.pointDifferential
    ]);

    return this.createCSVContent([headers, ...rows]);
  }

  /**
   * Convert predictions data to CSV
   */
  convertPredictionsToCSV(data) {
    const headers = [
      'Game ID', 'Season', 'Week', 'Home Team', 'Away Team', 'Game Date', 'Status',
      'Home Win %', 'Away Win %', 'Predicted Winner', 'Confidence', 'Predicted Home Score',
      'Predicted Away Score', 'Rating Difference', 'Home Field Advantage'
    ];
    const rows = data.predictions.map(game => [
      game.gameId,
      game.season,
      game.week,
      game.homeTeam,
      game.awayTeam,
      game.gameDate,
      game.status,
      game.homeWinProbability,
      game.awayWinProbability,
      game.predictedWinner,
      game.confidence,
      game.predictedHomeScore,
      game.predictedAwayScore,
      game.ratingDifference,
      game.homeFieldAdvantage
    ]);

    return this.createCSVContent([headers, ...rows]);
  }

  /**
   * Convert seasons data to CSV
   */
  convertSeasonsToCSV(data) {
    const headers = [
      'Year', 'Total Games', 'Total Teams', 'Average Rating', 'Rating Spread',
      'Competitive Balance', 'Top Team', 'Top Team Rating', 'Bottom Team', 'Bottom Team Rating'
    ];
    const rows = data.seasons.map(season => [
      season.year,
      season.totalGames,
      season.totalTeams,
      season.averageRating,
      season.ratingSpread,
      season.competitiveBalance,
      season.topTeam,
      season.topTeamRating,
      season.bottomTeam,
      season.bottomTeamRating
    ]);

    return this.createCSVContent([headers, ...rows]);
  }

  /**
   * Convert generic data to CSV
   */
  convertGenericToCSV(data) {
    // Flatten the data structure for CSV
    const flattened = this.flattenObject(data);
    const headers = Object.keys(flattened);
    const values = Object.values(flattened);

    return this.createCSVContent([headers, values]);
  }

  /**
   * Create CSV content
   */
  createCSVContent(rows) {
    return rows.map(row => 
      row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
    ).join('\n');
  }

  /**
   * Format data as JSON
   */
  formatAsJSON(data) {
    return JSON.stringify(data, null, 2);
  }

  /**
   * Format data as XLSX (Excel)
   */
  formatAsXLSX(data) {
    // For now, return JSON - in a real implementation, you'd use a library like xlsx
    return {
      type: 'xlsx',
      data: this.formatAsJSON(data),
      note: 'XLSX export requires additional library implementation'
    };
  }

  /**
   * Format data as PDF
   */
  formatAsPDF(data) {
    // For now, return JSON - in a real implementation, you'd use a library like jsPDF
    return {
      type: 'pdf',
      data: this.formatAsJSON(data),
      note: 'PDF export requires additional library implementation'
    };
  }

  /**
   * Flatten object for CSV conversion
   */
  flattenObject(obj, prefix = '') {
    const flattened = {};
    
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const newKey = prefix ? `${prefix}.${key}` : key;
        
        if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
          Object.assign(flattened, this.flattenObject(obj[key], newKey));
        } else {
          flattened[newKey] = obj[key];
        }
      }
    }
    
    return flattened;
  }

  /**
   * Get available export formats
   */
  getSupportedFormats() {
    return this.supportedFormats;
  }

  /**
   * Get available report templates
   */
  getReportTemplates() {
    return this.reportTemplates;
  }

  /**
   * Validate export configuration
   */
  validateExportConfig(config) {
    const errors = [];

    if (!config.format || !this.supportedFormats.includes(config.format)) {
      errors.push(`Invalid format. Supported formats: ${this.supportedFormats.join(', ')}`);
    }

    if (!config.type || !this.reportTemplates[config.type]) {
      errors.push(`Invalid report type. Available types: ${Object.keys(this.reportTemplates).join(', ')}`);
    }

    // Validate specific requirements based on type
    switch (config.type) {
      case 'elo-summary':
        if (!config.season) errors.push('Season is required for ELO summary');
        break;
      case 'predictions':
        if (!config.season || !config.week) errors.push('Season and week are required for predictions');
        break;
      case 'confidence-analysis':
        if (!config.season) errors.push('Season is required for confidence analysis');
        break;
      case 'historical-comparison':
        if (!config.seasons || !Array.isArray(config.seasons) || config.seasons.length < 2) {
          errors.push('At least 2 seasons are required for historical comparison');
        }
        break;
      case 'team-analysis':
        if (!config.team || !config.seasons || !Array.isArray(config.seasons)) {
          errors.push('Team and seasons are required for team analysis');
        }
        break;
      default:
        errors.push(`Unknown export type: ${config.type}`);
        break;
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Generate export filename
   */
  generateFilename(type, config, format) {
    const timestamp = new Date().toISOString().split('T')[0];
    const baseName = this.reportTemplates[type]?.toLowerCase().replace(/\s+/g, '-') || 'export';
    
    let filename = `${baseName}-${timestamp}`;
    
    // Add specific identifiers based on type
    switch (type) {
      case 'elo-summary':
        filename += `-season-${config.season}`;
        break;
      case 'predictions':
        filename += `-season-${config.season}-week-${config.week}`;
        break;
      case 'confidence-analysis':
        filename += `-season-${config.season}`;
        break;
      case 'historical-comparison':
        filename += `-seasons-${config.seasons.join('-')}`;
        break;
      case 'team-analysis':
        filename += `-${config.team}-seasons-${config.seasons.join('-')}`;
        break;
      default:
        filename += `-${type}`;
        break;
    }
    
    return `${filename}.${format}`;
  }

  /**
   * Download file
   */
  downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
  }

  /**
   * Get MIME type for format
   */
  getMimeType(format) {
    const mimeTypes = {
      'csv': 'text/csv',
      'json': 'application/json',
      'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'pdf': 'application/pdf'
    };
    
    return mimeTypes[format] || 'text/plain';
  }

  /**
   * Export with download
   */
  async exportAndDownload(config) {
    try {
      const validation = this.validateExportConfig(config);
      if (!validation.isValid) {
        throw new Error(`Export configuration invalid: ${validation.errors.join(', ')}`);
      }

      let content;
      switch (config.type) {
        case 'elo-summary':
          content = await this.exportEloRatings(config.season, config.config, config.format);
          break;
        case 'predictions':
          content = await this.exportPredictions(config.season, config.week, config.format);
          break;
        case 'confidence-analysis':
          content = await this.exportConfidenceAnalysis(config.season, config.format);
          break;
        case 'historical-comparison':
          content = await this.exportHistoricalComparison(config.seasons, config.format);
          break;
        case 'team-analysis':
          content = await this.exportTeamAnalysis(config.team, config.seasons, config.format);
          break;
        case 'custom':
          content = await this.generateCustomReport(config, config.format);
          break;
        default:
          throw new Error(`Unknown export type: ${config.type}`);
      }

      const filename = this.generateFilename(config.type, config, config.format);
      const mimeType = this.getMimeType(config.format);
      
      this.downloadFile(content, filename, mimeType);
      
      return {
        success: true,
        filename,
        message: `Export completed: ${filename}`
      };
    } catch (error) {
      console.error('Export failed:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// Create singleton instance
const exportService = new ExportService();

export default exportService;
