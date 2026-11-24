// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Boundary } from "@/lib/api";
import { describeOffset, prettyLocal } from "@/lib/time";

export type RibbonRange = { id: string; label: string; seconds: number; step: number };

export const RECTIFY_RANGES: RibbonRange[] = [
  { id: "20m", label: "±20 min", seconds: 1200, step: 1 },
  { id: "2h", label: "±2 h", seconds: 7200, step: 5 },
];
export const TRANSIT_RANGES: RibbonRange[] = [
  { id: "3d", label: "±3 days", seconds: 3 * 86400, step: 60 },
  { id: "1y", label: "±1 year", seconds: 366 * 86400, step: 3600 },
  { id: "12y", label: "±12 years", seconds: 12 * 366 * 86400, step: 86400 },
];

type Props = {
  value: number;
  onChange: (v: number) => void;
  range: RibbonRange;
  ranges: RibbonRange[];
  onRange: (r: RibbonRange) => void;
  momentMs: number;
  boundaries: Boundary[];
  highlightKeys: { key: string; label: string; strong: boolean }[];
  nudges: number[];
  zeroLabel: string;
};

export function TimeRibbon({ value, onChange, range, ranges, onRange, momentMs, boundaries,
  highlightKeys, nudges, zeroLabel }: Props) {
  const span = range.seconds * 2;
  const pct = (sec: number) => ((sec + range.seconds) / span) * 100;
  const keyMap = new Map(highlightKeys.map((k) => [k.key, k]));
  const ticks = boundaries
    .filter((b) => keyMap.has(b.key) && Math.abs(b.offset_min * 60) <= range.seconds)
    .map((b) => ({ ...b, ...keyMap.get(b.key)! }));
  const clamp = (v: number) => Math.max(-range.seconds, Math.min(range.seconds, v));

  return (
    <section className="ribbon">
      <div className="ribbon-readout">
        <output className="ribbon-moment" htmlFor="ribbon-input">{prettyLocal(momentMs)}</output>
        <span className="ribbon-offset">{value === 0 ? zeroLabel : describeOffset(value)}</span>
        <div className="ribbon-ranges" role="group" aria-label="Slider range">
          {ranges.map((r) => (
            <button key={r.id} type="button" aria-pressed={r.id === range.id}
              onClick={() => onRange(r)}>{r.label}</button>
          ))}
        </div>
      </div>

      <div className="ribbon-track">
        <div className="ribbon-ticks" aria-hidden="true">
          {ticks.map((t, i) => (
            <span key={i} className={t.strong ? "tick strong" : "tick"}
              style={{ left: `${pct(t.offset_min * 60)}%` }}
              title={`${t.label} changes at ${describeOffset(t.offset_min * 60)}`} />
          ))}
          <span className="tick zero" style={{ left: "50%" }} />
        </div>
        <input id="ribbon-input" type="range" min={-range.seconds} max={range.seconds}
          step={range.step} value={value} onChange={(e) => onChange(Number(e.target.value))}
          aria-valuetext={`${prettyLocal(momentMs)}, ${describeOffset(value)}`} />
      </div>

      <div className="ribbon-controls">
        <div className="nudges" role="group" aria-label="Step the time">
          {nudges.map((n) => (
            <button key={n} type="button" onClick={() => onChange(clamp(value + n))}>
              {describeOffset(n)}
            </button>
          ))}
          <button type="button" onClick={() => onChange(0)} disabled={value === 0}>Reset</button>
        </div>
        {highlightKeys.length > 0 && (
          <p className="ribbon-legend">
            Marks show where {highlightKeys.map((k) => k.label).join(" and ")} change sign.
          </p>
        )}
      </div>
    </section>
  );
}
