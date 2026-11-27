// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Transits } from "@/lib/api";
import { GRAHA_NAME, SIGNS } from "@/lib/jyotish";
import { prettyDate } from "@/lib/time";

const ORDER = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"];
const PHASE: Record<string, string> = {
  rising: "Sade Sati, rising (12th from the Moon)", peak: "Sade Sati, peak (over the Moon)",
  setting: "Sade Sati, setting (2nd from the Moon)", kantaka: "Kantaka Shani (4th from the Moon)",
  ashtama: "Ashtama Shani (8th from the Moon)",
};
const ord = (n: number) => `${n}${n === 1 ? "st" : n === 2 ? "nd" : n === 3 ? "rd" : "th"}`;
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
                  <td>{ord(t.house_from_moon)}{t.good && <span className="tag good">good</span>}</td>
                  <td>{t.vedha_from.length ? <span className="tag low">blocked by {t.vedha_from.map((x) => GRAHA_NAME[x]).join(", ")}</span> : NONE}</td>
                  <td>{t.tara}</td>
                  <td>{t.murthi ?? NONE}</td>
                  <td className="num">{t.av_score ?? NONE}</td>
                  <td className="num">{t.sav_score ?? NONE}</td>
                  <td>{t.kakshya ? <>{t.kakshya === "La" ? "Lagna" : GRAHA_NAME[t.kakshya]}{t.kakshya_good && <span className="tag good">bindu</span>}</> : NONE}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <section className="sade-sati" aria-labelledby="sade-sati-h">
        <h3 id="sade-sati-h">Sade Sati</h3>
        <p className="muted small">Saturn in the 12th, 1st and 2nd from the natal Moon; retrograde motion can
          repeat a phase. <span className="phase-key rising">rising</span> <span className="phase-key peak">peak</span>
          {" "}<span className="phase-key setting">setting</span></p>
        <ol className="cycles">
          {cycles(sadeSati).map((c, i) => {
            const a = ms(c[0].start), b = ms(c[c.length - 1].end);
            return (
              <li key={i} className="cycle">
                <span className="cycle-years">{prettyDate(c[0].start)} – {prettyDate(c[c.length - 1].end)}</span>
                <span className="cycle-bar">
                  {c.map((s, j) => (
                    <span key={j} className={`phase ${s.phase}`} title={`${s.phase}: ${prettyDate(s.start)} to ${prettyDate(s.end)}`}
                      style={{ left: `${((ms(s.start) - a) / (b - a)) * 100}%`, width: `${((ms(s.end) - ms(s.start)) / (b - a)) * 100}%` }} />
                  ))}
                </span>
                <span className="visually-hidden">
                  {c.map((s) => `${s.phase} ${prettyDate(s.start)} to ${prettyDate(s.end)}`).join("; ")}
                </span>
              </li>
            );
          })}
        </ol>
      </section>
      <p className="rules-note">Good houses, vedha and murthi follow Phaladeepika ch. 26 as Jagannatha
        Hora applies them. Murthi is set by the Moon when the graha entered its sign. AV is the graha&apos;s own
        Ashtakavarga bindus in the sign; the kakshya is marked when its lord gave a bindu there.</p>
    </div>
  );
}
