// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Panchanga, PanchangaElement, Span } from "@/lib/api";
import { t } from "@/lib/i18n";
import { grahaName, signName, term } from "@/lib/vocab";

// Local clock time of a UTC instant, h:mm, with "*" after the local midnight that ends
// the sunrise's date (JHora's convention).
const utcMs = (iso: string) => Date.parse(/(Z|[+-]\d\d:\d\d)$/.test(iso) ? iso : `${iso}Z`);

function clock(iso: string, offsetHours: number, dayStartMs: number): string {
  const ms = utcMs(iso) + offsetHours * 3600_000;
  const d = new Date(ms);
  const star = ms >= dayStartMs + 86_400_000 ? "*" : "";
  return `${d.getUTCHours()}:${String(d.getUTCMinutes()).padStart(2, "0")}${star}`;
}

const pct = (f: number) => t("{p}% left", { p: (f * 100).toFixed(1) });

export function PanchangaPanel({ p }: { p: Panchanga }) {
  const off = p.utc_offset_hours;
  const riseLocal = utcMs(p.day.sunrise_utc) + off * 3600_000;
  const dayStart = riseLocal - (riseLocal % 86_400_000);
  const at = (iso: string) => clock(iso, off, dayStart);
  const span = (s: Span) => `${at(s[0])}–${at(s[1])}`;
  const list = (els: PanchangaElement[], suffix = "") =>
    els.map((e, i) => `${term(e.name)}${suffix} ${i === els.length - 1 && utcMs(e.end_utc) >= utcMs(p.day.next_sunrise_utc) ? t("(whole day)") : t("till {time}", { time: at(e.end_utc) })}`).join(", ");
  const b = p.birth;
  const lord = (e: PanchangaElement) => (e.lord ? ` (${grahaName(e.lord)})` : "");
  return (
    <details className="special-points panchanga">
      <summary>{t("Panchanga")}</summary>
      <table className="planet-table">
        <caption className="visually-hidden">{t("Panchanga at birth")}</caption>
        <tbody>
          <tr><th scope="row">{t("Year, month")}</th><td>{term(b.samvatsara)}, {term(b.masa)}</td></tr>
          <tr><th scope="row">{t("Weekday")}</th><td>{term(b.weekday)} ({t("hora of {lord}", { lord: grahaName(b.hora_lord) })})</td></tr>
          <tr><th scope="row">{t("Tithi")}</th><td>{term(b.tithi.name)}{lord(b.tithi)}, {pct(b.tithi.fraction_left)}</td></tr>
          <tr><th scope="row">{t("Nakshatra")}</th><td>{term(b.nakshatra.name)}{lord(b.nakshatra)}, {pct(b.nakshatra.fraction_left)}</td></tr>
          <tr><th scope="row">{t("Yoga")}</th><td>{term(b.yoga.name)}{lord(b.yoga)}, {pct(b.yoga.fraction_left)}</td></tr>
          <tr><th scope="row">{t("Karana")}</th><td>{term(b.karana.name)}{lord(b.karana)}, {pct(b.karana.fraction_left)}</td></tr>
          <tr><th scope="row">{t("Janma ghatis")}</th><td>{b.janma_ghatis.toFixed(2)}</td></tr>
        </tbody>
      </table>
      <h3>{t("The day, sunrise to sunrise")}</h3>
      <p className="muted">{t("Local clock times; * is after midnight.")}</p>
      <table className="planet-table">
        <caption className="visually-hidden">{t("Day panchanga")}</caption>
        <tbody>
          <tr><th scope="row">{grahaName("Su")}</th><td>{t("rises {a}, sets {b}", { a: at(p.day.sunrise_utc), b: at(p.day.sunset_utc) })}</td></tr>
          <tr><th scope="row">{grahaName("Mo")}</th><td>
            {p.day.moonrise_utc && t("rises {a}", { a: at(p.day.moonrise_utc) })}
            {p.day.moonset_utc && `, ${t("sets {b}", { b: at(p.day.moonset_utc) })}`}
            {`; ${t("in {sign}", { sign: signName(p.day.moon_sign) })} ${p.day.moon_sign_end_utc ? t("till {time}", { time: at(p.day.moon_sign_end_utc) }) : t("(whole day)")}`}
          </td></tr>
          <tr><th scope="row">{t("Tithi")}</th><td>{list(p.day.tithis)}</td></tr>
          <tr><th scope="row">{t("Nakshatra")}</th><td>{list(p.day.nakshatras)}</td></tr>
          <tr><th scope="row">{t("Yoga")}</th><td>{list(p.day.yogas)}</td></tr>
          <tr><th scope="row">{t("Karana")}</th><td>{list(p.day.karanas)}</td></tr>
          <tr><th scope="row">{t("Rahu kala")}</th><td>{span(p.day.rahu_kala)}</td></tr>
          <tr><th scope="row">{t("Gulika kala")}</th><td>{span(p.day.gulika_kala)}</td></tr>
          <tr><th scope="row">{t("Yamaganda")}</th><td>{span(p.day.yamaganda)}</td></tr>
          <tr><th scope="row">{t("Durmuhurta")}</th><td>{p.day.durmuhurta.map(span).join(", ")}</td></tr>
          <tr><th scope="row">{t("Varjya")}</th><td>{p.day.varjya.map(span).join(", ") || t("none")}</td></tr>
        </tbody>
      </table>
    </details>
  );
}
