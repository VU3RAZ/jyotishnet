// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Boundary, FitCurve } from "@/lib/api";
import { describeOffset, prettyLocal } from "@/lib/time";

export type RibbonRange = { id: string; label: string; seconds: number; step: number };

export const RECTIFY_RANGES: RibbonRange[] = [
  { id: "20m", label: "±20 min", seconds: 1200, step: 1 },
  { id: "30m", label: "±30 min", seconds: 1800, step: 1 },
  { id: "2h", label: "±2 h", seconds: 7200, step: 5 },
];
// Default rectification window: ±30 min, as in the design's BTR section
// (unrated or C-rated birth times); widen to ±2 h when the time is doubtful.
export const DEFAULT_RECTIFY_RANGE = RECTIFY_RANGES[1];

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
  curve?: FitCurve | null;
};

export function TimeRibbon({ value, onChange, range, ranges, onRange, momentMs, boundaries,
  highlightKeys, nudges, zeroLabel, curve }: Props) {
  const span = range.seconds * 2;
  const pct = (sec: number) => ((sec + range.seconds) / span) * 100;
  const keyMap = new Map(highlightKeys.map((k) => [k.key, k]));
  const ticks = boundaries
    .filter((b) => keyMap.has(b.key) && Math.abs(b.offset_min * 60) <= range.seconds)
    .map((b) => ({ ...b, ...keyMap.get(b.key)! }));
  const clamp = (v: number) => Math.max(-range.seconds, Math.min(range.seconds, v));
  const pts = curve && curve.max_score > 0
    ? curve.points.filter((p) => Math.abs(p.offset_s) <= range.seconds) : [];
  const yOf = (s: number) => 52 - (s / (curve?.max_score || 1)) * 44;
  const line = pts.map((p) => `${pct(p.offset_s).toFixed(3)},${yOf(p.score).toFixed(2)}`).join(" ");
  const best = curve?.best && Math.abs(curve.best.offset_s) <= range.seconds ? curve.best : null;
  const sig = best ? curve?.significance ?? null : null;

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
        {pts.length > 1 && (
          <svg className="fit-curve" viewBox="0 0 100 56" preserveAspectRatio="none" aria-hidden="true">
            <polygon points={`${pct(pts[0].offset_s)},56 ${line} ${pct(pts[pts.length - 1].offset_s)},56`} />
            <polyline points={line} vectorEffect="non-scaling-stroke" />
            {best && <line x1={pct(best.offset_s)} x2={pct(best.offset_s)} y1={0} y2={56}
              className={`best ${sig && sig.verdict !== "unlikely by chance" ? "doubtful" : ""}`}
              vectorEffect="non-scaling-stroke" />}
          </svg>
        )}
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
          {best && (
            <button type="button" className={`best-fit ${sig && sig.verdict !== "unlikely by chance" ? "doubtful" : ""}`}
              onClick={() => onChange(best.offset_s)} disabled={value === best.offset_s}
              aria-describedby={sig ? "fit-significance" : undefined}>
              Jump to best fit ({best.offset_s === 0 ? "recorded time" : describeOffset(best.offset_s)})
            </button>
          )}
        </div>
        {sig && (
          <p id="fit-significance" className={`fit-significance ${sig.verdict.replace(/ /g, "-")}`}>
            {sig.verdict === "unlikely by chance" ? "Life-event fit unlikely by chance"
              : sig.verdict === "weak" ? "Weak life-event fit" : "No signal in the life events"}
            {": "}random dates fit as well in {sig.random_at_least} of {sig.shuffles} tries (p = {sig.p_value.toFixed(3)})
            {sig.verdict === "no signal" ? ", so the best fit says nothing about the birth time." : "."}
          </p>
        )}
        {highlightKeys.length > 0 && (
          <p className="ribbon-legend">
            Marks show where {highlightKeys.map((k) => k.label).join(" and ")} change sign
            {pts.length > 1 ? "; the shaded curve is the life-event fit" : ""}.
          </p>
        )}
      </div>
    </section>
  );
}
