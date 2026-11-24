// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useEffect, useRef, useState } from "react";
import { ChartFigure, ChartStyle } from "./ChartFigure";
import { Placement, VARGAS, VARGA_NAME } from "@/lib/jyotish";

type Props = {
  title: string;
  lagnaSign: number;
  bySign: Placement[][];
  degrees?: Record<string, number>;
  style: ChartStyle;
  varga?: number;
  onVarga?: (v: number) => void;
  note?: string;
  centre: string;
};

/** A chart with its heading; flashes planets whose sign changed since the last render. */
export function ChartCard({ title, lagnaSign, bySign, degrees, style, varga, onVarga, note, centre }: Props) {
  const prev = useRef<{ lagna: number; signOf: Record<string, number> } | null>(null);
  const [flash, setFlash] = useState<Set<string>>(new Set());
  const [flashKey, setFlashKey] = useState(0);

  useEffect(() => {
    const signOf: Record<string, number> = {};
    bySign.forEach((items, s) => items.forEach((p) => { signOf[p.code] = s; }));
    const p = prev.current;
    if (p) {
      const changed = new Set<string>();
      if (p.lagna !== lagnaSign) changed.add("La");
      for (const [code, s] of Object.entries(signOf)) if (p.signOf[code] !== s) changed.add(code);
      if (changed.size) {
        setFlash(changed);
        setFlashKey((k) => k + 1);
      }
    }
    prev.current = { lagna: lagnaSign, signOf };
  }, [lagnaSign, bySign]);

  return (
    <figure className="chart-card">
      <figcaption>
        {onVarga ? (
          <label className="varga-pick">
            <span className="visually-hidden">Divisional chart</span>
            <select value={varga} onChange={(e) => onVarga(Number(e.target.value))}>
              {VARGAS.filter((v) => v !== 1).map((v) => (
                <option key={v} value={v}>D{v} {VARGA_NAME[v]}</option>
              ))}
            </select>
          </label>
        ) : (
          <h2>{title}</h2>
        )}
        {note && <span className="chart-note">{note}</span>}
      </figcaption>
      <ChartFigure style={style} lagnaSign={lagnaSign} bySign={bySign} degrees={degrees}
        flash={flash} flashKey={flashKey} title={title} centre={centre} />
    </figure>
  );
}
