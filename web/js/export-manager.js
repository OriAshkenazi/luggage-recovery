/**
 * Export Manager - SVG/3D export functionality
 * Handles exporting precise geometry and 3D STL generation
 */

export class ExportManager {
  constructor(layoutEngine, qrGenerator, domBuilder) {
    this.layoutEngine = layoutEngine;
    this.qrGenerator = qrGenerator;
    this.domBuilder = domBuilder;
  }

  /**
   * Export precise SVG geometry from DOM elements
   */
  exportPreciseSVG(config, computed) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', config.tagW);
    svg.setAttribute('height', config.tagH);
    svg.setAttribute('viewBox', `0 0 ${config.tagW} ${config.tagH}`);
    svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

    const metadata = this.createSVGElement('metadata', svg);
    metadata.textContent = JSON.stringify({
      source: 'modular_web_layout',
      timestamp: Date.now(),
      config,
      computed
    });

    this.buildSide(svg, config, computed, {
      id: 'front-side',
      description: 'Front side (top layer)',
      tagKey: 'tag',
      mirrored: false
    });

    this.buildSide(svg, config, computed, {
      id: 'back-side',
      description: 'Back side mirrored for face-down printing',
      tagKey: 'tag-mirrored',
      mirrored: true
    });

    return svg;
  }

  buildSide(parent, config, computed, { id, description, tagKey, mirrored }) {
    const sideGroup = this.createSVGGroup(parent, id, description);
    const targetGroup = mirrored ? this.createSVGElement('g', sideGroup) : sideGroup;
    if (mirrored) {
      targetGroup.setAttribute('transform', `translate(${config.tagW},0) scale(-1,1)`);
    }

    this.addBaseOutline(targetGroup, config);
    this.addQRModules(targetGroup, config, computed);
    this.addTextElements(targetGroup, config, computed, tagKey);
    this.addSlitCutout(targetGroup, config, computed);

    return sideGroup;
  }

  /**
   * Add base outline to SVG
   */
  addBaseOutline(layer, config) {
    const rect = this.createSVGElement('rect', layer);
    rect.setAttribute('x', 0);
    rect.setAttribute('y', 0);
    rect.setAttribute('width', config.tagW);
    rect.setAttribute('height', config.tagH);
    rect.setAttribute('rx', 4); // corner radius
    rect.setAttribute('class', 'base-shape');
  }

  /**
   * Add QR modules from generated QR code
   */
  addQRModules(layer, config, computed) {
    const qrData = this.qrGenerator.getModuleData();
    if (!qrData) return;

    const qrCenterX = config.tagW / 2 + computed.qrCenter.x;
    const qrCenterY = config.tagH / 2 - computed.qrCenter.y;
    const qrSize = computed.qrSize;

    qrData.moduleElements.forEach(module => {
      if (module.isDark) {
        const rect = this.createSVGElement('rect', layer);

        // Convert from center-based coordinates to top-left SVG coordinates
        const svgX = qrCenterX - qrSize/2 + module.x;
        const svgY = qrCenterY - qrSize/2 + module.y;

        rect.setAttribute('x', svgX);
        rect.setAttribute('y', svgY);
        rect.setAttribute('width', module.size);
        rect.setAttribute('height', module.size);
        rect.setAttribute('class', 'qr-module');
        rect.setAttribute('data-row', module.row);
        rect.setAttribute('data-col', module.col);
      }
    });
  }

  /**
   * Add text elements with precise positioning
   */
  addTextElements(layer, config, computed, sideKey = 'tag') {
    const elements = this.domBuilder.getElements();
    const side = elements[sideKey];

    if (!side) return;

    const textElements = [
      { el: side.header, className: 'header' },
      { el: side.name, className: 'name' },
      { el: side.phone, className: 'phone' },
      { el: side.email, className: 'email' },
      { el: side.footer, className: 'footer' }
    ];

    textElements.forEach(({ el, className }) => {
      if (el) {
        const rect = el.getBoundingClientRect();
        const tagRect = side.tag.getBoundingClientRect();

        // Calculate relative position and scale to mm
        const relativeX = (rect.left - tagRect.left) * (config.tagW / tagRect.width);
        const relativeY = (rect.top - tagRect.top) * (config.tagH / tagRect.height);
        const width = rect.width * (config.tagW / tagRect.width);
        const height = rect.height * (config.tagH / tagRect.height);

        const textRect = this.createSVGElement('rect', layer);
        textRect.setAttribute('x', relativeX);
        textRect.setAttribute('y', relativeY);
        textRect.setAttribute('width', width);
        textRect.setAttribute('height', height);
        textRect.setAttribute('class', `text-${className}`);
        textRect.setAttribute('data-text', el.textContent);
        textRect.setAttribute('data-font-size', this.getFontSizeForClass(className, config));
      }
    });
  }

  /**
   * Add slit cutout
   */
  addSlitCutout(layer, config, computed) {
    const rect = this.createSVGElement('rect', layer);

    const slitX = config.tagW / 2 + computed.slitCenter.x - config.slitWidth / 2;
    const slitY = config.tagH / 2 - computed.slitCenter.y - config.slitHeight / 2;

    rect.setAttribute('x', slitX);
    rect.setAttribute('y', slitY);
    rect.setAttribute('width', config.slitWidth);
    rect.setAttribute('height', config.slitHeight);
    rect.setAttribute('rx', config.slitWidth / 2);
    rect.setAttribute('class', 'slit-cutout');
  }

  /**
   * Get font size for text class
   */
  getFontSizeForClass(className, config) {
    const fontSizes = {
      header: config.fsH,
      name: config.fsN,
      phone: config.fsP,
      email: config.fsE,
      footer: config.fsF
    };
    return fontSizes[className] || 8;
  }

  /**
   * Download SVG file
   */
  downloadSVG(config, computed, filename = 'luggage_tag_precise.svg') {
    const svg = this.exportPreciseSVG(config, computed);
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svg);

    this.downloadFile(svgString, filename, 'image/svg+xml');
  }

  /**
   * Export configuration JSON
   */
  exportConfigJSON(config, computed, filename = 'luggage_tag_config.json') {
    const qrData = this.qrGenerator.getModuleData();

    const exportConfig = {
      input: config,
      computed: computed,
      qr: qrData ? {
        url: qrData.url,
        size: qrData.size,
        moduleCount: qrData.moduleElements.length
      } : null,
      stacking: {
        topSide: {
          mirrored: false,
          description: "non-mirrored - reads normally when viewed from above"
        },
        bottomSide: {
          mirrored: true,
          mirrorPlane: "YZ",
          description: "mirrored across YZ - reads correctly after 180 degree Y-rotation"
        },
        webThickness: 0.4,
        totalThickness: 3.0,
        halfDepth: (3.0 - 0.4) / 2
      },
      meta: {
        generatedAt: new Date().toISOString(),
        source: "modular_web_layout",
        version: "2.0.0"
      }
    };

    const jsonString = JSON.stringify(exportConfig, null, 2);
    this.downloadFile(jsonString, filename, 'application/json');
  }

  /**
   * Generate 3D STL files (placeholder for now)
   */
  async generate3DSTL(config, computed) {
    try {
      // This would integrate with a WebAssembly 3D library
      // For now, return a promise that resolves with file info

      const svg = this.exportPreciseSVG(config, computed);
      const serializer = new XMLSerializer();
      const svgString = serializer.serializeToString(svg);

      const buildSingleSide = (groupId) => {
        const group = svg.querySelector(`#${groupId}`);
        if (!group) return null;
        const single = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        single.setAttribute('width', config.tagW);
        single.setAttribute('height', config.tagH);
        single.setAttribute('viewBox', `0 0 ${config.tagW} ${config.tagH}`);
        single.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        single.appendChild(group.cloneNode(true));
        return serializer.serializeToString(single);
      };

      const frontSvg = buildSingleSide('front-side');
      const backSvg = buildSingleSide('back-side');

      console.log('3D STL Generation:', {
        config,
        computed,
        svgLength: svgString.length,
        frontSvgLength: frontSvg ? frontSvg.length : 0,
        backSvgLength: backSvg ? backSvg.length : 0,
        qrModules: this.qrGenerator.getModuleData()?.moduleElements.length || 0
      });

      // Simulate processing time
      await new Promise(resolve => setTimeout(resolve, 1000));

      return {
        success: true,
        message: '3D STL generation complete (simulated)',
        files: [
          { name: 'luggage_tag_base.stl', size: '~25MB' },
          { name: 'luggage_tag_features.stl', size: '~25MB' }
        ],
        svg: {
          combined: svgString,
          front: frontSvg,
          back: backSvg
        }
      };

    } catch (error) {
      return {
        success: false,
        message: `3D generation failed: ${error.message}`
      };
    }
  }

  /**
   * Utility: Create SVG element
   */
  createSVGElement(tagName, parent = null) {
    const element = document.createElementNS('http://www.w3.org/2000/svg', tagName);
    if (parent) parent.appendChild(element);
    return element;
  }

  /**
   * Utility: Create SVG group
   */
  createSVGGroup(parent, id, description) {
    const group = this.createSVGElement('g', parent);
    group.setAttribute('id', id);
    group.setAttribute('data-description', description);
    return group;
  }

  /**
   * Utility: Download file
   */
  downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();

    URL.revokeObjectURL(url);
  }
}
