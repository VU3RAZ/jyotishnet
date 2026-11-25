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
  nadiamsa?: { division: number; index: number; name: string };
};

export type Chart = {
  jd_ut: number;
  ayanamsa: number;
  lagna: Point;
  grahas: Record<string, Point>;
  special?: Record<string, Point>;
  yogi?: { point: number; yogi: string; sahayogi: string; avayogi_point: number; avayogi: string };
  karakas?: Record<string, string>;   // AK, AmK, ... -> graha
  arudhas?: number[];                 // signs of A1 (AL) .. A12 (UL)
  sunrise_utc: string;
  warnings?: string[];
};

export type RunningPeriod = { lord: string; name?: string | null; level: number; start: string; end: string };

export type Boundary = { key: string; offset_min: number; utc: string; before: number; after: number };

async function post<T>(path: string, body: unknown, signal?: AbortSignal, method = "POST"): Promise<T> {
  const r = await fetch(`/api${path}`, {
    method,
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
  required_rupas: number; ratio: number; cheshta_counted: boolean; ishta: number; kashta: number;
};
export type Shadbala = {
  planets: Record<string, PlanetStrength>;
  wars: { planets: string[]; separation_deg: number }[];
  houses: {
    house: number; sign: number; lord: string; lord_virupas: number; dig: number; drik: number;
    total_virupas: number; rupas: number;
  }[];
  avasthas: Record<string, { baladi: string; jagradadi: string; moods: string[] }>;
};
export type DashaSystem = "vimshottari" | "ashtottari" | "yogini" | "chara" | "narayana"
  | "lagnamsaka" | "padanaathamsa" | "sudasa" | "drig" | "lagna_kendradi" | "ak_kendradi"
  | "trikona" | "chara_parasara" | "chara_rangacharya" | "yogardha" | "shoola" | "niryana_shoola"
  | "brahma" | "sthira" | "mandooka_knrao" | "navamsa" | "varnada";
const GRAHA_DASHAS: DashaSystem[] = ["vimshottari", "ashtottari", "yogini"];
export type DashaPeriod = {
  lord: string; name?: string | null; start: string; end: string; level: number;
  children?: DashaPeriod[];
};

export type TransitPlanet = {
  code: string; longitude: number; sign: number; house_from_moon: number; good: boolean;
  vedha_from: string[]; vedha_to: string[]; tara: string; tara_number: number; murthi: string | null;
  av_score: number | null; sav_score: number | null; kakshya: string | null; kakshya_good: boolean | null;
  bindu_from: string[];
};
export type Transits = {
  planets: Record<string, TransitPlanet>;
  saturn_phase: string | null;
  saturn_spells: { phase: string; start: string; end: string }[];
};

export type PanchangaElement = {
  kind: string; index: number; name: string; lord: string | null; end_utc: string; fraction_left: number;
};
export type Span = [string, string];
export type Panchanga = {
  utc_offset_hours: number;
  birth: {
    samvatsara: string; masa: string; weekday: string; tithi: PanchangaElement;
    nakshatra: PanchangaElement; yoga: PanchangaElement; karana: PanchangaElement;
    hora_lord: string; sunrise_utc: string; sunset_utc: string; janma_ghatis: number;
  };
  day: {
    sunrise_utc: string; sunset_utc: string; next_sunrise_utc: string; weekday: string;
    tithis: PanchangaElement[]; nakshatras: PanchangaElement[]; yogas: PanchangaElement[];
    karanas: PanchangaElement[]; rahu_kala: Span; gulika_kala: Span; yamaganda: Span;
    durmuhurta: Span[]; varjya: Span[]; moonrise_utc: string | null; moonset_utc: string | null;
    moon_sign: number; moon_sign_end_utc: string | null;
  };
};

export type Vimshopaka = {
  planets: Record<string, Record<string, number>>;     // graha -> scheme -> points of 20
  weights: Record<string, Record<string, number>>;     // scheme -> "D9" -> weight
};
export type YogaOptions = { strong_lord: "dignity" | "shadbala"; gajakesari: "bphs" | "phaladeepika" };
export const DEFAULT_YOGA_OPTIONS: YogaOptions = { strong_lord: "dignity", gajakesari: "bphs" };

export const analysis = {
  panchanga: (birth: Birth) => post<Panchanga>("/v1/panchanga", { birth }),
  yogas: (birth: Birth, options: YogaOptions = DEFAULT_YOGA_OPTIONS) =>
    post<{ yogas: Yoga[] }>("/v1/yogas", { birth, include_absent: true, ...options }),
  vimshopaka: (birth: Birth, saptavarga_weights: "bphs" | "jhora") =>
    post<Vimshopaka>("/v1/vimshopaka", { birth, saptavarga_weights }),
  ashtakavarga: (birth: Birth) => post<Ashtakavarga>("/v1/ashtakavarga", { birth }),
  shadbala: (birth: Birth) => post<Shadbala>("/v1/shadbala", { birth }),
  transits: (birth: Birth, transit: Birth) => post<Transits>("/v1/transits", { birth, transit }),
  dashas: (birth: Birth, system: DashaSystem) =>
    post<{ system: string; periods: DashaPeriod[]; applicable?: boolean }>("/v1/dasha",
      { birth, system, levels: GRAHA_DASHAS.includes(system) ? 3 : 2 }),
};

// Saved charts (M3.1): kept in a SQLite file next to the API, never sent elsewhere.
export type Note = { id: number; text: string; created: string; updated: string };
export type SavedChart = {
  id: number; name: string; birth: Birth; place: string; events: LifeEvent[];
  created: string; updated: string; notes?: Note[]; note_count?: number;
};

async function call<T>(path: string, method = "GET"): Promise<T> {
  const r = await fetch(`/api${path}`, { method });
  if (!r.ok) throw new Error(`${path} failed (${r.status})`);
  return (r.status === 204 ? undefined : r.json()) as Promise<T>;
}

export const library = {
  list: (q = "") => call<{ charts: SavedChart[] }>(`/v1/charts?q=${encodeURIComponent(q)}`),
  get: (id: number) => call<SavedChart>(`/v1/charts/${id}`),
  create: (c: { name: string; birth: Birth; place?: string; events?: LifeEvent[] }) =>
    post<SavedChart>("/v1/charts", c),
  update: (id: number, c: Partial<{ name: string; birth: Birth; place: string; events: LifeEvent[] }>) =>
    post<SavedChart>(`/v1/charts/${id}`, c, undefined, "PUT"),
  remove: (id: number) => call<void>(`/v1/charts/${id}`, "DELETE"),
  addNote: (id: number, text: string) => post<Note>(`/v1/charts/${id}/notes`, { text }),
  updateNote: (noteId: number, text: string) => post<Note>(`/v1/notes/${noteId}`, { text }, undefined, "PUT"),
  removeNote: (noteId: number) => call<void>(`/v1/notes/${noteId}`, "DELETE"),
};
