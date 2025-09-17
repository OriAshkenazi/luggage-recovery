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
        FORM_ENDPOINT: 'https://formspree.io/f/xdknzpko',
        DEFAULT_LANG: 'en',
        SUPPORTED_LANGUAGES: ['en', 'he'],
        STORAGE_KEY: 'luggage_recovery_preferences'
    };

    // Translation cache
    let translations = {};
    let currentLanguage = CONFIG.DEFAULT_LANG;

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
        }
    };

    // Translation System
    const I18n = {
        async init() {
            this.detectLanguage();
            await this.loadTranslation(currentLanguage);
            this.setupLanguageSwitcher();
            this.applyTranslations();
        },

        detectLanguage: function() {
            // NUCLEAR OPTION: Clear ALL storage to ensure English default
            try {
                localStorage.clear();
                sessionStorage.clear();
                
                // Also clear individual keys just to be sure
                ['preferred_language', 'luggage_recovery_preferences', 'language', 'lang'].forEach(key => {
                    localStorage.removeItem(key);
                    sessionStorage.removeItem(key);
                });
            } catch (e) {
                // Ignore storage errors
            }
            
            // Remove any URL lang parameter to prevent persistence
            const url = new URL(window.location);
            if (url.searchParams.has('lang')) {
                url.searchParams.delete('lang');
                window.history.replaceState({}, '', url);
            }
            
            // ALWAYS start with English, no exceptions
            currentLanguage = CONFIG.DEFAULT_LANG;
        },

        async loadTranslation(lang) {
            if (translations[lang]) {
                return translations[lang];
            }

            try {
                const response = await fetch(`i18n/${lang}.json`);
                if (!response.ok) {
                    throw new Error(`Failed to load ${lang}.json`);
                }
                translations[lang] = await response.json();
                return translations[lang];
            } catch (error) {
                console.warn(`Failed to load translation for ${lang}:`, error);
                if (lang !== CONFIG.DEFAULT_LANG) {
                    return await this.loadTranslation(CONFIG.DEFAULT_LANG);
                }
                return {};
            }
        },

        async setLanguage(lang) {
            if (!CONFIG.SUPPORTED_LANGUAGES.includes(lang)) {
                return;
            }

            currentLanguage = lang;
            await this.loadTranslation(lang);
            this.applyTranslations();
            this.updateHTMLLang(lang);
            this.updateActiveButton(lang);
            
            // Update contact button URLs for new language
            ContactEnhancer.enhanceContactButtons();
            
            // Do not store language preference OR URL parameter to ensure English always loads first
            // Remove URL parameter so refresh always goes back to English
            const url = new URL(window.location);
            url.searchParams.delete('lang');
            window.history.replaceState({}, '', url);
        },

        updateHTMLLang(lang) {
            document.documentElement.setAttribute('lang', lang);
            
            // Update RTL for Hebrew
            if (lang === 'he') {
                document.documentElement.setAttribute('dir', 'rtl');
            } else {
                document.documentElement.setAttribute('dir', 'ltr');
            }
        },

        updateActiveButton(lang) {
            const languageSelect = utils.$('#language-select');
            if (languageSelect) {
                languageSelect.value = lang;
            }
        },

        applyTranslations() {
            const currentTranslation = translations[currentLanguage] || {};
            
            // Apply text translations
            utils.$$('[data-i18n]').forEach(element => {
                const key = element.getAttribute('data-i18n');
                const translation = this.getNestedValue(currentTranslation, key);
                
                if (translation) {
                    if (element.tagName === 'INPUT' && element.type === 'submit') {
                        element.value = translation;
                    } else {
                        element.textContent = translation;
                    }
                }
            });

            // Apply placeholder translations
            utils.$$('[data-i18n-placeholder]').forEach(element => {
                const key = element.getAttribute('data-i18n-placeholder');
                const translation = this.getNestedValue(currentTranslation, key);
                
                if (translation) {
                    element.placeholder = translation;
                }
            });

            // Update page title
            const titleTranslation = this.getNestedValue(currentTranslation, 'page.title');
            if (titleTranslation) {
                document.title = titleTranslation;
            }
        },

        getNestedValue(obj, path) {
            return path.split('.').reduce((current, key) => {
                return current && current[key] !== undefined ? current[key] : null;
            }, obj);
        },

        setupLanguageSwitcher() {
            const languageSelect = utils.$('#language-select');

            if (languageSelect) {
                utils.on(languageSelect, 'change', async (e) => {
                    const lang = e.target.value;
                    await this.setLanguage(lang);
                });
            }
        }
    };

    // Enhanced contact button functionality
    const ContactEnhancer = {
        init: function() {
            this.enhanceWhatsAppButton();
            this.enhanceContactButtons();
        },

        enhanceContactButtons: function() {
            this.enhanceWhatsAppButton();
            this.enhanceSmsButton();
            this.enhanceEmailButton();
            this.addButtonInteractions();
        },

        enhanceWhatsAppButton: function() {
            const whatsappBtn = utils.$('.whatsapp-btn');
            if (!whatsappBtn) return;

            const tagId = utils.getUrlParam('id') || 'unknown';
            
            let message;
            if (currentLanguage === 'he') {
                message = encodeURIComponent(
                    `היי אורי, מצאתי את המזוודה שלך! 🧳\n\n` +
                    `מזהה תג: ${tagId}\n` +
                    `מצאתי אותה ב: [בבקשה תכתוב איפה]\n` +
                    `זמן: ${new Date().toLocaleString('he-IL')}\n\n` +
                    `איך אני יכול להחזיר לך אותה?`
                );
            } else {
                message = encodeURIComponent(
                    `Hi Ori, I found your luggage! 🧳\n\n` +
                    `Tag ID: ${tagId}\n` +
                    `Found at: [Please specify location]\n` +
                    `Time: ${new Date().toLocaleString()}\n\n` +
                    `How can I return it to you?`
                );
            }

            whatsappBtn.href = `https://wa.me/972509713042?text=${message}`;
        },

        enhanceSmsButton: function() {
            const smsBtn = utils.$('.sms-btn');
            if (!smsBtn) return;

            let message;
            if (currentLanguage === 'he') {
                message = encodeURIComponent('היי אורי, מצאתי את המזוודה שלך! איך אני יכול להחזיר לך אותה?');
            } else {
                message = encodeURIComponent('Hi Ori, I found your luggage! How can I return it to you?');
            }

            smsBtn.href = `sms:+972509713042?body=${message}`;
        },

        enhanceEmailButton: function() {
            const emailBtn = utils.$('.email-btn');
            if (!emailBtn) return;

            let subject, body;
            if (currentLanguage === 'he') {
                subject = encodeURIComponent('מצאתי את המזוודה שלך!');
                body = encodeURIComponent(
                    'היי אורי,\n\n' +
                    'מצאתי את המזוודה שלך! איך אני יכול להחזיר לך אותה?\n\n' +
                    'מיקום: \n' +
                    'זמן: \n\n' +
                    'תודה!'
                );
            } else {
                subject = encodeURIComponent('Found Your Luggage!');
                body = encodeURIComponent(
                    'Hi Ori,\n\n' +
                    'I found your luggage! How can I return it to you?\n\n' +
                    'Location: \n' +
                    'Time: \n\n' +
                    'Thank you!'
                );
            }

            emailBtn.href = `mailto:oriashkenazi93@gmail.com?subject=${subject}&body=${body}`;
        },

        addButtonInteractions: function() {
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
                });

                // Add keyboard support
                utils.on(button, 'keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        button.click();
                    }
                });
            });
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
                const errorMsg = currentLanguage === 'he' ? 'שדה חובה' : 'This field is required';
                this.showError(field, errorMsg);
                return false;
            }

            // Email validation
            if (fieldName === 'contact' && value && value.includes('@')) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(value)) {
                    const errorMsg = currentLanguage === 'he' ? 
                        'אנא הכנס כתובת אימייל תקינה' : 
                        'Please enter a valid email address';
                    this.showError(field, errorMsg);
                    return false;
                }
            }

            // Phone validation
            if (fieldName === 'contact' && value && /^\+?[\d\s\-\(\)]+$/.test(value)) {
                if (value.replace(/\D/g, '').length < 10) {
                    const errorMsg = currentLanguage === 'he' ? 
                        'אנא הכנס מספר טלפון תקין' : 
                        'Please enter a valid phone number';
                    this.showError(field, errorMsg);
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
            const originalText = submitBtn.innerHTML;
            
            // Show loading state
            submitBtn.disabled = true;
            const loadingText = currentLanguage === 'he' ? 'שולח...' : 'Sending...';
            submitBtn.innerHTML = `<span class="btn-icon">⏳</span> ${loadingText}`;
            utils.addClass(submitBtn, 'form-submit--loading');
            
            // Prepare form data
            const formData = new FormData(this.form);
            
            // Add metadata
            formData.append('_timestamp', new Date().toISOString());
            formData.append('_tag_id', utils.getUrlParam('id') || 'unknown');
            formData.append('_language', currentLanguage);
            
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
                const errorMsg = currentLanguage === 'he' ? 
                    'מצטער, הייתה שגיאה בשליחת ההודעה. אנא נסה להתקשר או לשלוח וואטסאפ במקום.' :
                    'Sorry, there was an error sending your message. Please try calling or WhatsApp instead.';
                this.showError(null, errorMsg);
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
            
            const successTitle = currentLanguage === 'he' ? 'ההודעה נשלחה בהצלחה!' : 'Message Sent Successfully!';
            const successMsg = currentLanguage === 'he' ? 'תודה! אחזור אליך בהקדם האפשרי.' : 'Thank you! I\'ll get back to you as soon as possible.';
            
            successDiv.innerHTML = `
                <div class="form-success-content">
                    <span class="success-icon">✅</span>
                    <h3>${successTitle}</h3>
                    <p>${successMsg}</p>
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

    // Initialize all enhancements when DOM is ready
    async function init() {
        // Check if DOM is ready
        if (document.readyState === 'loading') {
            utils.on(document, 'DOMContentLoaded', init);
            return;
        }

        // Initialize all modules
        try {
            await I18n.init();
            ContactEnhancer.init();
            FormEnhancer.init();
            
            console.log('Lost Luggage Recovery System - Enhanced version loaded');
        } catch (error) {
            console.error('Enhancement initialization error:', error);
        }
    }

    // Start initialization
    init();

})();