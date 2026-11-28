# SPDX-License-Identifier: AGPL-3.0-or-later
"""The web interface's Hindi and Marathi catalogues cover every string it translates.

Keys are the English text inside t("...") and N("...") in web/ (lib/i18n.ts).
Only plain double-quoted literals count as keys, so the scan is exact.
"""
import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[1] / "web"
KEY = re.compile(r'\b[tN]\(\s*"((?:[^"\\]|\\.)*)"')
ENTRY = re.compile(r'^\s*"((?:[^"\\]|\\.)*)":\s*"((?:[^"\\]|\\.)*)",?\s*$')
PLACEHOLDER = re.compile(r"\{(\w+)\}")


def keys() -> dict[str, str]:
    found: dict[str, str] = {}
    for p in sorted([*WEB.glob("app/**/*.tsx"), *WEB.glob("components/**/*.tsx"), *WEB.glob("lib/*.ts")]):
        if p.name == "i18n.ts":
            continue
        for m in KEY.finditer(p.read_text()):
            found.setdefault(m.group(1), p.name)
    return found


def catalogue(lang: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (WEB / "lib" / "messages" / f"{lang}.ts").read_text().splitlines():
        m = ENTRY.match(line)
        if m:
            assert m.group(1) not in out, f"{lang}: duplicate key {m.group(1)!r}"
            out[m.group(1)] = m.group(2)
    return out


def test_keys_found():
    k = keys()
    assert len(k) > 200 and "Life events" in k and "Positions" in k


@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_catalogue_complete(lang):
    cat = catalogue(lang)
    missing = sorted(set(keys()) - set(cat))
    assert not missing, f"{lang}: {len(missing)} keys missing, e.g. {missing[:5]}"
    unused = sorted(set(cat) - set(keys()))
    assert not unused, f"{lang}: unused keys {unused[:5]}"


@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_placeholders_kept(lang):
    for en, tr in catalogue(lang).items():
        assert set(PLACEHOLDER.findall(en)) == set(PLACEHOLDER.findall(tr)), (lang, en, tr)
        assert tr.strip(), (lang, en)


@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_written_in_devanagari(lang):
    """Every entry has Devanagari in it, except labels that are only numbers or codes."""
    for en, tr in catalogue(lang).items():
        if re.search(r"[A-Za-z]{3,}", re.sub(r"\{\w+\}|BPHS|JHora|D\d+|UTC|YYYY-MM-DD|HH:MM(:SS)?|R1|AV|SAV|MT", "", en)):
            assert re.search(r"[ऀ-ॿ]", tr), (lang, en, tr)
