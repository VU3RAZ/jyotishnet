// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Chart } from "@/lib/api";
import { N, t } from "@/lib/i18n";
import { grahaName, signName } from "@/lib/vocab";

const KARAKAS: [string, string][] = [
  ["AK", N("Atma")], ["AmK", N("Amatya")], ["BK", N("Bhratru")], ["MK", N("Matru")], ["PiK", N("Pitru")],
  ["PK", N("Putra")], ["GK", N("Gnati")], ["DK", N("Dara")],
];
const padaName = (i: number) => (i === 0 ? "AL" : i === 11 ? "UL" : `A${i + 1}`);

export function JaiminiPoints({ chart }: { chart: Chart }) {
  const k = chart.karakas;
  const a = chart.arudhas;
  if (!k || !a) return null;
  return (
    <details className="special-points">
      <summary>{t("Chara karakas and arudhas")}</summary>
      <p>
        {KARAKAS.filter(([c]) => k[c]).map(([c, name]) => `${t(name)} (${c}) ${grahaName(k[c])}`).join(", ")}.
      </p>
      <table className="planet-table">
        <caption className="visually-hidden">{t("Bhava arudhas")}</caption>
        <thead>
          <tr><th scope="col">{t("Arudha")}</th><th scope="col">{t("Of house")}</th><th scope="col">{t("Sign")}</th></tr>
        </thead>
        <tbody>
          {a.map((s, i) => (
            <tr key={i}>
              <th scope="row">{padaName(i)}</th><td>{i + 1}</td><td>{signName(s)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
