/**
 * Lost Luggage Recovery System - Progressive Enhancement Script
 * This script enhances the user experience but the site works fully without it
 */

(function() {
    'use strict';

    // Check for basic JavaScript support
    if (!document.querySelector || !window.addEventListener) {
        return;
    }

    // Configuration
    const CONFIG = {
        FORM_ENDPOINT: 'https://formspree.io/f/YOUR_FORM_ID', // Replace with actual Formspree ID
        ANALYTICS_ID: '', // Optional: Add analytics ID
        DEFAULT_LANG: 'en',
        SUPPORTED_LANGUAGES: ['en', 'he'],
        STORAGE_KEY: 'luggage_recovery_preferences'
    };

    // Utility functions
    const utils = {
        // Get element safely
        $: function(selector, context) {
            return (context || document).querySelector(selector);
        },

        // Get all elements safely
        $$: function(selector, context) {
            return Array.from((context || document).querySelectorAll(selector));
        },

        // Add event listener with fallback
        on: function(element, event, handler) {
            if (element && element.addEventListener) {
                element.addEventListener(event, handler);
            }
        },

        // Remove class safely
        removeClass: function(element, className) {
            if (element && element.classList) {
                element.classList.remove(className);
            }
        },

        // Add class safely
        addClass: function(element, className) {
            if (element && element.classList) {
                element.classList.add(className);
            }
        },

        // Toggle class safely
        toggleClass: function(element, className) {
            if (element && element.classList) {
                element.classList.toggle(className);
            }
        },

        // Get/set localStorage safely
        storage: {
            get: function(key) {
                try {
                    return localStorage.getItem(key);
                } catch (e) {
                    return null;
                }
            },
            set: function(key, value) {
                try {
                    localStorage.setItem(key, value);
                    return true;
                } catch (e) {
                    return false;
                }
            }
        },

        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = function() {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Check if device is likely mobile
        isMobile: function() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
                   (window.innerWidth <= 768);
        },

        // Get URL parameters
        getUrlParam: function(param) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(param);
        },

        // Simple animation helper
        animate: function(element, property, from, to, duration) {
            if (!element || typeof element.style === 'undefined') return;
            
            const start = performance.now();
            const startValue = from;
            const change = to - from;
            
            function step(timestamp) {
                const progress = Math.min((timestamp - start) / duration, 1);
                const easeProgress = progress * (2 - progress); // ease-out
                
                element.style[property] = startValue + (change * easeProgress) + 'px';
                
                if (progress < 1) {
                    requestAnimationFrame(step);
                }
            }
            
            requestAnimationFrame(step);
        }
    };

    // Enhanced contact button functionality
    const ContactEnhancer = {
        init: function() {
            this.enhanceWhatsAppButton();
            this.enhanceContactButtons();
            this.addClickTracking();
        },

        enhanceWhatsAppButton: function() {
            const whatsappBtn = utils.$('.whatsapp-btn');
            if (!whatsappBtn) return;

            // Add enhanced WhatsApp URL with more context
            const currentUrl = window.location.href;
            const tagId = utils.getUrlParam('id') || 'unknown';
            const timestamp = new Date().toISOString();
            
            const enhancedMessage = encodeURIComponent(
                `Hi Ori, I found your luggage!\n\n` +
                `Tag ID: ${tagId}\n` +
                `Found at: [Please specify location]\n` +
                `Time: ${new Date().toLocaleString()}\n` +
                `Contact page: ${currentUrl}\n\n` +
                `Please let me know how to return it to you.`
            );

            const whatsappUrl = `https://wa.me/972509713042?text=${enhancedMessage}`;
            whatsappBtn.href = whatsappUrl;
        },

        enhanceContactButtons: function() {
            const buttons = utils.$$('.contact-btn');
            
            buttons.forEach(button => {
                // Add loading state functionality
                utils.on(button, 'click', function(e) {
                    // Add visual feedback
                    utils.addClass(button, 'contact-btn--loading');
                    
                    // Remove loading state after a delay
                    setTimeout(() => {
                        utils.removeClass(button, 'contact-btn--loading');
                    }, 1000);

                    // Track the click
                    ContactEnhancer.trackContactClick(button);
                });

                // Add keyboard support
                utils.on(button, 'keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        button.click();
                    }
                });
            });
        },

        addClickTracking: function() {
            // Simple analytics tracking (privacy-friendly)
            const trackingData = {
                timestamp: Date.now(),
                userAgent: navigator.userAgent,
                referrer: document.referrer,
                tagId: utils.getUrlParam('id')
            };

            // Store locally for potential debugging
            utils.storage.set('last_visit', JSON.stringify(trackingData));
        },

        trackContactClick: function(button) {
            const contactMethod = button.className.includes('whatsapp') ? 'whatsapp' :
                                 button.className.includes('sms') ? 'sms' :
                                 button.className.includes('email') ? 'email' :
                                 button.className.includes('call') ? 'call' : 'unknown';
            
            // Log for debugging (remove in production)
            console.log('Contact method used:', contactMethod);
            
            // Could send to analytics service here
            this.sendAnalytics('contact_click', { method: contactMethod });
        },

        sendAnalytics: function(event, data) {
            // Privacy-friendly analytics - only if user consents
            if (!CONFIG.ANALYTICS_ID) return;
            
            // Placeholder for analytics implementation
            console.log('Analytics event:', event, data);
        }
    };

    // Form enhancement
    const FormEnhancer = {
        init: function() {
            this.form = utils.$('.contact-form');
            if (!this.form) return;

            this.setupValidation();
            this.setupSubmission();
            this.setupAutoSave();
        },

        setupValidation: function() {
            const inputs = utils.$$('.form-input, .form-textarea', this.form);
            
            inputs.forEach(input => {
                utils.on(input, 'blur', () => this.validateField(input));
                utils.on(input, 'input', utils.debounce(() => this.clearError(input), 300));
            });

            utils.on(this.form, 'submit', (e) => this.handleSubmit(e));
        },

        validateField: function(field) {
            const value = field.value.trim();
            const fieldName = field.name;
            const isRequired = field.hasAttribute('required');
            
            // Clear previous errors
            this.clearError(field);
            
            // Required field validation
            if (isRequired && !value) {
                this.showError(field, 'This field is required');
                return false;
            }

            // Email validation
            if (fieldName === 'contact' && value && value.includes('@')) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(value)) {
                    this.showError(field, 'Please enter a valid email address');
                    return false;
                }
            }

            // Phone validation
            if (fieldName === 'contact' && value && /^\+?[\d\s\-\(\)]+$/.test(value)) {
                if (value.replace(/\D/g, '').length < 10) {
                    this.showError(field, 'Please enter a valid phone number');
                    return false;
                }
            }

            return true;
        },

        showError: function(field, message) {
            utils.addClass(field, 'form-input--error');
            
            // Remove existing error message
            const existingError = utils.$('.form-error', field.parentNode);
            if (existingError) {
                existingError.remove();
            }
            
            // Add error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'form-error';
            errorDiv.textContent = message;
            errorDiv.setAttribute('role', 'alert');
            
            field.parentNode.appendChild(errorDiv);
        },

        clearError: function(field) {
            utils.removeClass(field, 'form-input--error');
            const errorMsg = utils.$('.form-error', field.parentNode);
            if (errorMsg) {
                errorMsg.remove();
            }
        },

        handleSubmit: function(e) {
            e.preventDefault();
            
            // Validate all fields
            const inputs = utils.$$('.form-input, .form-textarea', this.form);
            let isValid = true;
            
            inputs.forEach(input => {
                if (!this.validateField(input)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                const firstError = utils.$('.form-input--error', this.form);
                if (firstError) {
                    firstError.focus();
                }
                return;
            }
            
            this.submitForm();
        },

        submitForm: function() {
            const submitBtn = utils.$('.form-submit', this.form);
            const originalText = submitBtn.textContent;
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="btn-icon">⏳</span> Sending...';
            utils.addClass(submitBtn, 'form-submit--loading');
            
            // Prepare form data
            const formData = new FormData(this.form);
            
            // Add metadata
            formData.append('_timestamp', new Date().toISOString());
            formData.append('_tag_id', utils.getUrlParam('id') || 'unknown');
            formData.append('_user_agent', navigator.userAgent);
            
            // Submit via fetch API
            fetch(this.form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    this.showSuccess();
                    this.clearForm();
                } else {
                    throw new Error('Network response was not ok');
                }
            })
            .catch(error => {
                console.error('Form submission error:', error);
                this.showError(null, 'Sorry, there was an error sending your message. Please try calling or WhatsApp instead.');
            })
            .finally(() => {
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                utils.removeClass(submitBtn, 'form-submit--loading');
            });
        },

        showSuccess: function() {
            const successDiv = document.createElement('div');
            successDiv.className = 'form-success';
            successDiv.innerHTML = `
                <div class="form-success-content">
                    <span class="success-icon">✅</span>
                    <h3>Message Sent Successfully!</h3>
                    <p>Thank you! I'll get back to you as soon as possible.</p>
                </div>
            `;
            successDiv.setAttribute('role', 'alert');
            successDiv.setAttribute('aria-live', 'polite');
            
            this.form.parentNode.insertBefore(successDiv, this.form);
            this.form.style.display = 'none';
            
            // Scroll to success message
            successDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        },

        setupAutoSave: function() {
            const inputs = utils.$$('.form-input, .form-textarea', this.form);
            
            inputs.forEach(input => {
                // Load saved data
                const savedValue = utils.storage.get(`form_${input.name}`);
                if (savedValue && !input.value) {
                    input.value = savedValue;
                }
                
                // Save on input
                utils.on(input, 'input', utils.debounce(() => {
                    utils.storage.set(`form_${input.name}`, input.value);
                }, 1000));
            });
        },

        clearForm: function() {
            const inputs = utils.$$('.form-input, .form-textarea', this.form);
            inputs.forEach(input => {
                input.value = '';
                utils.storage.set(`form_${input.name}`, '');
            });
        }
    };

    // Language support
    const LanguageManager = {
        init: function() {
            this.detectLanguage();
            this.setupLanguageSwitcher();
        },

        detectLanguage: function() {
            const urlLang = utils.getUrlParam('lang');
            const storedLang = utils.storage.get('preferred_language');
            
            // Default to English unless explicitly overridden by URL or stored preference
            let selectedLang = urlLang || storedLang || CONFIG.DEFAULT_LANG;
            
            if (!CONFIG.SUPPORTED_LANGUAGES.includes(selectedLang)) {
                selectedLang = CONFIG.DEFAULT_LANG;
            }
            
            this.setLanguage(selectedLang);
        },

        setLanguage: function(lang) {
            document.documentElement.setAttribute('lang', lang);
            
            // Update RTL for Hebrew
            if (lang === 'he') {
                document.documentElement.setAttribute('dir', 'rtl');
            } else {
                document.documentElement.setAttribute('dir', 'ltr');
            }
            
            // Update active language button
            utils.$$('.lang-btn').forEach(btn => {
                utils.removeClass(btn, 'lang-btn--active');
                if (btn.getAttribute('data-lang') === lang) {
                    utils.addClass(btn, 'lang-btn--active');
                }
            });
            
            // Store preference
            utils.storage.set('preferred_language', lang);
            
            // Load translations if available
            this.loadTranslations(lang);
        },

        loadTranslations: function(lang) {
            // For now, only English content is in the HTML
            // Hebrew/Arabic would require translation files to be loaded
            if (lang !== 'en') {
                console.log('Translation loading would happen here for:', lang);
                // Future: fetch(`/i18n/${lang}.json`) and update DOM
            }
        },

        setupLanguageSwitcher: function() {
            const langButtons = utils.$$('.lang-btn');
            
            langButtons.forEach(btn => {
                utils.on(btn, 'click', (e) => {
                    e.preventDefault();
                    const lang = btn.getAttribute('data-lang');
                    this.setLanguage(lang);
                    
                    // Update URL without reload
                    const url = new URL(window.location);
                    url.searchParams.set('lang', lang);
                    window.history.replaceState({}, '', url);
                });
            });
        }
    };

    // Performance monitoring
    const PerformanceMonitor = {
        init: function() {
            if (!window.performance) return;
            
            // Monitor Core Web Vitals
            this.measureCLS();
            this.measureFID();
            this.measureLCP();
            
            utils.on(window, 'load', () => {
                setTimeout(() => this.reportMetrics(), 1000);
            });
        },

        measureCLS: function() {
            // Cumulative Layout Shift measurement
            if (!('PerformanceObserver' in window)) return;
            
            try {
                const observer = new PerformanceObserver(list => {
                    for (const entry of list.getEntries()) {
                        if (!entry.hadRecentInput) {
                            this.cls = (this.cls || 0) + entry.value;
                        }
                    }
                });
                
                observer.observe({ type: 'layout-shift', buffered: true });
            } catch (e) {
                // Silently fail
            }
        },

        measureFID: function() {
            // First Input Delay measurement
            if (!('PerformanceObserver' in window)) return;
            
            try {
                const observer = new PerformanceObserver(list => {
                    for (const entry of list.getEntries()) {
                        this.fid = entry.processingStart - entry.startTime;
                        break; // Only report the first input
                    }
                });
                
                observer.observe({ type: 'first-input', buffered: true });
            } catch (e) {
                // Silently fail
            }
        },

        measureLCP: function() {
            // Largest Contentful Paint measurement
            if (!('PerformanceObserver' in window)) return;
            
            try {
                const observer = new PerformanceObserver(list => {
                    const entries = list.getEntries();
                    this.lcp = entries[entries.length - 1].startTime;
                });
                
                observer.observe({ type: 'largest-contentful-paint', buffered: true });
            } catch (e) {
                // Silently fail
            }
        },

        reportMetrics: function() {
            const metrics = {
                cls: this.cls || 0,
                fid: this.fid || 0,
                lcp: this.lcp || 0,
                loadTime: window.performance.timing.loadEventEnd - window.performance.timing.navigationStart,
                domComplete: window.performance.timing.domComplete - window.performance.timing.navigationStart
            };
            
            // Store metrics for debugging
            utils.storage.set('performance_metrics', JSON.stringify(metrics));
            
            // Log for debugging (remove in production)
            console.log('Performance metrics:', metrics);
        }
    };

    // Accessibility enhancements
    const AccessibilityEnhancer = {
        init: function() {
            this.setupSkipLink();
            this.setupKeyboardNavigation();
            this.setupScreenReaderEnhancements();
            this.setupFocusManagement();
        },

        setupSkipLink: function() {
            // Create skip link for screen readers
            const skipLink = document.createElement('a');
            skipLink.href = '#main';
            skipLink.className = 'skip-link';
            skipLink.textContent = 'Skip to main content';
            
            document.body.insertBefore(skipLink, document.body.firstChild);
            
            const main = utils.$('.main-content');
            if (main) {
                main.setAttribute('id', 'main');
            }
        },

        setupKeyboardNavigation: function() {
            // Enhanced keyboard navigation for buttons
            const focusableElements = utils.$$('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            
            focusableElements.forEach(element => {
                utils.on(element, 'keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        if (element.tagName === 'A' || element.tagName === 'BUTTON') {
                            // Let default behavior happen
                        }
                    }
                });
            });
        },

        setupScreenReaderEnhancements: function() {
            // Add screen reader friendly status updates
            const statusDiv = document.createElement('div');
            statusDiv.setAttribute('aria-live', 'polite');
            statusDiv.setAttribute('aria-atomic', 'true');
            statusDiv.className = 'sr-only';
            statusDiv.id = 'status-updates';
            document.body.appendChild(statusDiv);
        },

        setupFocusManagement: function() {
            // Ensure focus is visible and managed properly
            let focusOutlineEnabled = true;
            
            // Disable focus outline when using mouse
            utils.on(document, 'mousedown', () => {
                focusOutlineEnabled = false;
                document.body.classList.add('using-mouse');
            });
            
            // Re-enable focus outline when using keyboard
            utils.on(document, 'keydown', (e) => {
                if (e.key === 'Tab') {
                    focusOutlineEnabled = true;
                    document.body.classList.remove('using-mouse');
                }
            });
        },

        announceToScreenReader: function(message) {
            const statusDiv = utils.$('#status-updates');
            if (statusDiv) {
                statusDiv.textContent = message;
                
                // Clear after 3 seconds
                setTimeout(() => {
                    statusDiv.textContent = '';
                }, 3000);
            }
        }
    };

    // Initialize all enhancements when DOM is ready
    function init() {
        // Check if DOM is ready
        if (document.readyState === 'loading') {
            utils.on(document, 'DOMContentLoaded', init);
            return;
        }

        // Initialize all modules
        try {
            ContactEnhancer.init();
            FormEnhancer.init();
            LanguageManager.init();
            AccessibilityEnhancer.init();
            PerformanceMonitor.init();
            
            console.log('Lost Luggage Recovery System - Enhanced version loaded');
        } catch (error) {
            console.error('Enhancement initialization error:', error);
        }
    }

    // Start initialization
    init();

    // Export for debugging (remove in production)
    window.LuggageRecovery = {
        ContactEnhancer,
        FormEnhancer,
        LanguageManager,
        AccessibilityEnhancer,
        PerformanceMonitor,
        utils
    };

})();