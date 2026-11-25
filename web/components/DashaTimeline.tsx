// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useEffect, useState } from "react";
import { DashaPeriod, DashaSystem } from "@/lib/api";
import { GRAHA_NAME } from "@/lib/jyotish";
import { prettyDate } from "@/lib/time";

const SYSTEMS: { id: DashaSystem; label: string }[] = [
  { id: "vimshottari", label: "Vimshottari" }, { id: "ashtottari", label: "Ashtottari" },
  { id: "yogini", label: "Yogini" },
];
// Jaimini rasi dashas, as Jagannatha Hora 8.0 computes them with its default settings.
const RASI: { id: DashaSystem; label: string }[] = [
  { id: "chara", label: "Chara (K. N. Rao)" }, { id: "narayana", label: "Narayana" },
  { id: "lagnamsaka", label: "Lagnamsaka (from D-9)" }, { id: "padanaathamsa", label: "Padanaathamsa (D-9)" },
  { id: "sudasa", label: "Sudasa" }, { id: "drig", label: "Drig" },
  { id: "lagna_kendradi", label: "Lagna Kendradi" }, { id: "ak_kendradi", label: "Atma Karaka Kendradi" },
  { id: "trikona", label: "Trikona" }, { id: "chara_parasara", label: "Chara (Parashara)" },
  { id: "chara_rangacharya", label: "Chara (Iranganti Rangacharya)" }, { id: "yogardha", label: "Yogardha" },
  { id: "shoola", label: "Shoola" }, { id: "niryana_shoola", label: "Niryana Shoola" },
  { id: "brahma", label: "Brahma" }, { id: "sthira", label: "Sthira" },
  { id: "mandooka_knrao", label: "Mandooka (K. N. Rao)" }, { id: "navamsa", label: "Navamsa" },
  { id: "varnada", label: "Varnada" },
];
const LEVEL = ["Mahadasha", "Antardasha", "Pratyantar"];

const label = (p: DashaPeriod) => p.name ?? GRAHA_NAME[p.lord] ?? p.lord;
const t = (iso: string) => Date.parse(iso);
const yr = (iso: string) => iso.slice(0, 4);
const contains = (p: DashaPeriod, ms: number) => t(p.start) <= ms && ms < t(p.end);

type Props = {
  system: DashaSystem;
  onSystem: (s: DashaSystem) => void;
  periods: DashaPeriod[];
  applicable?: boolean;
  birthIso: string;     // UTC
  refIso: string;       // UTC: the date that is marked and opened first
  refLabel: string;
};

export function DashaTimeline({ system, onSystem, periods, applicable, birthIso, refIso, refLabel }: Props) {
  const ref = t(refIso);
  const [maha, setMaha] = useState<number>(0);
  const [antar, setAntar] = useState<number | null>(null);

  useEffect(() => {
    const i = periods.findIndex((p) => contains(p, ref));
    setMaha(i >= 0 ? i : 0);
    const a = i >= 0 ? (periods[i].children ?? []).findIndex((p) => contains(p, ref)) : -1;
    setAntar(a >= 0 ? a : null);
  }, [periods, ref]);

  if (!periods.length) return null;
  const start = t(birthIso);
  const end = Math.min(t(periods[periods.length - 1].end), start + 120 * 365.25 * 86400_000);
  const span = end - start;
  const x = (ms: number) => `${Math.max(0, Math.min(100, ((ms - start) / span) * 100))}%`;
  const md = periods[maha];
  const ad = antar !== null ? md.children?.[antar] : undefined;

  return (
    <div className="dasha-view">
      <div className="dasha-toolbar">
        <div role="group" aria-label="Dasha system" className="segmented quiet">
          {SYSTEMS.map((s) => (
            <button key={s.id} type="button" aria-pressed={system === s.id} onClick={() => onSystem(s.id)}>
              {s.label}
            </button>
          ))}
        </div>
        <label className="rasi-pick">
          Rasi dasha{" "}
          <select value={RASI.some((r) => r.id === system) ? system : ""}
            onChange={(e) => e.target.value && onSystem(e.target.value as DashaSystem)}>
            <option value="">choose…</option>
            {RASI.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
          </select>
        </label>
        {system === "ashtottari" && applicable !== undefined && (
          <p className="muted">{applicable
            ? "Ashtottari applies: Rahu is in a kendra or trikona from the Lagna lord."
            : "By the usual rule Ashtottari does not apply to this chart (Rahu is not in a kendra or trikona from the Lagna lord, or is in the Lagna)."}</p>
        )}
      </div>

      <div className="timeline" aria-label="Mahadashas from birth">
        {periods.map((p, i) => {
          const s = Math.max(t(p.start), start), e = Math.min(t(p.end), end);
          if (e <= s) return null;
          return (
            <button key={i} type="button" className={`tl-seg ${i === maha ? "selected" : ""}`}
              style={{ left: x(s), width: `calc(${x(e)} - ${x(s)})` }}
              onClick={() => { setMaha(i); setAntar(null); }}
              title={`${label(p)}: ${prettyDate(p.start)} to ${prettyDate(p.end)}`}>
              <span>{label(p)}</span>
            </button>
          );
        })}
        {ref >= start && ref <= end && (
          <span className="tl-ref" style={{ left: x(ref) }} title={refLabel} aria-hidden="true" />
        )}
      </div>
      <div className="tl-axis" aria-hidden="true">
        {Array.from({ length: 13 }, (_, i) => i * 10).filter((a) => a <= 120).map((a) => (
          <span key={a} style={{ left: x(start + a * 365.25 * 86400_000) }}>{a}</span>
        ))}
      </div>
      <p className="muted tl-note">Ages in years. The marked line is {refLabel}.</p>

      <div className="dasha-columns">
        <PeriodList title={`${label(md)} ${LEVEL[0].toLowerCase()}: ${LEVEL[1]}s`}
          items={md.children ?? []} selected={antar} onSelect={setAntar} ref_={ref} />
        {ad && ad.children && ad.children.length > 0 && (
          <PeriodList title={`${label(md)}–${label(ad)}: ${LEVEL[2]}s`} items={ad.children}
            selected={null} onSelect={() => {}} ref_={ref} />
        )}
      </div>
    </div>
  );
}

function PeriodList({ title, items, selected, onSelect, ref_ }: {
  title: string; items: DashaPeriod[]; selected: number | null;
  onSelect: (i: number) => void; ref_: number;
}) {
  return (
    <section className="period-list">
      <h3>{title}</h3>
      <ol>
        {items.map((p, i) => (
          <li key={i} className={contains(p, ref_) ? "current" : ""}>
            <button type="button" aria-pressed={selected === i} onClick={() => onSelect(i)}
              disabled={!p.children?.length}>
              <span>{label(p)}</span>
              <span className="years">{prettyDate(p.start)} – {prettyDate(p.end)}</span>
            </button>
          </li>
        ))}
      </ol>
      {items.length > 0 && <p className="muted">From {yr(items[0].start)} to {yr(items[items.length - 1].end)}.</p>}
    </section>
  );
}
