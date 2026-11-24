// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Chart } from "@/lib/api";
import { GRAHA_NAME, SIGNS, dms } from "@/lib/jyotish";

const POINTS: [string, string][] = [
  ["BL", "Bhava Lagna"], ["HL", "Hora Lagna"], ["GL", "Ghati Lagna"], ["ViL", "Vighati Lagna"],
  ["PP", "Pranapada"], ["VL", "Varnada Lagna"], ["SL", "Sree Lagna"], ["IL", "Indu Lagna"],
  ["BB", "Bhrigu Bindu"], ["Md", "Maandi"], ["Gk", "Gulika"], ["Kl", "Kaala"], ["Mr", "Mrityu"],
  ["AP", "Artha Prahara"], ["YG", "Yama Ghantaka"], ["Dh", "Dhooma"], ["Vy", "Vyatipata"],
  ["Pv", "Parivesha"], ["IC", "Indra Chapa"], ["UK", "Upaketu"],
];

export function SpecialPoints({ chart }: { chart: Chart }) {
  const sp = chart.special;
  if (!sp) return null;
  const y = chart.yogi;
  return (
    <details className="special-points">
      <summary>Special lagnas and upagrahas</summary>
      {y && (
        <p>
          Yogi point {SIGNS[Math.floor(y.point / 30)]} {dms(y.point % 30)}: Yogi {GRAHA_NAME[y.yogi]},
          Sahayogi {GRAHA_NAME[y.sahayogi]}; Avayogi {GRAHA_NAME[y.avayogi]}.
        </p>
      )}
      <table className="planet-table">
        <caption className="visually-hidden">Special lagnas and upagrahas</caption>
        <thead>
          <tr>
            <th scope="col">Point</th><th scope="col">Sign</th>
            <th scope="col" className="num">Degree</th><th scope="col">Nakshatra</th>
          </tr>
        </thead>
        <tbody>
          {POINTS.filter(([k]) => sp[k]).map(([k, name]) => (
            <tr key={k}>
              <th scope="row">{name}</th><td>{SIGNS[sp[k].sign]}</td>
              <td className="num">{dms(sp[k].degree)}</td><td>{sp[k].nakshatra} {sp[k].pada}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
