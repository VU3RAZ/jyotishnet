// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { FormEvent, useState } from "react";
import { EventCheck, EventRule, LifeEvent, RuleSet } from "@/lib/api";
import { GRAHA_NAME } from "@/lib/jyotish";
import { prettyDate } from "@/lib/time";

type Props = {
  rules: EventRule[];
  events: LifeEvent[];
  checks: EventCheck[] | null;
  helps: boolean[] | null;
  loading: boolean;
  ruleSet: RuleSet;
  onRuleSet: (r: RuleSet) => void;
  onAdd: (e: LifeEvent) => void;
  onRemove: (i: number) => void;
};

function linkText(links: string[], ruleSet: RuleSet): string {
  return links.length ? links.join(", ") : ruleSet === "classical" ? "does not give it" : "not linked";
}

const RULE_SET_LABEL: Record<RuleSet, string> = {
  classical: "Classical (BPHS, Phaladeepika)",
  modern: "Modern (R1 links)",
};

function qualityText(c: EventCheck): string {
  if (!c.quality) return "–";
  return `${c.quality} antardasha`;
}

export function EventPanel({ rules, events, checks, helps, loading, ruleSet, onRuleSet, onAdd, onRemove }: Props) {
  const [type, setType] = useState("marriage");
  const [date, setDate] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    if (!date) return;
    onAdd({ type, date });
    setDate("");
  }

  return (
    <section className="events" aria-busy={loading}>
      <div className="events-head">
        <h2>Life events</h2>
        <p className="muted">
          Enter dated events the person is sure of. Each is checked against the dasha and transits
          for the birth time on the ribbon; the curve on the ribbon adds them up.
        </p>
        <div role="group" aria-label="Rectification rules" className="segmented quiet">
          {(Object.keys(RULE_SET_LABEL) as RuleSet[]).map((r) => (
            <button key={r} type="button" aria-pressed={ruleSet === r} onClick={() => onRuleSet(r)}>
              {RULE_SET_LABEL[r]}
            </button>
          ))}
        </div>
      </div>

      <form className="event-form" onSubmit={submit}>
        <label className="field"><span>Event</span>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {rules.map((r) => (
              <option key={r.id} value={r.id}>{r.name}{r.check_only ? " (check only)" : ""}</option>
            ))}
          </select>
        </label>
        <label className="field"><span>Date</span>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </label>
        <button type="submit" className="primary">Add event</button>
      </form>

      {events.length === 0 ? (
        <p className="muted">No events yet. Add well-dated events (marriage, first child, first job);
          the more there are, the better. The ribbon says whether together they point to a birth time
          or could fit as well by chance.</p>
      ) : (
        <div className="table-wrap">
          <table className="event-table">
            <thead>
              <tr>
                <th scope="col">Event</th>
                <th scope="col">Dasha then</th>
                <th scope="col">{ruleSet === "classical" ? "Gives the event" : "Links"}</th>
                <th scope="col">{ruleSet === "classical" ? "Period and transit" : "Jupiter and Saturn"}</th>
                <th scope="col">Fit</th>
                <th scope="col"><span className="visually-hidden">Remove</span></th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev, i) => {
                const c = checks?.[i];
                const rule = rules.find((r) => r.id === ev.type);
                return (
                  <tr key={`${ev.type}-${ev.date}-${i}`}>
                    <th scope="row">
                      {rule?.name ?? ev.type}
                      <span className="event-date">{prettyDate(`${ev.date}T00:00:00Z`)}</span>
                    </th>
                    <td>{c ? `${GRAHA_NAME[c.mahadasha ?? ""] ?? "–"} / ${GRAHA_NAME[c.antardasha ?? ""] ?? "–"}` : "…"}</td>
                    <td className="links">
                      {c && <>
                        <span><b>{GRAHA_NAME[c.antardasha ?? ""]}</b>: {linkText(c.antar_links, c.rule_set)}</span>
                        <span><b>{GRAHA_NAME[c.mahadasha ?? ""]}</b>: {linkText(c.maha_links, c.rule_set)}</span>
                      </>}
                    </td>
                    {c?.rule_set === "classical" ? (
                      <td className="links">
                        <span title={c.quality_reasons.join("\n")}>
                          <span className={`tag quality-${c.quality ?? "none"}`}>{qualityText(c)}</span>
                          {c.quality_reasons.length > 0 && <small> {c.quality_reasons.join("; ")}</small>}
                        </span>
                        {c.transit.length > 0 && <span>{c.transit.join(", ")}</span>}
                      </td>
                    ) : (
                      <td>{c ? (c.double_transit_houses.length
                        ? `Both on house ${c.double_transit_houses.join(", ")}` : "No double transit") : ""}</td>
                    )}
                    <td>
                      {c && <span className={`verdict ${c.verdict}`}>{c.verdict} ({c.score} of {c.max_score})</span>}
                      {helps?.[i] && <span className="helps" title="The verdict changes within the window, so this event helps choose a time"> helps decide</span>}
                    </td>
                    <td>
                      <button type="button" className="link-button" onClick={() => onRemove(i)}
                        aria-label={`Remove ${rule?.name ?? ev.type}`}>Remove</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {ruleSet === "classical" ? (
        <p className="rules-note">Scoring: antardasha lord gives the event +1, mahadasha lord +0.5
          (by the cited rules, e.g. Phaladeepika 10.13 for marriage, 12.25 for children, BPHS 48 for
          house lords); antardasha good +0.5, mixed +0.25 (or bad, for check-only events); Jupiter&apos;s
          transit +0.5 where a text gives one. Strong from 75% of the event&apos;s maximum, partial from
          37.5%. Events with no classical timing rule are scored on the period alone. Every rule cites
          its verse; all are drafts awaiting expert review.</p>
      ) : (
        <p className="rules-note">Scoring: antardasha lord linked +1, mahadasha lord +0.5, double
          transit +0.5; strong from 1.5, partial from 0.75. Links count lordship, occupancy or natural
          karaka in D1 and the event&apos;s varga. These are modern rules, not stated in BPHS; drafts
          awaiting expert review.</p>
      )}
    </section>
  );
}
