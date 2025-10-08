/**
 * DOM Builder - Dynamic element creation and manipulation
 * Builds and updates the tag preview elements
 */

export class DOMBuilder {
  constructor() {
    this.elements = {};
  }

  /**
   * Create the main tag structure
   */
  createTagStructure() {
    const tagContainer = document.createElement('div');
    tagContainer.style.cssText = 'display: flex; gap: 7mm; flex-wrap: wrap; justify-content: center;';

    // Front side tag
    const frontTag = this.createSingleTag('tag', false);
    tagContainer.appendChild(frontTag);

    // Back side tag (mirrored)
    const backTag = this.createSingleTag('tag-mirrored', true);
    tagContainer.appendChild(backTag);

    return tagContainer;
  }

  /**
   * Create a single tag element
   */
  createSingleTag(id, isMirrored = false) {
    const tagWrapper = document.createElement('div');

    // Label
    const label = document.createElement('h3');
    label.textContent = isMirrored ? 'Back Side (face-on view)' : 'Front Side';
    label.style.cssText = 'text-align: center; margin: 0 0 3mm 0; font-size: 4mm; color: #666;';

    // Tag element
    const tag = document.createElement('div');
    tag.id = id;
    tag.className = isMirrored ? 'tag mirrored' : 'tag';

    // Content grid
    const content = document.createElement('div');
    content.className = 'content';

    // QR column
    const qrCol = document.createElement('div');
    qrCol.className = 'qr-col';

    const qrBox = document.createElement('div');
    qrBox.className = 'qr-box';
    qrCol.appendChild(qrBox);

    // Gutter spacer
    const gutterSpacer = document.createElement('div');
    gutterSpacer.className = 'gutter-spacer';

    // Text column
    const textCol = document.createElement('div');
    textCol.className = 'text-col';

    // Header
    const header = document.createElement('div');
    header.className = 'header';
    header.textContent = 'FOUND MY LUGGAGE?';

    // Contact info container
    const contactInfo = document.createElement('div');
    contactInfo.className = 'contact-info';

    const name = document.createElement('div');
    name.className = 'name';
    name.textContent = 'ORI ASHKENAZI';

    const phone = document.createElement('div');
    phone.className = 'phone';
    phone.textContent = '+972-50-971-3042';

    const email = document.createElement('div');
    email.className = 'email';
    email.textContent = 'ORIASHKENAZI93@GMAIL.COM';

    contactInfo.appendChild(name);
    contactInfo.appendChild(phone);
    contactInfo.appendChild(email);

    // Footer
    const footer = document.createElement('div');
    footer.className = 'footer';
    footer.textContent = 'SCAN QR OR CALL/TEXT';

    // Assemble text column
    textCol.appendChild(header);
    textCol.appendChild(contactInfo);
    textCol.appendChild(footer);

    // Assemble content
    content.appendChild(qrCol);
    content.appendChild(gutterSpacer);
    content.appendChild(textCol);

    // Slit column with slit element inside
    const slitCol = document.createElement('div');
    slitCol.className = 'slit-col';
    const slit = document.createElement('div');
    slit.className = 'slit';
    slitCol.appendChild(slit);

    // Assemble tag (4 columns inside content)
    content.appendChild(slitCol);
    tag.appendChild(content);

    // Assemble wrapper
    tagWrapper.appendChild(label);
    tagWrapper.appendChild(tag);

    // Store references
    this.elements[id] = {
      wrapper: tagWrapper,
      tag: tag,
      content: content,
      qrCol: qrCol,
      qrBox: qrBox,
      textCol: textCol,
      slitCol: slitCol,
      header: header,
      contactInfo: contactInfo,
      name: name,
      phone: phone,
      email: email,
      footer: footer,
      slit: slit
    };

    return tagWrapper;
  }

