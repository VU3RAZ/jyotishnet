// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { KeyboardEvent, ReactNode, useRef } from "react";

export type TabId = "positions" | "vargas" | "yogas" | "readings" | "ashtakavarga" | "shadbala" | "dashas" | "transits";
const TABS: { id: TabId; label: string }[] = [
  { id: "positions", label: "Positions" }, { id: "vargas", label: "Vargas" },
  { id: "yogas", label: "Yogas" }, { id: "readings", label: "Readings" },
  { id: "ashtakavarga", label: "Ashtakavarga" }, { id: "shadbala", label: "Strengths" },
  { id: "dashas", label: "Dashas" }, { id: "transits", label: "Transits" },
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
      <div role="tablist" aria-label="Analysis" className="tabs">
        {TABS.map((t, i) => (
          <button key={t.id} ref={(el) => { refs.current[i] = el; }} role="tab" type="button"
            id={`tab-${t.id}`} aria-selected={tab === t.id} aria-controls="analysis-panel"
            tabIndex={tab === t.id ? 0 : -1} onClick={() => onTab(t.id)} onKeyDown={(e) => key(e, i)}>
            {t.label}
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
