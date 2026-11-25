// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Panchanga, PanchangaElement, Span } from "@/lib/api";
import { GRAHA_NAME, SIGNS } from "@/lib/jyotish";

// Local clock time of a UTC instant, h:mm, with "*" after the local midnight that ends
// the sunrise's date (JHora's convention).
const utcMs = (iso: string) => Date.parse(/(Z|[+-]\d\d:\d\d)$/.test(iso) ? iso : `${iso}Z`);

function clock(iso: string, offsetHours: number, dayStartMs: number): string {
  const ms = utcMs(iso) + offsetHours * 3600_000;
  const d = new Date(ms);
  const star = ms >= dayStartMs + 86_400_000 ? "*" : "";
  return `${d.getUTCHours()}:${String(d.getUTCMinutes()).padStart(2, "0")}${star}`;
}

const pct = (f: number) => `${(f * 100).toFixed(1)}% left`;

export function PanchangaPanel({ p }: { p: Panchanga }) {
  const off = p.utc_offset_hours;
  const riseLocal = utcMs(p.day.sunrise_utc) + off * 3600_000;
  const dayStart = riseLocal - (riseLocal % 86_400_000);
  const t = (iso: string) => clock(iso, off, dayStart);
  const span = (s: Span) => `${t(s[0])}–${t(s[1])}`;
  const list = (els: PanchangaElement[], suffix = "") =>
    els.map((e, i) => `${e.name}${suffix} ${i === els.length - 1 && utcMs(e.end_utc) >= utcMs(p.day.next_sunrise_utc) ? "(whole day)" : `till ${t(e.end_utc)}`}`).join(", ");
  const b = p.birth;
  const lord = (e: PanchangaElement) => (e.lord ? ` (${GRAHA_NAME[e.lord] ?? e.lord})` : "");
  return (
    <details className="special-points panchanga">
      <summary>Panchanga</summary>
      <table className="planet-table">
        <caption className="visually-hidden">Panchanga at birth</caption>
        <tbody>
          <tr><th scope="row">Year, month</th><td>{b.samvatsara}, {b.masa}</td></tr>
          <tr><th scope="row">Weekday</th><td>{b.weekday} (hora of {GRAHA_NAME[b.hora_lord]})</td></tr>
          <tr><th scope="row">Tithi</th><td>{b.tithi.name}{lord(b.tithi)}, {pct(b.tithi.fraction_left)}</td></tr>
          <tr><th scope="row">Nakshatra</th><td>{b.nakshatra.name}{lord(b.nakshatra)}, {pct(b.nakshatra.fraction_left)}</td></tr>
          <tr><th scope="row">Yoga</th><td>{b.yoga.name}{lord(b.yoga)}, {pct(b.yoga.fraction_left)}</td></tr>
          <tr><th scope="row">Karana</th><td>{b.karana.name}{lord(b.karana)}, {pct(b.karana.fraction_left)}</td></tr>
          <tr><th scope="row">Janma ghatis</th><td>{b.janma_ghatis.toFixed(2)}</td></tr>
        </tbody>
      </table>
      <h3>The day, sunrise to sunrise</h3>
      <p className="muted">Local clock times; * is after midnight.</p>
      <table className="planet-table">
        <caption className="visually-hidden">Day panchanga</caption>
        <tbody>
          <tr><th scope="row">Sun</th><td>rises {t(p.day.sunrise_utc)}, sets {t(p.day.sunset_utc)}</td></tr>
          <tr><th scope="row">Moon</th><td>
            {p.day.moonrise_utc && `rises ${t(p.day.moonrise_utc)}`}
            {p.day.moonset_utc && `, sets ${t(p.day.moonset_utc)}`}
            {`; in ${SIGNS[p.day.moon_sign]} ${p.day.moon_sign_end_utc ? `till ${t(p.day.moon_sign_end_utc)}` : "(whole day)"}`}
          </td></tr>
          <tr><th scope="row">Tithi</th><td>{list(p.day.tithis)}</td></tr>
          <tr><th scope="row">Nakshatra</th><td>{list(p.day.nakshatras)}</td></tr>
          <tr><th scope="row">Yoga</th><td>{list(p.day.yogas)}</td></tr>
          <tr><th scope="row">Karana</th><td>{list(p.day.karanas)}</td></tr>
          <tr><th scope="row">Rahu kala</th><td>{span(p.day.rahu_kala)}</td></tr>
          <tr><th scope="row">Gulika kala</th><td>{span(p.day.gulika_kala)}</td></tr>
          <tr><th scope="row">Yamaganda</th><td>{span(p.day.yamaganda)}</td></tr>
          <tr><th scope="row">Durmuhurta</th><td>{p.day.durmuhurta.map(span).join(", ")}</td></tr>
          <tr><th scope="row">Varjya</th><td>{p.day.varjya.map(span).join(", ") || "none"}</td></tr>
        </tbody>
      </table>
    </details>
  );
}
