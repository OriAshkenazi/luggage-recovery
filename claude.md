# Claude Development Guide

This document outlines coding standards, practices, and workflows for the Lost Luggage Recovery System project.

## 🎯 Project Philosophy

- **Mobile-first**: Every decision prioritizes mobile user experience
- **Accessibility-first**: Design for users in stressful situations
- **Progressive enhancement**: Core functionality works without JavaScript
- **Minimalist approach**: Simple, focused solutions over complex ones
- **Resilient design**: System should gracefully handle failures

## 🏗️ Architecture Principles

### Component Separation
- **Website**: Stateless, client-side only, GitHub Pages compatible
- **3D Models**: Self-contained STL files with minimal dependencies
- **Scripts**: Pure Python with standard libraries where possible

### Technology Constraints
- **No server-side processing**: GitHub Pages limitations
- **No databases**: Use local storage or configuration files
- **Minimal dependencies**: Reduce complexity and security vectors
- **Cross-platform compatibility**: Works on all major platforms

## 📂 File Organization

### Directory Structure
```
├── docs/             # Web component - GitHub Pages root
├── 3d-models/        # Physical component - STL files
├── scripts/          # Automation component - Python tools
├── .github/          # GitHub Actions and templates
└── assets/           # Shared resources (logos, fonts)
```

### Naming Conventions
- **Files**: `kebab-case.ext` (e.g., `tag-holder.stl`, `generate-qr.py`)
- **Directories**: `kebab-case` (e.g., `3d-models`, `user-guides`)
- **Variables**: `snake_case` in Python, `camelCase` in JavaScript
- **Constants**: `UPPER_SNAKE_CASE`
- **CSS classes**: `kebab-case` with BEM methodology

## 💻 Coding Standards

### HTML
- HTML5 semantic elements
- Valid markup (W3C validator)
- Accessible form labels and ARIA attributes
- Meta tags for mobile optimization
- Progressive enhancement structure

### CSS
- Mobile-first responsive design
- Custom properties for theming
- BEM methodology for class naming
- Minimal external dependencies
- Print media queries for tag layouts

### JavaScript
- Vanilla JavaScript (no frameworks)
- Progressive enhancement patterns
- Feature detection over browser detection
- Error handling with graceful fallbacks
- ES6+ syntax with appropriate fallbacks

### Python
- PEP 8 style guidelines
- Type hints where beneficial
- Comprehensive docstrings
- Error handling with descriptive messages
- Virtual environment usage

## 🌐 Internationalization

### Language Support
- English (default): `en`
- Hebrew: `he` 
- Arabic: `ar`

### Implementation
- HTML `lang` attributes
- CSS logical properties for RTL support
- Separate translation files in `docs/i18n/`
- Browser locale detection with manual override

### Text Guidelines
- Clear, concise emergency communication
- Cultural sensitivity for international users
- Technical terms in local languages where appropriate

## 🧪 Testing Approach

### Website Testing
- **Browsers**: Chrome, Safari, Firefox, Edge (mobile versions)
- **Devices**: iOS, Android, various screen sizes
- **Connections**: Slow 3G simulation
- **Accessibility**: Screen readers, keyboard navigation
- **Print**: Tag layouts render correctly

### 3D Model Testing
- **Slicing**: BambuLab Studio compatibility
- **Materials**: PETG and ABS test prints
- **Fit**: NFC tags and QR code stickers
- **Durability**: Drop tests and wear simulation

### Script Testing
- **Python versions**: 3.8+
- **Operating systems**: Windows, macOS, Linux
- **Dependencies**: Minimal and well-tested
- **Output**: QR codes scan correctly

## 🔄 Git Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/description`: Individual features
- `hotfix/description`: Critical fixes

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

feat(docs): add WhatsApp contact button
fix(scripts): resolve QR code encoding issue
docs(readme): update installation instructions
style(css): improve mobile responsiveness
refactor(3d): optimize tag holder geometry
test(docs): add accessibility tests
chore(deps): update Python requirements
```

### Pull Request Process
1. Feature branch from `develop`
2. Implement with tests
3. Update documentation
4. Self-review checklist
5. Submit PR with description template
6. Address review feedback
7. Squash merge to `develop`

## 📋 Code Review Criteria

### Functionality
- [ ] Feature works as intended
- [ ] Edge cases handled appropriately
- [ ] Error handling implemented
- [ ] Performance considerations addressed

### Code Quality
- [ ] Follows project coding standards
- [ ] Adequate test coverage
- [ ] Documentation updated
- [ ] No security vulnerabilities

### User Experience
- [ ] Mobile-friendly implementation
- [ ] Accessible to disabled users
- [ ] Graceful degradation
- [ ] Cross-browser compatibility

## 🚀 Development Environment

### Required Tools
- **Git**: Version control
- **Python 3.8+**: Script development
- **Modern browser**: Testing
- **Text editor**: VS Code recommended

### Recommended Extensions (VS Code)
- Python extension
- Live Server for local testing
- Prettier for code formatting
- ESLint for JavaScript
- WAVE Web Accessibility Evaluator

### Local Setup
```bash
# Clone repository
git clone <repository-url>
cd luggage-recovery

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r scripts/requirements.txt

# Start local web server
cd docs
python -m http.server 8000
```

## 📊 Performance Requirements

### Website Performance
- **Load time**: <3 seconds on 3G
- **First contentful paint**: <1.5 seconds
- **Cumulative layout shift**: <0.1
- **Largest contentful paint**: <2.5 seconds

### 3D Model Requirements
- **Print time**: <2 hours per tag holder
- **Material usage**: <20g per holder
- **Support material**: Minimal or none
- **Post-processing**: Minimal cleanup required

### Script Performance
- **QR generation**: <1 second per code
- **Batch processing**: Handle 100+ tags efficiently
- **Memory usage**: <100MB for typical operations

## 🔒 Security Considerations

### Website Security
- No sensitive data storage
- HTTPS enforcement
- Content Security Policy headers
- Input sanitization for forms

### Script Security
- No hardcoded credentials
- Safe file handling practices
- Input validation for user data
- Secure random generation

## 📈 Deployment Strategy

### Website Deployment
- **Hosting**: GitHub Pages
- **Domain**: Custom domain with HTTPS
- **CDN**: GitHub's global CDN
- **Updates**: Automatic on push to main

### Release Process
1. Development in feature branches
2. Integration testing in develop
3. Release candidate creation
4. Final testing and documentation
5. Merge to main and tag release
6. GitHub Pages automatic deployment

## 🎨 Design System

### Color Palette
- **Primary**: Blue (#0066CC) - Trust and reliability
- **Secondary**: Green (#00AA44) - Success and recovery
- **Accent**: Orange (#FF6600) - Urgency and action
- **Neutral**: Gray scale for text and backgrounds

### Typography
- **Headlines**: System fonts for performance
- **Body**: Readable sans-serif
- **Code**: Monospace for technical content
- **Multi-language**: Unicode support for Hebrew/Arabic

### Spacing
- **Base unit**: 8px grid system
- **Touch targets**: Minimum 44px for mobile
- **Breakpoints**: 320px, 768px, 1024px, 1440px

## 🔍 Monitoring and Analytics

### Privacy-First Approach
- No user tracking or personal data collection
- Optional, anonymous usage statistics only
- GDPR compliance for EU users
- Clear privacy policy

### Error Monitoring
- Client-side error logging
- Performance monitoring
- Accessibility issue detection
- Regular security audits

---

*This guide evolves with the project. Suggest improvements through pull requests.*