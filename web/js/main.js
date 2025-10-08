/**
 * Main Application - Coordination and initialization
 * Brings together all modules and manages the application lifecycle
 */

import { LayoutEngine } from './layout-engine.js';
import { QRGenerator } from './qr-generator.js';
import { DOMBuilder } from './dom-builder.js';
import { ExportManager } from './export-manager.js';

class LuggageTagApp {
  constructor() {
    this.layoutEngine = new LayoutEngine();
    this.qrGenerator = new QRGenerator();
    this.domBuilder = new DOMBuilder();
    this.exportManager = new ExportManager(this.layoutEngine, this.qrGenerator, this.domBuilder);

    this.elements = {};
    this.inputs = {};
    this.isInitialized = false;
  }

  /**
   * Initialize the application
   */
  async init() {
    try {
      console.log('[INIT] Initializing Luggage Tag App...');

      // Build DOM structure
      this.buildInterface();

      // Setup event listeners
      this.setupEventListeners();

      // Initial layout calculation
      await this.updateLayout();

      // Generate initial QR code if generator is available; otherwise show placeholder
      try { await this.updateQRCode(); } catch (e) { this.qrGenerator.addPlaceholder(this.elements.qrBox, 'QR preview disabled'); }

      this.isInitialized = true;
      console.log('[SUCCESS] App initialized successfully');

    } catch (error) {
      console.error('L Initialization failed:', error);
      this.showError('App initialization failed: ' + error.message);
    }
  }

  /**
   * Build the user interface
   */
  buildInterface() {
    const app = document.getElementById('app');
    if (!app) {
      throw new Error('App container element not found');
    }

    // Clear existing content
    app.innerHTML = '';

    // Create header
    const header = document.createElement('h1');
    header.textContent = 'Reversible Tag - Modular Web Layout';
    header.style.cssText = 'margin: 8px 0 12px; text-align: center;';
    app.appendChild(header);

    // Create controls
    const controls = this.domBuilder.createControlPanel();
    app.appendChild(controls);

    // Create tag preview
    const tagContainer = this.domBuilder.createTagStructure();
    app.appendChild(tagContainer);

    // Create metrics display
    const metrics = this.domBuilder.createMetricsDisplay();
    app.appendChild(metrics);

    // Store element references
    this.elements = this.domBuilder.getElements();
    this.inputs = this.domBuilder.getAllInputs();

    console.log('[BUILD] Interface built successfully');
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Layout update on input changes
    Object.values(this.inputs).forEach(input => {
      input.addEventListener('input', () => this.updateLayout());
      input.addEventListener('change', () => this.updateLayout());
    });

    // QR URL changes
    if (this.inputs.qrUrl) {
      this.inputs.qrUrl.addEventListener('input', this.debounce(() => this.updateQRCode(), 500));
      this.inputs.qrUrl.addEventListener('change', () => this.updateQRCode());
    }

    // Debug mode toggle
    if (this.inputs.showDebug) {
      this.inputs.showDebug.addEventListener('change', (e) => {
        document.body.classList.toggle('debug-mode', e.target.checked);
      });
    }

    // Export buttons
    const exportSVG = document.getElementById('exportSVG');
    const exportConfig = document.getElementById('exportConfig');
    const generate3D = document.getElementById('generate3D');

    if (exportSVG) {
      exportSVG.addEventListener('click', () => this.handleExportSVG());
    }

    if (exportConfig) {
      exportConfig.addEventListener('click', () => this.handleExportConfig());
    }

    if (generate3D) {
      generate3D.addEventListener('click', () => this.handleGenerate3D());
    }

    console.log('[EVENTS] Event listeners attached');
  }

