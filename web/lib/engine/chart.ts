// SPDX-License-Identifier: AGPL-3.0-or-later
// Browser port of src/jyotishnet_engine/chart.py build_chart (default SchoolConfig),
// with vargas, nakshatras, dignities, special lagnas, upagrahas and Jaimini points.
// Each function mirrors its Python original line by line (same float operations, in
// the same order) so results equal the API's; web/e2e/engine_parity.py checks them.

import { BODIES, imod, pyfloordiv, pymod, SE_CALC_RISE, SE_CALC_SET, Swe } from "./swe.ts";

/** DEFAULT_CONFIG.key(): the parity test fails if the Python default config changes. */
export const CONFIG_KEY = "3b2def92cf953ccd";

const SIGN_LORD = ["Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju"];
const GRAHAS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"];
const NAKSHATRAS = [
  "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
  "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
  "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
  "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
  "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
];
export const NAKSHATRA_SPAN = 360.0 / 27.0;
export const VIMSHOTTARI_LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"];
const EXALTATION: Record<string, number> = { Su: 0, Mo: 1, Ma: 9, Me: 5, Ju: 3, Ve: 11, Sa: 6 };
const MOOLATRIKONA: Record<string, [number, number, number]> = {
  Su: [4, 0.0, 20.0], Mo: [1, 4.0, 20.0], Ma: [0, 0.0, 12.0], Me: [5, 16.0, 20.0],
  Ju: [8, 0.0, 10.0], Ve: [6, 0.0, 15.0], Sa: [10, 0.0, 20.0],
};
const OWN_SIGNS: Record<string, number[]> = {
  Su: [4], Mo: [3], Ma: [0, 7], Me: [2, 5], Ju: [8, 11], Ve: [1, 6], Sa: [9, 10],
};
const NATURAL_FRIENDS: Record<string, string[]> = {
  Su: ["Mo", "Ma", "Ju"], Mo: ["Su", "Me"], Ma: ["Su", "Mo", "Ju"], Me: ["Su", "Ve"],
  Ju: ["Su", "Mo", "Ma"], Ve: ["Me", "Sa"], Sa: ["Me", "Ve"],
};
const NATURAL_ENEMIES: Record<string, string[]> = {
  Su: ["Ve", "Sa"], Mo: [], Ma: ["Me"], Me: ["Mo"], Ju: ["Me", "Ve"], Ve: ["Su", "Mo"], Sa: ["Su", "Mo", "Ma"],
};
const GRAHA_DRISHTI: Record<string, number[]> = {
  Su: [7], Mo: [7], Me: [7], Ve: [7], Ma: [4, 7, 8], Ju: [5, 7, 9], Sa: [3, 7, 10], Ra: [7], Ke: [7],
};

export type Point = {
  code: string; longitude: number; sign: number; degree: number; nakshatra: string;
  pada: number; nakshatra_lord: string; house: number; vargas: Record<string, number>;
  speed: number | null; retrograde: boolean | null; dignity: string | null;
  vargottama: boolean | null; aspects_houses: number[];
  nadiamsa: { division: number; index: number; name: string };
};

export type EngineChart = {
  jd_ut: number; ayanamsa: number; config_key: string; lagna: Point;
  grahas: Record<string, Point>; special: Record<string, Point>;
  house_lords: Record<string, string>; house_cusps: number[]; sunrise_jd: number;
  yogi: { point: number; yogi: string; sahayogi: string; avayogi_point: number; avayogi: string };
  karakas: Record<string, string>; arudhas: number[];
  sunrise_utc: string; warnings: string[];
};

export type EngineBirth = {
  local_datetime: string; latitude: number; longitude: number; utc_offset_hours: number;
  altitude_m?: number;
};

const norm = (d: number) => pymod(d, 360.0);
const signOf = (lon: number) => Math.trunc(pyfloordiv(lon, 30));
const isOdd = (sign: number) => sign % 2 === 0;

