// SPDX-License-Identifier: AGPL-3.0-or-later
// Swiss Ephemeris 2.10.03 as WebAssembly (built by tools/build_swe_wasm.sh from the
// sources pyswisseph 2.10.3.2 bundles), called with the same arguments as the API's
// src/jyotishnet_engine/ephemeris.py. No ephemeris files: Moshier, as the API.
// Licensing: Swiss Ephemeris is AGPL or commercially licensed (see README).

const SE_SUN = 0;
const SE_MEAN_NODE = 10;
export const BODIES: Record<string, number> = { Su: 0, Mo: 1, Ma: 4, Me: 2, Ju: 5, Ve: 3, Sa: 6 };
const SEFLG_MOSEPH = 4;
const SEFLG_SPEED = 256;
const SEFLG_TRUEPOS = 16;
const SEFLG_SIDEREAL = 64 * 1024;
const SE_SIDM_LAHIRI = 1;
const SE_GREG_CAL = 1;
export const SE_CALC_RISE = 1;
export const SE_CALC_SET = 2;
const SE_BIT_DISC_CENTER = 256;
const SE_BIT_NO_REFRACTION = 512;
// Default config: true positions; sunrise by the disc centre without refraction.
const PLANET_FLAGS = SEFLG_MOSEPH | SEFLG_TRUEPOS | SEFLG_SIDEREAL;
const RISE_BITS = SE_BIT_DISC_CENTER | SE_BIT_NO_REFRACTION;

type Exports = {
  memory: WebAssembly.Memory;
  _initialize: () => void;
  malloc: (n: number) => number;
  free: (p: number) => void;
  swe_calc_ut: (jd: number, ipl: number, iflag: number, xx: number, serr: number) => number;
  swe_set_sid_mode: (mode: number, t0: number, ayanT0: number) => void;
  swe_get_ayanamsa_ut: (jd: number) => number;
  swe_houses_ex: (jd: number, iflag: number, lat: number, lon: number, hsys: number,
    cusps: number, ascmc: number) => number;
  swe_rise_trans: (jd: number, ipl: number, star: number, epheflag: number, rsmi: number,
    geopos: number, atpress: number, attemp: number, tret: number, serr: number) => number;
  swe_julday: (y: number, m: number, d: number, h: number, cal: number) => number;
  swe_revjul: (jd: number, cal: number, y: number, m: number, d: number, h: number) => void;
};

// The module opens no files and reads no environment: WASI calls get "bad file".
function wasiStubs(mem: () => WebAssembly.Memory) {
  const EBADF = 8;
  const zero2 = (a: number, b: number) => {
    const v = new DataView(mem().buffer); v.setUint32(a, 0, true); v.setUint32(b, 0, true); return 0;
  };
  return {
    environ_get: () => 0,
    environ_sizes_get: zero2,
    fd_close: () => 0,
    fd_fdstat_get: () => EBADF,
    fd_prestat_get: () => EBADF,
    fd_prestat_dir_name: () => EBADF,
    fd_read: () => EBADF,
    fd_seek: () => EBADF,
    fd_write: (_fd: number, iovs: number, n: number, written: number) => {
      const v = new DataView(mem().buffer);
      let total = 0;
      for (let i = 0; i < n; i++) total += v.getUint32(iovs + i * 8 + 4, true);
      v.setUint32(written, total, true);
      return 0;
    },
    path_open: () => 44, // ENOENT
    proc_exit: (code: number) => { throw new Error(`swe exited (${code})`); },
    random_get: (buf: number, len: number) => {
      crypto.getRandomValues(new Uint8Array(mem().buffer, buf, len));
      return 0;
    },
  };
}

export class Swe {
  private x: Exports;
  private buf: number;        // scratch: 64 doubles
  private serr: number;       // 256-byte error string
  private star: number;       // empty star name, as pyswisseph passes
  private sidMode = -1;

  private constructor(x: Exports) {
    this.x = x;
    x._initialize();
    this.buf = x.malloc(64 * 8);
    this.serr = x.malloc(256);
    this.star = x.malloc(128);
    new Uint8Array(x.memory.buffer, this.star, 128).fill(0);
  }

  static async load(source: BufferSource | Response | Promise<Response>): Promise<Swe> {
    let memory: WebAssembly.Memory | null = null;
    const imports = { wasi_snapshot_preview1: wasiStubs(() => memory!) };
    const resp = await source;
    const { instance } = resp instanceof Response
      ? await WebAssembly.instantiate(await resp.arrayBuffer(), imports)
      : await WebAssembly.instantiate(resp, imports);
    const x = instance.exports as unknown as Exports;
    memory = x.memory;
    return new Swe(x);
  }

