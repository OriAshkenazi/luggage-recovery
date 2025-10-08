/**
 * QR Generator - Real QR code generation and rendering
 * Uses qrcode.js library to generate actual QR codes with individual modules
 */

export class QRGenerator {
  constructor() {
    this.currentQRData = null;
    this.modules = [];
    this.debugRecords = [];

    if (typeof window !== 'undefined') {
      window.__qrModuleDump = () => JSON.parse(JSON.stringify(this.debugRecords || []));
      window.__qrModuleSummary = () => {
        const record = window.__lastQrModuleRecord;
        if (!record || !record.summaryLines) {
          return 'No QR module data recorded yet.';
        }
        return record.summaryLines.join('\n');
      };
    }
  }

  /**
   * Generate QR code data from URL
   */
  async generateQRData(url, options = {}) {
    try {
      if (typeof QRCode === 'undefined' || typeof QRCode.create !== 'function') {
        throw new Error('QR library not available');
      }

      const qr = QRCode.create(url, { errorCorrectionLevel: 'L' });
      const size = qr.modules.size;
      const modules = [];
      for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
          const isDark = qr.modules.get(x, y);
          modules.push(!!isDark);
        }
      }

      this.currentQRData = {
        url,
        modules,
        size,
        version: qr.version || Math.floor((size - 21) / 4) + 1,
        errorCorrectionLevel: 'L'
      };

      console.log(`QR generated: ${size}x${size}, ${modules.filter(m => m).length} dark modules`);