  /**
   * Update layout calculations and apply to DOM
   */
  async updateLayout() {
    if (!this.isInitialized && !this.inputs.tagW) return;

    try {
      // Get current configuration
      const config = this.getCurrentConfig();

      // Validate configuration
      const errors = this.layoutEngine.validateConfig(config);
      if (errors.length > 0) {
        this.showLayoutErrors(errors);
        return;
      }

      // Compute layout
      const computed = this.layoutEngine.computeLayout(config);

      // Apply CSS variables
      this.layoutEngine.applyCSSVariables(config, computed);

      // Update metrics
      const { lines, warnings } = this.layoutEngine.generateMetrics(config, computed);
      this.domBuilder.updateMetrics({ lines }, warnings);

      // Update QR box display if we have data; otherwise ensure placeholders match mm box (front and back)
      if (this.qrGenerator.currentQRData) {
        this.updateQRDisplay(config, computed);
      } else {
        const frontQRBox = this.elements['tag']?.qrBox;
        const backQRBox = this.elements['tag-mirrored']?.qrBox;
        [frontQRBox, backQRBox].forEach(qrBox => {
          if (!qrBox) return;
          this.qrGenerator.clearQRBox(qrBox);
          qrBox.style.width = `${computed.qrSize}mm`;
          qrBox.style.height = `${computed.qrSize}mm`;
          const placeholder = document.createElement('div');
          placeholder.style.cssText = `width: ${computed.qrSize}mm; height: ${computed.qrSize}mm; border: 1px dashed #ccc; display:flex;align-items:center;justify-content:center;color:#888;font-size:12px;`;
          placeholder.textContent = 'QR (mm box)';
          qrBox.appendChild(placeholder);
        });
      }

    } catch (error) {
      console.error('Layout update failed:', error);
      this.showError('Layout update failed: ' + error.message);
    }
  }

  /**
   * Update QR code generation and display
   */
  async updateQRCode() {
    if (!this.inputs.qrUrl) return;

    const qrInfo = document.getElementById('qrInfo');
    const url = this.inputs.qrUrl.value.trim();

    try {
      if (!url) {
        if (qrInfo) qrInfo.textContent = 'No URL provided';
        this.clearQRDisplays();
        return;
      }

      // Validate URL
      const validation = QRGenerator.validateURL(url);
      if (!validation.valid) {
        if (qrInfo) {
          qrInfo.textContent = validation.error;
          qrInfo.className = 'error';
        }
        return;
      }

      if (qrInfo) {
        qrInfo.textContent = 'Generating QR code...';
        qrInfo.className = '';
      }

      // Generate QR code
      await this.qrGenerator.generateQRData(url);

      // Update all QR displays
      const config = this.getCurrentConfig();
      const computed = this.layoutEngine.computeLayout(config);
      this.updateQRDisplay(config, computed);
      const summary = this.layoutEngine.generateMetrics(config, computed);
      this.domBuilder.updateMetrics({ lines: summary.lines }, summary.warnings);

      // Update QR info
      if (qrInfo) {
        qrInfo.textContent = this.qrGenerator.generateQRInfo();
        qrInfo.className = 'success';
      }

      console.log('[QR] QR code updated:', url);

    } catch (error) {
      console.error('QR generation failed:', error);
      if (qrInfo) {
        qrInfo.textContent = 'QR generation failed: ' + error.message;
        qrInfo.className = 'error';
      }
    }
  }

  /**
   * Update QR display in both tag previews
   */
  updateQRDisplay(config, computed) {
    if (!this.qrGenerator.currentQRData) return;

    // Update front side QR
    const frontQRBox = this.elements.tag?.qrBox;
    if (frontQRBox) {
      this.qrGenerator.renderQRModules(frontQRBox, config, computed);
    }

    // Update back side QR
    const backQRBox = this.elements['tag-mirrored']?.qrBox;
    if (backQRBox) {
      this.qrGenerator.renderQRModules(backQRBox, config, computed);
    }
  }

  /**
   * Clear QR displays
   */
  clearQRDisplays() {
    Object.values(this.elements).forEach(tagElements => {
      if (tagElements.qrBox) {
        this.qrGenerator.addPlaceholder(tagElements.qrBox);
      }
    });
  }

