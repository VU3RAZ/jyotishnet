// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { KeyboardEvent, ReactNode, useRef } from "react";
import { N, t } from "@/lib/i18n";

export type TabId = "positions" | "vargas" | "yogas" | "readings" | "ashtakavarga" | "shadbala" | "dashas" | "transits";
const TABS: { id: TabId; label: string }[] = [
  { id: "positions", label: N("Positions") }, { id: "vargas", label: N("Vargas") },
  { id: "yogas", label: N("Yogas") }, { id: "readings", label: N("Readings") },
  { id: "ashtakavarga", label: N("Ashtakavarga") }, { id: "shadbala", label: N("Strengths") },
  { id: "dashas", label: N("Dashas") }, { id: "transits", label: N("Transits") },
];

export function AnalysisTabs({ tab, onTab, children, busy }: {
  tab: TabId; onTab: (t: TabId) => void; children: ReactNode; busy: boolean;
}) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  function key(e: KeyboardEvent, i: number) {
    const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (!d) return;
    const j = (i + d + TABS.length) % TABS.length;
    onTab(TABS[j].id);
    refs.current[j]?.focus();
  }
  return (
    <section className="analysis">
      <div role="tablist" aria-label={t("Analysis")} className="tabs">
        {TABS.map((tab_, i) => (
          <button key={tab_.id} ref={(el) => { refs.current[i] = el; }} role="tab" type="button"
            id={`tab-${tab_.id}`} aria-selected={tab === tab_.id} aria-controls="analysis-panel"
            tabIndex={tab === tab_.id ? 0 : -1} onClick={() => onTab(tab_.id)} onKeyDown={(e) => key(e, i)}>
            {t(tab_.label)}
          </button>
        ))}
      </div>
      <div role="tabpanel" id="analysis-panel" aria-labelledby={`tab-${tab}`} aria-busy={busy}
        className="tab-panel">
        {children}
      </div>
    </section>
  );
}