// --- time ------------------------------------------------------------------------
/** BirthData.jd_ut(): local clock time minus the offset (to the microsecond), then
 *  swe.julday with hour = h + m/60 + (s + us/1e6)/3600, as timeutil.datetime_to_jd. */
export function jdUt(swe: Swe, b: EngineBirth): number {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?$/.exec(b.local_datetime);
  if (!m) throw new Error(`bad local_datetime ${b.local_datetime}`);
  const localUs = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +(m[6] ?? 0)) * 1000
    + (m[7] ? +m[7].padEnd(6, "0") : 0);
  const offsetUs = Math.round(b.utc_offset_hours * 3600 * 1e6);
  const utcUs = localUs - offsetUs;
  const ms = Math.floor(utcUs / 1000);
  const us = utcUs - ms * 1000 + (ms % 1000 + 1000) % 1000 * 1000;
  const d = new Date(ms);
  const hour = d.getUTCHours() + d.getUTCMinutes() / 60 + (d.getUTCSeconds() + us / 1e6) / 3600;
  return swe.julday(d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate(), hour);
}

/** jd_to_datetime(jd).isoformat() for UTC (microseconds, "+00:00"). */
export function isoUtc(swe: Swe, jd: number): string {
  const [y, mo, d, h] = swe.revjul(jd);
  // timedelta(hours=h) rounds to the microsecond (half to even).
  const x = h * 3600 * 1e6;
  let us = Math.round(x);
  if (Math.abs(x - Math.trunc(x)) === 0.5 && us % 2 !== 0) us -= 1;
  const base = Date.UTC(y, mo - 1, d);
  const t = new Date(base + Math.floor(us / 1000));
  const frac = us % 1000000;
  const p = (n: number, w = 2) => String(n).padStart(w, "0");
  const s = `${p(t.getUTCFullYear(), 4)}-${p(t.getUTCMonth() + 1)}-${p(t.getUTCDate())}T${p(t.getUTCHours())}:`
    + `${p(t.getUTCMinutes())}:${p(t.getUTCSeconds())}`;
  return (frac ? `${s}.${p(frac, 6)}` : s) + "+00:00";
}

// --- nakshatra, dignity ----------------------------------------------------------
export function nakshatraOf(lon: number) {
  lon = pymod(lon, 360.0);
  const idx = Math.min(Math.trunc(pyfloordiv(lon, NAKSHATRA_SPAN)), 26);
  const frac = (lon - idx * NAKSHATRA_SPAN) / NAKSHATRA_SPAN;
  const pada = Math.min(Math.trunc(frac * 4) + 1, 4);
  return { index: idx, name: NAKSHATRAS[idx], pada, lord: VIMSHOTTARI_LORDS[idx % 9], fraction: frac };
}

function dignity(planet: string, lon: number): string {
  if (planet === "Ra" || planet === "Ke") return "node";
  lon = pymod(lon, 360.0);
  const sign = signOf(lon);
  const deg = lon - sign * 30;
  const ex = EXALTATION[planet];
  if (sign === ex) return "exalted";
  if (sign === (ex + 6) % 12) return "debilitated";
  const [mt, a, z] = MOOLATRIKONA[planet];
  if (sign === mt && a <= deg && deg < z) return "moolatrikona";
  if (OWN_SIGNS[planet].includes(sign)) return "own";
  const lord = SIGN_LORD[sign];
  if (NATURAL_FRIENDS[planet].includes(lord)) return "friend";
  if (NATURAL_ENEMIES[planet].includes(lord)) return "enemy";
  return "neutral";
}

// --- vargas (vargas.py, default schemes) -------------------------------------------
function parts(lon: number, n: number): [number, number] {
  lon = pymod(lon, 360.0);
  const sign = signOf(lon);
  const within = lon - sign * 30;
  const scaled = within * n / 30.0;
  return [sign, Math.min(Math.trunc(scaled), n - 1)];
}
const PANCHAMSA_ODD = [0, 10, 8, 2, 6];
const PANCHAMSA_EVEN = [1, 5, 11, 9, 7];
const TRIMSAMSA_ODD: [number, number][] = [[5, 0], [10, 10], [18, 8], [25, 2], [30, 6]];
const TRIMSAMSA_EVEN: [number, number][] = [[5, 1], [12, 5], [20, 11], [25, 9], [30, 7]];

