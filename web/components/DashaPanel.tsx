// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { RunningPeriod } from "@/lib/api";
import { GRAHA_NAME } from "@/lib/jyotish";
import { prettyDate } from "@/lib/time";

const LEVEL = ["Mahadasha", "Antardasha", "Pratyantar"];

type Props = {
  running: RunningPeriod[] | null;
  loading: boolean;
  date: string;                       // YYYY-MM-DD
  onDate?: (d: string) => void;       // editable in rectification
};

export function DashaPanel({ running, loading, date, onDate }: Props) {
  return (
    <section className="dasha" aria-busy={loading}>
      <h2>Vimshottari periods</h2>
      {onDate ? (
        <label className="field dasha-date">
          <span>Running on (an event date helps rectification)</span>
          <input type="date" value={date} onChange={(e) => e.target.value && onDate(e.target.value)} />
        </label>
      ) : (
        <p className="muted dasha-on">Running on {prettyDate(`${date}T00:00:00Z`)}</p>
      )}
      {running && running.length ? (
        <ol>
          {running.map((p) => (
            <li key={p.level}>
              <span className="dasha-level">{LEVEL[p.level - 1]}</span>
              <span className="dasha-lord">{GRAHA_NAME[p.lord] ?? p.lord}</span>
              <span className="dasha-dates">{prettyDate(p.start)} to {prettyDate(p.end)}</span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="muted">{loading ? "Working out the periods…" : "This date falls outside the 120 years counted from birth."}</p>
      )}
    </section>
  );
}
