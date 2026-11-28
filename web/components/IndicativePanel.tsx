// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { IndicativePeriod, RuleSet } from "@/lib/api";
import { GRAHA_NAME } from "@/lib/jyotish";

const LABEL: Record<string, string> = {
  marriage: "Marriage", child: "Children", career: "Career", relocation: "Relocation or property",
};

function year(iso: string) { return iso.slice(0, 4); }

export function IndicativePanel({ periods, loading, ruleSet }: {
  periods: Record<string, IndicativePeriod[]> | null; loading: boolean; ruleSet: RuleSet;
}) {
  return (
    <section className="indicative" aria-busy={loading}>
      <h2>Indicative periods at this time</h2>
      <p className="muted">
        {ruleSet === "classical"
          ? "Antardashas whose lord gives the matter by the cited rules and is well placed and dignified, with nothing against it. "
          : "Antardashas whose two lords both link to the matter (modern rules). "}
        Listed from age 16 (the texts set no age limit). Such periods cover roughly a tenth to a fifth of adult life, so one match with a known event
        is weak evidence; several together, or the life-event fit above, say more.</p>
      {periods && (
        <div className="indicative-grid">
          {Object.entries(LABEL).map(([key, label]) => (
            <div key={key}>
              <h3>{label}</h3>
              {(periods[key] ?? []).length === 0 ? <p className="muted">None from age 16 to 90</p> : (
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