  /**
   * Create control panel
   */
  createControlPanel() {
    const controls = document.createElement('div');
    controls.className = 'controls';

    // QR Code group
    const qrGroup = this.createControlGroup('QR Code', [
      { type: 'text', id: 'qrUrl', label: 'URL', value: 'https://oriashkenazi.github.io/luggage-recovery', style: 'width: 80mm;' },
      { type: 'number', id: 'moduleSize', label: 'Module size (mm)', value: '2.0', step: '0.1', min: '0.5', max: '4' },
      { type: 'number', id: 'quiet', label: 'Quiet zone (modules)', value: '0', step: '1', min: '0', max: '8' }
    ]);

    const qrInfo = document.createElement('div');
    qrInfo.innerHTML = '<small id="qrInfo">QR: Loading...</small>';
    qrGroup.appendChild(qrInfo);

    // Canvas group
    const canvasGroup = this.createControlGroup('Canvas', [
      { type: 'number', id: 'tagW', label: 'Width (mm)', value: '200.0', step: '1', min: '40' },
      { type: 'number', id: 'tagH', label: 'Height (mm)', value: '74.0', step: '1', min: '30' }
    ]);

    // Outer margins
    const outerLabel = document.createElement('em');
    outerLabel.textContent = 'Outer margins (per side)';
    outerLabel.style.cssText = 'font-size:3.5mm;opacity:.8';
    canvasGroup.appendChild(outerLabel);

    const outerControls = [
      { type: 'number', id: 'outerT', label: 'Top', value: '4', step: '0.5', min: '0' },
      { type: 'number', id: 'outerR', label: 'Right', value: '4', step: '0.5', min: '0' },
      { type: 'number', id: 'outerB', label: 'Bottom', value: '4', step: '0.5', min: '0' },
      { type: 'number', id: 'outerL', label: 'Left', value: '4', step: '0.5', min: '0' },
      { type: 'number', id: 'gutter', label: 'Gutter (mm)', value: '3', step: '0.5', min: '0' }
    ];

    outerControls.forEach(control => {
      canvasGroup.appendChild(this.createControl(control));
    });

    // Text sizes group
    const textGroup = this.createControlGroup('Text Sizes', [
      { type: 'number', id: 'fsH', label: 'Header size (mm)', value: '10.0', step: '0.2', min: '2' },
      { type: 'number', id: 'fsN', label: 'Name size (mm)', value: '6.0', step: '0.2', min: '2' },
      { type: 'number', id: 'fsP', label: 'Phone size (mm)', value: '5.0', step: '0.2', min: '2' },
      { type: 'number', id: 'fsE', label: 'Email size (mm)', value: '5.0', step: '0.2', min: '2' },
      { type: 'number', id: 'fsF', label: 'Footer size (mm)', value: '7.0', step: '0.2', min: '2' }
    ]);

    // Padding groups
    const qrPadGroup = this.createControlGroup('QR Padding (mm)', [
      { type: 'number', id: 'qrPadT', label: 'Top', value: '0', step: '0.5', min: '0' },
      { type: 'number', id: 'qrPadR', label: 'Right', value: '0', step: '0.5', min: '0' },
      { type: 'number', id: 'qrPadB', label: 'Bottom', value: '0', step: '0.5', min: '0' },
      { type: 'number', id: 'qrPadL', label: 'Left', value: '0', step: '0.5', min: '0' }
    ]);

    const txPadGroup = this.createControlGroup('Text Padding', [
      { type: 'number', id: 'txPadT', label: 'Top', value: '8', step: '0.5', min: '0' },
      { type: 'number', id: 'txPadR', label: 'Right', value: '3', step: '0.5', min: '0' },
      { type: 'number', id: 'txPadB', label: 'Bottom', value: '8', step: '0.5', min: '0' },
      { type: 'number', id: 'txPadL', label: 'Left', value: '3', step: '0.5', min: '0' }
    ]);

    // Slit group
    const slitGroup = this.createControlGroup('Slit', [
      { type: 'number', id: 'slitWidth', label: 'Width (mm)', value: '5.0', step: '0.5', min: '1' },
      { type: 'number', id: 'slitHeight', label: 'Height (mm)', value: '20.0', step: '0.5', min: '3' },
      { type: 'number', id: 'slitMarginL', label: 'Left margin (mm)', value: '4.0', step: '0.5', min: '0' },
      { type: 'number', id: 'slitMarginR', label: 'Right margin (mm)', value: '5.0', step: '0.5', min: '0' }
    ]);

    // Debug group
    const debugGroup = this.createControlGroup('Debug', [
      { type: 'checkbox', id: 'showDebug', label: 'Show outlines' },
      { type: 'checkbox', id: 'showTelemetry', label: 'Enable telemetry' }
    ]);

    // Export group
    const exportGroup = this.createControlGroup('Export', []);
    const exportSVGBtn = document.createElement('button');
    exportSVGBtn.id = 'exportSVG';
    exportSVGBtn.textContent = 'Export SVG';
    exportSVGBtn.type = 'button';

    const exportConfigBtn = document.createElement('button');
    exportConfigBtn.id = 'exportConfig';
    exportConfigBtn.textContent = 'Export Config JSON';
    exportConfigBtn.type = 'button';

    const generate3DBtn = document.createElement('button');
    generate3DBtn.id = 'generate3D';
    generate3DBtn.textContent = 'Generate 3D STL';
    generate3DBtn.type = 'button';

    exportGroup.appendChild(exportSVGBtn);
    exportGroup.appendChild(exportConfigBtn);
    exportGroup.appendChild(generate3DBtn);

    // Assemble controls
    controls.appendChild(qrGroup);
    controls.appendChild(canvasGroup);
    controls.appendChild(textGroup);
    controls.appendChild(qrPadGroup);
    controls.appendChild(txPadGroup);
    controls.appendChild(slitGroup);
    controls.appendChild(debugGroup);
    controls.appendChild(exportGroup);

    return controls;
  }

