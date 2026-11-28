// SPDX-License-Identifier: AGPL-3.0-or-later
// Interface language (English, Hindi, Marathi). Layers 1 and 2: the Jyotish
// vocabulary (lib/vocab.ts) and the interface text (lib/messages/*.ts). Text the
// engine writes (reading drafts, reasons, yoga evidence) is still English.
//
// The English text is the key (gettext style): t("Life events") returns the
// Hindi or Marathi entry, or the English text when the catalogue has none.
// tests/test_web_i18n.py checks every t("…") key is in both catalogues.
//
// The language lives in the workbench's state; the workbench calls setLang()
// at the top of each render, so every component it renders reads the same
// language (no component is memoised).

import { HI } from "./messages/hi";
import { MR } from "./messages/mr";

export type Lang = "en" | "hi" | "mr";
export const LANGS: { id: Lang; label: string }[] = [
  { id: "en", label: "English" }, { id: "hi", label: "हिन्दी" }, { id: "mr", label: "मराठी" },
];
export const LANG_KEY = "jyotishnet.lang";

const CATALOGUES: Record<Lang, Record<string, string>> = { en: {}, hi: HI, mr: MR };
let current: Lang = "en";

export function setLang(l: Lang) { current = l; }
export function getLang(): Lang { return current; }
export function isLang(s: unknown): s is Lang { return s === "en" || s === "hi" || s === "mr"; }

/** Translate an interface string; {name} placeholders are filled from vars. */
export function t(key: string, vars?: Record<string, string | number>): string {
  const s = CATALOGUES[current][key] ?? key;
  return vars ? s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : s;
}

/** Pick per language, for the few strings whose grammar differs too much for a template. */
export function pick<T>(by: { en: T; hi?: T; mr?: T }): T {
  return by[current] ?? by.en;
}

/** Marks a string in a constant table as a catalogue key; translate it with t() where shown. */
export const N = (s: string) => s;