export function vargaSign(lon: number, n: number): number {
  const [sign, part] = parts(lon, n);
  if (n === 2) return (sign * 2 + (isOdd(sign) ? part : 1 - part)) % 12;   // Uma-Shambhu
  const odd = isOdd(sign);
  const mod = sign % 3;
  switch (n) {
    case 1: return sign;
    case 3: return (sign + 4 * part) % 12;
    case 4: return (sign + 3 * part) % 12;
    case 5: return (odd ? PANCHAMSA_ODD : PANCHAMSA_EVEN)[part];
    case 6: return ((odd ? 0 : 6) + part) % 12;
    case 7: return (sign + part + (odd ? 0 : 6)) % 12;
    case 8: return ([0, 8, 4][mod] + part) % 12;
    case 9: return ([sign, sign + 8, sign + 4][mod] + part) % 12;
    case 10: return (sign + part + (odd ? 0 : 8)) % 12;
    case 11: return imod(part - sign, 12);                                  // Rath
    case 12: return (sign + part) % 12;
    case 16: return ([0, 4, 8][mod] + part) % 12;
    case 20: return ([0, 8, 4][mod] + part) % 12;
    case 24: return ((odd ? 4 : 3) + part) % 12;
    case 27: return ([0, 3, 6, 9][sign % 4] + part) % 12;
    case 30: {
      const l = pymod(lon, 360.0);
      const s = signOf(l);
      const within = l - s * 30;
      const table = isOdd(s) ? TRIMSAMSA_ODD : TRIMSAMSA_EVEN;
      for (const [end, target] of table) if (within < end) return target;
      return table[table.length - 1][1];
    }
    case 40: return ((odd ? 0 : 6) + part) % 12;
    case 45: return ([0, 4, 8][mod] + part) % 12;
    case 60: return (sign + part) % 12;
    case 81: return Math.trunc(pymod(lon, 360.0) * 81 / 30.0) % 12;
    case 108: return (vargaSign(lon, 9) + part) % 12;                       // navamsa scheme
    case 144: return (vargaSign(lon, 12) + part) % 12;
  }
  throw new Error(`Unsupported varga D${n}`);
}

