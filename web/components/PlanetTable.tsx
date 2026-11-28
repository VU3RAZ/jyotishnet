// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Chart } from "@/lib/api";
import { GRAHA_ORDER, dms } from "@/lib/jyotish";
import { t } from "@/lib/i18n";
import { grahaName, retroMark, signName, term } from "@/lib/vocab";

export function PlanetTable({ chart, varga }: { chart: Chart; varga: number }) {
  const rows = [{ ...chart.lagna, code: "La" }, ...GRAHA_ORDER.map((c) => chart.grahas[c]).filter(Boolean)];
  return (
    <table className="planet-table">
      <caption className="visually-hidden">{t("Planet positions")}</caption>
      <thead>
        <tr>
          <th scope="col">{t("Graha")}</th>
          <th scope="col">{t("Sign")}</th>
          <th scope="col" className="num">{t("Degree")}</th>
          <th scope="col">{t("Nakshatra")}</th>
          <th scope="col">D{varga}</th>
          <th scope="col">{t("Nadiamsa (D150)")}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((p) => (
          <tr key={p.code}>
            <th scope="row">
              {grahaName(p.code)}
              {p.retrograde && p.code !== "Ra" && p.code !== "Ke" && <span className="retro-tag" title={t("Retrograde")}> {retroMark()}</span>}
            </th>
            <td>
              {signName(p.sign)}
              {p.dignity === "exalted" && <span className="dig exalted"> {t("exalted")}</span>}
              {p.dignity === "debilitated" && <span className="dig debilitated"> {t("debilitated")}</span>}
              {p.dignity === "own" && <span className="dig"> {t("own")}</span>}
              {p.dignity === "moolatrikona" && <span className="dig"> {t("MT")}</span>}
            </td>
            <td className="num">{dms(p.degree)}</td>
            <td>{term(p.nakshatra)} {p.pada}</td>
            <td>{p.vargas[String(varga)] === undefined ? "…"
              : signName(p.vargas[String(varga)])}{p.vargottama && varga === 9 ? ` (${t("vargottama")})` : ""}</td>
            <td>{p.nadiamsa ? `${p.nadiamsa.index} ${p.nadiamsa.name}` : "…"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
