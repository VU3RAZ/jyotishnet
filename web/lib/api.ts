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