const NADI_STARTS = [
  0, 252, 336, 378, 504, 560, 630, 672, 756, 945, 1008, 1120, 1134, 1260, 1344, 1512,
  1680, 1764, 1890, 2016, 2160, 2240, 2268, 2352, 2520, 2646, 2688, 2772, 2800, 2835,
  3024, 3150, 3276, 3360, 3402, 3528, 3696, 3780, 3920, 4032, 4158, 4284, 4320, 4368,
  4410, 4480, 4536, 4704, 4725, 4788, 4914, 5040, 5292, 5376, 5544, 5600, 5670, 5712,
  5796, 6048, 6160, 6300, 6384, 6426, 6480, 6552, 6615, 6720, 6804, 6930, 7056, 7182,
  7280, 7308, 7392, 7560, 7728, 7812, 7840, 7938, 8064, 8190, 8316, 8400, 8505, 8568,
  8640, 8694, 8736, 8820, 8960, 9072, 9324, 9408, 9450, 9520, 9576, 9744, 9828, 10080,
  10206, 10332, 10395, 10416, 10584, 10640, 10710, 10752, 10800, 10836, 10962, 11088,
  11200, 11340, 11424, 11592, 11718, 11760, 11844, 11970, 12096, 12285, 12320, 12348,
  12432, 12474, 12600, 12768, 12852, 12880, 12960, 13104, 13230, 13356, 13440, 13608,
  13776, 13860, 13986, 14000, 14112, 14175, 14364, 14448, 14490, 14560, 14616, 14742,
  14784, 14868,
];
const NADI_NAMES = [
  "Vasudha", "Vaishnavi", "Braahmi", "Kaalakoota", "Sankari", "Sudhakarasama",
  "Saumya", "Suraa", "Maayaa", "Manohara", "Maadhavi", "Manjuswana", "Ghora",
  "Kumbhini", "Kutila", "Prabhaa", "Paraa", "Payaswini", "Maalaa", "Jagati",
  "Jarjhari", "Dhruva", "Musala", "Mudgala", "Paasaa", "Chambaka", "Daamini", "Mahi",
  "Kalusha", "Kamala", "Kaantaa", "Kaalaa", "Karikara", "Kshamaa", "Durdharaa",
  "Durbhagaa", "Viswa", "Visirna", "Vihwala", "Anilaa", "Bheema", "Sukhaprada",
  "Snigdha", "Sodara", "Surasundari", "Amritapraasini", "Kaalaa/Karaalaa",
  "Kaamadrikkara Veerini", "Gahwaraa", "Kundini", "Kaanthaa", "Vishaakhya (Visha)",
  "Vishanaasini", "Nirmada", "Seetala", "Nimnaa", "Preeta", "Priyavivardhini",
  "Manaadha (Maanaghna)", "Durbhaga", "Chitra", "Vichitra", "Chiranjeevini", "Bhoopa",
  "Gadaaharaa", "Naalaa", "Gaalavee", "Nirmalaa", "Nadee", "Sudhaa", "Mritamsuga",
  "Kaali", "Kaalikaa", "Kalushaankuraa", "Trailokya Mohanakari", "Mahaamaayaa",
  "Suseetalaa", "Sukhadaa", "Suprabhaa", "Sobhaa", "Sobhana", "Sivadaa", "Sivaa",
  "Balaa", "Jwaalaa", "Gadaa", "Gaadaa", "Sootana (Nootana)", "Sumanoharaa",
  "Somavalli", "Somalataa", "Mangala", "Mudrikaa", "Sudhaa", "Melaa", "Apavargaa",
  "Pasyathaa", "Navaneetaa", "Nisaachari", "Nivriti", "Nirgatha", "Saaraa",
  "Saamagaa", "Saamadaa", "Samaa", "Viswambharaa", "Kumaari", "Kokilaa",
  "Kunjarakriti", "Indra", "Swaahaa", "Swadhaa", "Vahni", "Peetha", "Yakshi",
  "Achalaprabhaa", "Saarini", "Madhuraa", "Maitri", "Harini", "Haarini", "Marutaa",
  "Dhananjaya", "Dhanakari", "Dhanadaa", "Kachchapaa", "Ambujaa", "Isaani", "Soolini",
  "Roudri", "Sivaasivakari", "Kalaa", "Kunda", "Mukunda", "Bharata", "Kadali",
  "Smaraa", "Basita", "Kodala", "Kokilamsa", "Kaamini", "Kalasodbhava", "Viraprasoo",
  "Sangaraa", "Satayajnaa", "Sataavari", "Sragvi", "Paatalini", "Naagapankaja",
  "Parameswari",
];

function nadiamsa(lon: number) {
  lon = pymod(lon, 360.0);
  const sign = signOf(lon);
  const units = (lon - sign * 30) * 504.0;
  let lo = 0, hi = NADI_STARTS.length;                 // bisect_right
  while (lo < hi) { const mid = (lo + hi) >> 1; if (units < NADI_STARTS[mid]) hi = mid; else lo = mid + 1; }
  const div = Math.min(Math.max(lo - 1, 0), 149);
  const mod = sign % 3;
  const index = mod === 0 ? div : mod === 1 ? 149 - div : (div + 75) % 150;
  return { division: div + 1, index: index + 1, name: NADI_NAMES[index] };
}

