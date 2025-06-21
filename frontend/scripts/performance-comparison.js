const fs = require('fs');
const path = require('path');

// Performance metrics tracking
class PerformanceTracker {
  constructor() {
    this.metrics = {
      timestamp: new Date().toISOString(),
      lighthouse: {},
      bundle: {},
      runtime: {},
    };
  }

  // Parse Lighthouse report
  parseLighthouseReport(reportPath) {
    try {
      const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
      const audits = report.audits;

      return {
        fcp: audits['first-contentful-paint']?.numericValue || 0,
        lcp: audits['largest-contentful-paint']?.numericValue || 0,
        cls: audits['cumulative-layout-shift']?.numericValue || 0,
        fid: audits['max-potential-fid']?.numericValue || 0,
        tti: audits['interactive']?.numericValue || 0,
        tbt: audits['total-blocking-time']?.numericValue || 0,
        speedIndex: audits['speed-index']?.numericValue || 0,
        performance: report.categories?.performance?.score * 100 || 0,
      };
    } catch (error) {
      console.error('Error parsing Lighthouse report:', error);
      return {};
    }
  }

  // Analyze bundle size
  analyzeBundleSize(buildPath = 'build') {
    try {
      const jsFiles = this.getJSFiles(buildPath);
      const cssFiles = this.getCSSFiles(buildPath);

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

      return {
        jsSize: totalJS,
        cssSize: totalCSS,
        totalSize: totalJS + totalCSS,
        jsFiles: jsFiles.length,
        cssFiles: cssFiles.length,
      };
    } catch (error) {
      console.error('Error analyzing bundle:', error);
      return {};
    }
  }

  getJSFiles(dir) {
    const files = [];
    const items = fs.readdirSync(dir);

    items.forEach(item => {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        files.push(...this.getJSFiles(fullPath));
      } else if (item.endsWith('.js')) {
        files.push(fullPath);
      }
    });

    return files;
  }

  getCSSFiles(dir) {
    const files = [];
    const items = fs.readdirSync(dir);

    items.forEach(item => {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        files.push(...this.getCSSFiles(fullPath));
      } else if (item.endsWith('.css')) {
        files.push(fullPath);
      }
    });

    return files;
  }

  // Generate performance report
  generateReport() {
    const report = {
      timestamp: this.metrics.timestamp,
      summary: {
        performance: this.metrics.lighthouse.performance || 0,
        fcp: this.metrics.lighthouse.fcp || 0,
        lcp: this.metrics.lighthouse.lcp || 0,
        cls: this.metrics.lighthouse.cls || 0,
        bundleSize: this.metrics.bundle.totalSize || 0,
      },
      details: this.metrics,
      recommendations: this.generateRecommendations(),
    };

    return report;
  }

  // Generate performance recommendations
  generateRecommendations() {
    const recommendations = [];

    if (this.metrics.lighthouse.fcp > 2000) {
      recommendations.push(
        'First Contentful Paint is slow. Consider optimizing critical rendering path.'
      );
    }

    if (this.metrics.lighthouse.lcp > 2500) {
      recommendations.push(
        'Largest Contentful Paint is slow. Optimize image loading and server response.'
      );
    }

    if (this.metrics.lighthouse.cls > 0.1) {
      recommendations.push(
        'Cumulative Layout Shift is high. Fix layout shifts and use proper image dimensions.'
      );
    }

    if (this.metrics.bundle.totalSize > 2000000) {
      recommendations.push('Bundle size is large. Consider code splitting and lazy loading.');
    }

    return recommendations;
  }

  // Save report to file
  saveReport(filename = 'performance-report.json') {
    const report = this.generateReport();
    fs.writeFileSync(filename, JSON.stringify(report, null, 2));
    console.log(`Performance report saved to ${filename}`);
  }

  // Compare with baseline
  compareWithBaseline(baselinePath) {
    try {
      const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
      const current = this.generateReport();

      const comparison = {
        timestamp: new Date().toISOString(),
        baseline: baseline.summary,
        current: current.summary,
        improvements: {
          performance: (
            ((current.summary.performance - baseline.performance) / baseline.performance) *
            100
          ).toFixed(2),
          fcp: (((baseline.fcp - current.summary.fcp) / baseline.fcp) * 100).toFixed(2),
          lcp: (((baseline.lcp - current.summary.lcp) / baseline.lcp) * 100).toFixed(2),
          cls: (((baseline.cls - current.summary.cls) / baseline.cls) * 100).toFixed(2),
          bundleSize: (
            ((baseline.bundleSize - current.summary.bundleSize) / baseline.bundleSize) *
            100
          ).toFixed(2),
        },
      };

      return comparison;
    } catch (error) {
      console.error('Error comparing with baseline:', error);
      return null;
    }
  }
}

// Main execution
if (require.main === module) {
  const tracker = new PerformanceTracker();

  // Check if Lighthouse report exists
  const lighthouseReportPath = './lighthouse-report.json';
  if (fs.existsSync(lighthouseReportPath)) {
    tracker.metrics.lighthouse = tracker.parseLighthouseReport(lighthouseReportPath);
  }

  // Analyze bundle if build directory exists
  if (fs.existsSync('./build')) {
    tracker.metrics.bundle = tracker.analyzeBundleSize('./build');
  }

  // Generate and save report
  tracker.saveReport();

  // Compare with baseline if exists
  const baselinePath = './baseline-performance.json';
  if (fs.existsSync(baselinePath)) {
    const comparison = tracker.compareWithBaseline(baselinePath);
    if (comparison) {
      console.log('\n=== Performance Comparison ===');
      console.log(`Performance Score: ${comparison.improvements.performance}% change`);
      console.log(`FCP: ${comparison.improvements.fcp}% improvement`);
      console.log(`LCP: ${comparison.improvements.lcp}% improvement`);
      console.log(`CLS: ${comparison.improvements.cls}% improvement`);
      console.log(`Bundle Size: ${comparison.improvements.bundleSize}% reduction`);
    }
  }
}

module.exports = PerformanceTracker;