  /**
   * Get current configuration from inputs
   */
  getCurrentConfig() {
    // Get modules from QR data if available, otherwise use default
    const qrModules = this.qrGenerator.currentQRData?.size || 29;

    return {
      // QR settings
      modules: qrModules,
      moduleSize: parseFloat(this.inputs.moduleSize?.value || 2.0),
      quiet: parseInt(this.inputs.quiet?.value || 0),

      // Canvas
      tagW: parseFloat(this.inputs.tagW?.value || 240.0),
      tagH: parseFloat(this.inputs.tagH?.value || 94.0),

      // Outer margins
      outerT: parseFloat(this.inputs.outerT?.value || 4),
      outerR: parseFloat(this.inputs.outerR?.value || 4),
      outerB: parseFloat(this.inputs.outerB?.value || 4),
      outerL: parseFloat(this.inputs.outerL?.value || 4),
      gutter: parseFloat(this.inputs.gutter?.value || 3),

      // QR padding
      qrPadT: parseFloat(this.inputs.qrPadT?.value || 3),
      qrPadR: parseFloat(this.inputs.qrPadR?.value || 3),
      qrPadB: parseFloat(this.inputs.qrPadB?.value || 3),
      qrPadL: parseFloat(this.inputs.qrPadL?.value || 3),

      // Text padding
      txPadT: parseFloat(this.inputs.txPadT?.value || 8),
      txPadR: parseFloat(this.inputs.txPadR?.value || 3),
      txPadB: parseFloat(this.inputs.txPadB?.value || 8),
      txPadL: parseFloat(this.inputs.txPadL?.value || 3),

      // Font sizes
      fsH: parseFloat(this.inputs.fsH?.value || 12.0),
      fsN: parseFloat(this.inputs.fsN?.value || 8.0),
      fsP: parseFloat(this.inputs.fsP?.value || 6.0),
      fsE: parseFloat(this.inputs.fsE?.value || 6.0),
      fsF: parseFloat(this.inputs.fsF?.value || 8.0),

      // Slit
      slitWidth: parseFloat(this.inputs.slitWidth?.value || 4.5),
      slitHeight: parseFloat(this.inputs.slitHeight?.value || 20.0),
      slitMarginL: parseFloat(this.inputs.slitMarginL?.value || 3.0),
      slitMarginR: parseFloat(this.inputs.slitMarginR?.value || 9.0)
    };
  }

  /**
   * Export handlers
   */
  async handleExportSVG() {
    try {
      const config = this.getCurrentConfig();
      const computed = this.layoutEngine.computeLayout(config);
      this.exportManager.downloadSVG(config, computed);
      console.log('[EXPORT] SVG exported');
    } catch (error) {
      this.showError('SVG export failed: ' + error.message);
    }
  }

  async handleExportConfig() {
    try {
      const config = this.getCurrentConfig();
      const computed = this.layoutEngine.computeLayout(config);
      this.exportManager.exportConfigJSON(config, computed);
      console.log('[EXPORT] Config exported');
    } catch (error) {
      this.showError('Config export failed: ' + error.message);
    }
  }

  async handleGenerate3D() {
    const button = document.getElementById('generate3D');
    if (!button) return;

    try {
      button.classList.add('loading');
      button.disabled = true;

      const config = this.getCurrentConfig();
      const computed = this.layoutEngine.computeLayout(config);

      const result = await this.exportManager.generate3DSTL(config, computed);

      if (result.success) {
        alert(`3D STL Generation Complete!\n\nFiles generated:\n${result.files.map(f => `" ${f.name} (${f.size})`).join('\n')}`);
        console.log('[3D] 3D STL generated');
      } else {
        throw new Error(result.message);
      }

    } catch (error) {
      this.showError('3D generation failed: ' + error.message);
    } finally {
      button.classList.remove('loading');
      button.disabled = false;
    }
  }

  /**
   * Error handling
   */
  showError(message) {
    console.error('L', message);
    const metrics = document.getElementById('metrics');
    if (metrics) {
      metrics.textContent = 'L ' + message;
      metrics.className = 'metrics error';
    }
  }

  showLayoutErrors(errors) {
    const metrics = document.getElementById('metrics');
    if (metrics) {
      metrics.textContent = 'L Configuration Errors:\n' + errors.join('\n');
      metrics.className = 'metrics error';
    }
  }

  /**
   * Utility: Debounce function
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
}

// Wait for QRCode library to load
function waitForQRCode() {
  return new Promise((resolve) => {
    if (typeof QRCode !== 'undefined') {
      resolve();
    } else {
      setTimeout(() => {
        waitForQRCode().then(resolve);
      }, 100);
    }
  });
}

// Initialize app when DOM is ready and QRCode is available
document.addEventListener('DOMContentLoaded', async () => {
  console.log('DOM loaded, waiting for QRCode library...');
  await waitForQRCode();
  console.log('QRCode library available, initializing app...');

  const app = new LuggageTagApp();
  await app.init();

  // Make app available globally for debugging
  window.luggageTagApp = app;
});
