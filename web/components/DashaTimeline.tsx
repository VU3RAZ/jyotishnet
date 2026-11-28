// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useEffect, useState } from "react";
import { DashaPeriod, DashaSystem } from "@/lib/api";
import { N, t } from "@/lib/i18n";
import { grahaName, term } from "@/lib/vocab";
import { prettyDate } from "@/lib/time";

const SYSTEMS: { id: DashaSystem; label: string }[] = [
  { id: "vimshottari", label: N("Vimshottari") }, { id: "ashtottari", label: N("Ashtottari") },
  { id: "yogini", label: N("Yogini") },
];
// Jaimini rasi dashas, as Jagannatha Hora 8.0 computes them with its default settings.
const RASI: { id: DashaSystem; label: string }[] = [
  { id: "chara", label: N("Chara (K. N. Rao)") }, { id: "narayana", label: N("Narayana") },
  { id: "lagnamsaka", label: N("Lagnamsaka (from D-9)") }, { id: "padanaathamsa", label: N("Padanaathamsa (D-9)") },
  { id: "sudasa", label: N("Sudasa") }, { id: "drig", label: N("Drig") },
  { id: "lagna_kendradi", label: N("Lagna Kendradi") }, { id: "ak_kendradi", label: N("Atma Karaka Kendradi") },
  { id: "trikona", label: N("Trikona") }, { id: "chara_parasara", label: N("Chara (Parashara)") },
  { id: "chara_rangacharya", label: N("Chara (Iranganti Rangacharya)") }, { id: "yogardha", label: N("Yogardha") },
  { id: "shoola", label: N("Shoola") }, { id: "niryana_shoola", label: N("Niryana Shoola") },
  { id: "brahma", label: N("Brahma") }, { id: "sthira", label: N("Sthira") },
  { id: "mandooka_knrao", label: N("Mandooka (K. N. Rao)") }, { id: "navamsa", label: N("Navamsa") },
  { id: "varnada", label: N("Varnada") },
];


const label = (p: DashaPeriod) => (p.name ? term(p.name) : grahaName(p.lord));
const at = (iso: string) => Date.parse(iso);
const yr = (iso: string) => iso.slice(0, 4);
const contains = (p: DashaPeriod, ms: number) => at(p.start) <= ms && ms < at(p.end);

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
  const ref = at(refIso);
  const [maha, setMaha] = useState<number>(0);
  const [antar, setAntar] = useState<number | null>(null);

  useEffect(() => {
    const i = periods.findIndex((p) => contains(p, ref));
    setMaha(i >= 0 ? i : 0);
    const a = i >= 0 ? (periods[i].children ?? []).findIndex((p) => contains(p, ref)) : -1;
    setAntar(a >= 0 ? a : null);
  }, [periods, ref]);

  if (!periods.length) return null;
  const start = at(birthIso);
  const end = Math.min(at(periods[periods.length - 1].end), start + 120 * 365.25 * 86400_000);
  const span = end - start;
  const x = (ms: number) => `${Math.max(0, Math.min(100, ((ms - start) / span) * 100))}%`;
  const md = periods[maha];
  const ad = antar !== null ? md.children?.[antar] : undefined;

  return (
    <div className="dasha-view">
      <div className="dasha-toolbar">
        <div role="group" aria-label={t("Dasha system")} className="segmented quiet">
          {SYSTEMS.map((s) => (
            <button key={s.id} type="button" aria-pressed={system === s.id} onClick={() => onSystem(s.id)}>
              {t(s.label)}
            </button>
          ))}
        </div>
        <label className="rasi-pick">
          {t("Rasi dasha")}{" "}
          <select value={RASI.some((r) => r.id === system) ? system : ""}
            onChange={(e) => e.target.value && onSystem(e.target.value as DashaSystem)}>
            <option value="">{t("choose…")}</option>
            {RASI.map((r) => <option key={r.id} value={r.id}>{t(r.label)}</option>)}
          </select>
        </label>
        {system === "ashtottari" && applicable !== undefined && (
          <p className="muted">{applicable
            ? t("Ashtottari applies: Rahu is in a kendra or trikona from the Lagna lord.")
            : t("By the usual rule Ashtottari does not apply to this chart (Rahu is not in a kendra or trikona from the Lagna lord, or is in the Lagna).")}</p>
        )}
      </div>

      <div className="timeline" aria-label={t("Mahadashas from birth")}>
        {periods.map((p, i) => {
          const s = Math.max(at(p.start), start), e = Math.min(at(p.end), end);
          if (e <= s) return null;
          return (
            <button key={i} type="button" className={`tl-seg ${i === maha ? "selected" : ""}`}
              style={{ left: x(s), width: `calc(${x(e)} - ${x(s)})` }}
              onClick={() => { setMaha(i); setAntar(null); }}
              title={`${label(p)}: ${t("{a} to {b}", { a: prettyDate(p.start), b: prettyDate(p.end) })}`}>
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
      <p className="muted tl-note">{t("Ages in years. The marked line is {ref}.", { ref: refLabel })}</p>

      <div className="dasha-columns">
        <PeriodList title={t("{lord} mahadasha: antardashas", { lord: label(md) })}
          items={md.children ?? []} selected={antar} onSelect={setAntar} ref_={ref} />
        {ad && ad.children && ad.children.length > 0 && (
          <PeriodList title={t("{a}–{b}: pratyantars", { a: label(md), b: label(ad) })} items={ad.children}
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
      {items.length > 0 && <p className="muted">{t("From {a} to {b}.", { a: yr(items[0].start), b: yr(items[items.length - 1].end) })}</p>}
    </section>
  );
}
