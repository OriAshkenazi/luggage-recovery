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

The picker always offers English and Hebrew. Before a trip, set the destination's language in
`trip.json` to add a third button:

```json
{ "destination_language": "el" }
```

Available: `es` Spanish, `fr` French, `de` German, `it` Italian, `el` Greek, `ar` Arabic
(right-to-left). `null` shows English and Hebrew only. Commit and push; the page picks it up on
the next visit.

- English is always shown first; nothing is remembered between visits.
- Translations mirror the English element by element: same meaning, nothing added or dropped.
  Hebrew is gender-neutral: neutral spellings (מצאת, אליך), infinitives and nouns, never
  imperatives (השאר / השאירי).
- Pre-filled WhatsApp, SMS and email messages in a destination language include the English
  too, so the owner can read what the finder sends.
- Headlines size themselves from their column and the language's longest line
  (`--title-chars` in `style.css`), so each language keeps two lines from 320 px up.
- Assistant covers Latin and Hebrew; Greek and Arabic use the system font.
- The non-English translations were written without a native-speaker review; have one checked
  before relying on it.

To add a language: create `i18n/<code>.json` with the same keys as `en.json` (tests enforce it),
add `<code>` to `DESTINATIONS` (and `RTL` if needed) in `script.js`, and give it a
`--title-chars` value in `style.css`.

## Checks

`pytest tests/test_site.py` covers translation keys, static English, relative asset and
service-worker paths, the form's fallback, contact links and the light-only rule.
`python tools/contrast_check.py tokens/buttons.json` checks the colour pairs (WCAG AA).
