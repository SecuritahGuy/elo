/**
 * Prediction Analytics Service
 * Advanced analytics for prediction performance, model evaluation, and insights
 */

import apiService from './api';

class PredictionAnalyticsService {
  constructor() {
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Calculate Brier Score for prediction calibration
   * Lower scores indicate better calibration
   */
  calculateBrierScore(predictions) {
    if (!predictions || predictions.length === 0) return null;

    let totalBrierScore = 0;
    let validPredictions = 0;

    predictions.forEach(prediction => {
      if (prediction.homeWinProb !== undefined && prediction.actualWinner !== undefined) {
        const actualOutcome = prediction.actualWinner === prediction.homeTeam ? 1 : 0;
        const predictedProb = prediction.homeWinProb;
        const brierScore = Math.pow(predictedProb - actualOutcome, 2);
        totalBrierScore += brierScore;
        validPredictions++;
      }
    });

    return validPredictions > 0 ? totalBrierScore / validPredictions : null;
  }

  /**
   * Calculate Log Loss for prediction accuracy
   * Lower scores indicate better predictions
   */
  calculateLogLoss(predictions) {
    if (!predictions || predictions.length === 0) return null;

    let totalLogLoss = 0;
    let validPredictions = 0;

    predictions.forEach(prediction => {
      if (prediction.homeWinProb !== undefined && prediction.actualWinner !== undefined) {
        const actualOutcome = prediction.actualWinner === prediction.homeTeam ? 1 : 0;
        const predictedProb = Math.max(0.001, Math.min(0.999, prediction.homeWinProb)); // Clamp to avoid log(0)
        const logLoss = -(actualOutcome * Math.log(predictedProb) + (1 - actualOutcome) * Math.log(1 - predictedProb));
        totalLogLoss += logLoss;
        validPredictions++;
      }
    });

    return validPredictions > 0 ? totalLogLoss / validPredictions : null;
  }

  /**
   * Calculate reliability diagram data for calibration analysis
   */
  calculateReliabilityDiagram(predictions, bins = 10) {
    if (!predictions || predictions.length === 0) return null;

    const binSize = 1.0 / bins;
    const binData = Array(bins).fill(null).map(() => ({
      binMin: 0,
      binMax: 0,
      binCenter: 0,
      count: 0,
      accuracy: 0,
      avgConfidence: 0,
      expectedAccuracy: 0
    }));

    // Initialize bins
    for (let i = 0; i < bins; i++) {
      binData[i].binMin = i * binSize;
      binData[i].binMax = (i + 1) * binSize;
      binData[i].binCenter = (binData[i].binMin + binData[i].binMax) / 2;
      binData[i].expectedAccuracy = binData[i].binCenter;
    }

    // Group predictions into bins
    predictions.forEach(prediction => {
      if (prediction.homeWinProb !== undefined && prediction.actualWinner !== undefined) {
        const actualOutcome = prediction.actualWinner === prediction.homeTeam ? 1 : 0;
        const predictedProb = prediction.homeWinProb;
        
        const binIndex = Math.min(Math.floor(predictedProb / binSize), bins - 1);
        binData[binIndex].count++;
        binData[binIndex].accuracy += actualOutcome;
        binData[binIndex].avgConfidence += predictedProb;
      }
    });

    // Calculate final metrics for each bin
    binData.forEach(bin => {
      if (bin.count > 0) {
        bin.accuracy = bin.accuracy / bin.count;
        bin.avgConfidence = bin.avgConfidence / bin.count;
      }
    });

    return binData.filter(bin => bin.count > 0);
  }

  /**
   * Calculate Sharpness - measures how often the model makes confident predictions
   */
  calculateSharpness(predictions) {
    if (!predictions || predictions.length === 0) return null;

    let totalSharpness = 0;
    let validPredictions = 0;

    predictions.forEach(prediction => {
      if (prediction.homeWinProb !== undefined) {
        const confidence = Math.abs(prediction.homeWinProb - 0.5) * 2; // Convert to 0-1 scale
        totalSharpness += confidence;
        validPredictions++;
      }
    });

    return validPredictions > 0 ? totalSharpness / validPredictions : null;
  }

  /**
   * Calculate Resolution - measures how well the model distinguishes between different outcomes
   */
  calculateResolution(predictions) {
    if (!predictions || predictions.length === 0) return null;

    const overallAccuracy = this.calculateOverallAccuracy(predictions);
    if (overallAccuracy === null) return null;

    let totalResolution = 0;
    let validPredictions = 0;

    predictions.forEach(prediction => {
      if (prediction.homeWinProb !== undefined && prediction.actualWinner !== undefined) {
        const actualOutcome = prediction.actualWinner === prediction.homeTeam ? 1 : 0;
        const predictedProb = prediction.homeWinProb;
        const resolution = Math.pow(predictedProb - overallAccuracy, 2);
        totalResolution += resolution;
        validPredictions++;
      }
    });

    return validPredictions > 0 ? totalResolution / validPredictions : null;
  }

  /**
   * Calculate overall accuracy
   */
  calculateOverallAccuracy(predictions) {
    if (!predictions || predictions.length === 0) return null;

    let correctPredictions = 0;
    let totalPredictions = 0;

    predictions.forEach(prediction => {
      if (prediction.predictedWinner && prediction.actualWinner) {
        if (prediction.predictedWinner === prediction.actualWinner) {
          correctPredictions++;
        }
        totalPredictions++;
      }
    });

    return totalPredictions > 0 ? correctPredictions / totalPredictions : null;
  }

  /**
   * Calculate confidence-weighted accuracy
   */
  calculateConfidenceWeightedAccuracy(predictions) {
    if (!predictions || predictions.length === 0) return null;

    let weightedCorrect = 0;
    let totalWeight = 0;

    predictions.forEach(prediction => {
      if (prediction.predictedWinner && prediction.actualWinner && prediction.confidence !== undefined) {
        const isCorrect = prediction.predictedWinner === prediction.actualWinner;
        const weight = prediction.confidence;
        
        if (isCorrect) {
          weightedCorrect += weight;
        }
        totalWeight += weight;
      }
    });

    return totalWeight > 0 ? weightedCorrect / totalWeight : null;
  }

  /**
   * Calculate model performance by confidence level
   */
  calculateConfidencePerformance(predictions) {
    if (!predictions || predictions.length === 0) return null;

    const confidenceLevels = [
      { name: 'Very Low', min: 0, max: 0.2 },
      { name: 'Low', min: 0.2, max: 0.4 },
      { name: 'Medium', min: 0.4, max: 0.6 },
      { name: 'High', min: 0.6, max: 0.8 },
      { name: 'Very High', min: 0.8, max: 1.0 }
    ];

    return confidenceLevels.map(level => {
      const levelPredictions = predictions.filter(p => 
        p.confidence !== undefined && 
        p.confidence >= level.min && 
        p.confidence < level.max
      );

      const accuracy = this.calculateOverallAccuracy(levelPredictions);
      const avgConfidence = levelPredictions.length > 0 
        ? levelPredictions.reduce((sum, p) => sum + p.confidence, 0) / levelPredictions.length 
        : 0;

      return {
        ...level,
        count: levelPredictions.length,
        accuracy: accuracy || 0,
        avgConfidence,
        expectedAccuracy: (level.min + level.max) / 2,
        calibrationError: accuracy ? Math.abs(accuracy - (level.min + level.max) / 2) : 0
      };
    });
  }

  /**
   * Calculate team-specific performance metrics
   */
  calculateTeamPerformance(predictions) {
    if (!predictions || predictions.length === 0) return null;

    const teamStats = new Map();

    predictions.forEach(prediction => {
      if (prediction.homeTeam && prediction.awayTeam && prediction.actualWinner) {
        // Home team stats
        if (!teamStats.has(prediction.homeTeam)) {
          teamStats.set(prediction.homeTeam, {
            team: prediction.homeTeam,
            totalGames: 0,
            correctPredictions: 0,
            homeGames: 0,
            awayGames: 0,
            avgConfidence: 0,
            totalConfidence: 0
          });
        }

        const homeStats = teamStats.get(prediction.homeTeam);
        homeStats.totalGames++;
        homeStats.homeGames++;
        homeStats.totalConfidence += prediction.confidence || 0;

        if (prediction.predictedWinner === prediction.homeTeam && prediction.actualWinner === prediction.homeTeam) {
          homeStats.correctPredictions++;
        }

        // Away team stats
        if (!teamStats.has(prediction.awayTeam)) {
          teamStats.set(prediction.awayTeam, {
            team: prediction.awayTeam,
            totalGames: 0,
            correctPredictions: 0,
            homeGames: 0,
            awayGames: 0,
            avgConfidence: 0,
            totalConfidence: 0
          });
        }

        const awayStats = teamStats.get(prediction.awayTeam);
        awayStats.totalGames++;
        awayStats.awayGames++;
        awayStats.totalConfidence += prediction.confidence || 0;

        if (prediction.predictedWinner === prediction.awayTeam && prediction.actualWinner === prediction.awayTeam) {
          awayStats.correctPredictions++;
        }
      }
    });

    // Calculate final metrics
    const teamPerformance = Array.from(teamStats.values()).map(stats => ({
      ...stats,
      accuracy: stats.totalGames > 0 ? stats.correctPredictions / stats.totalGames : 0,
      avgConfidence: stats.totalGames > 0 ? stats.totalConfidence / stats.totalGames : 0,
      homeAccuracy: stats.homeGames > 0 ? stats.correctPredictions / stats.homeGames : 0,
      awayAccuracy: stats.awayGames > 0 ? stats.correctPredictions / stats.awayGames : 0
    }));

    return teamPerformance.sort((a, b) => b.accuracy - a.accuracy);
  }

  /**
   * Calculate temporal performance trends
   */
  calculateTemporalTrends(predictions) {
    if (!predictions || predictions.length === 0) return null;

    // Group by week
    const weeklyStats = new Map();
    
    predictions.forEach(prediction => {
      if (prediction.week && prediction.actualWinner) {
        if (!weeklyStats.has(prediction.week)) {
          weeklyStats.set(prediction.week, {
            week: prediction.week,
            totalGames: 0,
            correctPredictions: 0,
            avgConfidence: 0,
            totalConfidence: 0
          });
        }

        const weekStats = weeklyStats.get(prediction.week);
        weekStats.totalGames++;
        weekStats.totalConfidence += prediction.confidence || 0;

        if (prediction.predictedWinner === prediction.actualWinner) {
          weekStats.correctPredictions++;
        }
      }
    });

    // Calculate final metrics
    const weeklyTrends = Array.from(weeklyStats.values()).map(stats => ({
      ...stats,
      accuracy: stats.totalGames > 0 ? stats.correctPredictions / stats.totalGames : 0,
      avgConfidence: stats.totalGames > 0 ? stats.totalConfidence / stats.totalGames : 0
    }));

    return weeklyTrends.sort((a, b) => a.week - b.week);
  }

  /**
   * Calculate model stability metrics
   */
  calculateModelStability(predictions) {
    if (!predictions || predictions.length === 0) return null;

    const weeklyTrends = this.calculateTemporalTrends(predictions);
    if (!weeklyTrends || weeklyTrends.length < 2) return null;

    const accuracies = weeklyTrends.map(week => week.accuracy);
    const confidences = weeklyTrends.map(week => week.avgConfidence);

    // Calculate standard deviation
    const avgAccuracy = accuracies.reduce((sum, acc) => sum + acc, 0) / accuracies.length;
    const avgConfidence = confidences.reduce((sum, conf) => sum + conf, 0) / confidences.length;

    const accuracyVariance = accuracies.reduce((sum, acc) => sum + Math.pow(acc - avgAccuracy, 2), 0) / accuracies.length;
    const confidenceVariance = confidences.reduce((sum, conf) => sum + Math.pow(conf - avgConfidence, 2), 0) / confidences.length;

    return {
      accuracyStdDev: Math.sqrt(accuracyVariance),
      confidenceStdDev: Math.sqrt(confidenceVariance),
      accuracyRange: Math.max(...accuracies) - Math.min(...accuracies),
      confidenceRange: Math.max(...confidences) - Math.min(...confidences),
      stabilityScore: 1 - (Math.sqrt(accuracyVariance) + Math.sqrt(confidenceVariance)) / 2
    };
  }

  /**
   * Generate comprehensive analytics report
   */
  async generateAnalyticsReport(season, week = null) {
    const cacheKey = `analytics_${season}_${week || 'all'}`;
    const cached = this.cache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }

    try {
      // Get prediction data
      const predictions = await this.getPredictionData(season, week);
      
      if (!predictions || predictions.length === 0) {
        throw new Error('No prediction data available');
      }

      // Calculate all metrics
      const report = {
        metadata: {
          season,
          week,
          totalPredictions: predictions.length,
          generatedAt: new Date().toISOString()
        },
        overallMetrics: {
          accuracy: this.calculateOverallAccuracy(predictions),
          brierScore: this.calculateBrierScore(predictions),
          logLoss: this.calculateLogLoss(predictions),
          sharpness: this.calculateSharpness(predictions),
          resolution: this.calculateResolution(predictions),
          confidenceWeightedAccuracy: this.calculateConfidenceWeightedAccuracy(predictions)
        },
        calibration: {
          reliabilityDiagram: this.calculateReliabilityDiagram(predictions),
          confidencePerformance: this.calculateConfidencePerformance(predictions)
        },
        teamPerformance: this.calculateTeamPerformance(predictions),
        temporalTrends: this.calculateTemporalTrends(predictions),
        modelStability: this.calculateModelStability(predictions),
        insights: this.generateInsights(predictions)
      };

      // Cache the result
      this.cache.set(cacheKey, {
        data: report,
        timestamp: Date.now()
      });

      return report;
    } catch (error) {
      console.error('Error generating analytics report:', error);
      throw error;
    }
  }

