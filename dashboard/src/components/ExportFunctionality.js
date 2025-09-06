/**
 * Export Functionality Component
 * Provides data export and custom report generation interface
 */

import React, { useState, useEffect } from 'react';
import { Download, FileText, BarChart3, Users, Calendar, Settings, CheckCircle, AlertCircle } from 'lucide-react';
import exportService from '../services/exportService';

const ExportFunctionality = () => {
  const [exportConfig, setExportConfig] = useState({
    type: 'elo-summary',
    format: 'csv',
    season: 2025,
    week: 1,
    seasons: [2021, 2022, 2023, 2024, 2025],
    team: 'PHI',
    config: 'comprehensive',
    sections: []
  });
  const [customSections, setCustomSections] = useState([]);
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState(null);
  const [availableFormats, setAvailableFormats] = useState([]);
  const [reportTemplates, setReportTemplates] = useState({});

  useEffect(() => {
    // Load available formats and templates
    setAvailableFormats(exportService.getSupportedFormats());
    setReportTemplates(exportService.getReportTemplates());
  }, []);

  const handleConfigChange = (field, value) => {
    setExportConfig(prev => ({
      ...prev,
      [field]: value
    }));
    setExportResult(null);
  };

  const handleCustomSectionAdd = () => {
    const newSection = {
      type: 'elo-ratings',
      title: '',
      season: 2025,
      week: 1,
      seasons: [2021, 2022, 2023, 2024, 2025],
      team: 'PHI',
      config: 'comprehensive'
    };
    setCustomSections(prev => [...prev, newSection]);
  };

  const handleCustomSectionChange = (index, field, value) => {
    setCustomSections(prev => prev.map((section, i) => 
      i === index ? { ...section, [field]: value } : section
    ));
  };

  const handleCustomSectionRemove = (index) => {
    setCustomSections(prev => prev.filter((_, i) => i !== index));
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      setExportResult(null);

      let config = { ...exportConfig };
      
      if (config.type === 'custom') {
        config.sections = customSections;
      }

      const result = await exportService.exportAndDownload(config);
      setExportResult(result);
    } catch (error) {
      setExportResult({
        success: false,
        error: error.message
      });
    } finally {
      setExporting(false);
    }
  };

  const renderExportForm = () => (
    <div className="space-y-6">
      {/* Report Type Selection */}
      <div className="dashboard-card">
        <h3 className="text-lg font-semibold mb-4">Export Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Type
            </label>
            <select
              value={exportConfig.type}
              onChange={(e) => handleConfigChange('type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
            >
              {Object.entries(reportTemplates).map(([key, value]) => (
                <option key={key} value={key}>{value}</option>
              ))}
            </select>
          </div>

          {/* Export Format */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Format
            </label>
            <select
              value={exportConfig.format}
              onChange={(e) => handleConfigChange('format', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
            >
              {availableFormats.map(format => (
                <option key={format} value={format}>{format.toUpperCase()}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Type-specific Configuration */}
      {exportConfig.type === 'elo-summary' && (
        <div className="dashboard-card">
          <h4 className="text-md font-semibold mb-4">ELO Summary Configuration</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Season
              </label>
              <select
                value={exportConfig.season}
                onChange={(e) => handleConfigChange('season', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
              >
                <option value={2025}>2025</option>
                <option value={2024}>2024</option>
                <option value={2023}>2023</option>
                <option value={2022}>2022</option>
                <option value={2021}>2021</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Configuration
              </label>
              <select
                value={exportConfig.config}
                onChange={(e) => handleConfigChange('config', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
              >
                <option value="comprehensive">Comprehensive</option>
                <option value="baseline">Baseline</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {exportConfig.type === 'predictions' && (
        <div className="dashboard-card">
          <h4 className="text-md font-semibold mb-4">Predictions Configuration</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Season
              </label>
              <select
                value={exportConfig.season}
                onChange={(e) => handleConfigChange('season', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
              >
                <option value={2025}>2025</option>
                <option value={2024}>2024</option>
                <option value={2023}>2023</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Week
              </label>
              <select
                value={exportConfig.week}
                onChange={(e) => handleConfigChange('week', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
              >
                {Array.from({ length: 18 }, (_, i) => i + 1).map(week => (
                  <option key={week} value={week}>Week {week}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {exportConfig.type === 'confidence-analysis' && (
        <div className="dashboard-card">
          <h4 className="text-md font-semibold mb-4">Confidence Analysis Configuration</h4>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Season
            </label>
            <select
              value={exportConfig.season}
              onChange={(e) => handleConfigChange('season', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
            >
              <option value={2025}>2025</option>
              <option value={2024}>2024</option>
              <option value={2023}>2023</option>
            </select>
          </div>
        </div>
      )}

      {exportConfig.type === 'historical-comparison' && (
        <div className="dashboard-card">
          <h4 className="text-md font-semibold mb-4">Historical Comparison Configuration</h4>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Seasons (select multiple)
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {[2021, 2022, 2023, 2024, 2025].map(year => (
                <label key={year} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={exportConfig.seasons.includes(year)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        handleConfigChange('seasons', [...exportConfig.seasons, year]);
                      } else {
                        handleConfigChange('seasons', exportConfig.seasons.filter(s => s !== year));
                      }
                    }}
                    className="mr-2"
                  />
                  <span className="text-sm">{year}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}

      {exportConfig.type === 'team-analysis' && (
        <div className="dashboard-card">
          <h4 className="text-md font-semibold mb-4">Team Analysis Configuration</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Team
              </label>
              <select
                value={exportConfig.team}
                onChange={(e) => handleConfigChange('team', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent"
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Seasons
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[2021, 2022, 2023, 2024, 2025].map(year => (
                  <label key={year} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={exportConfig.seasons.includes(year)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleConfigChange('seasons', [...exportConfig.seasons, year]);
                        } else {
                          handleConfigChange('seasons', exportConfig.seasons.filter(s => s !== year));
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm">{year}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Custom Report Sections */}
      {exportConfig.type === 'custom' && (
        <div className="dashboard-card">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-md font-semibold">Custom Report Sections</h4>
            <button
              onClick={handleCustomSectionAdd}
              className="px-3 py-1 bg-nfl-primary text-white rounded-lg hover:bg-nfl-primary-dark transition-colors text-sm"
            >
              Add Section
            </button>
          </div>
          
          {customSections.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No sections added yet. Click "Add Section" to get started.</p>
          ) : (
            <div className="space-y-4">
              {customSections.map((section, index) => (
                <div key={index} className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h5 className="font-medium">Section {index + 1}</h5>
                    <button
                      onClick={() => handleCustomSectionRemove(index)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Title
                      </label>
                      <input
                        type="text"
                        value={section.title}
                        onChange={(e) => handleCustomSectionChange(index, 'title', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent text-sm"
                        placeholder="Section title"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Type
                      </label>
                      <select
                        value={section.type}
                        onChange={(e) => handleCustomSectionChange(index, 'type', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nfl-primary focus:border-transparent text-sm"
                      >
                        <option value="elo-ratings">ELO Ratings</option>
                        <option value="predictions">Predictions</option>
                        <option value="confidence-analysis">Confidence Analysis</option>
                        <option value="historical-comparison">Historical Comparison</option>
                        <option value="team-analysis">Team Analysis</option>
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Export Button */}
      <div className="dashboard-card">
        <button
          onClick={handleExport}
          disabled={exporting || (exportConfig.type === 'custom' && customSections.length === 0)}
          className="w-full flex items-center justify-center px-6 py-3 bg-nfl-primary text-white rounded-lg hover:bg-nfl-primary-dark disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {exporting ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Exporting...
            </>
          ) : (
            <>
              <Download className="w-5 h-5 mr-2" />
              Export Data
            </>
          )}
        </button>
      </div>
    </div>
  );

  const renderExportResult = () => {
    if (!exportResult) return null;

    return (
      <div className="dashboard-card">
        <div className={`flex items-center p-4 rounded-lg ${
          exportResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          {exportResult.success ? (
            <>
              <CheckCircle className="w-6 h-6 text-green-600 mr-3" />
              <div>
                <h4 className="font-semibold text-green-800">Export Successful</h4>
                <p className="text-green-700">{exportResult.message}</p>
              </div>
            </>
          ) : (
            <>
              <AlertCircle className="w-6 h-6 text-red-600 mr-3" />
              <div>
                <h4 className="font-semibold text-red-800">Export Failed</h4>
                <p className="text-red-700">{exportResult.error}</p>
              </div>
            </>
          )}
        </div>
      </div>
    );
  };

  const renderQuickExports = () => (
    <div className="dashboard-card">
      <h3 className="text-lg font-semibold mb-4">Quick Exports</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <button
          onClick={() => {
            setExportConfig(prev => ({ ...prev, type: 'elo-summary', format: 'csv' }));
            handleExport();
          }}
          className="p-4 border border-gray-200 rounded-lg hover:border-nfl-primary hover:bg-nfl-primary/5 transition-colors text-left"
        >
          <BarChart3 className="w-8 h-8 text-nfl-primary mb-2" />
          <h4 className="font-medium">Current ELO Ratings</h4>
          <p className="text-sm text-gray-600">Export current season ELO ratings as CSV</p>
        </button>

        <button
          onClick={() => {
            setExportConfig(prev => ({ ...prev, type: 'predictions', format: 'csv' }));
            handleExport();
          }}
          className="p-4 border border-gray-200 rounded-lg hover:border-nfl-primary hover:bg-nfl-primary/5 transition-colors text-left"
        >
          <Calendar className="w-8 h-8 text-nfl-primary mb-2" />
          <h4 className="font-medium">This Week's Predictions</h4>
          <p className="text-sm text-gray-600">Export current week predictions as CSV</p>
        </button>

        <button
          onClick={() => {
            setExportConfig(prev => ({ ...prev, type: 'historical-comparison', format: 'csv' }));
            handleExport();
          }}
          className="p-4 border border-gray-200 rounded-lg hover:border-nfl-primary hover:bg-nfl-primary/5 transition-colors text-left"
        >
          <Users className="w-8 h-8 text-nfl-primary mb-2" />
          <h4 className="font-medium">Season Comparison</h4>
          <p className="text-sm text-gray-600">Export historical season comparison as CSV</p>
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Export Functionality</h1>
          <p className="text-gray-600">Export data and generate custom reports</p>
        </div>
      </div>

      {/* Quick Exports */}
      {renderQuickExports()}

      {/* Export Form */}
      {renderExportForm()}

      {/* Export Result */}
      {renderExportResult()}
    </div>
  );
};

export default ExportFunctionality;
