// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Transits } from "@/lib/api";
import { GRAHA_NAME, SIGNS } from "@/lib/jyotish";

const ORDER = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"];
const PHASE: Record<string, string> = {
  rising: "Sade Sati, rising (12th from the Moon)", peak: "Sade Sati, peak (over the Moon)",
  setting: "Sade Sati, setting (2nd from the Moon)", kantaka: "Kantaka Shani (4th from the Moon)",
  ashtama: "Ashtama Shani (8th from the Moon)",
};
const ord = (n: number) => `${n}${n === 1 ? "st" : n === 2 ? "nd" : n === 3 ? "rd" : "th"}`;
const day = (iso: string) => iso.slice(0, 10);

export function GocharaView({ tr, when }: { tr: Transits; when: string }) {
  const p = tr.planets;
  const sadeSati = tr.saturn_spells.filter((s) => ["rising", "peak", "setting"].includes(s.phase));
  return (
    <div className="gochara-view">
      <p className="view-lead">
        Transits on {when}, counted from the natal Moon. Saturn: {tr.saturn_phase ? PHASE[tr.saturn_phase] : "no Sade Sati, Kantaka or Ashtama phase"}.
      </p>
      <div className="table-wrap">
        <table className="grid-table">
          <caption className="visually-hidden">Gochara: transits from the natal Moon</caption>
          <thead>
            <tr>
              <th scope="col">Graha</th><th scope="col">Sign</th><th scope="col">From Moon</th>
              <th scope="col">Vedha</th><th scope="col">Tara</th><th scope="col">Murthi</th>
              <th scope="col" className="num">AV</th><th scope="col" className="num">SAV</th>
              <th scope="col">Kakshya</th>
            </tr>
          </thead>
          <tbody>
            {ORDER.map((g) => {
              const t = p[g];
              return (
                <tr key={g}>
                  <th scope="row">{GRAHA_NAME[g]}</th>
                  <td>{SIGNS[t.sign]}</td>
                  <td>{ord(t.house_from_moon)}{t.good ? " (good)" : ""}</td>
                  <td>{t.vedha_from.length ? `blocked by ${t.vedha_from.map((x) => GRAHA_NAME[x]).join(", ")}` : "—"}</td>
                  <td>{t.tara}</td>
                  <td>{t.murthi ?? "—"}</td>
                  <td className="num">{t.av_score ?? "—"}</td>
                  <td className="num">{t.sav_score ?? "—"}</td>
                  <td>{t.kakshya ? `${t.kakshya === "La" ? "Lagna" : GRAHA_NAME[t.kakshya]}${t.kakshya_good ? " (bindu)" : ""}` : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <h3>Sade Sati periods</h3>
      <ul className="spell-list">
        {sadeSati.map((s, i) => (
          <li key={i}>{day(s.start)} to {day(s.end)}: {s.phase}</li>
        ))}
      </ul>
      <p className="rules-note">Good houses, vedha and murthi follow Phaladeepika ch. 26 as Jagannatha
        Hora applies them. Murthi is set by the Moon when the graha entered its sign. AV is the graha&apos;s own
        Ashtakavarga bindus in the sign; the kakshya is marked when its lord gave a bindu there.</p>
    </div>
  );
}
