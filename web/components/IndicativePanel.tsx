// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { IndicativePeriod } from "@/lib/api";
import { GRAHA_NAME } from "@/lib/jyotish";

const LABEL: Record<string, string> = {
  marriage: "Marriage", child: "Children", career: "Career", relocation: "Relocation or property",
};

function year(iso: string) { return iso.slice(0, 4); }

export function IndicativePanel({ periods, loading }: {
  periods: Record<string, IndicativePeriod[]> | null; loading: boolean;
}) {
  return (
    <section className="indicative" aria-busy={loading}>
      <h2>Indicative periods at this time</h2>
      <p className="muted">Antardashas whose two lords both link to the matter. Compare them with
        the person&apos;s life: periods that fit known events support this birth time.</p>
      {periods && (
        <div className="indicative-grid">
          {Object.entries(LABEL).map(([key, label]) => (
            <div key={key}>
              <h3>{label}</h3>
              {(periods[key] ?? []).length === 0 ? <p className="muted">None in 90 years</p> : (
                <ul>
                  {periods[key].slice(0, 8).map((p) => (
                    <li key={p.start}>
                      <span>{GRAHA_NAME[p.mahadasha]}–{GRAHA_NAME[p.antardasha]}</span>
                      <span className="years">{year(p.start)}–{year(p.end)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
