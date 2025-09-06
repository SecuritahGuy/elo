#!/usr/bin/env node
/**
 * Integration Test Runner
 * Runs comprehensive frontend-backend integration tests
 */

const { spawn } = require('child_process');
const path = require('path');

const testSuites = [
  'src/__tests__/integration/api-integration.test.js',
  'src/__tests__/integration/weekly-schedule-integration.test.js',
  'src/__tests__/integration/elo-projection-integration.test.js',
  'src/__tests__/services/api-service.test.js'
];

const runTests = async () => {
  console.log('🧪 Running Frontend-Backend Integration Tests');
  console.log('==============================================\n');

  for (const testSuite of testSuites) {
    console.log(`📋 Running: ${testSuite}`);
    
    const testProcess = spawn('npm', ['test', '--', testSuite, '--watchAll=false', '--verbose'], {
      stdio: 'inherit',
      shell: true,
      cwd: process.cwd()
    });

    await new Promise((resolve, reject) => {
      testProcess.on('close', (code) => {
        if (code === 0) {
          console.log(`✅ ${testSuite} - PASSED\n`);
          resolve();
        } else {
          console.log(`❌ ${testSuite} - FAILED (exit code: ${code})\n`);
          reject(new Error(`Test suite ${testSuite} failed`));
        }
      });
    });
  }

  console.log('🎉 All integration tests completed!');
};

const runCoverageAnalysis = async () => {
  console.log('\n📊 Running Coverage Analysis');
  console.log('============================\n');

  const coverageProcess = spawn('npm', ['test', '--', '--coverage', '--watchAll=false'], {
    stdio: 'inherit',
    shell: true,
    cwd: process.cwd()
  });

  await new Promise((resolve, reject) => {
    coverageProcess.on('close', (code) => {
      if (code === 0) {
        console.log('\n✅ Coverage analysis completed');
        resolve();
      } else {
        console.log('\n❌ Coverage analysis failed');
        reject(new Error('Coverage analysis failed'));
      }
    });
  });
};

const main = async () => {
  try {
    await runTests();
    await runCoverageAnalysis();
    
    console.log('\n🎯 Integration Test Summary:');
    console.log('============================');
    console.log('✅ API Integration Tests');
    console.log('✅ WeeklySchedule Integration Tests');
    console.log('✅ ELO Projection Integration Tests');
    console.log('✅ API Service Tests');
    console.log('✅ Coverage Analysis');
    
  } catch (error) {
    console.error('\n💥 Test execution failed:', error.message);
    process.exit(1);
  }
};

if (require.main === module) {
  main();
}

module.exports = { runTests, runCoverageAnalysis };
