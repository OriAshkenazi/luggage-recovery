# Web-to-3D Layout Integration

This document describes the complete integration system between the web layout preview and 3D model generation, ensuring perfect synchronization between web preview and physical output.

## 🎯 Integration Overview

**Problem Solved**: Previously, web layout and 3D model generation used separate, hardcoded layout values that could drift out of sync. Now they share a single source of truth.

**Solution**: Web layout engine exports configuration that 3D script imports, ensuring pixel-perfect matching between preview and physical output.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Layout    │───▶│  Node.js Bridge  │───▶│  Python 3D Gen  │
│  (tag_layout)   │    │                  │    │ (reversible_tag) │
│                 │    │ • extract_layout │    │                 │
│ • CSS Grid      │    │ • JSON export    │    │ • JSON import   │
│ • User inputs   │    │ • SVG export     │    │ • Exact layout  │
│ • Live preview  │    │                  │    │   replication   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Files and Components

### Web Layout (`/web/`)
- **`tag_layout.html`**: Complete web layout engine with live preview
  - CSS Grid layout calculation
  - User input controls
  - SVG export functionality
  - JSON config export
- **`extract_layout.js`**: Node.js bridge script
- **`package.json`**: Node.js dependencies (none required)

### 3D Models (`/3d-models/`)
- **`reversible_tag.py`**: Updated 3D generation script
  - Loads `layout_config.json`
  - Falls back to new defaults if config missing
  - Implements correct stacking/mirroring logic
- **`layout_config.json`**: Generated configuration file
- **`test_config_loading.py`**: Validation script (no CadQuery required)

## 🔄 Workflow

### 1. Extract Layout Configuration
```bash
cd web
node extract_layout.js
```
**Output**:
- `web/layout_config.json`
- `3d-models/layout_config.json` (copy)

### 2. Generate 3D Models
```bash
cd 3d-models
python reversible_tag.py
```
**Uses**: `layout_config.json` for exact web layout replication

### 3. Verify Integration
```bash
cd 3d-models
python test_config_loading.py
```
**Validates**: Configuration loading and value matching

## 📊 Configuration Structure

```json
{
  "input": {
    "tagW": 240.0, "tagH": 94.0,
    "modules": 37, "moduleSize": 2.0, "quiet": 0,
    "outerT": 4, "outerR": 4, "outerB": 4, "outerL": 4,
    "qrPadT": 3, "qrPadR": 3, "qrPadB": 3, "qrPadL": 3,
    "txPadT": 8, "txPadR": 3, "txPadB": 8, "txPadL": 3,
    "gutter": 3, "slitWidth": 4.5, "slitHeight": 20.0,
    "slitMarginL": 3.0, "slitMarginR": 9.0,
    "fsH": 12.0, "fsN": 8.0, "fsP": 6.0, "fsE": 6.0, "fsF": 8.0
  },
  "computed": {
    "qrSize": 74.0, "leftColMm": 80.0, "rightColMm": 149.0,
    "qrCenter": {"x": -79.0, "y": 0},
    "slitCenter": {"x": 108.75, "y": 0},
    "textArea": {
      "left": -72.0, "right": 116.0, "top": 39.0, "bottom": -39.0,
      "width": 188.0, "height": 78.0
    }
  },
  "stacking": {
    "topSide": {
      "mirrored": false,
      "description": "non-mirrored - reads normally when viewed from above"
    },
    "bottomSide": {
      "mirrored": true,
      "mirrorPlane": "YZ",
      "description": "mirrored across YZ - reads correctly after 180° Y-rotation"
    },
    "webThickness": 0.4,
    "totalThickness": 3.0,
    "halfDepth": 1.3
  }
}
```

## 🎨 Stacking and Mirroring Logic

**CRITICAL**: The reversible tag uses dual-stack mirrored features to ensure readable text on both sides when physically flipped.

