/**
 * Confidence Scoring Service
 * Provides better confidence calibration and display for predictions
 */

import predictionService from './predictionService';

class ConfidenceService {
  constructor() {
    this.calibrationData = new Map();
    this.historicalAccuracy = new Map();
    this.confidenceBins = [
      { min: 0, max: 20, label: 'Very Low' },
      { min: 20, max: 40, label: 'Low' },
      { min: 40, max: 60, label: 'Medium' },
      { min: 60, max: 80, label: 'High' },
      { min: 80, max: 100, label: 'Very High' }
    ];
  }

  /**
   * Calibrate confidence scores based on historical accuracy
   */
  async calibrateConfidence(season = 2025) {
    try {
      const calibrationResults = {
        bins: [],
        overallCalibration: 0,
        reliability: 0,
        sharpness: 0,
        recommendations: []
      };

      // Analyze confidence bins
      for (const bin of this.confidenceBins) {
        const binData = await this.analyzeConfidenceBin(bin, season);
        calibrationResults.bins.push(binData);
      }

      // Calculate overall calibration metrics
      calibrationResults.overallCalibration = this.calculateOverallCalibration(calibrationResults.bins);
      calibrationResults.reliability = this.calculateReliability(calibrationResults.bins);
      calibrationResults.sharpness = this.calculateSharpness(calibrationResults.bins);

      // Generate recommendations
      calibrationResults.recommendations = this.generateCalibrationRecommendations(calibrationResults);

      // Store calibration data
      this.calibrationData.set(season, calibrationResults);

      return calibrationResults;
    } catch (error) {
      console.error('Error calibrating confidence:', error);
      throw error;
    }
  }

  /**
   * Analyze a specific confidence bin
   */
  async analyzeConfidenceBin(bin, season) {
    const binData = {
      range: `${bin.min}-${bin.max}%`,
      label: bin.label,
      predictedCount: 0,
      actualAccuracy: 0,
      expectedAccuracy: (bin.min + bin.max) / 2,
      calibrationError: 0,
      reliability: 0
    };

    // Get historical predictions for this confidence range
    const historicalPredictions = await this.getHistoricalPredictions(season, bin);
    
    if (historicalPredictions.length === 0) {
      return binData;
    }

    binData.predictedCount = historicalPredictions.length;
    
    // Calculate actual accuracy
    const correctPredictions = historicalPredictions.filter(p => 
      p.actualWinner === p.predictedWinner
    ).length;
    
    binData.actualAccuracy = (correctPredictions / historicalPredictions.length) * 100;
    binData.calibrationError = Math.abs(binData.actualAccuracy - binData.expectedAccuracy);
    binData.reliability = this.calculateBinReliability(historicalPredictions);

    return binData;
  }

  /**
   * Get historical predictions for a confidence range
   */
  async getHistoricalPredictions(season, bin) {
    const predictions = [];
    
    // Get predictions for each week
    for (let week = 1; week <= 18; week++) {
      try {
        const weeklyPredictions = await predictionService.getGamePredictions(season, week);
        
        // Filter predictions in this confidence range
        const binPredictions = weeklyPredictions.filter(game => 
          game.prediction && 
          game.prediction.confidence >= bin.min && 
          game.prediction.confidence < bin.max
        );
        
        predictions.push(...binPredictions);
      } catch (error) {
        console.warn(`Error getting predictions for week ${week}:`, error);
      }
    }
    
    return predictions;
  }

  /**
   * Calculate overall calibration score
   */
  calculateOverallCalibration(bins) {
    const totalPredictions = bins.reduce((sum, bin) => sum + bin.predictedCount, 0);
    
    if (totalPredictions === 0) return 0;
    
    const weightedCalibrationError = bins.reduce((sum, bin) => {
      return sum + (bin.calibrationError * bin.predictedCount);
    }, 0);
    
    return Math.max(0, 100 - (weightedCalibrationError / totalPredictions));
  }

