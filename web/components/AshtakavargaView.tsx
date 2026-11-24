// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { Ashtakavarga } from "@/lib/api";
import { GRAHA_NAME, SIGN_SHORT, SIGNS } from "@/lib/jyotish";

const GRAHAS7 = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"];
type Stage = "bav" | "bav_trikona" | "bav_reduced";
const STAGE_LABEL: Record<Stage, string> = {
  bav: "As counted", bav_trikona: "After Trikona shodhana", bav_reduced: "After Ekadhipatya shodhana",
};

/** Tint from 0 to max bindus, one hue, text stays legible. */
function tint(v: number, max: number) {
  return { background: `rgba(74, 87, 136, ${(0.05 + 0.4 * (v / max)).toFixed(3)})` };
}

export function AshtakavargaView({ av, lagnaSign }: { av: Ashtakavarga; lagnaSign: number }) {
  const [stage, setStage] = useState<Stage>("bav");
  const rows = av[stage];
  const sav = stage === "bav" ? av.sav
    : SIGNS.map((_, s) => GRAHAS7.reduce((t, g) => t + rows[g][s], 0));
  const max = stage === "bav" ? 8 : Math.max(1, ...GRAHAS7.flatMap((g) => rows[g]));
  const order = Array.from({ length: 12 }, (_, i) => (lagnaSign + i) % 12);
  return (
    <div className="av-view">
      <p className="view-lead">
        Bindus per sign, in house order from the Lagna. Sarvashtakavarga totals of 28 or more mark
        signs that support results; below 25 is weak.
      </p>
      <div role="group" aria-label="Reduction stage" className="segmented quiet">
        {(Object.keys(STAGE_LABEL) as Stage[]).map((s) => (
          <button key={s} type="button" aria-pressed={stage === s} onClick={() => setStage(s)}>
            {STAGE_LABEL[s]}
          </button>
        ))}
      </div>
      <div className="table-wrap">
        <table className="grid-table">
          <thead>
            <tr>
              <th scope="col">House</th>
              {order.map((s, i) => <th key={s} scope="col" className="num">{i + 1}</th>)}
              <th scope="col" className="num">Total</th>
            </tr>
            <tr className="sub">
              <th scope="col">Sign</th>
              {order.map((s) => <th key={s} scope="col" className="num" title={SIGNS[s]}>{SIGN_SHORT[s]}</th>)}
              <th scope="col" />
            </tr>
          </thead>
          <tbody>
            {GRAHAS7.map((g) => (
              <tr key={g}>
                <th scope="row">{GRAHA_NAME[g]}</th>
                {order.map((s) => (
                  <td key={s} className="num" style={tint(rows[g][s], max)}>{rows[g][s]}</td>
                ))}
                <td className="num total">{rows[g].reduce((a, b) => a + b, 0)}</td>
              </tr>
            ))}
            <tr className="sav-row">
              <th scope="row">Sarva</th>
              {order.map((s) => (
                <td key={s} className={`num ${stage === "bav" ? (sav[s] >= 28 ? "good" : sav[s] < 25 ? "low" : "") : ""}`}>
                  {sav[s]}
                </td>
              ))}
              <td className="num total">{sav.reduce((a, b) => a + b, 0)}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <h3>Shodhya pinda</h3>
      <div className="table-wrap">
        <table className="grid-table pinda">
          <thead>
            <tr><th scope="col">Graha</th><th scope="col" className="num">Rasi pinda</th>
              <th scope="col" className="num">Graha pinda</th><th scope="col" className="num">Shodhya pinda</th></tr>
          </thead>
          <tbody>
            {GRAHAS7.map((g) => (
              <tr key={g}>
                <th scope="row">{GRAHA_NAME[g]}</th>
                <td className="num">{av.rasi_pinda[g]}</td>
                <td className="num">{av.graha_pinda[g]}</td>
                <td className="num total">{av.shodhya_pinda[g]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
