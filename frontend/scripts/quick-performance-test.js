#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Quick Performance Test Starting...\n');

// Colors for console output
const colors = {
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m',
};

const log = (message, color = 'reset') => {
  console.log(`${colors[color]}${message}${colors.reset}`);
};

// Check if development server is running
const isDevServerRunning = () => {
  try {
    execSync('curl -s http://localhost:3000 > /dev/null', { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
};

// Start development server if not running
const startDevServer = () => {
  if (!isDevServerRunning()) {
    log('Starting development server...', 'blue');
    execSync('npm start', { stdio: 'ignore', detached: true });

    // Wait for server to start
    log('Waiting for server to start...', 'yellow');
    let attempts = 0;
    while (!isDevServerRunning() && attempts < 30) {
      setTimeout(() => {}, 1000);
      attempts++;
    }

    if (attempts >= 30) {
      log('❌ Failed to start development server', 'red');
      process.exit(1);
    }
  }
};

// Run Lighthouse test
const runLighthouse = () => {
  log('Running Lighthouse performance test...', 'blue');

  try {
    execSync(
      'npx lighthouse http://localhost:3000 --output=json --output-path=./lighthouse-report.json --chrome-flags="--headless"',
      {
        stdio: 'inherit',
      }
    );
    log('✅ Lighthouse test completed', 'green');
  } catch (error) {
    log('❌ Lighthouse test failed', 'red');
    console.error(error);
  }
};

// Analyze bundle size
const analyzeBundle = () => {
  log('Analyzing bundle size...', 'blue');

  try {
    execSync('npm run build', { stdio: 'inherit' });
    log('✅ Build completed', 'green');

    // Calculate bundle size
    const buildPath = './build';
    if (fs.existsSync(buildPath)) {
      const jsFiles = getJSFiles(buildPath);
      const cssFiles = getCSSFiles(buildPath);

      let totalJS = 0;
      let totalCSS = 0;

      jsFiles.forEach(file => {
        const stats = fs.statSync(file);
        totalJS += stats.size;
      });

      cssFiles.forEach(file => {
        const stats = fs.statSync(file);
        totalCSS += stats.size;
      });

      const totalSize = totalJS + totalCSS;

      log('\n📊 Bundle Analysis Results:', 'bold');
      log(`JavaScript: ${(totalJS / 1024 / 1024).toFixed(2)} MB`, 'blue');
      log(`CSS: ${(totalCSS / 1024).toFixed(2)} KB`, 'blue');
      log(`Total: ${(totalSize / 1024 / 1024).toFixed(2)} MB`, 'bold');
      log(`JS Files: ${jsFiles.length}`, 'blue');
      log(`CSS Files: ${cssFiles.length}`, 'blue');

      // Performance assessment
      if (totalSize < 1024 * 1024) {
        log('✅ Bundle size is excellent!', 'green');
      } else if (totalSize < 2 * 1024 * 1024) {
        log('⚠️ Bundle size is good', 'yellow');
      } else {
        log('❌ Bundle size is too large', 'red');
      }
    }
  } catch (error) {
    log('❌ Bundle analysis failed', 'red');
    console.error(error);
  }
};

// Parse Lighthouse results
const parseLighthouseResults = () => {
  const reportPath = './lighthouse-report.json';

  if (!fs.existsSync(reportPath)) {
    log('❌ Lighthouse report not found', 'red');
    return;
  }

  try {
    const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    const audits = report.audits;
    const categories = report.categories;

    const performance = categories?.performance?.score * 100 || 0;
    const fcp = audits['first-contentful-paint']?.numericValue || 0;
    const lcp = audits['largest-contentful-paint']?.numericValue || 0;
    const cls = audits['cumulative-layout-shift']?.numericValue || 0;
    const fid = audits['max-potential-fid']?.numericValue || 0;

    log('\n📊 Lighthouse Performance Results:', 'bold');
    log(
      `Overall Performance: ${performance.toFixed(1)}/100`,
      performance > 90 ? 'green' : performance > 70 ? 'yellow' : 'red'
    );
    log(
      `First Contentful Paint: ${fcp.toFixed(0)}ms`,
      fcp < 1800 ? 'green' : fcp < 3000 ? 'yellow' : 'red'
    );
    log(
      `Largest Contentful Paint: ${lcp.toFixed(0)}ms`,
      lcp < 2500 ? 'green' : lcp < 4000 ? 'yellow' : 'red'
    );
    log(
      `Cumulative Layout Shift: ${cls.toFixed(3)}`,
      cls < 0.1 ? 'green' : cls < 0.25 ? 'yellow' : 'red'
    );
    log(
      `First Input Delay: ${fid.toFixed(0)}ms`,
      fid < 100 ? 'green' : fid < 300 ? 'yellow' : 'red'
    );

    // Performance assessment
    log('\n🎯 Performance Assessment:', 'bold');
    if (performance >= 90 && fcp < 1800 && lcp < 2500 && cls < 0.1) {
      log('✅ Excellent performance!', 'green');
    } else if (performance >= 70 && fcp < 3000 && lcp < 4000 && cls < 0.25) {
      log('⚠️ Good performance, some room for improvement', 'yellow');
    } else {
      log('❌ Performance needs improvement', 'red');
    }

    // Generate recommendations
    const recommendations = [];
    if (fcp > 1800) recommendations.push('Optimize First Contentful Paint');
    if (lcp > 2500) recommendations.push('Optimize Largest Contentful Paint');
    if (cls > 0.1) recommendations.push('Fix layout shifts');
    if (fid > 100) recommendations.push('Reduce First Input Delay');

    if (recommendations.length > 0) {
      log('\n💡 Recommendations:', 'bold');
      recommendations.forEach(rec => log(`• ${rec}`, 'yellow'));
    }
  } catch (error) {
    log('❌ Error parsing Lighthouse results', 'red');
    console.error(error);
  }
};

// Helper functions
const getJSFiles = dir => {
  const files = [];
  const items = fs.readdirSync(dir);

  items.forEach(item => {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      files.push(...getJSFiles(fullPath));
    } else if (item.endsWith('.js')) {
      files.push(fullPath);
    }
  });

  return files;
};

const getCSSFiles = dir => {
  const files = [];
  const items = fs.readdirSync(dir);

  items.forEach(item => {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      files.push(...getCSSFiles(fullPath));
    } else if (item.endsWith('.css')) {
      files.push(fullPath);
    }
  });

  return files;
};

// Main execution
const main = async () => {
  try {
    startDevServer();
    runLighthouse();
    analyzeBundle();
    parseLighthouseResults();

    log('\n🎉 Performance test completed!', 'green');
    log('Check the generated reports for detailed analysis.', 'blue');
  } catch (error) {
    log('❌ Performance test failed', 'red');
    console.error(error);
    process.exit(1);
  }
};

main();