  private f64(i: number): number {
    return new Float64Array(this.x.memory.buffer, this.buf, 64)[i];
  }

  private sidereal() {
    if (this.sidMode !== SE_SIDM_LAHIRI) {
      this.x.swe_set_sid_mode(SE_SIDM_LAHIRI, 0, 0);
      this.sidMode = SE_SIDM_LAHIRI;
    }
  }

  julday(y: number, m: number, d: number, h: number): number {
    return this.x.swe_julday(y, m, d, h, SE_GREG_CAL);
  }

  revjul(jd: number): [number, number, number, number] {
    const b = this.buf;
    this.x.swe_revjul(jd, SE_GREG_CAL, b, b + 4, b + 8, b + 16);
    const v = new DataView(this.x.memory.buffer);
    return [v.getInt32(b, true), v.getInt32(b + 4, true), v.getInt32(b + 8, true), v.getFloat64(b + 16, true)];
  }

  ayanamsa(jd: number): number {
    this.sidereal();
    return this.x.swe_get_ayanamsa_ut(jd);
  }

  /** Sidereal [longitude, latitude, speed] of a body (SE number), as ephemeris.planets. */
  calc(jd: number, body: number, speed = true): [number, number, number] {
    this.sidereal();
    const r = this.x.swe_calc_ut(jd, body, PLANET_FLAGS | (speed ? SEFLG_SPEED : 0), this.buf, this.serr);
    if (r < 0) throw new Error("swe_calc_ut failed");
    return [this.f64(0), this.f64(1), this.f64(3)];
  }

  meanNode(jd: number, speed = true): [number, number, number] {
    return this.calc(jd, SE_MEAN_NODE, speed);
  }

  /** Raw (not normalised) sidereal ascendant from whole-sign houses, as ephemeris.ascendant. */
  ascendantRaw(jd: number, lat: number, lon: number): number {
    this.sidereal();
    const cusps = this.buf, ascmc = this.buf + 40 * 8;
    if (this.x.swe_houses_ex(jd, SEFLG_SIDEREAL, lat, lon, "W".charCodeAt(0), cusps, ascmc) < 0)
      throw new Error("swe_houses_ex failed");
    return this.f64(40);
  }

  /** Sidereal cusps 1..12 (raw), whole-sign houses. */
  cuspsRaw(jd: number, lat: number, lon: number): number[] {
    this.sidereal();
    const cusps = this.buf, ascmc = this.buf + 40 * 8;
    if (this.x.swe_houses_ex(jd, SEFLG_SIDEREAL, lat, lon, "W".charCodeAt(0), cusps, ascmc) < 0)
      throw new Error("swe_houses_ex failed");
    return Array.from({ length: 12 }, (_, i) => this.f64(i + 1));
  }

  /** swe_rise_trans for the Sun with the default sunrise bits; null when none is found. */
  sunEvent(jd: number, lat: number, lon: number, alt: number, kind: number): number | null {
    const geo = this.buf + 50 * 8, tret = this.buf;
    const v = new Float64Array(this.x.memory.buffer);
    v[geo / 8] = lon; v[geo / 8 + 1] = lat; v[geo / 8 + 2] = alt;
    for (let i = 0; i < 10; i++) v[tret / 8 + i] = 0;
    const rsmi = kind | RISE_BITS;
    // pyswisseph's default flag (SEFLG_SWIEPH) is replaced by the engine's base flags.
    const r = this.x.swe_rise_trans(jd, SE_SUN, this.star, SEFLG_MOSEPH, rsmi, geo, 0, 0, tret, this.serr);
    if (r === -1) throw new Error("swe_rise_trans failed");
    return r === 0 ? this.f64(0) : null;
  }
}

// --- Python float semantics (CPython's float % and //) ------------------------
export function pymod(a: number, b: number): number {
  let m = a % b;
  if (m !== 0) { if ((b < 0) !== (m < 0)) m += b; } else m = b < 0 ? -0 : 0;
  return m;
}

export function pyfloordiv(a: number, b: number): number {
  let mod = a % b;
  let div = (a - mod) / b;
  if (mod) { if ((b < 0) !== (mod < 0)) { mod += b; div -= 1; } }
  if (div) {
    let fd = Math.floor(div);
    if (div - fd > 0.5) fd += 1;
    return fd;
  }
  return 0;
}

/** Python's int % for a positive modulus. */
export function imod(a: number, n: number): number {
  return ((a % n) + n) % n;
}
