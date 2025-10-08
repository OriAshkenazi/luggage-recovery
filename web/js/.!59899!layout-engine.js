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

    // Compute required inner QR side with quiet zone
    const qrInner = cfg.moduleSize * (cfg.modules + cfg.quiet * 2);

    // Compute left column width (QR) from required inner size + padding
    const leftColMm = qrInner + (cfg.qrPadL + cfg.qrPadR);

    // Content area calculations
    const contentW = cfg.tagW - (cfg.outerL + cfg.outerR);
    const contentH = cfg.tagH - (cfg.outerT + cfg.outerB);

    // Column calculations
    const rightColMm = contentW - leftColMm - cfg.gutter;

    // QR positioning within left column
    const qrBoxW = leftColMm - (cfg.qrPadL + cfg.qrPadR);
    const qrBoxH = contentH - (cfg.qrPadT + cfg.qrPadB);
    const qrSize = Math.min(qrBoxW, qrBoxH);
    const actualModuleSize = qrSize / (cfg.modules + cfg.quiet * 2);

    // QR center position (relative to tag center)
    const qrCenterX = -cfg.tagW/2 + cfg.outerL + cfg.qrPadL + qrSize/2;
    const qrCenterY = 0; // centered vertically

    // Slit positioning
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
      leftColMm,
      rightColMm,
      contentW,
      contentH,
      qrSize,
      actualModuleSize,

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

    // Column widths
    root.style.setProperty('--left-col', this.mm(computed.leftColMm));
    root.style.setProperty('--right-col', this.mm(computed.rightColMm));

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

    // Back side adjustments for slit
    const slitBackTotalSpace = config.slitMarginL + config.slitWidth + config.slitMarginR;
    root.style.setProperty('--slit-back-total-space', this.mm(slitBackTotalSpace));
  }

  /**
   * Generate layout metrics for debugging
   */
  generateMetrics(config, computed) {
    const metrics = {