### Physical Stacking Order
```
TOP SIDE (when viewed from above):
├── Back Stack: NON-MIRRORED features (reads normally)
├── Central Web: 0.4mm structural layer
└── Front Stack: MIRRORED across YZ (horizontally flipped)
BOTTOM SIDE (when tag is flipped 180°):
```

### Implementation Details
- **Top Side**: Features remain normal orientation
- **Bottom Side**: Features mirrored across YZ plane
- **Result**: When tag is flipped 180° around Y-axis, both sides read correctly
- **Central Web**: Prevents feature stacks from merging (avoids through-cuts)

## 🎯 Key Benefits

### ✅ Perfect Synchronization
- Web preview exactly matches 3D output
- Single source of truth for all layout calculations
- No manual value copying or sync issues

### ✅ User-Driven Configuration
- Any web layout change flows automatically to 3D
- Users can preview changes before generating STL files
- Real-time validation of dimensions and constraints

### ✅ Maintainable System
- No code duplication between web and 3D systems
- Clear separation of concerns
- Easy to add new layout parameters

### ✅ Extensible Design
- SVG export for additional tools
- JSON config can drive other outputs (laser cutting, documentation)
- Bridge script can be extended for additional validations

## 🧪 Testing and Validation

### Manual Testing Workflow
1. **Modify web layout** via `tag_layout.html`
2. **Export configuration** via "Export Config JSON" button
3. **Run bridge script**: `node extract_layout.js`
4. **Generate 3D models**: `python reversible_tag.py`
5. **Verify in slicer**: Check dimensions match web preview

### Automated Validation
```bash
# Test configuration extraction
npm run test

# Test configuration loading
cd ../3d-models && python test_config_loading.py

# Full integration test
node extract_layout.js && cd ../3d-models && python test_config_loading.py
```

## ⚙️ Advanced Usage

### Custom Configuration Override
```bash
# Create override file
echo '{"tagW": 250.0, "modules": 41}' > custom_config.json

# Use override
node extract_layout.js custom_config.json
```

### Programmatic Integration
```javascript
const { extractLayoutConfig } = require('./extract_layout.js');
const config = extractLayoutConfig({
  tagW: 200.0,
  modules: 33
});
// Use config...
```

### Python Configuration Override
```python
override_config = {"tagW": 250.0, "modules": 41}
create_truly_reversible_tag(override_config=override_config)
```

## 🐛 Troubleshooting

### Configuration Not Found
```
❌ Layout config not found at layout_config.json
```
**Solution**: Run `node extract_layout.js` to generate configuration

### Dimension Warnings
```
⚠️  Width 240.0mm may be too small (needs 242.3mm)
```
**Action**: Check web layout constraints and adjust canvas size

### Module Size Mismatch
```
⚠️  QR code has 41 modules but config expects 37
```
**Cause**: QR URL generates different module count than configured
**Solution**: Update web layout modules setting to match actual QR

### Stacking Configuration Missing
```
🔄 Using default stacking: bottom mirrored YZ, top normal
```
**Info**: Fallback behavior when layout_config.json unavailable

## 📚 Related Documentation

- **CLAUDE.md**: Overall project guidelines and architecture
- **Web Layout**: `tag_layout.html` inline documentation
- **3D Models**: `reversible_tag.py` docstrings
- **Stacking Logic**: See `reversible_tag.py` lines 308-325

## 🚀 Future Enhancements

### Planned Features
- **Real-time 3D preview**: Generate STL preview in browser
- **Batch processing**: Generate multiple configurations at once
- **Material optimization**: Calculate print time and material usage
- **Quality validation**: Automated checks for printability

### Extension Points
- **Additional export formats**: DXF for laser cutting
- **Template system**: Pre-defined layout configurations
- **Integration with slicers**: Direct STL upload to OctoPrint/Bambu
- **Version control**: Track layout configuration changes

---

*This integration ensures that what you see in the web preview is exactly what you get from the 3D printer - no more layout surprises! 🎯*