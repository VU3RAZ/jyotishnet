// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { Reading, ReadingFactor, ReadingTopic } from "@/lib/api";
import { getLang, N, t } from "@/lib/i18n";
import { grahaName, term, topicName } from "@/lib/vocab";

export type ReadingScope = "natal" | "period";
export type Verdict = "accept" | "reject";

const ROLE: Record<string, string> = {
  lord: N("House lord"), occupant: N("Occupant"), aspect: N("Aspect"), karaka: N("Karaka"),
  varga_lord: N("Varga lord"), varga_occupant: N("Varga occupant"), yoga: N("Yoga"),
  dasha_maha: N("Mahadasha lord"), dasha_antar: N("Antardasha lord"),
};

function subjectName(f: ReadingFactor): string {
  return f.role === "yoga" ? f.reasons[0] ?? f.subject : grahaName(f.subject);
}
const roleName = (f: ReadingFactor) => (ROLE[f.role] ? t(ROLE[f.role]) : f.role);
// How each factor reads, in every topic (the API sends the English labels).
const DIRECTION = { supports: N("favours the native"), obstructs: N("against the native"), mixed: N("mixed") };
const dirLabel = (r: Reading, d: keyof typeof DIRECTION) => (getLang() === "en" ? r.topic.labels[d] : t(DIRECTION[d]));

