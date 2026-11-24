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
