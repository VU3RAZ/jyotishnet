// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Chart } from "@/lib/api";
import { dms } from "@/lib/jyotish";
import { N, t } from "@/lib/i18n";
import { grahaName, signName, term } from "@/lib/vocab";

const POINTS: [string, string][] = [
  ["BL", N("Bhava Lagna")], ["HL", N("Hora Lagna")], ["GL", N("Ghati Lagna")], ["ViL", N("Vighati Lagna")],
  ["PP", N("Pranapada")], ["VL", N("Varnada Lagna")], ["SL", N("Sree Lagna")], ["IL", N("Indu Lagna")],
  ["BB", N("Bhrigu Bindu")], ["Md", N("Maandi")], ["Gk", N("Gulika")], ["Kl", N("Kaala")], ["Mr", N("Mrityu")],
  ["AP", N("Artha Prahara")], ["YG", N("Yama Ghantaka")], ["Dh", N("Dhooma")], ["Vy", N("Vyatipata")],
  ["Pv", N("Parivesha")], ["IC", N("Indra Chapa")], ["UK", N("Upaketu")],
];

export function SpecialPoints({ chart }: { chart: Chart }) {
  const sp = chart.special;
  if (!sp) return null;
  const y = chart.yogi;
  return (
    <details className="special-points">
      <summary>{t("Special lagnas and upagrahas")}</summary>
      {y && (
        <p>
          {t("Yogi point {sign} {deg}: Yogi {y}, Sahayogi {s}; Avayogi {a}.", { sign: signName(Math.floor(y.point / 30)),
            deg: dms(y.point % 30), y: grahaName(y.yogi), s: grahaName(y.sahayogi), a: grahaName(y.avayogi) })}
        </p>
      )}
      <table className="planet-table">
        <caption className="visually-hidden">{t("Special lagnas and upagrahas")}</caption>
        <thead>
          <tr>
            <th scope="col">{t("Point")}</th><th scope="col">{t("Sign")}</th>
            <th scope="col" className="num">{t("Degree")}</th><th scope="col">{t("Nakshatra")}</th>
          </tr>
        </thead>
        <tbody>
          {POINTS.filter(([k]) => sp[k]).map(([k, name]) => (
            <tr key={k}>
              <th scope="row">{t(name)}</th><td>{signName(sp[k].sign)}</td>
              <td className="num">{dms(sp[k].degree)}</td><td>{term(sp[k].nakshatra)} {sp[k].pada}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
