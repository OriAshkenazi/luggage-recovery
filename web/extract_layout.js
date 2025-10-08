#!/usr/bin/env node

/**
 * Node.js Bridge Script: Extract Web Layout Configuration
 *
 * Runs the web layout engine headlessly to extract exact configuration
 * for use by the Python 3D model generation script.
 *
 * Usage: node extract_layout.js [config_overrides.json]
 */

const fs = require('fs');
const path = require('path');

// Default configuration matching web layout defaults
const DEFAULT_CONFIG = {
  modules: 29,
  moduleSize: 2.0,
  quiet: 0,
  tagW: 240.0,
  tagH: 94.0,
  outerT: 4, outerR: 4, outerB: 4, outerL: 4,
  gutter: 3,
  slitWidth: 4.5,
  slitHeight: 20.0,
  slitMarginL: 3.0,
  slitMarginR: 9.0,
  fsH: 12.0, fsN: 8.0, fsP: 6.0, fsE: 6.0, fsF: 8.0,
  qrPadT: 3, qrPadR: 3, qrPadB: 3, qrPadL: 3,
  txPadT: 8, txPadR: 3, txPadB: 8, txPadL: 3
};

function extractLayoutConfig(config = DEFAULT_CONFIG) {
  console.log('🔄 Extracting layout configuration...');

  // Replicate the web's layout() function logic
  const cfg = { ...config };

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

  const layoutConfig = {
    // Input configuration
    input: cfg,

    // Computed dimensions
    computed: {
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
    },

    // Stacking and mirroring configuration
    // CRITICAL: Based on reversible_tag.py lines 227-231
    stacking: {
      // TOP side (back stack) remains NON-MIRRORED so it reads normally when viewed from above
      topSide: {
        mirrored: false,
        description: "non-mirrored - reads normally when viewed from above"
      },
      // BOTTOM side (front stack) is MIRRORED across YZ, so after a 180° Y-rotation
      // the back reads correctly when flipped
      bottomSide: {
        mirrored: true,
        mirrorPlane: "YZ", // horizontal flip
        description: "mirrored across YZ - reads correctly after 180° Y-rotation"
      },

      // Physical stacking
      webThickness: 0.4, // central web thickness (mm)
      totalThickness: 3.0, // total tag thickness (mm)
      halfDepth: (3.0 - 0.4) / 2, // feature depth per side

      // Dual-stack approach: features are split into two stacks with central web
      // This prevents through-cuts and maintains structural integrity
      stackOrder: "front_stack_mirrored + central_web + back_stack_normal"
    },

    // Export metadata
    meta: {
      generatedAt: new Date().toISOString(),
      source: "web_layout_engine",
      version: "1.0.0"
    }
  };

  // Validation
  if (layoutConfig.computed.actualModuleSize < 1.8) {
    console.warn(`⚠️  Module size ${layoutConfig.computed.actualModuleSize.toFixed(2)}mm may be too small for reliable scanning`);
  }

  if (layoutConfig.computed.rightColMm < 100) {
    console.warn(`⚠️  Right column ${layoutConfig.computed.rightColMm.toFixed(1)}mm may be too narrow for text`);
  }

  console.log(`✅ Layout extracted: ${cfg.tagW}×${cfg.tagH}mm, QR ${cfg.modules}×${cfg.modules} @ ${layoutConfig.computed.actualModuleSize.toFixed(2)}mm/module`);

  return layoutConfig;
}

function main() {
  try {
    // Check for config override file
    let config = DEFAULT_CONFIG;
    if (process.argv[2]) {
      const overridePath = process.argv[2];
      if (fs.existsSync(overridePath)) {
        const overrides = JSON.parse(fs.readFileSync(overridePath, 'utf8'));
        config = { ...DEFAULT_CONFIG, ...overrides };
        console.log(`📖 Loaded config overrides from ${overridePath}`);
      }
    }

    // Extract layout configuration
    const layoutConfig = extractLayoutConfig(config);

    // Write to output file
    const outputPath = path.join(__dirname, 'layout_config.json');
    fs.writeFileSync(outputPath, JSON.stringify(layoutConfig, null, 2));
    console.log(`💾 Saved layout config to ${outputPath}`);

    // Also write to 3d-models directory for easy access
    const modelsOutputPath = path.join(__dirname, '../3d-models/layout_config.json');
    fs.writeFileSync(modelsOutputPath, JSON.stringify(layoutConfig, null, 2));
    console.log(`💾 Copied layout config to ${modelsOutputPath}`);

    // Print summary
    console.log('\n📊 Layout Summary:');
    console.log(`   Canvas: ${config.tagW} × ${config.tagH} mm`);
    console.log(`   QR: ${config.modules}×${config.modules} @ ${layoutConfig.computed.actualModuleSize.toFixed(2)}mm/module`);
    console.log(`   Columns: left ${layoutConfig.computed.leftColMm.toFixed(1)}mm | right ${layoutConfig.computed.rightColMm.toFixed(1)}mm`);
    console.log(`   Slit: ${config.slitWidth}×${config.slitHeight}mm @ (${layoutConfig.computed.slitCenter.x.toFixed(1)}, ${layoutConfig.computed.slitCenter.y.toFixed(1)})`);
    console.log(`   Stacking: bottom mirrored ${layoutConfig.stacking.bottomSide.mirrorPlane}, top normal`);

  } catch (error) {
    console.error('❌ Error extracting layout:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { extractLayoutConfig, DEFAULT_CONFIG };
