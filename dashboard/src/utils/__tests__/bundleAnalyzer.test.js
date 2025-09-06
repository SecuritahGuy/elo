/**
 * Tests for Bundle Analyzer
 * Comprehensive test suite for bundle analysis and optimization
 */

import { BundleAnalyzer, BundleOptimizer } from '../bundleAnalyzer';

describe('BundleAnalyzer', () => {
  let analyzer;

  beforeEach(() => {
    analyzer = new BundleAnalyzer();
  });

  describe('Bundle Analysis', () => {
    test('should analyze bundle composition', () => {
      const analysis = analyzer.analyzeBundle();

      expect(analysis).toHaveProperty('totalSize');
      expect(analysis).toHaveProperty('chunks');
      expect(analysis).toHaveProperty('dependencies');
      expect(analysis).toHaveProperty('assets');
      expect(analysis).toHaveProperty('duplicates');

      expect(analysis.totalSize).toHaveProperty('total');
      expect(analysis.totalSize.total).toBeGreaterThan(0);
    });

    test('should estimate bundle size correctly', () => {
      const sizes = analyzer.estimateBundleSize();

      expect(sizes).toHaveProperty('main');
      expect(sizes).toHaveProperty('vendor');
      expect(sizes).toHaveProperty('styles');
      expect(sizes).toHaveProperty('assets');
      expect(sizes).toHaveProperty('total');

      expect(sizes.total).toBeGreaterThan(sizes.main);
      expect(sizes.total).toBeGreaterThan(sizes.vendor);
    });

    test('should analyze chunks correctly', () => {
      const chunks = analyzer.analyzeChunks();

      expect(chunks).toHaveProperty('main');
      expect(chunks).toHaveProperty('vendor');
      expect(chunks).toHaveProperty('styles');
      expect(chunks).toHaveProperty('assets');

      Object.values(chunks).forEach(chunk => {
        expect(chunk).toHaveProperty('size');
        expect(chunk).toHaveProperty('modules');
        expect(chunk).toHaveProperty('description');
        expect(chunk.size).toBeGreaterThan(0);
        expect(chunk.modules).toBeGreaterThan(0);
      });
    });

    test('should analyze dependencies correctly', () => {
      const dependencies = analyzer.analyzeDependencies();

      expect(dependencies).toHaveProperty('react');
      expect(dependencies).toHaveProperty('react-dom');
      expect(dependencies).toHaveProperty('axios');

      Object.values(dependencies).forEach(dep => {
        expect(dep).toHaveProperty('size');
        expect(dep).toHaveProperty('version');
        expect(dep).toHaveProperty('critical');
        expect(dep.size).toBeGreaterThan(0);
        expect(typeof dep.critical).toBe('boolean');
      });
    });

    test('should analyze assets correctly', () => {
      const assets = analyzer.analyzeAssets();

      expect(assets).toHaveProperty('images');
      expect(assets).toHaveProperty('fonts');
      expect(assets).toHaveProperty('icons');

      expect(assets.images).toHaveProperty('count');
      expect(assets.images).toHaveProperty('totalSize');
      expect(assets.images).toHaveProperty('optimization');

      expect(assets.fonts).toHaveProperty('count');
      expect(assets.fonts).toHaveProperty('totalSize');
      expect(assets.fonts).toHaveProperty('formats');
    });

    test('should find duplicates correctly', () => {
      const duplicates = analyzer.findDuplicates();

      expect(Array.isArray(duplicates)).toBe(true);

      duplicates.forEach(dup => {
        expect(dup).toHaveProperty('name');
        expect(dup).toHaveProperty('versions');
        expect(dup).toHaveProperty('totalSize');
        expect(dup).toHaveProperty('recommendation');
        expect(Array.isArray(dup.versions)).toBe(true);
        expect(dup.versions.length).toBeGreaterThan(1);
      });
    });
  });

  describe('Optimization Recommendations', () => {
    test('should generate recommendations for large bundles', () => {
      // Mock large bundle size
      analyzer.analysisResults = {
        totalSize: { total: 600000 }, // 600KB
        dependencies: {},
        duplicates: []
      };

      const recommendations = analyzer.generateOptimizationRecommendations();

      expect(Array.isArray(recommendations)).toBe(true);
      expect(recommendations.length).toBeGreaterThan(0);

      const bundleSizeRec = recommendations.find(rec => rec.type === 'bundle_size');
      expect(bundleSizeRec).toBeDefined();
      expect(bundleSizeRec.priority).toBe('high');
    });

    test('should generate recommendations for large dependencies', () => {
      analyzer.analysisResults = {
        totalSize: { total: 400000 },
        dependencies: {
          'large-lib': { size: 100000, critical: false },
          'another-large-lib': { size: 80000, critical: false }
        },
        duplicates: []
      };

      const recommendations = analyzer.generateOptimizationRecommendations();

      const depRec = recommendations.find(rec => rec.type === 'dependencies');
      expect(depRec).toBeDefined();
      expect(depRec.priority).toBe('medium');
    });

    test('should generate recommendations for duplicates', () => {
      analyzer.analysisResults = {
        totalSize: { total: 400000 },
        dependencies: {},
        duplicates: [
          { name: 'lodash', versions: ['4.17.20', '4.17.21'], totalSize: 15000 }
        ]
      };

      const recommendations = analyzer.generateOptimizationRecommendations();

      const dupRec = recommendations.find(rec => rec.type === 'duplicates');
      expect(dupRec).toBeDefined();
      expect(dupRec.priority).toBe('medium');
    });

    test('should generate recommendations for asset optimization', () => {
      analyzer.analysisResults = {
        totalSize: { total: 400000 },
        dependencies: {},
        duplicates: [],
        assets: {
          images: { totalSize: 60000 }
        }
      };

      const recommendations = analyzer.generateOptimizationRecommendations();

      const assetRec = recommendations.find(rec => rec.type === 'assets');
      expect(assetRec).toBeDefined();
      expect(assetRec.priority).toBe('low');
    });
  });

  describe('Optimization Plan', () => {
    test('should generate optimization plan', () => {
      analyzer.analysisResults = {
        totalSize: { total: 600000 },
        dependencies: {
          'large-lib': { size: 100000, critical: false }
        },
        duplicates: [
          { name: 'lodash', versions: ['4.17.20', '4.17.21'], totalSize: 15000 }
        ],
        assets: {
          images: { totalSize: 60000 }
        }
      };

      const recommendations = analyzer.generateOptimizationRecommendations();
      const plan = analyzer.generateOptimizationPlan();

      expect(plan).toHaveProperty('immediate');
      expect(plan).toHaveProperty('shortTerm');
      expect(plan).toHaveProperty('longTerm');
      expect(plan).toHaveProperty('estimatedSavings');

      expect(Array.isArray(plan.immediate)).toBe(true);
      expect(Array.isArray(plan.shortTerm)).toBe(true);
      expect(Array.isArray(plan.longTerm)).toBe(true);
      expect(plan.estimatedSavings).toBeGreaterThan(0);
    });

    test('should categorize recommendations by priority', () => {
      analyzer.analysisResults = {
        totalSize: { total: 600000 },
        dependencies: {},
        duplicates: [],
        assets: {}
      };

      const recommendations = analyzer.generateOptimizationRecommendations();
      const plan = analyzer.generateOptimizationPlan();

      // High priority should go to immediate
      const highPriorityRecs = recommendations.filter(rec => rec.priority === 'high');
      expect(plan.immediate.length).toBeGreaterThanOrEqual(highPriorityRecs.length);

      // Medium priority should go to short term
      const mediumPriorityRecs = recommendations.filter(rec => rec.priority === 'medium');
      expect(plan.shortTerm.length).toBeGreaterThanOrEqual(mediumPriorityRecs.length);

      // Low priority should go to long term
      const lowPriorityRecs = recommendations.filter(rec => rec.priority === 'low');
      expect(plan.longTerm.length).toBeGreaterThanOrEqual(lowPriorityRecs.length);
    });
  });

  describe('Report Generation', () => {
    test('should generate comprehensive report', () => {
      const report = analyzer.generateReport();

      expect(report).toHaveProperty('timestamp');
      expect(report).toHaveProperty('analysis');
      expect(report).toHaveProperty('recommendations');
      expect(report).toHaveProperty('plan');
      expect(report).toHaveProperty('summary');

      expect(report.summary).toHaveProperty('currentSize');
      expect(report.summary).toHaveProperty('estimatedSavings');
      expect(report.summary).toHaveProperty('potentialSize');
      expect(report.summary).toHaveProperty('optimizationScore');
    });

    test('should calculate optimization score correctly', () => {
      const analysis = {
        totalSize: { total: 400000 } // 400KB
      };
      const plan = {
        estimatedSavings: 100000 // 100KB savings
      };

      const score = analyzer.calculateOptimizationScore(analysis, plan);
      expect(score).toBe(100); // Should be 100% since potential size (300KB) < target (500KB)
    });

    test('should calculate optimization score for large bundles', () => {
      const analysis = {
        totalSize: { total: 800000 } // 800KB
      };
      const plan = {
        estimatedSavings: 100000 // 100KB savings
      };

      const score = analyzer.calculateOptimizationScore(analysis, plan);
      expect(score).toBeLessThan(100);
      expect(score).toBeGreaterThan(0);
    });
  });
});

