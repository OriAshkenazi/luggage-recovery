"""Recovery page (docs/): translations, local assets, and the GitHub Pages pitfalls."""

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

DOCS = Path(__file__).resolve().parents[1] / "docs"


def _html():
    return BeautifulSoup((DOCS / "index.html").read_text(encoding="utf-8"), "html.parser")


def _lookup(data, key):
    for part in key.split("."):
        data = data[part]
    return data


def _keys(d, prefix=""):
    out = set()
    for k, v in d.items():
        out |= _keys(v, prefix + k + ".") if isinstance(v, dict) else {prefix + k}
    return out


def _langs():
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((DOCS / "i18n").glob("*.json"))}


def test_languages_have_identical_keys():
    langs = _langs()
    for code, data in langs.items():
        assert _keys(data) == _keys(langs["en"]), code


def test_trip_language_is_configurable_and_valid():
    script = (DOCS / "script.js").read_text()
    destinations = json.loads(re.search(r"var DESTINATIONS = (\[[^\]]*\])", script).group(1).replace("'", '"'))
    assert set(destinations) | {"en", "he"} == set(_langs())  # every offered language has a file
    trip = json.loads((DOCS / "trip.json").read_text())
    assert trip["destination_language"] in destinations + [None]
    for code in ("he", "ar"):
        assert f"{code}: true" in script  # right-to-left
    for code, data in _langs().items():
        assert data["lang"]["short"] and data["lang"]["name"], code
        # Messages Ori receives stay readable: other languages carry the English too
        if code not in ("en", "he"):
            assert "I found your luggage" in data["messages"]["greeting"], code


def test_every_i18n_key_exists_in_both_languages():
    doc = _html()
    keys = set()
    for attr in ("data-i18n", "data-i18n-html", "data-i18n-placeholder", "data-i18n-aria"):
        keys |= {el[attr] for el in doc.select(f"[{attr}]")}
    keys |= {"messages.greeting", "messages.email_subject", "messages.email_body", "form.required", "form.sent", "form.failed"}
    for lang in ("en", "he"):
        data = json.loads((DOCS / "i18n" / f"{lang}.json").read_text(encoding="utf-8"))
        for key in sorted(keys):
            assert isinstance(_lookup(data, key), str), f"{lang}: {key}"


def test_static_english_matches_en_json():
    """Without JavaScript the page shows the HTML text, so it must equal the English strings."""
    en = _langs()["en"]
    for el in _html().select("[data-i18n]"):
        if el.name == "title":
            continue
        assert el.get_text() == _lookup(en, el["data-i18n"]), el["data-i18n"]


def test_local_assets_exist_and_paths_are_relative():
    doc = _html()
    refs = [el.get("href") for el in doc.select("link[href]")] + [el.get("src") for el in doc.select("script[src]")]
    manifest = json.loads((DOCS / "manifest.json").read_text())
    refs += [icon["src"] for icon in manifest["icons"]]
    for ref in refs:
        url = urlparse(ref)
        if url.scheme:
            continue
        # GitHub Pages serves the site under /luggage-recovery/: root-absolute paths break
        assert not ref.startswith("/"), ref
        assert (DOCS / url.path).exists(), ref


def test_service_worker_precache_is_relative_and_present():
    sw = (DOCS / "sw.js").read_text()
    block = re.search(r"PRECACHE = \[(.*?)\]", sw, re.S).group(1)
    entries = re.findall(r"'([^']+)'", block)
    assert entries
    for entry in entries:
        assert not entry.startswith("/"), entry
        if entry != "./":
            assert (DOCS / urlparse(entry).path).exists(), entry
    assert "navigator.serviceWorker.register('sw.js')" in (DOCS / "script.js").read_text()


def test_script_does_not_wipe_storage():
    # localStorage is shared by every page on oriashkenazi.github.io
    assert "localStorage.clear" not in (DOCS / "script.js").read_text()


def test_form_posts_to_formspree_and_works_without_js():
    form = _html().select_one("form.form")
    assert form["method"].upper() == "POST"
    assert form["action"].startswith("https://formspree.io/f/")
    names = {el["name"] for el in form.select("[name]")}
    assert {"name", "contact", "location", "message", "_gotcha"} <= names
    for field in form.select("input[required], textarea[required]"):
        assert form.select_one(f'label[for="{field["id"]}"]'), field["id"]


def test_contact_links_and_touch_targets():
    doc = _html()
    hrefs = {a["data-contact"]: a["href"] for a in doc.select("[data-contact]")}
    assert hrefs["whatsapp"].startswith("https://wa.me/")
    assert hrefs["call"].startswith("tel:+")
    assert hrefs["sms"].startswith("sms:+")
    assert hrefs["email"].startswith("mailto:")
    css = (DOCS / "style.css").read_text()
    assert "--touch: 44px" in css


def test_light_only():
    for path in DOCS.rglob("*"):
        if path.suffix in {".css", ".js", ".html"}:
            assert "prefers-color-scheme" not in path.read_text(encoding="utf-8"), path


def test_static_english_html_strings_match_en_json():
    en = json.loads((DOCS / "i18n" / "en.json").read_text(encoding="utf-8"))
    for el in _html().select("[data-i18n-html]"):
        rendered = el.decode_contents().replace("<br/>", "<br>")
        assert rendered == _lookup(en, el["data-i18n-html"]), el["data-i18n-html"]


def test_hebrew_avoids_gendered_imperatives():
    """Hebrew copy stays gender-neutral. Past-tense 2nd person (מצאת, סרקת) is spelled the same
    for everyone; imperatives are not (השאר / השאירי), so use infinitives or nouns instead."""
    text = (DOCS / "i18n" / "he.json").read_text(encoding="utf-8")
    for word in ("השאר ", "שלח ", "התקשר", "צור קשר", "לחץ", "כתוב", "ספר "):
        assert word not in text, word