  /**
   * Get prediction data from API or mock data
   */
  async getPredictionData(season, week = null) {
    try {
      // Try to get real data from API
      const response = await apiService.getWeekPredictions(week || 1);
      return response.data.predictions || [];
    } catch (error) {
      console.warn('API data not available for prediction analytics');
      // Return empty array instead of mock data
      return [];
    }
  }

  /**
   * Generate mock prediction data for testing
   */
  generateMockPredictionData(season, week = null) {
    const teams = ['KC', 'BUF', 'SF', 'BAL', 'DAL', 'PHI', 'GB', 'MIN', 'DET', 'CIN', 'LAR', 'TB', 'MIA', 'NYJ', 'NE', 'PIT'];
    const predictions = [];
    
    const weeks = week ? [week] : Array.from({length: 18}, (_, i) => i + 1);
    
    weeks.forEach(w => {
      for (let i = 0; i < teams.length; i += 2) {
        if (i + 1 < teams.length) {
          const homeTeam = teams[i];
          const awayTeam = teams[i + 1];
          const homeWinProb = Math.random();
          const predictedWinner = homeWinProb > 0.5 ? homeTeam : awayTeam;
          const actualWinner = Math.random() > 0.4 ? predictedWinner : (predictedWinner === homeTeam ? awayTeam : homeTeam);
          const confidence = Math.abs(homeWinProb - 0.5) * 2;
          
          predictions.push({
            season,
            week: w,
            homeTeam,
            awayTeam,
            homeWinProb,
            predictedWinner,
            actualWinner,
            confidence,
            gameDate: new Date(season, 8, w * 7).toISOString()
          });
        }
      }
    });

    return predictions;
  }

