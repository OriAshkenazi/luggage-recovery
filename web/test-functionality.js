/**
 * Comprehensive functionality test script for the luggage tag application
 * Tests QR generation, font loading, layout calculations, and module integration
 */

// Test results storage
const testResults = [];

function log(test, status, message = '') {
  const result = { test, status, message, timestamp: new Date().toISOString() };
  testResults.push(result);
  console.log(`[${status.toUpperCase()}] ${test}: ${message}`);
}

// Wait for all components to be ready
async function waitForApp() {
  return new Promise((resolve) => {
    const check = () => {
      if (window.luggageTagApp && window.luggageTagApp.isInitialized) {
        resolve(window.luggageTagApp);
      } else {
        setTimeout(check, 100);
      }
    };
    check();
  });
}

// Test QR Code library availability
function testQRCodeLibrary() {
  if (typeof QRCode !== 'undefined') {
    log('QR Library', 'PASS', 'QRCode library is available');
    return true;
  } else {
    log('QR Library', 'FAIL', 'QRCode library not found');
    return false;
  }
}

// Test font loading
async function testFontLoading() {
  try {
    await document.fonts.ready;

    // Create test element to check font
    const testEl = document.createElement('div');
    testEl.style.fontFamily = "'SF Pro Rounded', system-ui, sans-serif";
    testEl.style.fontSize = '16px';
    testEl.textContent = 'Test';
    testEl.style.position = 'absolute';
    testEl.style.visibility = 'hidden';
    document.body.appendChild(testEl);

    const computedStyle = window.getComputedStyle(testEl);
    const fontFamily = computedStyle.fontFamily;

    document.body.removeChild(testEl);

    if (fontFamily.includes('SF Pro Rounded')) {
      log('SF Pro Font', 'PASS', `Font loaded: ${fontFamily}`);
      return true;
    } else {
      log('SF Pro Font', 'WARN', `Using fallback font: ${fontFamily}`);
      return false;
    }
  } catch (error) {
    log('SF Pro Font', 'FAIL', `Error checking font: ${error.message}`);
    return false;
  }
}

// Test QR generation functionality
async function testQRGeneration(app) {
  try {
    const testUrl = 'https://example.com/test-luggage-tag';

    // Test QR data generation
    const qrData = await app.qrGenerator.generateQRData(testUrl);

    if (qrData && qrData.modules && qrData.size > 0) {
      log('QR Generation', 'PASS', `Generated ${qrData.size}×${qrData.size} QR code with ${qrData.modules.filter(m => m).length} modules`);

      // Test QR rendering
      const testBox = document.createElement('div');
      testBox.style.position = 'absolute';
      testBox.style.visibility = 'hidden';
      document.body.appendChild(testBox);

      const config = app.getCurrentConfig();
      const computed = app.layoutEngine.computeLayout(config);

      const renderResult = app.qrGenerator.renderQRModules(testBox, config, computed);

      document.body.removeChild(testBox);

      if (renderResult.moduleCount > 0) {
        log('QR Rendering', 'PASS', `Rendered ${renderResult.moduleCount} QR modules`);
        return true;
      } else {
        log('QR Rendering', 'FAIL', 'No QR modules rendered');
        return false;
      }
    } else {
      log('QR Generation', 'FAIL', 'QR generation returned invalid data');
      return false;
    }
  } catch (error) {
    log('QR Generation', 'FAIL', `QR generation error: ${error.message}`);
    return false;
  }
}

