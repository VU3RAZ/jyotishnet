// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Shadbala } from "@/lib/api";
import { N, t } from "@/lib/i18n";
import { grahaName, signName, term } from "@/lib/vocab";

const GRAHAS7 = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"];
const sum = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const r1 = (v: number) => (v / 60).toFixed(2);

export function ShadbalaView({ sb }: { sb: Shadbala }) {
  const p = sb.planets;
  const rows: { label: string; get: (g: string) => number; sub?: boolean }[] = [
    { label: N("Sthana"), get: (g) => sum(p[g].sthana) },
    { label: N("Dig"), get: (g) => p[g].dig },
    { label: N("Kala"), get: (g) => sum(p[g].kala) },
    { label: N("of which Yuddha"), get: (g) => p[g].kala.yuddha ?? 0, sub: true },
    { label: N("Cheshta"), get: (g) => p[g].cheshta },
    { label: N("Naisargika"), get: (g) => p[g].naisargika },
    { label: N("Drik"), get: (g) => p[g].drik },
  ];
  const maxRatio = Math.max(1.6, ...GRAHAS7.map((g) => p[g].ratio));
  const maxHouse = Math.max(...sb.houses.map((h) => h.rupas));
  const ranked = [...GRAHAS7].sort((a, b) => p[b].ratio - p[a].ratio);
  return (
    <div className="sb-view">
      <h3>{t("Shadbala")}</h3>
      <p className="view-lead">
        {t("Strongest: {a} ({x} × required); weakest: {b} ({y} ×). A ratio of 1 or more meets the required strength.", {
          a: grahaName(ranked[0]), x: p[ranked[0]].ratio.toFixed(2), b: grahaName(ranked[6]), y: p[ranked[6]].ratio.toFixed(2) })}
      </p>
      <figure className="ratio-chart" aria-label={t("Shadbala as a multiple of the required strength")}>
        {ranked.map((g) => (
          <div key={g} className="ratio-row">
            <span className="ratio-name">{grahaName(g)}</span>
            <span className="ratio-track">
              <span className={`ratio-bar ${p[g].ratio >= 1 ? "met" : "short"}`}
                style={{ width: `${(p[g].ratio / maxRatio) * 100}%` }} />
              <span className="ratio-one" style={{ left: `${(1 / maxRatio) * 100}%` }} />
            </span>
            <span className="ratio-value">{p[g].ratio.toFixed(2)}</span>
          </div>
        ))}
        <figcaption>{t("Bars show Shadbala ÷ required rupas; the line marks 1.0.")}</figcaption>
      </figure>
      <div className="table-wrap">
        <table className="grid-table">
          <caption className="visually-hidden">{t("Shadbala components in rupas")}</caption>
          <thead>
            <tr><th scope="col">{t("Rupas")}</th>{GRAHAS7.map((g) => <th key={g} scope="col" className="num">{grahaName(g)}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.label} className={r.sub ? "sub-row" : ""}>
                <th scope="row">{t(r.label)}</th>
                {GRAHAS7.map((g) => <td key={g} className="num">{r1(r.get(g))}</td>)}
              </tr>
            ))}
            <tr className="sav-row">
              <th scope="row">{t("Total")}</th>
              {GRAHAS7.map((g) => (
                <td key={g} className={`num total ${p[g].ratio >= 1 ? "good" : "low"}`}>{p[g].rupas.toFixed(2)}</td>
              ))}
            </tr>
            <tr>
              <th scope="row">{t("Required")}</th>
              {GRAHAS7.map((g) => <td key={g} className="num">{p[g].required_rupas.toFixed(1)}</td>)}
            </tr>
            <tr>
              <th scope="row">{t("Ishta phala")}</th>
              {GRAHAS7.map((g) => <td key={g} className="num">{p[g].ishta.toFixed(2)}</td>)}
            </tr>
            <tr>
              <th scope="row">{t("Kashta phala")}</th>
              {GRAHAS7.map((g) => <td key={g} className="num">{p[g].kashta.toFixed(2)}</td>)}
            </tr>
          </tbody>
        </table>
      </div>
      {sb.wars.length > 0 && (
        <p>{t("Planetary war")}: {sb.wars.map((w) => t("{who} {deg}° apart", { who: w.planets.map((x) => grahaName(x)).join(t(" and ")), deg: w.separation_deg.toFixed(2) })).join("; ")}.</p>
      )}
      <h3>{t("Bhava bala")}</h3>
      <div className="table-wrap">
        <table className="grid-table">
          <caption className="visually-hidden">{t("Bhava bala of the twelve houses in rupas")}</caption>
          <thead>
            <tr>
              <th scope="col">{t("House")}</th><th scope="col">{t("Sign")}</th><th scope="col">{t("Lord")}</th>
              <th scope="col" className="num">{t("Lord's bala")}</th><th scope="col" className="num">{t("Dig")}</th>
              <th scope="col" className="num">{t("Drik")}</th><th scope="col" className="num">{t("Total")}</th>
              <td className="bar-cell" aria-hidden="true" />
            </tr>
          </thead>
          <tbody>
            {sb.houses.map((h) => (
              <tr key={h.house}>
                <th scope="row">{h.house}</th><td>{signName(h.sign)}</td><td>{grahaName(h.lord)}</td>
                <td className="num">{r1(h.lord_virupas)}</td><td className="num">{r1(h.dig)}</td>
                <td className="num">{r1(h.drik)}</td><td className="num total">{h.rupas.toFixed(2)}</td>
                <td className="bar-cell" aria-hidden="true">
                  <span className="inline-bar" style={{ width: `${(h.rupas / maxHouse) * 100}%` }} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3>{t("Avasthas")}</h3>
      <div className="table-wrap">
        <table className="grid-table">
          <caption className="visually-hidden">{t("Avasthas (planetary states) in the Rasi chart")}</caption>
          <thead>
            <tr><th scope="col">{t("Graha")}</th><th scope="col">{t("Age (Baladi)")}</th>
              <th scope="col">{t("Alertness (Jagradadi)")}</th><th scope="col">{t("Mood")}</th></tr>
          </thead>
          <tbody>
            {Object.entries(sb.avasthas).map(([g, a]) => (
              <tr key={g}>
                <th scope="row">{grahaName(g)}</th><td>{term(a.baladi)}</td><td>{term(a.jagradadi)}</td>
                <td>{a.moods.map(term).join(", ") || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="rules-note">{t("Cheshta bala uses astronomical mean motions rather than Jagannatha Hora's tables, so totals can differ from JHora by a few tenths of a rupa. The Sun's and Moon's Cheshta bala are not counted in their totals (as JHora); they still feed Ishta and Kashta phala. A house's Bhava bala is its lord's Shadbala plus its Dig and Drik bala (BPHS ch. 27).")}</p>
    </div>
  );
}