  /**
   * Generate insights based on analytics
   */
  generateInsights(predictions) {
    const overallAccuracy = this.calculateOverallAccuracy(predictions);
    const brierScore = this.calculateBrierScore(predictions);
    const confidencePerformance = this.calculateConfidencePerformance(predictions);
    const teamPerformance = this.calculateTeamPerformance(predictions);
    const modelStability = this.calculateModelStability(predictions);

    const insights = [];

    // Accuracy insights
    if (overallAccuracy !== null) {
      if (overallAccuracy > 0.65) {
        insights.push({
          type: 'positive',
          category: 'accuracy',
          message: `Excellent overall accuracy of ${(overallAccuracy * 100).toFixed(1)}%`,
          recommendation: 'Model is performing very well. Consider increasing prediction frequency.'
        });
      } else if (overallAccuracy > 0.55) {
        insights.push({
          type: 'neutral',
          category: 'accuracy',
          message: `Good overall accuracy of ${(overallAccuracy * 100).toFixed(1)}%`,
          recommendation: 'Model is performing well. Monitor for consistency.'
        });
      } else {
        insights.push({
          type: 'warning',
          category: 'accuracy',
          message: `Accuracy of ${(overallAccuracy * 100).toFixed(1)}% could be improved`,
          recommendation: 'Consider reviewing model parameters or adding more features.'
        });
      }
    }

    // Calibration insights
    if (brierScore !== null) {
      if (brierScore < 0.2) {
        insights.push({
          type: 'positive',
          category: 'calibration',
          message: `Excellent calibration with Brier score of ${brierScore.toFixed(3)}`,
          recommendation: 'Model confidence levels are well-calibrated.'
        });
      } else if (brierScore < 0.3) {
        insights.push({
          type: 'neutral',
          category: 'calibration',
          message: `Good calibration with Brier score of ${brierScore.toFixed(3)}`,
          recommendation: 'Model calibration is acceptable but could be improved.'
        });
      } else {
        insights.push({
          type: 'warning',
          category: 'calibration',
          message: `Poor calibration with Brier score of ${brierScore.toFixed(3)}`,
          recommendation: 'Model confidence levels need significant improvement.'
        });
      }
    }

    // Confidence performance insights
    if (confidencePerformance) {
      const highConfidence = confidencePerformance.find(level => level.name === 'High' || level.name === 'Very High');
      if (highConfidence && highConfidence.count > 0) {
        if (highConfidence.accuracy > 0.8) {
          insights.push({
            type: 'positive',
            category: 'confidence',
            message: `High confidence predictions are very accurate (${(highConfidence.accuracy * 100).toFixed(1)}%)`,
            recommendation: 'Model is well-calibrated for high-confidence predictions.'
          });
        } else if (highConfidence.accuracy < 0.6) {
          insights.push({
            type: 'warning',
            category: 'confidence',
            message: `High confidence predictions are less accurate than expected (${(highConfidence.accuracy * 100).toFixed(1)}%)`,
            recommendation: 'Model may be overconfident. Consider adjusting confidence thresholds.'
          });
        }
      }
    }

    // Team performance insights
    if (teamPerformance && teamPerformance.length > 0) {
      const bestTeam = teamPerformance[0];
      const worstTeam = teamPerformance[teamPerformance.length - 1];
      
      if (bestTeam.accuracy > 0.8) {
        insights.push({
          type: 'positive',
          category: 'team_performance',
          message: `Excellent predictions for ${bestTeam.team} (${(bestTeam.accuracy * 100).toFixed(1)}% accuracy)`,
          recommendation: 'Consider analyzing what makes this team predictable.'
        });
      }
      
      if (worstTeam.accuracy < 0.4) {
        insights.push({
          type: 'warning',
          category: 'team_performance',
          message: `Poor predictions for ${worstTeam.team} (${(worstTeam.accuracy * 100).toFixed(1)}% accuracy)`,
          recommendation: 'Investigate why this team is difficult to predict.'
        });
      }
    }

    // Stability insights
    if (modelStability) {
      if (modelStability.stabilityScore > 0.8) {
        insights.push({
          type: 'positive',
          category: 'stability',
          message: `Model shows excellent stability (score: ${modelStability.stabilityScore.toFixed(2)})`,
          recommendation: 'Model is consistent across different time periods.'
        });
      } else if (modelStability.stabilityScore < 0.5) {
        insights.push({
          type: 'warning',
          category: 'stability',
          message: `Model shows poor stability (score: ${modelStability.stabilityScore.toFixed(2)})`,
          recommendation: 'Model performance varies significantly. Consider retraining or parameter adjustment.'
        });
      }
    }

    return insights;
  }

  /**
   * Clear cache
   */
  clearCache() {
    this.cache.clear();
  }
}

export default new PredictionAnalyticsService();
