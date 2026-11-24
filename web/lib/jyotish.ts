// SPDX-License-Identifier: AGPL-3.0-or-later
export const SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];
export const SIGN_SHORT = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"];
export const GRAHA_ORDER = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"];
export const GRAHA_NAME: Record<string, string> = {
  Su: "Sun", Mo: "Moon", Ma: "Mars", Me: "Mercury", Ju: "Jupiter", Ve: "Venus",
  Sa: "Saturn", Ra: "Rahu", Ke: "Ketu", La: "Lagna",
};
export const VARGA_NAME: Record<number, string> = {
  1: "Rasi", 2: "Hora", 3: "Drekkana", 4: "Chaturthamsa", 7: "Saptamsa", 9: "Navamsa",
  10: "Dasamsa", 12: "Dwadasamsa", 16: "Shodasamsa", 20: "Vimsamsa", 24: "Chaturvimsamsa",
  27: "Bhamsa", 30: "Trimsamsa", 40: "Khavedamsa", 45: "Akshavedamsa", 60: "Shashtiamsa",
  5: "Panchamsa", 6: "Shashthamsa", 8: "Ashtamsa", 11: "Rudramsa", 81: "Navanavamsa",
  108: "Ashtottaramsa", 144: "Dwadasa-dwadasamsa",
};
export const VARGAS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24, 27, 30, 40, 45, 60, 81, 108, 144];

/** 16°53′ style degree within a sign. */
export function dms(deg: number): string {
  const d = Math.floor(deg);
  const m = Math.floor((deg - d) * 60);
  return `${d}°${String(m).padStart(2, "0")}′`;
}

export type Placement = { code: string; label: string; retro: boolean; dignity: string | null };

/** Group the chart's points by sign for one varga, or null when the chart was
 * computed without that varga (e.g. the previous response while a new one loads). */
export function placements(chart: { lagna: { vargas: Record<string, number> };
  grahas: Record<string, { vargas: Record<string, number>; retrograde: boolean | null; dignity: string | null }> },
  varga: number): { lagnaSign: number; bySign: Placement[][] } | null {
  if (chart.lagna.vargas[String(varga)] === undefined) return null;
  const bySign: Placement[][] = Array.from({ length: 12 }, () => []);
  for (const code of GRAHA_ORDER) {
    const g = chart.grahas[code];
    if (!g) continue;
    const s = g.vargas[String(varga)];
    if (s === undefined) continue;
    bySign[s].push({ code, label: code, retro: !!g.retrograde && code !== "Ra" && code !== "Ke",
      dignity: varga === 1 ? g.dignity : null });
  }
  return { lagnaSign: chart.lagna.vargas[String(varga)], bySign };
}