function point(code: string, lon: number, lagnaSign: number, vargas: number[]): Point {
  const nk = nakshatraOf(lon);
  const sign = signOf(lon);
  return {
    code, longitude: lon, sign, degree: lon - sign * 30, nakshatra: nk.name, pada: nk.pada,
    nakshatra_lord: nk.lord, house: imod(sign - lagnaSign, 12) + 1,
    vargas: Object.fromEntries(vargas.map((n) => [String(n), vargaSign(lon, n)])),
    speed: null, retrograde: null, dignity: null, vargottama: null, aspects_houses: [],
    nadiamsa: nadiamsa(lon),
  };
}

// --- sunrise, special lagnas, upagrahas -------------------------------------------
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

function sunEventAfter(swe: Swe, jd: number, lat: number, lon: number, alt: number, kind: number): number {
  const t = swe.sunEvent(jd, lat, lon, alt, kind);
  if (t === null) throw new Error("No solar event found at this latitude.");
  return t;
}

const sunLon = (swe: Swe, jd: number) => norm(swe.calc(jd, BODIES.Su, false)[0]);
const ascendant = (swe: Swe, jd: number, lat: number, lon: number) => norm(swe.ascendantRaw(jd, lat, lon));

const CYCLE = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", null];
const WEEKDAY = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"];
const TIME_UPAGRAHAS: [string, string, number][] = [
  ["Kl", "Su", 0.5], ["Mr", "Ma", 0.5], ["AP", "Me", 0.5], ["YG", "Ju", 0.5], ["Gk", "Sa", 0.0], ["Md", "Sa", 0.5],
];
const KALAS: Record<string, number> = { Su: 30, Mo: 16, Ma: 6, Me: 8, Ju: 10, Ve: 12, Sa: 1 };

function timeUpagrahas(swe: Swe, jd: number, lat: number, lon: number, alt: number): Record<string, number> {
  const rise = previousSunrise(swe, jd, lat, lon, alt);
  const sunset = sunEventAfter(swe, rise, lat, lon, alt, SE_CALC_SET);
  const weekday = imod(Math.trunc(Math.floor(rise + 0.5 + lon / 360.0 + 1.0)), 7);
  let start: number, end: number, first: number;
  if (jd < sunset) { start = rise; end = sunset; first = weekday; }
  else { start = sunset; end = sunEventAfter(swe, rise + 0.01, lat, lon, alt, SE_CALC_RISE); first = (weekday + 4) % 7; }
  const part = (end - start) / 8.0;
  const out: Record<string, number> = {};
  for (const [code, lord, frac] of TIME_UPAGRAHAS) {
    const k = imod(CYCLE.indexOf(lord) - CYCLE.indexOf(WEEKDAY[first]), 8);
    out[code] = ascendant(swe, start + part * (k + frac), lat, lon);
  }
  return out;
}

function sunUpagrahas(sun: number): Record<string, number> {
  const dh = pymod(sun + 133.0 + 1.0 / 3.0, 360.0);
  const vy = pymod(360.0 - dh, 360.0);
  const pv = pymod(vy + 180.0, 360.0);
  const ic = pymod(360.0 - pv, 360.0);
  const uk = pymod(ic + 16.0 + 2.0 / 3.0, 360.0);
  return { Dh: dh, Vy: vy, Pv: pv, IC: ic, UK: uk };
}

const count = (sign: number) => (sign % 2 === 0 ? sign + 1 : 12 - sign);

function varnadaLagna(lagna: number, hora: number): number {
  const a = signOf(lagna), b = signOf(hora);
  const ca = count(a), cb = count(b);
  let n = (a % 2) === (b % 2) ? ca + cb : Math.abs(ca - cb);
  n = n % 12 || 12;
  const sign = a % 2 === 0 ? n - 1 : imod(12 - n, 12);
  return sign * 30.0 + pymod(lagna, 30.0);
}

function induLagna(lagna: number, moon: number): number {
  const ls = signOf(lagna), ms = signOf(moon);
  const total = KALAS[SIGN_LORD[(ls + 8) % 12]] + KALAS[SIGN_LORD[(ms + 8) % 12]];
  const r = total % 12 || 12;
  return ((ms + r - 1) % 12) * 30.0 + pymod(moon, 30.0);
}

