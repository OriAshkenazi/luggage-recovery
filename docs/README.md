# Lost Luggage Recovery Website

Mobile-first contact website for lost luggage recovery system.

## 🎯 Purpose

This website serves as the landing page when someone scans a QR code or NFC tag on lost luggage. It provides multiple ways to contact the luggage owner quickly and easily.

## 🏗️ Architecture

- **Static Site**: No server required, works on GitHub Pages
- **Progressive Enhancement**: Core functionality works without JavaScript
- **Mobile-First**: Optimized for phone usage in stressful situations
- **Offline Capable**: Service worker caches essential content

## 📁 Files

- `index.html` - Main contact page with semantic HTML
- `style.css` - Mobile-first CSS with accessibility features
- `script.js` - Progressive enhancement JavaScript
- `sw.js` - Service worker for offline functionality
- `manifest.json` - PWA manifest for app-like experience
- `robots.txt` - SEO configuration

## 🚀 Quick Start

### Local Development

1. **Start local server:**
   ```bash
   cd website
   python -m http.server 8000
   ```

2. **Open browser:**
   ```
   http://localhost:8000
   ```

### GitHub Pages Deployment

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add website files"
   git push origin main
   ```

2. **Enable GitHub Pages:**
   - Go to repository Settings
   - Navigate to Pages section
   - Set source to "Deploy from a branch"
   - Select "main" branch and "/website" folder
   - Save settings

3. **Configure custom domain (optional):**
   - Add CNAME file with your domain
   - Configure DNS records

## 🎨 Customization

### Contact Information

Update contact details in `index.html`:

```html
<!-- WhatsApp -->
<a href="https://wa.me/972509713042?text=...">

<!-- SMS -->
<a href="sms:+972509713042?body=...">

<!-- Email -->
<a href="mailto:oriashkenazi93@gmail.com?subject=...">
```

### Form Handler

Replace Formspree endpoint in both `index.html` and `script.js`:

```html
<form action="https://formspree.io/f/YOUR_FORM_ID">
```

```javascript
FORM_ENDPOINT: 'https://formspree.io/f/YOUR_FORM_ID'
```

### Colors and Branding

Modify CSS custom properties in `style.css`:

```css
:root {
    --color-primary: #0066CC;    /* Main brand color */
    --color-secondary: #00AA44;  /* Success/WhatsApp green */
    --color-accent: #FF6600;     /* Urgent/call to action */
}
```

### Theme Policy

This site is light-only. Dark mode is not supported, and automatic theme switching is disabled. The CSS sets `:root { color-scheme: light; }` and the HTML includes `<meta name="color-scheme" content="light">`.

## 🌐 Multi-Language Support

The website supports English, Hebrew, and Arabic:

### Adding Translations

1. Create language files in `i18n/` directory:
   ```
   i18n/
   ├── en.json
   ├── he.json
   └── ar.json
   ```

2. Add translation keys to JSON files:
   ```json
   {
     "hero.title": "You Found My Luggage!",
     "hero.subtitle": "Thank you for being honest and helpful!"
   }
   ```

3. Update JavaScript to load translations:
   ```javascript
   // Language loading logic in script.js
   ```

### RTL Support

Hebrew and Arabic automatically get RTL layout via CSS:

```css
[dir="rtl"] {
    /* RTL-specific styles */
}
```

## 📱 Features

### Progressive Web App (PWA)

- **Offline Access**: Cached with service worker
- **Add to Home Screen**: Installable on mobile devices
- **Fast Loading**: Critical resources cached locally

### Accessibility

- **WCAG 2.1 AA Compliance**: Screen reader compatible
- **Keyboard Navigation**: Full functionality without mouse
- **High Contrast**: Meets accessibility color requirements
- **Focus Management**: Clear visual focus indicators

### Performance

- **Core Web Vitals Optimized**: LCP, FID, CLS targets met
- **Mobile-First**: Under 100KB total size
- **Critical CSS**: Inlined critical rendering path styles
- **Service Worker**: Offline functionality and fast repeat visits

## 🧪 Testing

### Manual Testing Checklist

- [ ] **Mobile Devices**: iOS and Android phones
- [ ] **Contact Methods**: All buttons work correctly
- [ ] **Form Submission**: Form sends and shows confirmation
- [ ] **Offline Mode**: Core content accessible without internet
- [ ] **Screen Readers**: VoiceOver/TalkBack compatibility
- [ ] **Keyboard Navigation**: Tab through all interactive elements

### Performance Testing

Run Lighthouse audit:
```bash
npx lighthouse http://localhost:8000 --view
```

Target scores:
- Performance: >90
- Accessibility: 100
- Best Practices: >90
- SEO: >90

### Browser Testing

Test in major browsers:
- Chrome (Android)
- Safari (iOS)
- Firefox
- Edge

## 🔧 Troubleshooting

### Common Issues

**Contact buttons not working:**
- Check phone number format (+972509713042)
- Verify URL encoding in href attributes
- Test on actual mobile device

**Form not submitting:**
- Confirm Formspree endpoint is correct
- Check browser console for JavaScript errors
- Verify internet connection

**Styles not loading:**
- Check CSS file path is correct
- Clear browser cache
- Verify file permissions

**Service worker not registering:**
- Ensure HTTPS (required for service workers)
- Check browser developer tools console
- Clear application cache and reload

### Performance Issues

**Slow loading:**
- Optimize images (use WebP format)
- Minify CSS and JavaScript
- Check network connection

**Poor mobile experience:**
- Test on actual devices, not just browser dev tools
- Check touch target sizes (minimum 44px)
- Verify viewport meta tag is correct

## 📊 Analytics

### Privacy-First Approach

- No personal data collection
- No tracking cookies
- Anonymous usage statistics only

### Metrics to Monitor

- **Contact Success Rate**: Which methods are used most
- **Load Performance**: Core Web Vitals scores
- **Error Rates**: JavaScript errors, failed requests
- **Accessibility Issues**: Screen reader compatibility

### Setup Analytics (Optional)

1. Add analytics ID to `script.js`:
   ```javascript
   ANALYTICS_ID: 'YOUR_ANALYTICS_ID'
   ```

2. Implement privacy-compliant tracking
3. Add cookie consent if required by jurisdiction

## 🔒 Security

### Best Practices Implemented

- **HTTPS Only**: All external requests use HTTPS
- **Content Security Policy**: XSS protection headers
- **Input Sanitization**: Form inputs validated
- **No Sensitive Data**: No personal info stored locally

### Maintenance

- Regularly update dependencies
- Monitor for security advisories
- Test contact methods periodically
- Update contact information as needed

## 📈 Future Enhancements

### Planned Features

- [ ] **GPS Integration**: Automatic location detection
- [ ] **Photo Upload**: Allow finder to send pictures
- [ ] **Real-time Chat**: WebRTC video/audio calling
- [ ] **Reward System**: Cryptocurrency micro-payments
- [ ] **Airlines Integration**: Direct reporting to lost & found

### Technical Improvements

- [ ] **WebP Images**: Better image compression
- [ ] **HTTP/2 Push**: Faster resource loading
- [ ] **CDN Integration**: Global content delivery
- [ ] **A/B Testing**: Optimize contact conversion rates

---

For technical issues or contributions, see the main project documentation.
