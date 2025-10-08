/**
 * Layout Engine - Core layout calculations and CSS variable management
 * Handles the mathematical layout system that drives the tag positioning
 */

export class LayoutEngine {
  constructor() {
    this.mm = (v) => `${v}mm`;
  }

  /**
   * Compute layout values from configuration
   */
  computeLayout(config) {
    const cfg = config;

    // Compute QR data area/quiet zone sizes in mm
    const quietMm = cfg.moduleSize * cfg.quiet;
    const qrInner = cfg.moduleSize * cfg.modules; // data-only area
    const qrTotal = qrInner + quietMm * 2; // bounding box including quiet zone

    // Compute left column width (QR) from required total size + padding
    const leftColMm = qrTotal + (cfg.qrPadL + cfg.qrPadR);

    // Content area calculations
    const contentW = cfg.tagW - (cfg.outerL + cfg.outerR);
    const contentH = cfg.tagH - (cfg.outerT + cfg.outerB);

    // Slit column widths (mm)
    const slitTrack = cfg.slitWidth + cfg.slitMarginL + cfg.slitMarginR;
    const slitColFront = slitTrack;
    const slitColBack = slitTrack;
    const slitColMax = slitTrack;

    // Column calculations (ensure both sides fit by reserving max slit width)
    const textColMm = Math.max(contentW - leftColMm - cfg.gutter - slitColMax, 0);
    const rightColMm = textColMm; // for front template naming

    // QR box (available space) and desired QR size
    const qrBoxW = leftColMm - (cfg.qrPadL + cfg.qrPadR);
    const qrBoxH = contentH - (cfg.qrPadT + cfg.qrPadB);
    const qrSize = qrInner; // data area only (tight fit around modules)
    const actualModuleSize = cfg.moduleSize; // honor mm module size

    // QR center position (relative to tag center)
    const qrCenterX = -cfg.tagW/2 + cfg.outerL + cfg.qrPadL + quietMm + qrSize/2;
    const qrCenterY = 0; // centered vertically

    // Slit positioning (centered visually; used for metrics only)
    const slitCenterX = cfg.tagW/2 - cfg.slitMarginR - cfg.slitWidth/2;
    const slitCenterY = 0; // centered vertically

    // Text column bounds
    const textColLeft = -cfg.tagW/2 + cfg.outerL + leftColMm + cfg.gutter;
    const textColRight = cfg.tagW/2 - cfg.outerR;
    const textColTop = cfg.tagH/2 - cfg.outerT;
    const textColBottom = -cfg.tagH/2 + cfg.outerB;

    // Text area (inside padding)
    const textAreaLeft = textColLeft + cfg.txPadL;
    const textAreaRight = textColRight - cfg.txPadR;
    const textAreaTop = textColTop - cfg.txPadT;
    const textAreaBottom = textColBottom + cfg.txPadB;

    return {
      // Core dimensions
      qrInner,
      qrTotal,
      leftColMm,
      rightColMm,
      contentW,
      contentH,
      qrSize,
      actualModuleSize,
      quietMm,

      // Positioning
      qrCenter: { x: qrCenterX, y: qrCenterY },
      slitCenter: { x: slitCenterX, y: slitCenterY },

      // Text column bounds
      textCol: {
        left: textColLeft,
        right: textColRight,
        top: textColTop,
        bottom: textColBottom
      },

      // Text area (inside padding)
      textArea: {
        left: textAreaLeft,
        right: textAreaRight,
        top: textAreaTop,
        bottom: textAreaBottom,
        width: textAreaRight - textAreaLeft,
        height: textAreaTop - textAreaBottom
      }
    };
  }

