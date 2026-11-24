// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { FormEvent, useState } from "react";
import { EventCheck, EventRule, LifeEvent } from "@/lib/api";
import { GRAHA_NAME } from "@/lib/jyotish";
import { prettyDate } from "@/lib/time";

type Props = {
  rules: EventRule[];
  events: LifeEvent[];
  checks: EventCheck[] | null;
  helps: boolean[] | null;
  loading: boolean;
  onAdd: (e: LifeEvent) => void;
  onRemove: (i: number) => void;
};

function linkText(links: string[]): string {
  return links.length ? links.join(", ") : "not linked";
}

export function EventPanel({ rules, events, checks, helps, loading, onAdd, onRemove }: Props) {
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
        <p className="muted">No events yet. Two or three well-dated events (marriage, first child,
          first job) are usually enough to see a peak.</p>
      ) : (
        <div className="table-wrap">
          <table className="event-table">
            <thead>
              <tr>
                <th scope="col">Event</th>
                <th scope="col">Dasha then</th>
                <th scope="col">Links</th>
                <th scope="col">Jupiter and Saturn</th>
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
                        <span><b>{GRAHA_NAME[c.antardasha ?? ""]}</b>: {linkText(c.antar_links)}</span>
                        <span><b>{GRAHA_NAME[c.mahadasha ?? ""]}</b>: {linkText(c.maha_links)}</span>
                      </>}
                    </td>
                    <td>{c ? (c.double_transit_houses.length
                      ? `Both on house ${c.double_transit_houses.join(", ")}` : "No double transit") : ""}</td>
                    <td>
                      {c && <span className={`verdict ${c.verdict}`}>{c.verdict} ({c.score})</span>}
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
      <p className="rules-note">Scoring: antardasha lord linked +1, mahadasha lord +0.5, double
        transit +0.5; strong from 1.5, partial from 0.75. Links count lordship, occupancy or natural
        karaka in D1 and the event&apos;s varga. These rules are drafts awaiting expert review.</p>
    </section>
  );
}