  /**
   * Create a control group
   */
  createControlGroup(title, controls) {
    const group = document.createElement('div');
    group.className = 'group';

    const strong = document.createElement('strong');
    strong.textContent = title;
    group.appendChild(strong);

    controls.forEach(control => {
      group.appendChild(this.createControl(control));
    });

    return group;
  }

  /**
   * Create an individual control
   */
  createControl(control) {
    const label = document.createElement('label');

    const span = document.createElement('span');
    span.textContent = control.label;

    const input = document.createElement('input');
    input.id = control.id;
    input.type = control.type;

    if (control.value) input.value = control.value;
    if (control.step) input.step = control.step;
    if (control.min) input.min = control.min;
    if (control.max) input.max = control.max;
    if (control.style) input.style.cssText = control.style;

    label.appendChild(span);
    label.appendChild(input);

    return label;
  }

  /**
   * Create metrics display
   */
  createMetricsDisplay() {
    const metrics = document.createElement('div');
    metrics.id = 'metrics';
    metrics.className = 'metrics';
    metrics.textContent = 'Initializing...';
    return metrics;
  }

  /**
   * Update metrics display
   */
  updateMetrics(metricsData, warnings = []) {
    const metricsEl = document.getElementById('metrics');
    if (!metricsEl) return;

    const hasLines = metricsData && Array.isArray(metricsData.lines);
    const lines = hasLines ? [...metricsData.lines] : ['Metrics unavailable'];

    if (warnings.length > 0) {
      lines.push('', ...warnings);
      metricsEl.className = 'metrics error';
    } else {
      metricsEl.className = 'metrics';
    }

    metricsEl.textContent = lines.join('\n');
  }

  /**
   * Get element references
   */
  getElements() {
    return this.elements;
  }

  /**
   * Get all input elements
   */
  getAllInputs() {
    const inputs = {};
    const inputElements = document.querySelectorAll('.controls input');

    inputElements.forEach(input => {
      inputs[input.id] = input;
    });

    return inputs;
  }
}
