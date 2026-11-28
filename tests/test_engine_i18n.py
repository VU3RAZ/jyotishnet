# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine text in Hindi and Marathi (interface layer 3; jyotishnet_engine.i18n).

- Every template the engine writes (M("...") literals, the vocabulary, the names,
  summaries, notes and cited paraphrases in the rule files) is in both catalogues,
  with the same placeholders, written in Devanagari; no catalogue entry is unused.
- English output is unchanged by the templates (the engine's own tests check it).
- Localized results hold no English prose, keep the safety filter's rules, and
  name planets and signs as the web interface does (web/lib/vocab.ts).
"""
import ast
import re
import sys
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent / "golden"))
from jhora_parser import load_all  # noqa: E402

from jyotishnet_engine import BirthData, build_chart  # noqa: E402
from jyotishnet_engine.btr import check_events, event_rules, indicative_periods  # noqa: E402
from jyotishnet_engine.constants import GRAHA_NAMES, SIGNS  # noqa: E402
from jyotishnet_engine.i18n import Code, Join, M, catalogue, localize, vocabulary  # noqa: E402
from jyotishnet_engine.readings import BLOCKED_DEVA, reading, topics  # noqa: E402
from jyotishnet_engine.timeutil import zone_warnings  # noqa: E402
from jyotishnet_engine.yogas import YogaOptions, find_yogas, load_rules  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "src" / "jyotishnet_engine"
PLACEHOLDER = re.compile(r"\{(\w+)(?::[^}]*)?\}")
# Keys with no words to translate: verse references and codes only.
CODES_ONLY = re.compile(r"^[\sA-Z0-9.,;:()\-–]*$|^(BPHS|PD|Phaladeepika) [\d.\-, ;]+$")
DEVA = re.compile(r"[ऀ-ॿ]")


def _literal_keys() -> set[str]:
    keys = set()
    for p in [*ENGINE.glob("*.py"), ROOT / "src" / "jyotishnet_api" / "main.py"]:
        for node in ast.walk(ast.parse(p.read_text())):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("M", "Msg")
                    and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                keys.add(node.args[0].value)
    return keys


def _rule_keys() -> set[str]:
    keys = set()
    for r in load_rules():
        keys |= {r.name, r.summary}
    for t in topics().values():
        keys.add(t.theme or t.name[0].lower() + t.name[1:])
        if t.note:
            keys.add(t.note)
        for rules in t.house_rules.values():
            for part in rules.values():
                for v in part.values():
                    if isinstance(v, dict) and "cite" in v:
                        keys.add(v["cite"])
                    elif isinstance(v, dict):
                        keys |= {x["cite"] for x in v.values() if isinstance(x, dict) and "cite" in x}
    for r in yaml.safe_load((ENGINE / "rules" / "btr_classical.yaml").read_text(encoding="utf-8")):
        keys |= {c["cite"] for c in r.get("significators") or ()}
        if r.get("transit"):
            keys.add(r["transit"]["cite"])
    return keys


def _has_words(k: str) -> bool:
    return not CODES_ONLY.match(PLACEHOLDER.sub("", k))


def all_keys() -> set[str]:
    return _literal_keys() | _rule_keys() | set(vocabulary())


def keys() -> set[str]:
    """Templates that need an entry: those with words in them. The others (only
    placeholders, numbers and verse references) may have one, e.g. for the danda."""
    return {k for k in all_keys() if _has_words(k)}


def test_keys_found():
    k = keys()
    assert len(k) > 250 and "{p} is in {s}, the {h} house of D{v}." in k and "Gajakesari" in k


@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_catalogue_complete(lang):
    cat = catalogue(lang)
    missing = sorted(keys() - set(cat))
    assert not missing, f"{lang}: {len(missing)} missing, e.g. {missing[:8]}"
    unused = sorted(set(cat) - all_keys())
    assert not unused, f"{lang}: unused {unused[:8]}"


@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_placeholders_kept(lang):
    for en, tr in catalogue(lang).items():
        assert isinstance(tr, str) and tr.strip(), (lang, en)
        assert sorted(PLACEHOLDER.findall(en)) == sorted(PLACEHOLDER.findall(tr)), (lang, en, tr)
        assert DEVA.search(tr) or not _has_words(en), (lang, en, tr)


@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_vocabulary_matches_the_web_interface(lang):
    """Planet, sign and yoga names are those of web/lib/vocab.ts."""
    vocab = (ROOT / "web" / "lib" / "vocab.ts").read_text()
    cat = catalogue(lang)

    def table(name):
        body = re.search(rf"const {name}: Table = \{{(.*?)\n\}};", vocab, re.S).group(1)
        out = {}
        for m in re.finditer(r'(\w+): \{ hi: "([^"]+)"(?:, mr: "([^"]+)")? \}', body):
            out[m.group(1)] = m.group(3) if lang == "mr" and m.group(3) else m.group(2)
        return out

    graha = table("GRAHA")
    for code, en in GRAHA_NAMES.items():
        if code in graha:
            assert cat[en] == graha[code], (lang, en)
    deva = re.findall(r'"([^"]+)"', re.search(r"const SIGNS_DEVA = \[(.*?)\];", vocab, re.S).group(1))
    for en, dv in zip(SIGNS, deva):
        assert cat[en] == dv, (lang, en)
    yoga = table("YOGA")
    for r in load_rules():
        assert cat[r.name] == yoga[r.id], (lang, r.id, cat[r.name], yoga[r.id])


def test_msg_keeps_english_and_renders_from_values():
    m = M("{p} is in {s}, the {h} house of D{v}.", p=M("Mars"), s=M("Aries"), h=M("7th"), v=9)
    assert m == "Mars is in Aries, the 7th house of D9." and isinstance(m, str)
    assert m.render("hi") == "मंगल मेष राशि में है, D9 का सप्तम भाव।"
    assert m.render("mr") == "मंगळ मेष राशीत आहे, D9 चे सप्तम स्थान."
    assert Join(M(" and "), [Code("Ju"), Code("Mo")]) == "Ju and Mo"
    assert Join(M(" and "), [Code("Ju"), Code("Mo")]).render("mr") == "गुरु व चंद्र"
    assert M("{x} {r:.2f}", x=M("Mars"), r=1.234).render("hi") == "मंगल 1.23"   # no entry: values still localized
    assert localize({"a": [m, 1, "x"]}, "en") == {"a": ["Mars is in Aries, the 7th house of D9.", 1, "x"]}
    assert type(localize(m, "en")) is str
    ev = M("{who} in the 2nd from {ref}: {a}; in the 12th: {b}", who=M("benefics"), ref=M("Lagna"), a=Code("Ju"), b=Code("Ve"))
    assert ev.render("mr") == "लग्नापासून द्वितीय स्थानात शुभ ग्रह: गुरु; द्वादश स्थानात: शुक्र"
    assert M("{name} other than {ex}", name=M("benefics"), ex=Code("Mo")).render("mr") == "चंद्राव्यतिरिक्त शुभ ग्रह"


# ------------------------------------------------------------ localized results

PROSE = {"text", "reasons", "notes", "disclaimers", "reason", "tied", "evidence", "summary",
         "maha_links", "antar_links", "quality_reasons", "transit", "warnings"}
# What may stay Latin inside Hindi or Marathi text: varga names (D9), verse references,
# source names, Lagna degrees and dates, technical verifier details.
ALLOWED_LATIN = re.compile(r"\bD\d+\b|\b(BPHS|PD|Phaladeepika|Saravali|Jataka Parijata|Brihat Jataka|Hora Sara|"
                           r"Jagannatha Hora|Chamatkar Chintamani|Uttara Kalamrita|Mansagari|JHora|UTC|IST|ch|v|"
                           r"vv|deg|min)\b")


def _charts():
    return [c for c in load_all() if not c.name.startswith("edge_3")][:3]


def _results(b):
    out = {t: reading(b, t, date(2001, 6, 1)).to_dict() for t in topics()}
    ch = build_chart(b, vargas=[1])
    out["yogas"] = [asdict(y) for y in find_yogas(ch, include_absent=True)]
    out["yogas_sb"] = [asdict(y) for y in find_yogas(ch, include_absent=True,
                                                     options=YogaOptions("shadbala", "phaladeepika"), birth=b)]
    ev = [(e, date(b.local_datetime.year + 25 + i, 3, 1)) for i, e in enumerate(event_rules())]
    for rs in ("classical", "modern"):
        out["btr_" + rs] = [asdict(x) for x in check_events(b, ev, rule_set=rs)]
        out["ind_" + rs] = indicative_periods(b, rule_set=rs)
    return out


def _prose(obj, key=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "dropped":
                yield from (d["reason"] for d in v)
            elif k not in ("data", "source"):        # source: book titles stay as cited
                yield from _prose(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from _prose(v, key)
    elif isinstance(obj, str) and key in PROSE:
        yield obj


@pytest.mark.parametrize("lang", ["hi", "mr"])
@pytest.mark.parametrize("c", _charts(), ids=lambda c: c.name)
def test_localized_results_hold_no_english_prose(lang, c):
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours)
    res = localize(_results(b), lang)
    seen = 0
    for s in _prose(res):
        seen += 1
        rest = ALLOWED_LATIN.sub("", re.split(r"स्रोत:", s)[0])      # source: book titles stay as cited
        if s.startswith(("सत्यापक", "जाँचकर्ता", "तपासणी")):      # verifier details stay technical
            rest = rest.split(":", 1)[0]
        assert not re.search(r"[A-Za-z]{3,}", rest), (lang, s)
    assert seen > 200


@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_localized_sentences_pass_the_safety_filter(lang):
    c = _charts()[0]
    b = BirthData(c.local, c.latitude, c.longitude, utc_offset_hours=c.utc_offset_hours)
    for t in topics():
        for s in localize(reading(b, t, date(2001, 6, 1)).to_dict(), lang)["sentences"]:
            assert not any(rx.search(s["text"]) for rx, _ in BLOCKED_DEVA), s["text"]


def test_devanagari_safety_filter_blocks():
    from jyotishnet_engine.readings import safety
    for text in ("संतान योग से पुत्र का संकेत", "मृत्यु का समय", "अपघाताचा योग", "रोगाची शक्यता"):
        assert any(rx.search(text) for rx, _ in BLOCKED_DEVA), text
    assert safety(M("{x}", x=M("Mars"))) is None


@pytest.mark.parametrize("lang", ["hi", "mr"])
def test_localized_warnings(lang):
    for args in [(1950, 19.0, 72.8, 5.5), (1940, 22.5, 88.3, 5.5), (1900, 13.0, 80.2, 5.5), (1943, 28.6, 77.2, 5.5)]:
        ws = localize(zone_warnings(datetime(args[0], 5, 1, 10), *args[1:]), lang)
        assert ws and all(DEVA.search(w) for w in ws), ws