// --- Jaimini: chara karakas (8) and bhava arudhas (JHora defaults) -------------------
const KARAKAS_8 = ["AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"];

function charaKarakas(lons: Record<string, number>): Record<string, string> {
  const deg = (p: string) => { const d = pymod(lons[p], 30.0); return p === "Ra" ? 30.0 - d : d; };
  const ranked = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra"]
    .map((p, i) => ({ p, d: deg(p), i }))
    .sort((x, y) => (y.d - x.d) || (x.i - y.i))
    .map((x) => x.p);
  return Object.fromEntries(KARAKAS_8.map((k, i) => [k, ranked[i]]));
}

const J_EXALT: Record<string, number> = { Su: 0, Mo: 1, Ma: 9, Me: 5, Ju: 3, Ve: 11, Sa: 6, Ra: 2, Ke: 8 };

function sees(a: number, b: number): boolean {
  if (a === b) return true;
  const ma = a % 3, mb = b % 3;
  if (ma === 2) return mb === 2;
  if ((ma === 0 && mb === 1) || (ma === 1 && mb === 0)) return (a + 1) % 12 !== b && (b + 1) % 12 !== a;
  return false;
}

function bhavaArudhas(lagna: number, signs: Record<string, number>, lons: Record<string, number>): number[] {
  const occupants = (s: number) => GRAHAS.filter((p) => signs[p] === s).length;
  const helpers = (sign: number) => {
    let n = Number(sees(sign, signs.Me)) + Number(sees(sign, signs.Ju));
    if (sees(sign, signs[SIGN_LORD[sign]])) n += 1;
    else if (sign === 7 && sees(7, signs.Ke)) n += 1;
    else if (sign === 10 && sees(10, signs.Ra)) n += 1;
    return n;
  };
  const advance = (p: string) => { const d = pymod(lons[p], 30.0); return p === "Ra" || p === "Ke" ? 30.0 - d : d; };
  const coLord = (a: string, b: string): string => {
    const own = a === "Sa" ? 10 : 7;
    const sa = signs[a], sb = signs[b];
    if (sa === own && sb !== own) return b;
    if (sb === own && sa !== own) return a;
    for (const key of [occupants, helpers]) {
      const ka = key(sa), kb = key(sb);
      if (ka !== kb) return ka > kb ? a : b;
    }
    const ea = J_EXALT[a] === sa, eb = J_EXALT[b] === sb;
    if (ea !== eb) return ea ? a : b;
    const da = (J_EXALT[a] + 6) % 12 === sa, db = (J_EXALT[b] + 6) % 12 === sb;
    if (da !== db) return da ? b : a;
    if (sa % 3 !== sb % 3) return sa % 3 > sb % 3 ? a : b;
    return advance(a) < advance(b) ? b : a;
  };
  const arudhaLords: Record<number, string> = { 10: coLord("Sa", "Ra"), 7: coLord("Ma", "Ke") };
  const out: number[] = [];
  for (let k = 0; k < 12; k++) {
    const sign = (lagna + k) % 12;
    const lord = arudhaLords[sign] ?? SIGN_LORD[sign];
    let pada = imod(2 * signs[lord] - sign, 12);
    if (imod(pada - sign, 6) === 0) pada = (pada + 9) % 12;
    out.push(pada);
  }
  return out;
}

// --- build_chart -------------------------------------------------------------------
const SHODASHAVARGA = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60];