  /**
   * Calculate reliability score
   */
  calculateReliability(bins) {
    const totalPredictions = bins.reduce((sum, bin) => sum + bin.predictedCount, 0);
    
    if (totalPredictions === 0) return 0;
    
    const weightedReliability = bins.reduce((sum, bin) => {
      return sum + (bin.reliability * bin.predictedCount);
    }, 0);
    
    return weightedReliability / totalPredictions;
  }

  /**
   * Calculate sharpness (how often high confidence predictions are made)
   */
  calculateSharpness(bins) {
    const highConfidenceBins = bins.filter(bin => bin.min >= 60);
    const totalPredictions = bins.reduce((sum, bin) => sum + bin.predictedCount, 0);
    
    if (totalPredictions === 0) return 0;
    
    const highConfidencePredictions = highConfidenceBins.reduce((sum, bin) => 
      sum + bin.predictedCount, 0
    );
    
    return (highConfidencePredictions / totalPredictions) * 100;
  }

  /**
   * Calculate reliability for a specific bin
   */
  calculateBinReliability(predictions) {
    if (predictions.length === 0) return 0;
    
    // Calculate variance in accuracy
    const accuracies = predictions.map(p => 
      p.actualWinner === p.predictedWinner ? 1 : 0
    );
    
    const mean = accuracies.reduce((sum, acc) => sum + acc, 0) / accuracies.length;
    const variance = accuracies.reduce((sum, acc) => sum + Math.pow(acc - mean, 2), 0) / accuracies.length;
    
    // Lower variance = higher reliability
    return Math.max(0, 100 - (variance * 100));
  }

  /**
   * Generate calibration recommendations
   */
  generateCalibrationRecommendations(calibrationResults) {
    const recommendations = [];
    
    // Check for overconfidence
    const overconfidentBins = calibrationResults.bins.filter(bin => 
      bin.actualAccuracy < bin.expectedAccuracy - 10
    );
    
    if (overconfidentBins.length > 0) {
      recommendations.push({
        type: 'overconfidence',
        severity: 'high',
        message: 'Model is overconfident in high-confidence predictions',
        affectedBins: overconfidentBins.map(bin => bin.range)
      });
    }
    
    // Check for underconfidence
    const underconfidentBins = calibrationResults.bins.filter(bin => 
      bin.actualAccuracy > bin.expectedAccuracy + 10
    );
    
    if (underconfidentBins.length > 0) {
      recommendations.push({
        type: 'underconfidence',
        severity: 'medium',
        message: 'Model is underconfident in some predictions',
        affectedBins: underconfidentBins.map(bin => bin.range)
      });
    }
    
    // Check for low sharpness
    if (calibrationResults.sharpness < 30) {
      recommendations.push({
        type: 'low_sharpness',
        severity: 'medium',
        message: 'Model makes too few high-confidence predictions',
        suggestion: 'Consider adjusting confidence thresholds'
      });
    }
    
    // Check for low reliability
    if (calibrationResults.reliability < 70) {
      recommendations.push({
        type: 'low_reliability',
        severity: 'high',
        message: 'Prediction accuracy is inconsistent',
        suggestion: 'Review model features and training data'
      });
    }
    
    return recommendations;
  }

