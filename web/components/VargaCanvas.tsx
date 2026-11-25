// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

// Several vargas side by side (M3.2). Hover a planet to light it up in every chart;
// click it (or a chip) to keep it lit. Follows the time ribbon like the main charts.

import { useState } from "react";
import { ChartCard } from "./ChartCard";
import type { ChartStyle } from "./ChartFigure";
import { Chart } from "@/lib/api";
import { GRAHA_NAME, GRAHA_ORDER, placements, SIGNS, VARGAS, VARGA_NAME } from "@/lib/jyotish";

export const VARGA_SETS: { name: string; vargas: number[] }[] = [
  { name: "Shadvarga", vargas: [1, 2, 3, 9, 12, 30] },
  { name: "Saptavarga", vargas: [1, 2, 3, 7, 9, 12, 30] },
  { name: "Dashavarga", vargas: [1, 2, 3, 7, 9, 10, 12, 16, 30, 60] },
  { name: "Shodashavarga", vargas: [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60] },
];
export const DEFAULT_CANVAS = VARGA_SETS[2].vargas;

type Props = {
  chart: Chart | null;
  vargas: number[];
  onVargas: (v: number[]) => void;
  style: ChartStyle;
};

export function VargaCanvas({ chart, vargas, onVargas, style }: Props) {
  const [pinned, setPinned] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const highlight = hover ?? pinned;
  const onHighlight = (code: string | null, pin: boolean) => {
    if (pin) setPinned((p) => (p === code ? null : code));
    else setHover(code);
  };
  const toggle = (v: number) =>
    onVargas(vargas.includes(v) ? vargas.filter((x) => x !== v) : [...vargas, v].sort((a, b) => a - b));
  const codes = ["La", ...GRAHA_ORDER.filter((c) => chart?.grahas[c])];
  const signIn = (code: string, v: number) =>
    code === "La" ? chart?.lagna.vargas[String(v)] : chart?.grahas[code]?.vargas[String(v)];

  return (
    <div className="varga-canvas">
      <div className="canvas-controls">
        <div role="group" aria-label="Varga sets" className="segmented quiet">
          {VARGA_SETS.map((s) => (
            <button key={s.name} type="button"
              aria-pressed={s.vargas.length === vargas.length && s.vargas.every((v) => vargas.includes(v))}
              onClick={() => onVargas(s.vargas)}>{s.name}</button>
          ))}
        </div>
        <details className="varga-choose">
          <summary>Choose vargas</summary>
          <div className="varga-checks">
            {VARGAS.map((v) => (
              <label key={v}>
                <input type="checkbox" checked={vargas.includes(v)} onChange={() => toggle(v)}
                  disabled={vargas.length === 1 && vargas.includes(v)} />
                D{v}
              </label>
            ))}
          </div>
        </details>
      </div>

      <div role="group" aria-label="Follow a planet" className="follow-chips">
        <span className="muted">Follow</span>
        {codes.map((c) => (
          <button key={c} type="button" aria-pressed={pinned === c} className={highlight === c ? "lit" : ""}
            onClick={() => setPinned((p) => (p === c ? null : c))}
            onMouseEnter={() => setHover(c)} onMouseLeave={() => setHover(null)}>
            {c === "La" ? "Lagna" : c}
          </button>
        ))}
      </div>

      {!chart ? <p className="muted">Casting the vargas…</p> : (
        <>
          <div className="canvas-grid">
            {vargas.map((v) => {
              const pl = placements(chart, v);
              if (!pl) return null;
              return (
                <ChartCard key={v} title={`D${v} ${VARGA_NAME[v] ?? ""}`.trim()} style={style}
                  lagnaSign={pl.lagnaSign} bySign={pl.bySign} centre={`D${v}`}
                  highlight={highlight} onHighlight={onHighlight} />
              );
            })}
          </div>
          {highlight && (
            <table className="planet-table follow-table">
              <caption>
                {highlight === "La" ? "The Lagna" : GRAHA_NAME[highlight] ?? highlight} in each varga
              </caption>
              <thead><tr>{vargas.map((v) => <th key={v} scope="col">D{v}</th>)}</tr></thead>
              <tbody><tr>{vargas.map((v) => {
                const s = signIn(highlight, v);
                return <td key={v}>{s === undefined ? "–" : SIGNS[s].slice(0, 3)}</td>;
              })}</tr></tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}
