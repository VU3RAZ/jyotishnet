# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Engine text in Hindi and Marathi (interface layer 3).

Text the engine writes (reading drafts, reasons, facts, yoga evidence, rectification
reasons, birth-record warnings) is built from templates. A `Msg` is a `str` holding
the English text, so the engine, the verifier, the safety filter and the tests work
on English exactly as before; it also keeps its template and arguments, so the API
can write the same message in another language from the same values
(`localize(result, "hi")`). Nothing is ever translated from finished English text.

Catalogues: locales/hi.yaml and locales/mr.yaml, keyed by the English template
(gettext style, as the web interface's catalogues). tests/test_engine_i18n.py
checks every template with words in it is in both catalogues, with the same
placeholders. Draft wording, for the
Jyotish reviewer.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import yaml

LANGS = ("en", "hi", "mr")
LOCALES = Path(__file__).parent / "locales"


@lru_cache(maxsize=None)
def catalogue(lang: str) -> dict[str, str]:
    if lang == "en":
        return {}
    return yaml.safe_load((LOCALES / f"{lang}.yaml").read_text(encoding="utf-8")) or {}


def render(v, lang: str):
    """A message in `lang`; anything that is not a Msg is returned unchanged."""
    return v.render(lang) if isinstance(v, Msg) else v


class Msg(str):
    """English text that remembers its template and arguments.

    Msg("{p} is in {s}.", p=graha("Su"), s=sign(0)) == "Sun is in Aries."
    Arguments that are Msg are rendered in the same language; numbers and plain
    strings (dates, verse numbers, codes) are kept, with any format spec.
    """

    tpl: str
    args: dict

    def __new__(cls, tpl: str, /, **args):
        obj = str.__new__(cls, tpl.format(**args) if args else tpl)
        obj.tpl, obj.args = tpl, args
        return obj

    def render(self, lang: str) -> str:
        if lang == "en":
            return str(self)
        # A template with no entry (only placeholders and numbers, or missing) keeps its
        # English wording; its arguments are still written in `lang`.
        tr = catalogue(lang).get(self.tpl, self.tpl)
        out = tr.format(**{k: render(v, lang) for k, v in self.args.items()}) if self.args else tr
        return _mr_join(out) if lang == "mr" else out

    # Immutable, like str: copies (dataclasses.asdict) keep the template.
    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __reduce__(self):
        return (str, (str(self),))


class Join(Msg):
    """Items joined by a separator, each rendered in the language asked for."""

    def __new__(cls, sep: str, items: Iterable):
        items = list(items)
        obj = str.__new__(cls, str(sep).join(items))
        obj.tpl, obj.args, obj.sep, obj.items = "", {}, sep, items
        return obj

    def render(self, lang: str) -> str:
        return render(self.sep, lang).join(str(render(i, lang)) for i in self.items)


class Code(Msg):
    """A planet code ("Su") that stays a code in English and is a name elsewhere."""

    def __new__(cls, code: str):
        obj = str.__new__(cls, code)
        obj.tpl, obj.args, obj.code = code, {}, code
        return obj

    def render(self, lang: str) -> str:
        return str(self) if lang == "en" else graha(self.code).render(lang)


M = Msg

# Marathi joins a postposition to the noun in its oblique form: लग्न पासून -> लग्नापासून,
# गुरु सोबत -> गुरूसोबत. Templates write the postposition apart after a name argument.
_MR_OBLIQUE = {"लग्न": "लग्ना", "चंद्र": "चंद्रा", "रवि": "रवी", "मंगळ": "मंगळा", "बुध": "बुधा",
               "गुरु": "गुरू", "शुक्र": "शुक्रा", "शनि": "शनी", "राहू": "राहू", "केतू": "केतू"}
_MR_POST = re.compile(r"(?<![\u0900-\u097F])(" + "|".join(_MR_OBLIQUE) + r") (पासून|सोबत|व्यतिरिक्त)(?![\u0900-\u097F])")


def _mr_join(text: str) -> str:
    return _MR_POST.sub(lambda m: _MR_OBLIQUE[m.group(1)] + m.group(2), text)

# ------------------------------------------------------------------ vocabulary
# Names are messages keyed by their English spelling; test_engine_i18n.py checks
# they match the web interface's vocabulary (web/lib/vocab.ts).


def graha(p: str) -> Msg:
    from .constants import GRAHA_NAMES
    return Msg(GRAHA_NAMES.get(p, p))


def sign(i: int) -> Msg:
    from .constants import SIGNS
    return Msg(SIGNS[i])


def ordinal(n: int) -> Msg:
    """"7th"; Hindi and Marathi use the Sanskrit ordinals (सप्तम) for houses 1-12."""
    if 1 <= n <= 12:
        return Msg({1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th"))
    return Msg("{n}th", n=n)


def vocabulary() -> list[str]:
    """Keys the engine builds from data rather than literals (checked by the tests)."""
    from .constants import GRAHA_NAMES, SIGNS
    return [*GRAHA_NAMES.values(), *SIGNS, *(str(ordinal(n)) for n in range(1, 13)), "{n}th"]


# ------------------------------------------------------------------------- API

def localize(obj, lang: str):
    """A result (dicts, lists, Msg) with every Msg written in `lang` as plain str."""
    if isinstance(obj, Msg):
        return obj.render(lang)
    if isinstance(obj, dict):
        return {k: localize(v, lang) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [localize(v, lang) for v in obj]
    return obj