describe('BundleOptimizer', () => {
  let optimizer;

  beforeEach(() => {
    optimizer = new BundleOptimizer();
  });

  describe('Code Splitting', () => {
    test('should implement code splitting configuration', () => {
      const config = optimizer.implementCodeSplitting();

      expect(config).toHaveProperty('vendorChunk');
      expect(config).toHaveProperty('commonChunk');
      expect(config).toHaveProperty('asyncChunk');

      expect(config.vendorChunk).toHaveProperty('test');
      expect(config.vendorChunk).toHaveProperty('name');
      expect(config.vendorChunk).toHaveProperty('chunks');
      expect(config.vendorChunk).toHaveProperty('priority');

      expect(optimizer.optimizations).toHaveLength(1);
      expect(optimizer.optimizations[0].type).toBe('code_splitting');
      expect(optimizer.optimizations[0].status).toBe('implemented');
    });
  });

  describe('Tree Shaking', () => {
    test('should configure tree shaking', () => {
      const config = optimizer.configureTreeShaking();

      expect(config).toHaveProperty('sideEffects');
      expect(config).toHaveProperty('usedExports');
      expect(config).toHaveProperty('providedExports');
      expect(config).toHaveProperty('concatenateModules');

      expect(config.sideEffects).toBe(false);
      expect(config.usedExports).toBe(true);

      expect(optimizer.optimizations).toHaveLength(1);
      expect(optimizer.optimizations[0].type).toBe('tree_shaking');
    });
  });

  describe('Dependency Optimization', () => {
    test('should optimize dependencies', () => {
      const config = optimizer.optimizeDependencies();

      expect(config).toHaveProperty('recharts');
      expect(config).toHaveProperty('lucide-react');
      expect(config).toHaveProperty('date-fns');

      Object.values(config).forEach(dep => {
        expect(dep).toHaveProperty('action');
        expect(dep).toHaveProperty('estimatedSavings');
        expect(dep.estimatedSavings).toBeGreaterThan(0);
      });

      expect(optimizer.optimizations).toHaveLength(1);
      expect(optimizer.optimizations[0].type).toBe('dependencies');
    });
  });

  describe('Asset Optimization', () => {
    test('should configure asset optimization', () => {
      const config = optimizer.configureAssetOptimization();

      expect(config).toHaveProperty('images');
      expect(config).toHaveProperty('fonts');
      expect(config).toHaveProperty('icons');

      expect(config.images).toHaveProperty('format');
      expect(config.images).toHaveProperty('quality');
      expect(config.images.format).toBe('webp');

      expect(optimizer.optimizations).toHaveLength(1);
      expect(optimizer.optimizations[0].type).toBe('assets');
    });
  });

  describe('Webpack Configuration', () => {
    test('should generate webpack configuration', () => {
      const config = optimizer.generateWebpackConfig();

      expect(config).toHaveProperty('optimization');
      expect(config).toHaveProperty('module');
      expect(config.optimization).toHaveProperty('splitChunks');
      expect(config.optimization).toHaveProperty('usedExports');

      expect(optimizer.optimizations).toHaveLength(1);
      expect(optimizer.optimizations[0].type).toBe('webpack_config');
    });
  });

  describe('Optimization Summary', () => {
    test('should provide optimization summary', () => {
      // Add some optimizations
      optimizer.implementCodeSplitting();
      optimizer.configureTreeShaking();
      optimizer.optimizeDependencies();

      const summary = optimizer.getOptimizationSummary();

      expect(summary).toHaveProperty('totalOptimizations');
      expect(summary).toHaveProperty('implemented');
      expect(summary).toHaveProperty('generated');
      expect(summary).toHaveProperty('types');

      expect(summary.totalOptimizations).toBe(3);
      expect(summary.implemented).toBe(3);
      expect(summary.generated).toBe(0);
      expect(Array.isArray(summary.types)).toBe(true);
    });
  });
});

describe('Integration Tests', () => {
  test('should work together for complete optimization', () => {
    const analyzer = new BundleAnalyzer();
    const optimizer = new BundleOptimizer();

    // Analyze bundle
    const analysis = analyzer.analyzeBundle();
    expect(analysis).toBeDefined();

    // Generate recommendations
    const recommendations = analyzer.generateOptimizationRecommendations();
    expect(recommendations.length).toBeGreaterThan(0);

    // Implement optimizations
    optimizer.implementCodeSplitting();
    optimizer.configureTreeShaking();
    optimizer.optimizeDependencies();

    // Check results
    const summary = optimizer.getOptimizationSummary();
    expect(summary.totalOptimizations).toBe(3);

    // Generate final report
    const report = analyzer.generateReport();
    expect(report).toHaveProperty('summary');
    expect(report.summary.optimizationScore).toBeGreaterThan(0);
  });
});