// Test layout engine functionality
function testLayoutEngine(app) {
  try {
    const config = app.getCurrentConfig();

    // Validate configuration
    const errors = app.layoutEngine.validateConfig(config);
    if (errors.length > 0) {
      log('Layout Validation', 'FAIL', `Configuration errors: ${errors.join(', ')}`);
      return false;
    }
    log('Layout Validation', 'PASS', 'Configuration valid');

    // Test layout computation
    const computed = app.layoutEngine.computeLayout(config);

    if (computed && computed.actualModuleSize > 0 && computed.qrSize > 0) {
      log('Layout Computation', 'PASS', `Computed layout: QR=${computed.qrSize}mm, Module=${computed.actualModuleSize}mm`);

      // Test CSS variable application
      app.layoutEngine.applyCSSVariables(config, computed);
      log('CSS Variables', 'PASS', 'CSS variables applied');

      // Test metrics generation
      const { metrics, warnings } = app.layoutEngine.generateMetrics(config, computed);
      if (metrics && metrics.length > 0) {
        log('Metrics Generation', 'PASS', `Generated ${metrics.length} metrics`);
        if (warnings.length > 0) {
          log('Metrics Warnings', 'WARN', `${warnings.length} warnings: ${warnings.join(', ')}`);
        }
      } else {
        log('Metrics Generation', 'FAIL', 'No metrics generated');
      }

      return true;
    } else {
      log('Layout Computation', 'FAIL', 'Invalid computed layout');
      return false;
    }
  } catch (error) {
    log('Layout Engine', 'FAIL', `Layout engine error: ${error.message}`);
    return false;
  }
}

// Test DOM builder functionality
function testDOMBuilder(app) {
  try {
    // Test that DOM elements were created
    if (app.elements && Object.keys(app.elements).length > 0) {
      log('DOM Builder', 'PASS', `Created ${Object.keys(app.elements).length} element sets`);

      // Test that inputs were created
      if (app.inputs && Object.keys(app.inputs).length > 0) {
        log('DOM Inputs', 'PASS', `Created ${Object.keys(app.inputs).length} input controls`);
        return true;
      } else {
        log('DOM Inputs', 'FAIL', 'No input controls found');
        return false;
      }
    } else {
      log('DOM Builder', 'FAIL', 'No DOM elements found');
      return false;
    }
  } catch (error) {
    log('DOM Builder', 'FAIL', `DOM builder error: ${error.message}`);
    return false;
  }
}

// Test export functionality
async function testExportManager(app) {
  try {
    const config = app.getCurrentConfig();
    const computed = app.layoutEngine.computeLayout(config);

    // Test SVG export capability (without actually downloading)
    const hasExportManager = app.exportManager && typeof app.exportManager.downloadSVG === 'function';
    if (hasExportManager) {
      log('Export Manager', 'PASS', 'Export manager available with SVG export');

      // Test config export
      const hasConfigExport = typeof app.exportManager.exportConfigJSON === 'function';
      if (hasConfigExport) {
        log('Config Export', 'PASS', 'Config export functionality available');
      } else {
        log('Config Export', 'FAIL', 'Config export not available');
      }

      return hasConfigExport;
    } else {
      log('Export Manager', 'FAIL', 'Export manager not available');
      return false;
    }
  } catch (error) {
    log('Export Manager', 'FAIL', `Export manager error: ${error.message}`);
    return false;
  }
}

// Run all tests
async function runAllTests() {
  console.log('🧪 Starting comprehensive functionality tests...');

  // Basic availability tests
  const qrLibraryOK = testQRCodeLibrary();
  const fontOK = await testFontLoading();

  // Wait for app to be ready
  console.log('⏳ Waiting for app initialization...');
  const app = await waitForApp();
  console.log('✅ App initialized, running component tests...');

  // Component tests
  const layoutOK = testLayoutEngine(app);
  const domOK = testDOMBuilder(app);
  const qrOK = await testQRGeneration(app);
  const exportOK = await testExportManager(app);

  // Summary
  const passed = testResults.filter(r => r.status === 'PASS').length;
  const failed = testResults.filter(r => r.status === 'FAIL').length;
  const warned = testResults.filter(r => r.status === 'WARN').length;

  console.log('📊 Test Results Summary:');
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`⚠️  Warnings: ${warned}`);
  console.log(`📝 Total: ${testResults.length}`);

  const allPassed = failed === 0;
  console.log(allPassed ? '🎉 All tests passed!' : '💥 Some tests failed!');

  return { allPassed, results: testResults };
}

// Auto-run tests when loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(runAllTests, 1000); // Give app time to initialize
  });
} else {
  setTimeout(runAllTests, 1000);
}

// Make test runner available globally
window.testRunner = {
  runAllTests,
  testResults
};