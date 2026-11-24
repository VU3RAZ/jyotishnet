// SPDX-License-Identifier: AGPL-3.0-or-later
// Local clock times are handled as "naive" wall-clock values: parsed as if UTC
// so arithmetic never meets the browser's own time zone or DST.

export function parseLocal(s: string): number {
  return Date.parse(s.length === 16 ? `${s}:00Z` : `${s}Z`);
}

export function formatLocal(ms: number): string {
  return new Date(ms).toISOString().slice(0, 19);
}

export function toUtcIso(localMs: number, offsetHours: number): string {
  return new Date(localMs - offsetHours * 3600_000).toISOString().slice(0, 19);
}

export function describeOffset(seconds: number): string {
  const sign = seconds < 0 ? "−" : "+";
  let s = Math.round(Math.abs(seconds));
  const d = Math.floor(s / 86400); s -= d * 86400;
  const h = Math.floor(s / 3600); s -= h * 3600;
  const m = Math.floor(s / 60); s -= m * 60;
  const parts = [];
  if (d) parts.push(`${d} d`);
  if (h) parts.push(`${h} h`);
  if (m) parts.push(`${m} min`);
  if (s || !parts.length) parts.push(`${s} s`);
  return `${seconds === 0 ? "" : sign}${parts.join(" ")}`;
}

export function prettyLocal(ms: number): string {
  const d = new Date(ms);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getUTCDate()} ${months[d.getUTCMonth()]} ${d.getUTCFullYear()}, ` +
    `${p(d.getUTCHours())}:${p(d.getUTCMinutes())}:${p(d.getUTCSeconds())}`;
}

export function prettyDate(iso: string): string {
  const d = new Date(iso);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${d.getUTCDate()} ${months[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}
