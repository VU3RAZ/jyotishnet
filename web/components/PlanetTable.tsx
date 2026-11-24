// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Chart } from "@/lib/api";
import { GRAHA_NAME, GRAHA_ORDER, SIGNS, dms } from "@/lib/jyotish";

export function PlanetTable({ chart, varga }: { chart: Chart; varga: number }) {
  const rows = [{ ...chart.lagna, code: "La" }, ...GRAHA_ORDER.map((c) => chart.grahas[c]).filter(Boolean)];
  return (
    <table className="planet-table">
      <caption className="visually-hidden">Planet positions</caption>
      <thead>
        <tr>
          <th scope="col">Graha</th>
          <th scope="col">Sign</th>
          <th scope="col" className="num">Degree</th>
          <th scope="col">Nakshatra</th>
          <th scope="col">D{varga}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((p) => (
          <tr key={p.code}>
            <th scope="row">
              {GRAHA_NAME[p.code]}
              {p.retrograde && p.code !== "Ra" && p.code !== "Ke" && <span className="retro-tag" title="Retrograde"> R</span>}
            </th>
            <td>
              {SIGNS[p.sign]}
              {p.dignity === "exalted" && <span className="dig exalted"> exalted</span>}
              {p.dignity === "debilitated" && <span className="dig debilitated"> debilitated</span>}
              {p.dignity === "own" && <span className="dig"> own</span>}
              {p.dignity === "moolatrikona" && <span className="dig"> MT</span>}
            </td>
            <td className="num">{dms(p.degree)}</td>
            <td>{p.nakshatra} {p.pada}</td>
            <td>{p.vargas[String(varga)] === undefined ? "…"
              : SIGNS[p.vargas[String(varga)]]}{p.vargottama && varga === 9 ? " (vargottama)" : ""}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