  /**
   * Apply computed layout to CSS variables
   */
  applyCSSVariables(config, computed) {
    const root = document.documentElement;

    // Set basic configuration variables
    root.style.setProperty('--tag-w', this.mm(config.tagW));
    root.style.setProperty('--tag-h', this.mm(config.tagH));
    root.style.setProperty('--outer-t', this.mm(config.outerT));
    root.style.setProperty('--outer-r', this.mm(config.outerR));
    root.style.setProperty('--outer-b', this.mm(config.outerB));
    root.style.setProperty('--outer-l', this.mm(config.outerL));
    root.style.setProperty('--gutter', this.mm(config.gutter));

    // QR settings
    root.style.setProperty('--qr-inner', this.mm(computed.qrInner));
    root.style.setProperty('--qr-total', this.mm(computed.qrTotal));
    root.style.setProperty('--qr-module', this.mm(config.moduleSize));
    root.style.setProperty('--qr-modules', config.modules);
    root.style.setProperty('--qr-quiet', config.quiet);

    // QR padding
    root.style.setProperty('--qr-pad-t', this.mm(config.qrPadT));
    root.style.setProperty('--qr-pad-r', this.mm(config.qrPadR));
    root.style.setProperty('--qr-pad-b', this.mm(config.qrPadB));
    root.style.setProperty('--qr-pad-l', this.mm(config.qrPadL));

    // Text padding
    root.style.setProperty('--tx-pad-t', this.mm(config.txPadT));
    root.style.setProperty('--tx-pad-r', this.mm(config.txPadR));
    root.style.setProperty('--tx-pad-b', this.mm(config.txPadB));
    root.style.setProperty('--tx-pad-l', this.mm(config.txPadL));

    // Column widths (front/back use dedicated variables)
    root.style.setProperty('--qr-col', this.mm(computed.leftColMm));
    root.style.setProperty('--text-col', this.mm(computed.rightColMm));
    root.style.setProperty('--slit-col-front', this.mm(config.slitWidth + config.slitMarginL + config.slitMarginR));
    root.style.setProperty('--slit-col-back', this.mm(config.slitWidth + config.slitMarginL + config.slitMarginR));

    // Slit properties
    root.style.setProperty('--slit-width', this.mm(config.slitWidth));
    root.style.setProperty('--slit-height', this.mm(config.slitHeight));
    root.style.setProperty('--slit-margin-l', this.mm(config.slitMarginL));
    root.style.setProperty('--slit-margin-r', this.mm(config.slitMarginR));

    // Font sizes
    root.style.setProperty('--fs-header', this.mm(config.fsH));
    root.style.setProperty('--fs-name', this.mm(config.fsN));
    root.style.setProperty('--fs-phone', this.mm(config.fsP));
    root.style.setProperty('--fs-email', this.mm(config.fsE));
    root.style.setProperty('--fs-footer', this.mm(config.fsF));

    // Quiet zone mm variable (for optional overlay)
    root.style.setProperty('--qr-quiet-mm', this.mm(computed.quietMm));
    root.classList.toggle('has-quiet', computed.quietMm > 0);
  }

  /**
   * Generate layout metrics for debugging
   */
  generateMetrics(config, computed) {
    const lines = [
      `QR: modules=${config.modules} | module size=${config.moduleSize.toFixed(2)}mm | quiet=${config.quiet} modules | data=${computed.qrSize.toFixed(1)}mm | footprint=${computed.qrTotal.toFixed(1)}mm`,
      `Canvas: width=${config.tagW}mm height=${config.tagH}mm | margins T/R/B/L ${config.outerT}/${config.outerR}/${config.outerB}/${config.outerL}mm | gutter=${config.gutter}mm`,
      `Text sizes (mm): header=${config.fsH.toFixed(1)}, name=${config.fsN.toFixed(1)}, phone=${config.fsP.toFixed(1)}, email=${config.fsE.toFixed(1)}, footer=${config.fsF.toFixed(1)}`,
      `QR padding (mm): T/R/B/L ${config.qrPadT}/${config.qrPadR}/${config.qrPadB}/${config.qrPadL}`,
      `Text padding (mm): T/R/B/L ${config.txPadT}/${config.txPadR}/${config.txPadB}/${config.txPadL}`,
      `Slit: width=${config.slitWidth}mm height=${config.slitHeight}mm | margins L/R ${config.slitMarginL}/${config.slitMarginR}mm`,
      `Computed columns (mm): left=${computed.leftColMm.toFixed(1)}, right=${computed.rightColMm.toFixed(1)}, gutter=${config.gutter.toFixed(1)}, slit track=${(config.slitWidth + config.slitMarginL + config.slitMarginR).toFixed(1)}`,
      `Text area (mm): ${computed.textArea.width.toFixed(1)} × ${computed.textArea.height.toFixed(1)}`
    ];

    // Check for warnings
    const warnings = [];
    if (computed.actualModuleSize < 1.8) {
      warnings.push(`WARNING: Module size ${computed.actualModuleSize.toFixed(2)}mm may be too small for PETG resolution`);
    }
    if (computed.rightColMm < 100) {
      warnings.push(`WARNING: Right column ${computed.rightColMm.toFixed(1)}mm may be too narrow for typography`);
    }
    if (computed.textArea.width < 80) {
      warnings.push(`WARNING: Text area ${computed.textArea.width.toFixed(1)}mm width may be too small`);
    }
    const usableW = config.tagW - (config.outerL + config.outerR);
    const usableH = config.tagH - (config.outerT + config.outerB);
    if (computed.qrTotal > usableW) {
      warnings.push('WARNING: QR width (data + quiet) exceeds available content width');
    }
    if (computed.qrTotal > usableH) {
      warnings.push('WARNING: QR height (data + quiet) exceeds available content height');
    }

    return { lines, warnings };
  }

  /**
   * Validate configuration values
   */
  validateConfig(config) {
    const errors = [];

    if (config.tagW < 50) errors.push("Canvas width too small (min 50mm)");
    if (config.tagH < 30) errors.push("Canvas height too small (min 30mm)");
    if (config.modules < 17 || config.modules > 73) errors.push("Invalid QR modules count");
    if (config.moduleSize < 0.5 || config.moduleSize > 10) errors.push("Invalid module size");

    // Check if content fits
    const computed = this.computeLayout(config);
    if (computed.rightColMm < 20) {
      errors.push("Content doesn't fit - canvas too narrow or QR too large");
    }

    return errors;
  }
}