      return this.currentQRData;
    } catch (error) {
      console.error('QR generation failed:', error);
      throw new Error(`QR generation failed: ${error.message}`);
    }
  }

  /**
   * Render QR code modules in the DOM
   */
  renderQRModules(qrBox, config, computed) {
    if (!this.currentQRData) {
      throw new Error('No QR data available. Generate QR code first.');
    }

    // Clear existing modules
    this.clearQRBox(qrBox);

    const data = this.currentQRData;
    // Render matrix at control-driven size if provided, else fallback to data
    const size = (typeof config.modules === 'number' && config.modules > 0) ? config.modules : data.size;
    const moduleSize = computed.actualModuleSize; // mm
    const quietMm = computed.quietMm || 0;
    const qrSize = computed.qrSize; // data mm
    const qrTotal = computed.qrTotal || (qrSize + quietMm * 2);

    // Create container for modules
    const moduleContainer = document.createElement('div');
    moduleContainer.className = 'qr-modules-container';
    moduleContainer.style.cssText = `
      position: relative;
      width: ${qrSize}mm;
      height: ${qrSize}mm;
      background: white;
    `;
    moduleContainer.dataset.qrSizeMm = qrSize.toFixed(3);
    moduleContainer.dataset.moduleSizeMm = moduleSize.toFixed(3);
    moduleContainer.dataset.quietZoneMm = quietMm.toFixed(3);
    moduleContainer.dataset.totalFootprintMm = qrTotal.toFixed(3);

    this.modules = [];

    // Align the visual qr-box to the requested data footprint (quiet-zone handled via ::after)
    qrBox.style.width = `${qrSize}mm`;
    qrBox.style.height = `${qrSize}mm`;

    // Generate individual module elements
    const srcSize = data.size;
    const scale = srcSize / size;
    for (let row = 0; row < size; row++) {
      for (let col = 0; col < size; col++) {
        // Nearest-neighbor sample from source matrix to target matrix size
        const srcRow = Math.min(srcSize - 1, Math.max(0, Math.floor((row + 0.5) * scale)));
        const srcCol = Math.min(srcSize - 1, Math.max(0, Math.floor((col + 0.5) * scale)));
        const index = srcRow * srcSize + srcCol;
        const isDark = Array.isArray(data.modules) ? !!data.modules[index] : ((row + col) % 2 === 0);

        if (isDark) {
          const module = document.createElement('div');
          module.className = 'qr-module';
          const leftMm = col * moduleSize;
          const topMm = row * moduleSize;
          module.style.cssText = `
            position: absolute;
            left: ${leftMm}mm;
            top: ${topMm}mm;
            width: ${moduleSize}mm;
            height: ${moduleSize}mm;
            background: #000;
          `;
          module.dataset.row = row;
          module.dataset.col = col;
          module.dataset.isDark = 'true';
          module.dataset.xMm = leftMm.toFixed(3);
          module.dataset.yMm = topMm.toFixed(3);
          module.dataset.sizeMm = moduleSize.toFixed(3);

          moduleContainer.appendChild(module);
          this.modules.push({
            element: module,
            row: row,
            col: col,
            isDark: true,
            x: leftMm,
            y: topMm,
            size: moduleSize
          });
        }
      }
    }

    qrBox.appendChild(moduleContainer);

    const containerRect = moduleContainer.getBoundingClientRect();
    const boxRect = qrBox.getBoundingClientRect();
    const pxPerMm = containerRect.width > 0 ? containerRect.width / qrSize : 0;
    const measuredContainer = {
      widthMm: pxPerMm ? Number((containerRect.width / pxPerMm).toFixed(3)) : qrSize,
      heightMm: pxPerMm ? Number((containerRect.height / pxPerMm).toFixed(3)) : qrSize
    };
    const measuredBox = {
      widthMm: pxPerMm ? Number((boxRect.width / pxPerMm).toFixed(3)) : qrSize,
      heightMm: pxPerMm ? Number((boxRect.height / pxPerMm).toFixed(3)) : qrSize
    };

    qrBox.dataset.qrInnerMm = qrSize.toFixed(3);
    qrBox.dataset.qrQuietMm = quietMm.toFixed(3);
    qrBox.dataset.qrFootprintMm = qrTotal.toFixed(3);
    qrBox.dataset.qrMeasuredWidthMm = measuredBox.widthMm.toFixed(3);
    qrBox.dataset.qrMeasuredHeightMm = measuredBox.heightMm.toFixed(3);
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const mod of this.modules) {
      if (!mod || typeof mod.x !== 'number' || typeof mod.y !== 'number') continue;
      minX = Math.min(minX, mod.x);
      minY = Math.min(minY, mod.y);
      maxX = Math.max(maxX, mod.x);
      maxY = Math.max(maxY, mod.y);
    }
    const hasModules = this.modules.length > 0 && isFinite(minX) && isFinite(minY) && isFinite(maxX) && isFinite(maxY);
    if (!hasModules) {
      minX = minY = 0;
      maxX = maxY = 0;
    }
    const darkSpanWidth = hasModules ? (maxX - minX + moduleSize) : 0;
    const darkSpanHeight = hasModules ? (maxY - minY + moduleSize) : 0;
    const darkEndX = hasModules ? maxX + moduleSize : 0;
    const darkEndY = hasModules ? maxY + moduleSize : 0;
    const deltaBoxW = measuredBox.widthMm - qrSize;
    const deltaBoxH = measuredBox.heightMm - qrSize;
    const deltaContainerW = measuredContainer.widthMm - qrSize;
    const deltaContainerH = measuredContainer.heightMm - qrSize;
    const summaryLines = [
      `Target: ${qrBox.id || qrBox.closest('.tag')?.id || 'unknown'} | modules=${size} | moduleSize=${moduleSize.toFixed(3)}mm`,
      `Requested data ${qrSize.toFixed(3)}mm, quiet ${quietMm.toFixed(3)}mm each side (footprint ${qrTotal.toFixed(3)}mm)`,
      `qr-box inner measured ${measuredBox.widthMm.toFixed(3)}×${measuredBox.heightMm.toFixed(3)}mm (Δw=${deltaBoxW.toFixed(3)}, Δh=${deltaBoxH.toFixed(3)})`,
      `module container measured ${measuredContainer.widthMm.toFixed(3)}×${measuredContainer.heightMm.toFixed(3)}mm (Δw=${deltaContainerW.toFixed(3)}, Δh=${deltaContainerH.toFixed(3)})`,
      hasModules
        ? `dark modules span X ${minX.toFixed(3)}→${darkEndX.toFixed(3)}mm (width ${darkSpanWidth.toFixed(3)}mm), Y ${minY.toFixed(3)}→${darkEndY.toFixed(3)}mm (height ${darkSpanHeight.toFixed(3)}mm)`
        : 'dark modules span: none'
    ];

    const record = {
      targetId: qrBox.id || qrBox.closest('.tag')?.id || null,
      timestamp: Date.now(),
      moduleSizeMm: moduleSize,
      qrSizeMm: qrSize,
      quietZoneMm: quietMm,
      totalFootprintMm: qrTotal,
      measured: {
        qrBox: measuredBox,
        container: measuredContainer
      },
      summaryLines,
      modules: this.modules.map(m => ({
        row: m.row,
        col: m.col,
        xMm: Number(m.x.toFixed(3)),
        yMm: Number(m.y.toFixed(3)),
        sizeMm: Number(m.size.toFixed(3))
      }))
    };
    this.debugRecords.push(record);
    if (this.debugRecords.length > 10) {
      this.debugRecords.shift();
    }

    if (typeof window !== 'undefined') {
      window.__lastQrModuleRecord = record;
      window.__lastQrModuleSummary = summaryLines.join('\n');
    }

    if (console && typeof console.debug === 'function') {
      console.debug('[QR] layout summary' + summaryLines.join('\n'));
    }

    return {
      moduleCount: this.modules.length,
      totalModules: size * size,
      moduleSize: moduleSize,
      qrSize: qrSize,
      qrTotal: qrTotal,
      quietMm
    };
  }

  /**
   * Clear QR box content
   */
  clearQRBox(qrBox) {
    const existing = qrBox.querySelector('.qr-modules-container');
    if (existing) {
      existing.remove();
    }

    // Also remove any placeholder text
    qrBox.innerHTML = '';
  }

  /**
   * Add placeholder when no QR is loaded
   */
  addPlaceholder(qrBox, text = 'QR Code Will Appear Here') {
    this.clearQRBox(qrBox);

    const placeholder = document.createElement('div');
    placeholder.className = 'qr-placeholder';
    placeholder.textContent = text;
    placeholder.style.cssText = `
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
      color: #666;
      font-size: 14px;
      text-align: center;
      border: 2px dashed #ccc;
      background: #f9f9f9;
    `;

    qrBox.appendChild(placeholder);
  }

  /**
   * Get QR module data for export
   */
  getModuleData() {
    if (!this.currentQRData) return null;

    return {
      url: this.currentQRData.url,
      modules: this.currentQRData.modules,
      size: this.currentQRData.size,
      version: this.currentQRData.version,
      moduleElements: this.modules.map(m => ({
        row: m.row,
        col: m.col,
        x: m.x,
        y: m.y,
        size: m.size,
        isDark: m.isDark
      }))
    };
  }

  /**
   * Generate QR info text for UI
   */
  generateQRInfo() {
    if (!this.currentQRData) {
      return 'No QR code generated';
    }

    const { size, version, errorCorrectionLevel } = this.currentQRData;
    const darkModules = this.modules.length;
    const totalModules = size * size;
    const fillRate = ((darkModules / totalModules) * 100).toFixed(1);

    return `QR v${version} (${size}x${size}): ${darkModules}/${totalModules} modules (${fillRate}% fill)`;
  }

  /**
   * Validate QR URL
   */
  static validateURL(url) {
    try {
      new URL(url);
      return { valid: true };
    } catch (error) {
      return {
        valid: false,
        error: 'Invalid URL format'
      };
    }
  }

  /**
   * Get optimal QR settings for given constraints
   */
  static getOptimalSettings(url, maxSize, targetModuleSize) {
    // This would analyze the URL and suggest optimal QR settings
    // For now, return reasonable defaults
    return {
      errorCorrectionLevel: 'L',
      estimatedSize: Math.ceil(url.length / 10) + 21, // Rough estimate
      recommendedModuleSize: Math.max(1.5, targetModuleSize)
    };
  }
}