  /**
   * Get calibrated confidence score
   */
  getCalibratedConfidence(rawConfidence, season = 2025) {
    const calibration = this.calibrationData.get(season);
    
    if (!calibration) {
      return {
        raw: rawConfidence,
        calibrated: rawConfidence,
        label: this.getConfidenceLabel(rawConfidence),
        adjustment: 0
      };
    }
    
    // Find the appropriate bin
    const bin = calibration.bins.find(b => 
      rawConfidence >= b.min && rawConfidence < b.max
    );
    
    if (!bin) {
      return {
        raw: rawConfidence,
        calibrated: rawConfidence,
        label: this.getConfidenceLabel(rawConfidence),
        adjustment: 0
      };
    }
    
    // Calculate calibration adjustment
    const expectedAccuracy = bin.expectedAccuracy;
    const actualAccuracy = bin.actualAccuracy;
    const adjustment = actualAccuracy - expectedAccuracy;
    
    // Apply adjustment with some smoothing
    const calibratedConfidence = Math.max(0, Math.min(100, 
      rawConfidence + (adjustment * 0.5)
    ));
    
    return {
      raw: rawConfidence,
      calibrated: Math.round(calibratedConfidence),
      label: this.getConfidenceLabel(calibratedConfidence),
      adjustment: Math.round(adjustment),
      bin: bin.range,
      actualAccuracy: Math.round(actualAccuracy),
      expectedAccuracy: Math.round(expectedAccuracy)
    };
  }

  /**
   * Get confidence label
   */
  getConfidenceLabel(confidence) {
    const bin = this.confidenceBins.find(b => 
      confidence >= b.min && confidence <= b.max
    );
    return bin ? bin.label : 'Unknown';
  }

  /**
   * Get confidence color
   */
  getConfidenceColor(confidence) {
    if (confidence >= 80) return 'text-green-600 bg-green-100';
    if (confidence >= 60) return 'text-yellow-600 bg-yellow-100';
    if (confidence >= 40) return 'text-orange-600 bg-orange-100';
    return 'text-red-600 bg-red-100';
  }

  /**
   * Get confidence icon
   */
  getConfidenceIcon(confidence) {
    if (confidence >= 80) return '🎯';
    if (confidence >= 60) return '📊';
    if (confidence >= 40) return '⚠️';
    return '❓';
  }

  /**
   * Generate confidence report
   */
  async generateConfidenceReport(season = 2025) {
    try {
      const calibration = await this.calibrateConfidence(season);
      
      const report = {
        season,
        generatedAt: new Date().toISOString(),
        summary: {
          overallCalibration: Math.round(calibration.overallCalibration),
          reliability: Math.round(calibration.reliability),
          sharpness: Math.round(calibration.sharpness),
          totalPredictions: calibration.bins.reduce((sum, bin) => sum + bin.predictedCount, 0)
        },
        bins: calibration.bins.map(bin => ({
          range: bin.range,
          label: bin.label,
          predictedCount: bin.predictedCount,
          actualAccuracy: Math.round(bin.actualAccuracy),
          expectedAccuracy: Math.round(bin.expectedAccuracy),
          calibrationError: Math.round(bin.calibrationError),
          reliability: Math.round(bin.reliability)
        })),
        recommendations: calibration.recommendations,
        status: this.getCalibrationStatus(calibration)
      };
      
      return report;
    } catch (error) {
      console.error('Error generating confidence report:', error);
      throw error;
    }
  }

  /**
   * Get calibration status
   */
  getCalibrationStatus(calibration) {
    if (calibration.overallCalibration >= 90) return 'excellent';
    if (calibration.overallCalibration >= 80) return 'good';
    if (calibration.overallCalibration >= 70) return 'fair';
    return 'poor';
  }

  /**
   * Get confidence trends over time
   */
  async getConfidenceTrends(season = 2025) {
    try {
      const trends = {
        weeklyCalibration: [],
        confidenceDistribution: [],
        accuracyByConfidence: []
      };
      
      // Analyze weekly calibration
      for (let week = 1; week <= 18; week++) {
        try {
          const weeklyCalibration = await this.calculateWeeklyCalibration(season, week);
          trends.weeklyCalibration.push({
            week,
            calibration: weeklyCalibration.calibration,
            reliability: weeklyCalibration.reliability,
            totalPredictions: weeklyCalibration.totalPredictions
          });
        } catch (error) {
          console.warn(`Error calculating calibration for week ${week}:`, error);
        }
      }
      
      // Analyze confidence distribution
      const distribution = await this.analyzeConfidenceDistribution(season);
      trends.confidenceDistribution = distribution;
      
      // Analyze accuracy by confidence
      const accuracyByConfidence = await this.analyzeAccuracyByConfidence(season);
      trends.accuracyByConfidence = accuracyByConfidence;
      
      return trends;
    } catch (error) {
      console.error('Error analyzing confidence trends:', error);
      throw error;
    }
  }

