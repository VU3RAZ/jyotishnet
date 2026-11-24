// SPDX-License-Identifier: AGPL-3.0-or-later
// Typed client for the JyotishNet API (proxied at /api).

export type Birth = {
  local_datetime: string; // "YYYY-MM-DDTHH:MM:SS", local clock time
  latitude: number;
  longitude: number;
  utc_offset_hours: number;
};

export type Point = {
  code: string;
  longitude: number;
  sign: number;
  degree: number;
  nakshatra: string;
  pada: number;
  nakshatra_lord: string;
  house: number;
  vargas: Record<string, number>;
  speed: number | null;
  retrograde: boolean | null;
  dignity: string | null;
  vargottama: boolean | null;
};

export type Chart = {
  jd_ut: number;
  ayanamsa: number;
  lagna: Point;
  grahas: Record<string, Point>;
  special?: Record<string, Point>;
  sunrise_utc: string;
  warnings?: string[];
};

export type RunningPeriod = { lord: string; name?: string | null; level: number; start: string; end: string };

export type Boundary = { key: string; offset_min: number; utc: string; before: number; after: number };

async function post<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const r = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!r.ok) {
    const detail = await r.text();
    throw new Error(`${path} failed (${r.status}): ${detail.slice(0, 200)}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  chart: (birth: Birth, vargas: number[], signal?: AbortSignal) =>
    post<Chart>("/v1/chart", { birth, vargas }, signal),
  runningDasha: (birth: Birth, atUtc: string, signal?: AbortSignal) =>
    post<{ running: RunningPeriod[] }>("/v1/dasha",
      { birth, system: "vimshottari", levels: 3, at: atUtc }, signal),
  /** Time-zone warnings for a birth record (India before 1956); never changes a chart. */
  birthWarnings: (birth: Birth, signal?: AbortSignal) =>
    post<{ warnings: string[] }>("/v1/birth/warnings", { birth }, signal),
  boundaries: (birth: Birth, windowMin: number, vargas: number[], signal?: AbortSignal) =>
    post<{ changes: Boundary[] }>("/v1/boundaries",
      { birth, window_min: windowMin, step_s: 10, vargas }, signal),
};

// --- Rectification helpers ---------------------------------------------------

export type EventRule = {
  id: string; name: string; d1_houses: number[]; varga: number; varga_houses: number[];
  karaka: string; check_only: boolean; indicative: boolean;
};
export type LifeEvent = { type: string; date: string };
export type EventCheck = {
  event: string; name: string; date: string; mahadasha: string | null; antardasha: string | null;
  maha_links: string[]; antar_links: string[]; double_transit_houses: number[];
  score: number; verdict: "strong" | "partial" | "weak"; check_only: boolean;
};
export type FitCurve = {
  points: { offset_s: number; score: number }[];
  best: { offset_s: number; score: number } | null;
  helps_decide: boolean[];
  max_score: number;
};
export type IndicativePeriod = {
  mahadasha: string; antardasha: string; start: string; end: string;
  maha_links: string[]; antar_links: string[];
};

export const btr = {
  events: () => fetch("/api/v1/btr/events").then((r) => r.json() as Promise<{ events: EventRule[] }>),
  check: (birth: Birth, events: LifeEvent[]) =>
    post<{ checks: EventCheck[] }>("/v1/btr/check", { birth, events }),
  curve: (birth: Birth, events: LifeEvent[], windowMin: number, stepS: number) =>
    post<FitCurve>("/v1/btr/curve", { birth, events, window_min: windowMin, step_s: stepS }),
  indicative: (birth: Birth) =>
    post<{ periods: Record<string, IndicativePeriod[]> }>("/v1/btr/indicative", { birth }),
};

// --- Analysis views -------------------------------------------------------------

export type Yoga = {
  id: string; name: string; group: string; present: boolean; cancelled: boolean;
  evidence: string[]; summary: string; source: { text: string; section: string }; status: string;
};
export type Ashtakavarga = {
  bav: Record<string, number[]>; sav: number[];
  bav_trikona: Record<string, number[]>; bav_reduced: Record<string, number[]>;
  rasi_pinda: Record<string, number>; graha_pinda: Record<string, number>;
  shodhya_pinda: Record<string, number>;
};
export type PlanetStrength = {
  sthana: Record<string, number>; dig: number; kala: Record<string, number>; cheshta: number;
  naisargika: number; drik: number; total_virupas: number; rupas: number;
  required_rupas: number; ratio: number;
};
export type Shadbala = {
  planets: Record<string, PlanetStrength>;
  wars: { planets: string[]; separation_deg: number }[];
};
export type DashaSystem = "vimshottari" | "ashtottari" | "yogini" | "chara";
export type DashaPeriod = {
  lord: string; name?: string | null; start: string; end: string; level: number;
  children?: DashaPeriod[];
};

export const analysis = {
  yogas: (birth: Birth) => post<{ yogas: Yoga[] }>("/v1/yogas", { birth, include_absent: true }),
  ashtakavarga: (birth: Birth) => post<Ashtakavarga>("/v1/ashtakavarga", { birth }),
  shadbala: (birth: Birth) => post<Shadbala>("/v1/shadbala", { birth }),
  dashas: (birth: Birth, system: DashaSystem) =>
    post<{ system: string; periods: DashaPeriod[]; applicable?: boolean }>("/v1/dasha",
      { birth, system, levels: system === "chara" ? 2 : 3 }),
};
