// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Transits } from "@/lib/api";
import { getLang, N, t } from "@/lib/i18n";
import { grahaName, signName, term } from "@/lib/vocab";
import { prettyDate } from "@/lib/time";

const ORDER = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"];
const PHASE: Record<string, string> = {
  rising: N("Sade Sati, rising (12th from the Moon)"), peak: N("Sade Sati, peak (over the Moon)"),
  setting: N("Sade Sati, setting (2nd from the Moon)"), kantaka: N("Kantaka Shani (4th from the Moon)"),
  ashtama: N("Ashtama Shani (8th from the Moon)"),
};
const PHASE_SHORT: Record<string, string> = { rising: N("rising"), peak: N("peak"), setting: N("setting") };
const phaseName = (ph: string) => (PHASE_SHORT[ph] ? t(PHASE_SHORT[ph]) : ph);
const ord = (n: number) => `${n}${n === 1 ? "st" : n === 2 ? "nd" : n === 3 ? "rd" : "th"}`;
const ordinal = (n: number) => (getLang() === "en" ? ord(n) : t("{n}th", { n }));
const ms = (iso: string) => Date.parse(/(Z|[+-]\d\d:\d\d)$/.test(iso) ? iso : `${iso}Z`);
const NONE = <span className="none">—</span>;
type Spell = { phase: string; start: string; end: string };

/** Spells of one Sade Sati: consecutive phases with less than a year between them. */
function cycles(spells: Spell[]): Spell[][] {
  const out: Spell[][] = [];
  for (const s of [...spells].sort((a, b) => ms(a.start) - ms(b.start))) {
    const last = out[out.length - 1];
    if (last && ms(s.start) - ms(last[last.length - 1].end) < 365 * 86400_000) last.push(s);
    else out.push([s]);
  }
  return out;
}

export function GocharaView({ tr, when }: { tr: Transits; when: string }) {
  const p = tr.planets;
  const sadeSati = tr.saturn_spells.filter((s) => ["rising", "peak", "setting"].includes(s.phase));
  return (
    <div className="gochara-view">
      <p className="view-lead">
        {t("Transits on {when}, counted from the natal Moon.", { when })} {t("Saturn")}: {tr.saturn_phase ? t(PHASE[tr.saturn_phase]) : t("no Sade Sati, Kantaka or Ashtama phase")}.
      </p>
      <div className="table-wrap">
        <table className="grid-table">
          <caption className="visually-hidden">{t("Gochara: transits from the natal Moon")}</caption>
          <thead>
            <tr>
              <th scope="col">{t("Graha")}</th><th scope="col">{t("Sign")}</th><th scope="col">{t("From Moon")}</th>
              <th scope="col">{t("Vedha")}</th><th scope="col">{t("Tara")}</th><th scope="col">{t("Murthi")}</th>
              <th scope="col" className="num">AV</th><th scope="col" className="num">SAV</th>
              <th scope="col">{t("Kakshya")}</th>
            </tr>
          </thead>
          <tbody>
            {ORDER.map((g) => {
              const x = p[g];
              return (
                <tr key={g}>
                  <th scope="row">{grahaName(g)}</th>
                  <td>{signName(x.sign)}</td>
                  <td>{ordinal(x.house_from_moon)}{x.good && <span className="tag good">{t("good")}</span>}</td>
                  <td>{x.vedha_from.length ? <span className="tag low">{t("blocked by {who}", { who: x.vedha_from.map((v) => grahaName(v)).join(", ") })}</span> : NONE}</td>
                  <td>{term(x.tara)}</td>
                  <td>{x.murthi ? term(x.murthi) : NONE}</td>
                  <td className="num">{x.av_score ?? NONE}</td>
                  <td className="num">{x.sav_score ?? NONE}</td>
                  <td>{x.kakshya ? <>{grahaName(x.kakshya)}{x.kakshya_good && <span className="tag good">{t("bindu")}</span>}</> : NONE}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <section className="sade-sati" aria-labelledby="sade-sati-h">
        <h3 id="sade-sati-h">{t("Sade Sati")}</h3>
        <p className="muted small">{t("Saturn in the 12th, 1st and 2nd from the natal Moon; retrograde motion can repeat a phase.")}
          {" "}<span className="phase-key rising">{phaseName("rising")}</span> <span className="phase-key peak">{phaseName("peak")}</span>
          {" "}<span className="phase-key setting">{phaseName("setting")}</span></p>
        <ol className="cycles">
          {cycles(sadeSati).map((c, i) => {
            const a = ms(c[0].start), b = ms(c[c.length - 1].end);
            return (
              <li key={i} className="cycle">
                <span className="cycle-years">{prettyDate(c[0].start)} – {prettyDate(c[c.length - 1].end)}</span>
                <span className="cycle-bar">
                  {c.map((s, j) => (
                    <span key={j} className={`phase ${s.phase}`} title={`${phaseName(s.phase)}: ${t("{a} to {b}", { a: prettyDate(s.start), b: prettyDate(s.end) })}`}
                      style={{ left: `${((ms(s.start) - a) / (b - a)) * 100}%`, width: `${((ms(s.end) - ms(s.start)) / (b - a)) * 100}%` }} />
                  ))}
                </span>
                <span className="visually-hidden">
                  {c.map((s) => `${phaseName(s.phase)} ${t("{a} to {b}", { a: prettyDate(s.start), b: prettyDate(s.end) })}`).join("; ")}
                </span>
              </li>
            );
          })}
        </ol>
      </section>
      <p className="rules-note">{t("Good houses, vedha and murthi follow Phaladeepika ch. 26 as Jagannatha Hora applies them. Murthi is set by the Moon when the graha entered its sign. AV is the graha's own Ashtakavarga bindus in the sign; the kakshya is marked when its lord gave a bindu there.")}</p>
    </div>
  );
}
