// SPDX-License-Identifier: AGPL-3.0-or-later
// Port of src/jyotishnet_engine/boundaries.py boundary_map, as /v1/boundaries returns
// it (changes only; the ribbon does not use segments).

import { isoUtc, jdUt, nakshatraOf, vargaSign, type EngineBirth } from "./chart.ts";
import { BODIES, pyfloordiv, pymod, SE_CALC_RISE, Swe } from "./swe.ts";

const MIN_PER_DAY = 1440.0;
type Value = number | [number, number];
export type Change = { key: string; offset_min: number; utc: string; before: Value; after: Value };

function previousSunrise(swe: Swe, jd: number, lat: number, lon: number, alt: number): number {
  let rise = swe.sunEvent(jd - 1.0, lat, lon, alt, SE_CALC_RISE);
  if (rise === null) throw new Error("No sunrise found (polar day or night at this latitude).");
  for (;;) {
    const next = swe.sunEvent(rise + 0.01, lat, lon, alt, SE_CALC_RISE);
    if (next === null || next > jd) break;
    rise = next;
  }
  return rise;
}

const signOf = (x: number) => Math.trunc(pyfloordiv(pymod(x, 360), 30));
/** Python's round(x, 4), close enough for display (it is not used in comparisons). */
const round4 = (x: number) => Math.round(x * 1e4) / 1e4;

export function boundaryMap(swe: Swe, birth: EngineBirth, windowMin: number, stepS: number,
  vargas: number[], precisionS = 1.0): Change[] {
  const jd0 = jdUt(swe, birth);
  const lat = birth.latitude, lon = birth.longitude, alt = birth.altitude_m ?? 0.0;
  const riseCache = new Map<number, [number, number]>();
  const bodyLon = (jd: number, b: number) => pymod(swe.calc(jd, b, false)[0], 360.0);

  const state = (offset: number): Record<string, Value> => {
    const jd = jd0 + offset / MIN_PER_DAY;
    const asc = pymod(swe.ascendantRaw(jd, lat, lon), 360.0);
    const out: Record<string, Value> = {};
    for (const n of vargas) out[`D${n}.lagna`] = vargaSign(asc, n);
    const moon = bodyLon(jd, BODIES.Mo);
    for (const n of vargas) out[`D${n}.moon`] = vargaSign(moon, n);
    const nk = nakshatraOf(moon);
    out["moon.pada"] = [nk.index, nk.pada];
    const key = Math.trunc(jd + 0.5);
    let hit = riseCache.get(key);
    if (hit === undefined || hit[0] > jd) {
      const rise = previousSunrise(swe, jd, lat, lon, alt);
      hit = [rise, bodyLon(rise, BODIES.Su)];
      riseCache.set(key, hit);
    }
    const [rise, sunRise] = hit;
    const minutes = (jd - rise) * MIN_PER_DAY;
    const sunNow = bodyLon(jd, BODIES.Su);
    out.BL = signOf(sunRise + minutes / 120 * 30);
    out.HL = signOf(sunRise + minutes / 60 * 30);
    out.GL = signOf(sunRise + minutes / 24 * 30);
    const off = [0.0, 240.0, 120.0][signOf(sunNow) % 3];
    out.PP = signOf(sunNow + off + minutes / 6 * 30);
    return out;
  };
  const same = (a: Value, b: Value) => JSON.stringify(a) === JSON.stringify(b);

  const step = stepS / 60.0, eps = precisionS / 60.0;
  const changes: { key: string; t: number; before: Value; after: Value }[] = [];
  let t = -windowMin;
  let prev = state(t);
  while (t < windowMin) {
    const tNext = Math.min(t + step, windowMin);
    const cur = state(tNext);
    for (const key of Object.keys(cur)) {
      if (same(cur[key], prev[key])) continue;
      let lo = t, hi = tNext;
      const vLo = prev[key];
      while (hi - lo > eps) {
        const mid = (lo + hi) / 2;
        if (same(state(mid)[key], vLo)) lo = mid; else hi = mid;
      }
      changes.push({ key, t: hi, before: prev[key], after: cur[key] });
    }
    prev = cur;
    t = tNext;
  }
  changes.sort((a, b) => a.t - b.t);
  return changes.map((c) => ({ key: c.key, offset_min: round4(c.t), utc: isoUtc(swe, jd0 + c.t / MIN_PER_DAY),
    before: c.before, after: c.after }));
}
