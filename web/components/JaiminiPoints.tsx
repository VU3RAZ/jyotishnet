// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Chart } from "@/lib/api";
import { GRAHA_NAME, SIGNS } from "@/lib/jyotish";

const KARAKAS: [string, string][] = [
  ["AK", "Atma"], ["AmK", "Amatya"], ["BK", "Bhratru"], ["MK", "Matru"], ["PiK", "Pitru"],
  ["PK", "Putra"], ["GK", "Gnati"], ["DK", "Dara"],
];
const padaName = (i: number) => (i === 0 ? "AL" : i === 11 ? "UL" : `A${i + 1}`);

export function JaiminiPoints({ chart }: { chart: Chart }) {
  const k = chart.karakas;
  const a = chart.arudhas;
  if (!k || !a) return null;
  return (
    <details className="special-points">
      <summary>Chara karakas and arudhas</summary>
      <p>
        {KARAKAS.filter(([c]) => k[c]).map(([c, name]) => `${name} (${c}) ${GRAHA_NAME[k[c]]}`).join(", ")}.
      </p>
      <table className="planet-table">
        <caption className="visually-hidden">Bhava arudhas</caption>
        <thead>
          <tr><th scope="col">Arudha</th><th scope="col">Of house</th><th scope="col">Sign</th></tr>
        </thead>
        <tbody>
          {a.map((s, i) => (
            <tr key={i}>
              <th scope="row">{padaName(i)}</th><td>{i + 1}</td><td>{SIGNS[s]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
