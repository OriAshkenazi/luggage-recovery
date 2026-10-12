/**
 * Lost Luggage Recovery: progressive enhancement.
 * The page works without this script (English, plain links, a normal form POST).
 * With it: Hebrew/English switching, localized pre-filled messages, inline form
 * validation, an in-page submit, and offline caching.
 */
(function () {
    'use strict';

    if (!document.querySelector || !window.fetch) return;

    var OWNER = { phone: '972509713042', email: 'oriashkenazi93@gmail.com' };
    var SUPPORTED = ['en', 'he'];
    var RTL = { he: true };
    var strings = {};
    var lang = 'en';

    function $(sel, ctx) { return (ctx || document).querySelector(sel); }
    function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

    function t(key) {
        var value = key.split('.').reduce(function (obj, k) { return obj && obj[k]; }, strings[lang]);
        return typeof value === 'string' ? value : null;
    }

    // ------------------------------------------------------------ language

    function load(code) {
        if (strings[code]) return Promise.resolve(strings[code]);
        return fetch('i18n/' + code + '.json').then(function (res) {
            if (!res.ok) throw new Error('Missing translation: ' + code);
            return res.json();
        }).then(function (data) {
            strings[code] = data;
            return data;
        });
    }

    function applyLanguage() {
        var root = document.documentElement;
        root.lang = lang;
        root.dir = RTL[lang] ? 'rtl' : 'ltr';

        $$('[data-i18n]').forEach(function (el) {
            var value = t(el.getAttribute('data-i18n'));
            if (value !== null) el.textContent = value;
        });
        // Only our own translation files feed this; it carries <br> line breaks.
        $$('[data-i18n-html]').forEach(function (el) {
            var value = t(el.getAttribute('data-i18n-html'));
            if (value !== null) el.innerHTML = value;
        });
        $$('[data-i18n-placeholder]').forEach(function (el) {
            var value = t(el.getAttribute('data-i18n-placeholder'));
            if (value !== null) el.setAttribute('placeholder', value);
        });
        $$('[data-i18n-aria]').forEach(function (el) {
            var value = t(el.getAttribute('data-i18n-aria'));
            if (value !== null) el.setAttribute('aria-label', value);
        });
        $$('.lang-switch__btn').forEach(function (btn) {
            btn.setAttribute('aria-pressed', String(btn.getAttribute('data-lang') === lang));
        });
        updateContactLinks();
    }

    function setLanguage(code) {
        if (SUPPORTED.indexOf(code) === -1) return;
        load(code).then(function () {
            lang = code;
            applyLanguage();
        }).catch(function (err) {
            console.warn(err);
        });
    }

    // ------------------------------------------------------------ pre-filled messages

    function updateContactLinks() {
        var greeting = t('messages.greeting');
        if (!greeting) return;
        var wa = $('[data-contact="whatsapp"]');
        var sms = $('[data-contact="sms"]');
        var mail = $('[data-contact="email"]');
        if (wa) wa.href = 'https://wa.me/' + OWNER.phone + '?text=' + encodeURIComponent(greeting);
        if (sms) sms.href = 'sms:+' + OWNER.phone + '?body=' + encodeURIComponent(greeting);
        if (mail) {
            mail.href = 'mailto:' + OWNER.email +
                '?subject=' + encodeURIComponent(t('messages.email_subject') || '') +
                '&body=' + encodeURIComponent(t('messages.email_body') || greeting);
        }
    }

    // ------------------------------------------------------------ form

    function setError(field, message) {
        var error = document.getElementById(field.id + '-error');
        field.setAttribute('aria-invalid', message ? 'true' : 'false');
        if (!error) return;
        if (message) {
            error.textContent = message;
            error.hidden = false;
            field.setAttribute('aria-describedby', error.id);
        } else {
            error.hidden = true;
            field.removeAttribute('aria-describedby');
        }
    }

    function validate(field) {
        var ok = !field.required || field.value.trim() !== '';
        setError(field, ok ? '' : (t('form.required') || 'This field is required'));
        return ok;
    }

    function setStatus(form, kind, message) {
        var status = $('.form__status', form);
        status.className = 'form__status form__status--' + kind;
        status.textContent = message;
        status.hidden = false;
    }

    function initForm() {
        var form = $('.form');
        if (!form) return;
        var fields = $$('.field__input', form);

        fields.forEach(function (field) {
            field.addEventListener('blur', function () { if (field.value) validate(field); });
            field.addEventListener('input', function () {
                if (field.getAttribute('aria-invalid') === 'true') validate(field);
            });
        });

        form.addEventListener('submit', function (event) {
            event.preventDefault();
            var invalid = fields.filter(function (f) { return !validate(f); });
            if (invalid.length) {
                invalid[0].focus();
                return;
            }
            var button = $('button[type="submit"]', form);
            button.disabled = true;
            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: { Accept: 'application/json' }
            }).then(function (res) {
                if (!res.ok) throw new Error('HTTP ' + res.status);
                form.reset();
                setStatus(form, 'ok', t('form.sent') || 'Thank you! Your message was sent.');
            }).catch(function () {
                setStatus(form, 'error', t('form.failed') || 'Sending failed. Please use WhatsApp, a call or email above.');
            }).then(function () {
                button.disabled = false;
            });
        });
    }

    // ------------------------------------------------------------ start

    function init() {
        $$('.lang-switch__btn').forEach(function (btn) {
            btn.addEventListener('click', function () { setLanguage(btn.getAttribute('data-lang')); });
        });
        // English always loads first and no language choice is stored between visits.
        load('en').catch(function () {});
        initForm();

        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function () {
                navigator.serviceWorker.register('sw.js').catch(function () {});
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
