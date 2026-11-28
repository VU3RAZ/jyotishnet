// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { RunningPeriod } from "@/lib/api";
import { N, t } from "@/lib/i18n";
import { grahaName } from "@/lib/vocab";
import { prettyDate } from "@/lib/time";

const LEVEL = [N("Mahadasha"), N("Antardasha"), N("Pratyantar")];

type Props = {
  running: RunningPeriod[] | null;
  loading: boolean;
  date: string;                       // YYYY-MM-DD
  onDate?: (d: string) => void;       // editable in rectification
};

export function DashaPanel({ running, loading, date, onDate }: Props) {
  return (
    <section className="dasha" aria-busy={loading}>
      <h2>{t("Vimshottari periods")}</h2>
      {onDate ? (
        <label className="field dasha-date">
          <span>{t("Running on (an event date helps rectification)")}</span>
          <input type="date" value={date} onChange={(e) => e.target.value && onDate(e.target.value)} />
        </label>
      ) : (
        <p className="muted dasha-on">{t("Running on {date}", { date: prettyDate(`${date}T00:00:00Z`) })}</p>
      )}
      {running && running.length ? (
        <ol>
          {running.map((p) => (
            <li key={p.level}>
              <span className="dasha-level">{t(LEVEL[p.level - 1])}</span>
              <span className="dasha-lord">{grahaName(p.lord)}</span>
              <span className="dasha-dates">{t("{a} to {b}", { a: prettyDate(p.start), b: prettyDate(p.end) })}</span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="muted">{loading ? t("Working out the periods…") : t("This date falls outside the 120 years counted from birth.")}</p>
      )}
    </section>
  );
}