  /**
   * Calculate weekly calibration
   */
  async calculateWeeklyCalibration(season, week) {
    const predictions = await predictionService.getGamePredictions(season, week);
    
    if (predictions.length === 0) {
      return { calibration: 0, reliability: 0, totalPredictions: 0 };
    }
    
    // Group by confidence bins
    const binGroups = {};
    for (const bin of this.confidenceBins) {
      binGroups[bin.range] = predictions.filter(p => 
        p.prediction && 
        p.prediction.confidence >= bin.min && 
        p.prediction.confidence <= bin.max
      );
    }
    
    // Calculate calibration for each bin
    let totalCalibrationError = 0;
    let totalPredictions = 0;
    
    for (const [range, binPredictions] of Object.entries(binGroups)) {
      if (binPredictions.length === 0) continue;
      
      const bin = this.confidenceBins.find(b => b.range === range);
      if (!bin) continue;
      const expectedAccuracy = (bin.min + bin.max) / 2;
      
      const correctPredictions = binPredictions.filter(p => 
        p.actualWinner === p.predictedWinner
      ).length;
      
      const actualAccuracy = (correctPredictions / binPredictions.length) * 100;
      const calibrationError = Math.abs(actualAccuracy - expectedAccuracy);
      
      totalCalibrationError += calibrationError * binPredictions.length;
      totalPredictions += binPredictions.length;
    }
    
    const calibration = totalPredictions > 0 ? 
      Math.max(0, 100 - (totalCalibrationError / totalPredictions)) : 0;
    
    return {
      calibration,
      reliability: 0, // Simplified for now
      totalPredictions
    };
  }

  /**
   * Analyze confidence distribution
   */
  async analyzeConfidenceDistribution(season) {
    const distribution = {};
    
    for (const bin of this.confidenceBins) {
      const predictions = await this.getHistoricalPredictions(season, bin);
      distribution[bin.range] = {
        count: predictions.length,
        percentage: 0 // Will be calculated after getting all counts
      };
    }
    
    const totalPredictions = Object.values(distribution).reduce((sum, bin) => sum + bin.count, 0);
    
    for (const bin of Object.values(distribution)) {
      bin.percentage = totalPredictions > 0 ? 
        Math.round((bin.count / totalPredictions) * 100) : 0;
    }
    
    return distribution;
  }

  /**
   * Analyze accuracy by confidence
   */
  async analyzeAccuracyByConfidence(season) {
    const accuracyByConfidence = [];
    
    for (const bin of this.confidenceBins) {
      const predictions = await this.getHistoricalPredictions(season, bin);
      
      if (predictions.length === 0) continue;
      
      const correctPredictions = predictions.filter(p => 
        p.actualWinner === p.predictedWinner
      ).length;
      
      const accuracy = (correctPredictions / predictions.length) * 100;
      
      accuracyByConfidence.push({
        range: bin.range,
        label: bin.label,
        count: predictions.length,
        accuracy: Math.round(accuracy),
        expectedAccuracy: Math.round((bin.min + bin.max) / 2)
      });
    }
    
    return accuracyByConfidence;
  }

  /**
   * Clear calibration data
   */
  clearCalibrationData() {
    this.calibrationData.clear();
    this.historicalAccuracy.clear();
  }

  /**
   * Get calibration statistics
   */
  getCalibrationStats() {
    return {
      calibratedSeasons: Array.from(this.calibrationData.keys()),
      totalCalibrations: this.calibrationData.size,
      confidenceBins: this.confidenceBins.length
    };
  }
}

// Create singleton instance
const confidenceService = new ConfidenceService();

export default confidenceService;
