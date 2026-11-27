// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useState } from "react";
import { Reading, ReadingFactor, ReadingTopic } from "@/lib/api";
import { GRAHA_NAME } from "@/lib/jyotish";

export type ReadingScope = "natal" | "period";
export type Verdict = "accept" | "reject";

const ROLE: Record<string, string> = {
  lord: "House lord", occupant: "Occupant", aspect: "Aspect", karaka: "Karaka",
  varga_lord: "Varga lord", varga_occupant: "Varga occupant", yoga: "Yoga",
  dasha_maha: "Mahadasha lord", dasha_antar: "Antardasha lord",
};
const DIRECTION: Record<ReadingFactor["direction"], string> = {
  supports: "supports", obstructs: "obstructs", mixed: "mixed",
};

function subjectName(f: ReadingFactor): string {
  return f.role === "yoga" ? f.reasons[0] ?? f.subject : GRAHA_NAME[f.subject] ?? f.subject;
}

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
        Factors the classical rules weigh for one topic, ranked by how much they matter to it, and a
        short draft in which every sentence cites the engine facts it rests on. A high rank means
        “examine this”, not “this will happen”. Rules are drafts awaiting expert review.
      </p>
      <div className="reading-options">
        <label className="field inline">
          <span>Topic</span>
          <select value={topic} onChange={(e) => onTopic(e.target.value)}>
            {groups.map((g) => (
              <optgroup key={g} label={g}>
                {topics.filter((t) => t.group === g).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </optgroup>
            ))}
          </select>
        </label>
        <div className="segmented quiet" role="group" aria-label="Scope">
          <button type="button" aria-pressed={scope === "natal"} onClick={() => onScope("natal")}>Natal promise</button>
          <button type="button" aria-pressed={scope === "period"} onClick={() => onScope("period")}>
            Periods running on {dateLabel}
          </button>
        </div>
      </div>

      {!r ? <p className="muted">{loading ? "Weighing the factors…" : "No reading yet."}</p> : (
        <>
          {(r.disclaimers.length > 0 || r.notes.length > 0) && (
            <ul className="reading-notes">
              {r.disclaimers.map((d) => <li key={d} className="disclaimer">{d}</li>)}
              {r.notes.map((n) => <li key={n}>{n}</li>)}
            </ul>
          )}

          <section className="reading-draft" aria-labelledby="reading-draft-h">
            <h3 id="reading-draft-h">Draft</h3>
            {r.sentences.length === 0 ? (
              <p className="muted">
                {topics.find((t) => t.id === topic)?.technical_only
                  ? "Technical topic: the factors are listed for your own judgment and no text is drafted."
                  : "No sentence passed the checks for this topic."}
              </p>
            ) : (
              <ol className="draft">
                {r.sentences.map((s) => (
                  <li key={s.factor} className={[s.factor === focus ? "focus" : "", s.uncertain ? "uncertain" : ""].join(" ")}
                    onMouseEnter={() => setFocus(s.factor)} onMouseLeave={() => setFocus(null)}>
                    {s.text}
                    {s.uncertain && <span className="uncertain-mark" title="Depends on a Lagna that changes sign near the birth time"> (uncertain)</span>}
                    {" "}
                    {s.cites.map((id) => (
                      <a key={id} className="cite" href={`#fact-${num(id)}`} title={facts.get(id)?.text}>[{num(id)}]</a>
                    ))}
                  </li>
                ))}
              </ol>
            )}
            <p className="source muted">
              {r.topic.source.text}, {r.topic.source.section} · {r.topic.status}. {r.note}
            </p>
          </section>

          <section aria-labelledby="reading-factors-h">
            <h3 id="reading-factors-h">Ranked factors</h3>
            <div className="table-wrap">
              <table className="reading-factors">
                <thead>
                  <tr><th scope="col">#</th><th scope="col">Factor</th><th scope="col">Reads as</th>
                    <th scope="col">Weight</th><th scope="col">Why</th><th scope="col">Your view</th></tr>
                </thead>
                <tbody>
                  {r.factors.map((f, i) => (
                    <tr key={f.key} className={f.key === focus ? "focus" : ""}
                      onMouseEnter={() => setFocus(f.key)} onMouseLeave={() => setFocus(null)}>
                      <td>{i + 1}</td>
                      <th scope="row">
                        {subjectName(f)}
                        <span className="muted"> · {ROLE[f.role] ?? f.role}{f.varga !== 1 ? `, D${f.varga}` : ""}</span>
                        {f.uncertain && <span className="uncertain-mark" title="Depends on a Lagna that changes sign near the birth time"> uncertain</span>}
                      </th>
                      <td><span className={`dir ${f.direction}`}>{DIRECTION[f.direction]}</span></td>
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
                            aria-label={`${v === "accept" ? "Accept" : "Reject"} ${subjectName(f)} (${ROLE[f.role] ?? f.role})`}
                            onClick={() => onVerdict(f.key, v)}>{v === "accept" ? "Accept" : "Reject"}</button>
                        ))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="muted small">Accept and reject are kept in this computer’s chart store as labels for later training.</p>
          </section>

          <section aria-labelledby="reading-facts-h">
            <h3 id="reading-facts-h">Facts cited</h3>
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
              <summary>{r.dropped.filter((d) => d.text).length} drafted sentence(s) withheld by the checks</summary>
              <ul>{r.dropped.filter((d) => d.text).map((d, i) => <li key={i}><em>{d.reason}</em></li>)}</ul>
            </details>
          )}
        </>
      )}
    </div>
  );
}
