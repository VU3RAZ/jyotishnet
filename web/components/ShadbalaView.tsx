// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Shadbala } from "@/lib/api";
import { GRAHA_NAME, SIGNS } from "@/lib/jyotish";

const GRAHAS7 = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"];
const sum = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const r1 = (v: number) => (v / 60).toFixed(2);

export function ShadbalaView({ sb }: { sb: Shadbala }) {
  const p = sb.planets;
  const rows: { label: string; get: (g: string) => number; sub?: boolean }[] = [
    { label: "Sthana", get: (g) => sum(p[g].sthana) },
    { label: "Dig", get: (g) => p[g].dig },
    { label: "Kala", get: (g) => sum(p[g].kala) },
    { label: "of which Yuddha", get: (g) => p[g].kala.yuddha ?? 0, sub: true },
    { label: "Cheshta", get: (g) => p[g].cheshta },
    { label: "Naisargika", get: (g) => p[g].naisargika },
    { label: "Drik", get: (g) => p[g].drik },
  ];
  const maxRatio = Math.max(1.6, ...GRAHAS7.map((g) => p[g].ratio));
  const ranked = [...GRAHAS7].sort((a, b) => p[b].ratio - p[a].ratio);
  return (
    <div className="sb-view">
      <p className="view-lead">
        Strongest: {GRAHA_NAME[ranked[0]]} ({p[ranked[0]].ratio.toFixed(2)} × required); weakest:
        {" "}{GRAHA_NAME[ranked[6]]} ({p[ranked[6]].ratio.toFixed(2)} ×). A ratio of 1 or more meets the
        required strength.
      </p>
      <figure className="ratio-chart" aria-label="Shadbala as a multiple of the required strength">
        {ranked.map((g) => (
          <div key={g} className="ratio-row">
            <span className="ratio-name">{GRAHA_NAME[g]}</span>
            <span className="ratio-track">
              <span className={`ratio-bar ${p[g].ratio >= 1 ? "met" : "short"}`}
                style={{ width: `${(p[g].ratio / maxRatio) * 100}%` }} />
              <span className="ratio-one" style={{ left: `${(1 / maxRatio) * 100}%` }} />
            </span>
            <span className="ratio-value">{p[g].ratio.toFixed(2)}</span>
          </div>
        ))}
        <figcaption>Bars show Shadbala ÷ required rupas; the line marks 1.0.</figcaption>
      </figure>
      <div className="table-wrap">
        <table className="grid-table">
          <caption className="visually-hidden">Shadbala components in rupas</caption>
          <thead>
            <tr><th scope="col">Rupas</th>{GRAHAS7.map((g) => <th key={g} scope="col" className="num">{GRAHA_NAME[g]}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.label} className={r.sub ? "sub-row" : ""}>
                <th scope="row">{r.label}</th>
                {GRAHAS7.map((g) => <td key={g} className="num">{r1(r.get(g))}</td>)}
              </tr>
            ))}
            <tr className="sav-row">
              <th scope="row">Total</th>
              {GRAHAS7.map((g) => <td key={g} className="num total">{p[g].rupas.toFixed(2)}</td>)}
            </tr>
            <tr>
              <th scope="row">Required</th>
              {GRAHAS7.map((g) => <td key={g} className="num">{p[g].required_rupas.toFixed(1)}</td>)}
            </tr>
          </tbody>
        </table>
      </div>
      {sb.wars.length > 0 && (
        <p>Planetary war: {sb.wars.map((w) => `${w.planets.map((x) => GRAHA_NAME[x]).join(" and ")} ${w.separation_deg.toFixed(2)}° apart`).join("; ")}.</p>
      )}
      <h3>Bhava bala</h3>
      <div className="table-wrap">
        <table className="grid-table">
          <caption className="visually-hidden">Bhava bala of the twelve houses in rupas</caption>
          <thead>
            <tr>
              <th scope="col">House</th><th scope="col">Sign</th><th scope="col">Lord</th>
              <th scope="col" className="num">Lord&apos;s bala</th><th scope="col" className="num">Dig</th>
              <th scope="col" className="num">Drik</th><th scope="col" className="num">Total</th>
            </tr>
          </thead>
          <tbody>
            {sb.houses.map((h) => (
              <tr key={h.house}>
                <th scope="row">{h.house}</th><td>{SIGNS[h.sign]}</td><td>{GRAHA_NAME[h.lord]}</td>
                <td className="num">{r1(h.lord_virupas)}</td><td className="num">{r1(h.dig)}</td>
                <td className="num">{r1(h.drik)}</td><td className="num total">{h.rupas.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="rules-note">Cheshta bala uses astronomical mean motions rather than Jagannatha
        Hora&apos;s tables, so totals can differ from JHora by a few tenths of a rupa. A house&apos;s
        Bhava bala is its lord&apos;s Shadbala plus its Dig and Drik bala (BPHS ch. 27).</p>
    </div>
  );
}