export function ReadingView({ topics, topic, onTopic, scope, onScope, dateLabel, reading, loading,
  verdicts, onVerdict }: {
  topics: ReadingTopic[]; topic: string; onTopic: (t: string) => void;
  scope: ReadingScope; onScope: (s: ReadingScope) => void; dateLabel: string;
  reading: Reading | null; loading: boolean;
  verdicts: Record<string, Verdict>; onVerdict: (factor: string, v: Verdict) => void;
}) {
  const [focus, setFocus] = useState<string | null>(null);
  const groups = Array.from(new Set(topics.map((t) => t.group)));
  const r = reading && reading.topic.id === topic ? reading : null;
  // Number the facts in the order the draft (or, without one, the factors) first cites them.
  const order: string[] = [];
  for (const ids of r ? (r.sentences.length ? r.sentences.map((s) => s.cites) : r.factors.map((f) => f.facts)) : [])
    for (const id of ids) if (!order.includes(id)) order.push(id);
  const facts = new Map(r?.facts.map((f) => [f.id, f]) ?? []);
  const num = (id: string) => order.indexOf(id) + 1;
  const focusFacts = new Set(r?.factors.find((f) => f.key === focus)?.facts ?? []);

  return (
    <div className="reading-view">
      <p className="view-lead">
        {t("Factors the classical rules weigh for one topic, ranked by how much they matter to it, and a short draft in which every sentence cites the engine facts it rests on. A high rank means “examine this”, not “this will happen”. Rules are drafts awaiting expert review.")}
      </p>
      <div className="reading-options">
        <label className="field inline">
          <span>{t("Topic")}</span>
          <select value={topic} onChange={(e) => onTopic(e.target.value)}>
            {groups.map((g) => (
              <optgroup key={g} label={term(g)}>
                {topics.filter((tp) => tp.group === g).map((tp) => <option key={tp.id} value={tp.id}>{topicName(tp.id, tp.name)}</option>)}
              </optgroup>
            ))}
          </select>
        </label>
        <div className="segmented quiet" role="group" aria-label={t("Scope")}>
          <button type="button" aria-pressed={scope === "natal"} onClick={() => onScope("natal")}>{t("Natal promise")}</button>
          <button type="button" aria-pressed={scope === "period"} onClick={() => onScope("period")}>
            {t("Periods running on {date}", { date: dateLabel })}
          </button>
        </div>
      </div>

      {!r ? <p className="muted">{loading ? t("Weighing the factors…") : t("No reading yet.")}</p> : (
        <>
          {(r.disclaimers.length > 0 || r.notes.length > 0) && (
            <ul className="reading-notes">
              {r.disclaimers.map((d) => <li key={d} className="disclaimer">{d}</li>)}
              {r.notes.map((n) => <li key={n}>{n}</li>)}
            </ul>
          )}

          {scope === "period" && (
            <section className="reading-periods" aria-labelledby="reading-periods-h">
              <h3 id="reading-periods-h">{t("Periods running on {date}", { date: dateLabel })}</h3>
              <ul>
                {r.periods.map((p) => (
                  <li key={p.level} className={p.factor ? "tied" : "not-tied"}>
                    <strong>{p.level === 1 ? t("Mahadasha of {lord}", { lord: grahaName(p.lord) }) : t("Antardasha of {lord}", { lord: grahaName(p.lord) })}</strong>
                    {" "}<span className="muted">({t("{a} to {b}", { a: p.start, b: p.end })})</span>:{" "}
                    {p.tied.length === 0
                      ? t("not tied to this topic (it lords none of the topic's houses, sits in none and is not its karaka), so it adds no factor.")
                      : p.factor
                        ? t("tied to this topic ({why}); added as a ranked factor below.", { why: p.tied.join("; ") })
                        : t("tied to this topic ({why}), but ranked below the factors shown.", { why: p.tied.join("; ") })}
                  </li>
                ))}
              </ul>
              {r.periods.length === 0 && (
                <p className="muted">{t("No Vimshottari period runs on this date: it falls outside the 120-year cycle from birth. Pick an event or transit date within it.")}</p>
              )}
              {r.periods.every((p) => !p.factor) && (
                <p className="muted">{t("So for this topic and date, the reading is the same as the natal promise.")}</p>
              )}
            </section>
          )}

          <section className="reading-draft" aria-labelledby="reading-draft-h">
            <h3 id="reading-draft-h">{t("Draft")}</h3>
            {r.sentences.length === 0 ? (
              <p className="muted">
                {topics.find((tp) => tp.id === topic)?.technical_only
                  ? t("Technical topic: the factors are listed for your own judgment and no text is drafted.")
                  : t("No sentence passed the checks for this topic.")}
              </p>
            ) : (
              <ol className="draft">
                {r.sentences.map((s) => (
                  <li key={s.factor} className={[s.factor === focus ? "focus" : "", s.uncertain ? "uncertain" : ""].join(" ")}
                    onMouseEnter={() => setFocus(s.factor)} onMouseLeave={() => setFocus(null)}>
                    {s.text}
                    {s.uncertain && <span className="uncertain-mark" title={t("Depends on a Lagna that changes sign near the birth time")}> ({t("uncertain")})</span>}
                    {" "}
                    {s.cites.map((id) => (
                      <a key={id} className="cite" href={`#fact-${num(id)}`} title={facts.get(id)?.text}>[{num(id)}]</a>
                    ))}
                  </li>
                ))}
              </ol>
            )}
            <p className="source muted">
              {r.topic.source.text}, {r.topic.source.section} · {r.topic.status === "draft" ? t("draft") : r.topic.status}. {r.note}
            </p>
          </section>

          <section aria-labelledby="reading-factors-h">
            <h3 id="reading-factors-h">{t("Ranked factors")}</h3>
            <p className="muted reads-as-note">
              {t("“Reads as” says how the rule in “Why” reads each factor for {theme}: “{a}”, “{b}” or “{c}”.", {
                theme: r.topic.theme,           // written by the engine in the interface language
                a: dirLabel(r, "supports"), b: dirLabel(r, "obstructs"), c: dirLabel(r, "mixed") })}
            </p>
            <div className="table-wrap">
              <table className="reading-factors">
                <thead>
                  <tr><th scope="col">#</th><th scope="col">{t("Factor")}</th><th scope="col">{t("Reads as")}</th>
                    <th scope="col">{t("Weight")}</th><th scope="col">{t("Why")}</th><th scope="col">{t("Your view")}</th></tr>
                </thead>
                <tbody>
                  {r.factors.map((f, i) => (
                    <tr key={f.key} className={f.key === focus ? "focus" : ""}
                      onMouseEnter={() => setFocus(f.key)} onMouseLeave={() => setFocus(null)}>
                      <td>{i + 1}</td>
                      <th scope="row">
                        {subjectName(f)}
                        <span className="muted"> · {roleName(f)}{f.varga !== 1 ? `, D${f.varga}` : ""}</span>
                        {f.uncertain && <span className="uncertain-mark" title={t("Depends on a Lagna that changes sign near the birth time")}> {t("uncertain")}</span>}
                      </th>
                      <td><span className={`dir ${f.direction}`}>{dirLabel(r, f.direction)}</span></td>
                      <td className="weight">
                        <span className="weight-track" aria-hidden="true">
                          <span className="inline-bar" style={{ width: `${Math.min(1, f.score) * 100}%` }} />
                        </span>
                        {f.score.toFixed(2)}
                      </td>
                      <td className="why">{f.reasons.join("; ")}</td>
                      <td className="verdict">
                        {(["accept", "reject"] as Verdict[]).map((v) => (
                          <button key={v} type="button" aria-pressed={verdicts[f.key] === v}
                            aria-label={`${v === "accept" ? t("Accept") : t("Reject")} ${subjectName(f)} (${roleName(f)})`}
                            onClick={() => onVerdict(f.key, v)}>{v === "accept" ? t("Accept") : t("Reject")}</button>
                        ))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="muted small">{t("Accept and reject are kept in this computer’s chart store as labels for later training.")}</p>
          </section>

          <section aria-labelledby="reading-facts-h">
            <h3 id="reading-facts-h">{t("Facts cited")}</h3>
            <ol className="reading-facts">
              {order.map((id) => (
                <li key={id} id={`fact-${num(id)}`} className={focusFacts.has(id) ? "focus" : ""}>
                  {facts.get(id)?.text ?? id} <code>{id}</code>
                </li>
              ))}
            </ol>
          </section>

          {r.dropped.some((d) => d.text) && (
            <details className="reading-dropped">
              <summary>{t("{n} drafted sentence(s) withheld by the checks", { n: r.dropped.filter((d) => d.text).length })}</summary>
              <ul>{r.dropped.filter((d) => d.text).map((d, i) => <li key={i}><em>{d.reason}</em></li>)}</ul>
            </details>
          )}
        </>
      )}
    </div>
  );
}
