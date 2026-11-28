// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

// Vimshopaka bala (M2.1): points out of 20 in four schemes, for the nine grahas.

import { Vimshopaka } from "@/lib/api";
import { GRAHA_ORDER } from "@/lib/jyotish";
import { N, t } from "@/lib/i18n";
import { grahaName } from "@/lib/vocab";

const SCHEMES: [string, string][] = [
  ["shadvarga", N("Shadvarga")], ["saptavarga", N("Saptavarga")],
  ["dashavarga", N("Dashavarga")], ["shodashavarga", N("Shodashavarga")],
];

export function VimshopakaView({ v, weights, onWeights }: {
  v: Vimshopaka; weights: "bphs" | "jhora"; onWeights: (w: "bphs" | "jhora") => void;
}) {
  return (
    <section className="vimshopaka">
      <div className="section-head">
        <h3>{t("Vimshopaka bala")}</h3>
        <label className="field inline">
          <span>{t("Saptavarga weights")}</span>
          <select value={weights} onChange={(e) => onWeights(e.target.value as "bphs" | "jhora")}>
            <option value="bphs">BPHS (D7 2.5, D9 4.5, D12 2, D30 1)</option>
            <option value="jhora">{t("Jagannatha Hora (D7 1, D9 2.5, D12 4.5, D30 2)")}</option>
          </select>
        </label>
      </div>
      <p className="muted">{t("Points out of 20: each varga adds its weight scaled by the planet's dignity there.")}</p>
      <div className="table-wrap">
        <table className="grid-table vim-table">
          <caption className="visually-hidden">{t("Vimshopaka bala out of 20")}</caption>
          <thead>
            <tr><th scope="col">{t("Scheme")}</th>
              {GRAHA_ORDER.map((g) => <th key={g} scope="col" className="num">{grahaName(g)}</th>)}</tr>
          </thead>
          <tbody>
            {SCHEMES.map(([k, label]) => (
              <tr key={k}>
                <th scope="row" title={Object.entries(v.weights[k] ?? {}).map(([d, w]) => `${d} ${w}`).join(", ")}>{t(label)}</th>
                {GRAHA_ORDER.map((g) => {
                  const x = v.planets[g]?.[k];
                  return (
                    <td key={g} className="num">
                      {x === undefined ? "–" : (
                        <span className="vim-cell">
                          <span>{x.toFixed(2)}</span>
                          <span className="vim-track" aria-hidden="true">
                            <span className="vim-bar" style={{ width: `${(x / 20) * 100}%` }} />
                          </span>
                        </span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
