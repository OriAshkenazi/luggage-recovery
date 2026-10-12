# Recovery page

The page a finder lands on after scanning the tag's QR code or tapping its NFC sticker.
Static, served by GitHub Pages from this folder at
`https://oriashkenazi.github.io/luggage-recovery/`. It uses the tag's look: safety yellow,
ink black, Assistant type.

## Files

- `index.html`: the whole page, in English. Works without JavaScript.
- `style.css`: mobile-first; tokens on `:root`; 768 px and 1024 px breakpoints; light only.
- `script.js`: Hebrew/English switch, localized pre-filled messages, form validation and
  in-page submit, service worker registration.
- `i18n/en.json`, `i18n/he.json`: every string; English must match the HTML (tested).
- `sw.js`: offline cache with paths relative to the site folder.
- `fonts/assistant.woff`: Assistant, subset to Latin and Hebrew (28 KB), self-hosted so finders'
  browsers never call a font CDN. License: `fonts/OFL.txt`.
- `favicon.svg`, `manifest.json`, `robots.txt`.

## Run locally

```bash
python -m http.server 8000 -d docs
# open http://localhost:8000/
```

## Contact methods

WhatsApp (primary), call, text message and email are plain links, so they work without
JavaScript. The script swaps in Hebrew pre-filled messages when Hebrew is selected. Update the
number or address in `index.html` and in `OWNER` at the top of `script.js`.

## Message form

The form posts to [Formspree](https://formspree.io) (`action` in `index.html`), which emails
each submission to the form owner's address. No server of our own.

- Without JavaScript: a normal POST; Formspree shows its own thank-you page.
- With JavaScript: required fields are checked inline, the form is sent with `fetch`
  (`Accept: application/json`) and the result is announced in place. On failure the page points
  the finder to WhatsApp, a call or email.
- `_gotcha` is Formspree's honeypot field for spam.

To change where messages go, create a form in the Formspree dashboard and replace the form id
in the `action` URL.

## Languages

Translations mirror the English element by element: same meaning, nothing added or dropped. Hebrew is gender-neutral: neutral spellings (מצאת, אליך), infinitives and nouns, never imperatives (השאר / השאירי).

English is always shown first; nothing is remembered between visits. Hebrew switches the page to
`dir="rtl"`, mirrors directional icons and drops letter-spacing and capitals. Add a language by
adding `i18n/<code>.json` with the same keys and a button in `.lang-switch`; add `<code>` to
`SUPPORTED` (and `RTL` if needed) in `script.js`.

## Checks

`pytest tests/test_site.py` covers translation keys, static English, relative asset and
service-worker paths, the form's fallback, contact links and the light-only rule.
`python tools/contrast_check.py tokens/buttons.json` checks the colour pairs (WCAG AA).
