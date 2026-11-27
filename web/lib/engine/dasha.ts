// SPDX-License-Identifier: AGPL-3.0-or-later
// Running Vimshottari periods (maha, antar, pratyantar) at a UTC moment: a port of
// src/jyotishnet_engine/dasha.py (vimshottari, YearClock with solar years, running),
// computing Julian days only for the periods the lookup visits.

import { isoUtc, jdUt, nakshatraOf, VIMSHOTTARI_LORDS, type EngineBirth } from "./chart.ts";
import { BODIES, pymod, Swe } from "./swe.ts";

const YEARS: Record<string, number> = { Ke: 7, Ve: 20, Su: 6, Mo: 10, Ma: 7, Ra: 18, Ju: 16, Sa: 19, Me: 17 };
const TOTAL = 120.0;
const SIDEREAL_YEAR_DAYS = 365.256363;
const SUN_MEAN_MOTION = 360.0 / SIDEREAL_YEAR_DAYS;

export type RunningPeriod = { lord: string; name: null; level: number; start: string; end: string };

class YearClock {
  private swe: Swe;
  private birthJd: number;
  private sun0: number;
  private cache = new Map<number, number>();
  constructor(swe: Swe, birthJd: number) {
    this.swe = swe;
    this.birthJd = birthJd;
    this.sun0 = this.sun(birthJd);
  }
  private sun(jd: number) { return pymod(this.swe.calc(jd, BODIES.Su, false)[0], 360.0); }
  jd(years: number): number {
    const key = Math.round(years * 1e12) / 1e12;
    const hit = this.cache.get(key);
    if (hit !== undefined) return hit;
    const target = 360.0 * years;
    let jd = this.birthJd + years * SIDEREAL_YEAR_DAYS;
    for (let i = 0; i < 6; i++) {
      const approx = (jd - this.birthJd) * SUN_MEAN_MOTION;
      const delta = pymod(this.sun(jd) - this.sun0 - approx + 180, 360) - 180;
      const err = target - (approx + delta);
      jd += err / SUN_MEAN_MOTION;
      if (Math.abs(err) < 1e-7) break;
    }
    this.cache.set(key, jd);
    return jd;
  }
}

type Span = { lord: string; idx: number; start: number; end: number };

function children(p: Span): Span[] {
  const span = p.end - p.start;
  let t = p.start;
  const out: Span[] = [];
  for (let i = 0; i < 9; i++) {
    const idx = (p.idx + i) % 9;
    const length = span * YEARS[VIMSHOTTARI_LORDS[idx]] / TOTAL;
    out.push({ lord: VIMSHOTTARI_LORDS[idx], idx, start: t, end: t + length });
    t += length;
  }
  return out;
}

/** The API's /v1/dasha "running" (vimshottari, levels 3) for a birth and a UTC Julian day. */
export function runningVimshottari(swe: Swe, birth: EngineBirth, atJd: number): RunningPeriod[] {
  const birthJd = jdUt(swe, birth);
  const moon = pymod(swe.calc(birthJd, BODIES.Mo)[0], 360.0);
  const nk = nakshatraOf(moon);
  const first = VIMSHOTTARI_LORDS.indexOf(nk.lord);
  const clock = new YearClock(swe, birthJd);
  const contains = (p: Span) => clock.jd(p.start) <= atJd && atJd < clock.jd(p.end);

  let level: Span[] = [];
  let t = -nk.fraction * YEARS[nk.lord];
  for (let i = 0; t < 120.0; i++) {
    const idx = (first + i) % 9;
    const lord = VIMSHOTTARI_LORDS[idx];
    level.push({ lord, idx, start: t, end: t + YEARS[lord] });
    t = t + YEARS[lord];
  }
  const out: RunningPeriod[] = [];
  for (let depth = 1; depth <= 3; depth++) {
    const hit = level.find(contains);
    if (!hit) break;
    out.push({ lord: hit.lord, name: null, level: depth,
      start: isoUtc(swe, clock.jd(hit.start)), end: isoUtc(swe, clock.jd(hit.end)) });
    level = depth < 3 ? children(hit) : [];
  }
  return out;
}