export function buildChart(swe: Swe, birth: EngineBirth, vargas: number[] = SHODASHAVARGA): EngineChart {
  const jd = jdUt(swe, birth);
  const lat = birth.latitude, lon = birth.longitude, alt = birth.altitude_m ?? 0.0;
  if (Math.abs(lat) > 66) throw new Error("Polar latitudes are not supported.");
  const asc = ascendant(swe, jd, lat, lon);
  const lagnaSign = signOf(asc);
  const lagna = point("La", asc, lagnaSign, vargas);

  const grahas: Record<string, Point> = {};
  const positions: Record<string, [number, number]> = {};
  for (const [code, body] of Object.entries(BODIES)) {
    const [l, , sp] = swe.calc(jd, body);
    positions[code] = [norm(l), sp];
  }
  const [nl, , nsp] = swe.meanNode(jd);
  positions.Ra = [norm(nl), nsp];
  positions.Ke = [norm(nl + 180.0), nsp];
  for (const code of GRAHAS) {
    const [l, sp] = positions[code];
    const p = point(code, l, lagnaSign, vargas);
    p.speed = sp;
    p.retrograde = code === "Ra" || code === "Ke" ? true : sp < 0;
    p.dignity = dignity(code, l);
    p.vargottama = vargaSign(l, 1) === vargaSign(l, 9);
    p.aspects_houses = GRAHA_DRISHTI[code].map((d) => imod(p.house - 1 + d - 1, 12) + 1);
    grahas[code] = p;
  }

  // special_lagnas()
  const rise = previousSunrise(swe, jd, lat, lon, alt);
  const minutes = (jd - rise) * 1440.0;
  const sunRise = sunLon(swe, rise);
  const sunNow = sunLon(swe, jd);
  const bl = pymod(sunRise + minutes / 120.0 * 30.0, 360.0);
  const hl = pymod(sunRise + minutes / 60.0 * 30.0, 360.0);
  const gl = pymod(sunRise + minutes / 24.0 * 30.0, 360.0);
  const offset = [0.0, 240.0, 120.0][signOf(sunNow) % 3];
  const pp = pymod(sunNow + offset + minutes / 6.0 * 30.0, 360.0);
  const vl = pymod(sunRise + minutes / 6.0 * 30.0, 360.0);

  const special: Record<string, Point> = {
    BL: point("BL", bl, lagnaSign, vargas), HL: point("HL", hl, lagnaSign, vargas),
    GL: point("GL", gl, lagnaSign, vargas), PP: point("PP", pp, lagnaSign, vargas),
    ViL: point("ViL", vl, lagnaSign, vargas),
  };
  const lons = Object.fromEntries(GRAHAS.map((k) => [k, grahas[k].longitude]));
  const frac = pymod(lons.Mo, NAKSHATRA_SPAN) / NAKSHATRA_SPAN;
  const points: Record<string, number> = {
    SL: pymod(asc + 360.0 * frac, 360.0), IL: induLagna(asc, lons.Mo),
    VL: varnadaLagna(asc, hl), BB: pymod(lons.Ra + pymod(lons.Mo - lons.Ra, 360.0) / 2.0, 360.0),
    ...sunUpagrahas(lons.Su),
    ...timeUpagrahas(swe, jd, lat, lon, alt),
  };
  for (const [k, v] of Object.entries(points)) special[k] = point(k, v, lagnaSign, vargas);

  const yp = pymod(lons.Su + lons.Mo + 93.0 + 1.0 / 3.0, 360.0);
  const ava = pymod(yp + 186.0 + 2.0 / 3.0, 360.0);
  const signs = Object.fromEntries(GRAHAS.map((k) => [k, grahas[k].sign]));

  return {
    jd_ut: jd, ayanamsa: swe.ayanamsa(jd), config_key: CONFIG_KEY, lagna, grahas, special,
    house_lords: Object.fromEntries(Array.from({ length: 12 }, (_, i) => [String(i + 1), SIGN_LORD[(lagnaSign + i) % 12]])),
    house_cusps: swe.cuspsRaw(jd, lat, lon).map(norm),
    sunrise_jd: rise,
    yogi: { point: yp, yogi: nakshatraOf(yp).lord, sahayogi: SIGN_LORD[signOf(yp)], avayogi_point: ava, avayogi: nakshatraOf(ava).lord },
    karakas: charaKarakas(lons),
    arudhas: bhavaArudhas(lagnaSign, signs, lons),
    sunrise_utc: isoUtc(swe, rise),
    warnings: [],
  };
}
