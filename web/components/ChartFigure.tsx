// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Placement, SIGN_SHORT } from "@/lib/jyotish";

export type ChartStyle = "north" | "south";

type Props = {
  style: ChartStyle;
  lagnaSign: number;
  bySign: Placement[][];
  degrees?: Record<string, number>; // shown in the Rasi chart only
  flash: Set<string>;               // planet codes (or "La") that just changed sign
  flashKey: number;                 // bumps to restart the flash animation
  title: string;
  centre: string;                   // short label for the South Indian centre
  highlight?: string | null;        // planet code (or "La") lit up in every linked chart
  onHighlight?: (code: string | null, pin: boolean) => void;
};

type Link = { highlight?: string | null; onHighlight?: (code: string | null, pin: boolean) => void };

// North Indian: houses are fixed, signs rotate. Polygons in a 400 x 400 box.
const NORTH_HOUSES: { poly: string; c: [number, number]; n: [number, number] }[] = [
  { poly: "200,0 300,100 200,200 100,100", c: [200, 95], n: [200, 182] },
  { poly: "0,0 200,0 100,100", c: [100, 38], n: [100, 84] },
  { poly: "0,0 100,100 0,200", c: [36, 100], n: [84, 104] },
  { poly: "0,200 100,100 200,200 100,300", c: [100, 200], n: [184, 204] },
  { poly: "0,200 100,300 0,400", c: [36, 300], n: [84, 304] },
  { poly: "0,400 100,300 200,400", c: [100, 364], n: [100, 324] },
  { poly: "200,400 100,300 200,200 300,300", c: [200, 305], n: [200, 226] },
  { poly: "200,400 300,300 400,400", c: [300, 364], n: [300, 324] },
  { poly: "400,400 300,300 400,200", c: [364, 300], n: [316, 304] },
  { poly: "400,200 300,300 200,200 300,100", c: [300, 200], n: [216, 204] },
  { poly: "400,200 300,100 400,0", c: [364, 100], n: [316, 104] },
  { poly: "400,0 300,100 200,0", c: [300, 38], n: [300, 84] },
];

// South Indian: signs are fixed in a 4 x 4 ring (Pisces top-left).
const SOUTH_CELL: [number, number][] = [
  [1, 0], [2, 0], [3, 0], [3, 1], [3, 2], [3, 3], [2, 3], [1, 3], [0, 3], [0, 2], [0, 1], [0, 0],
];

function PlanetLines({ items, x, y, compact, degrees, flash, flashKey, highlight, onHighlight }: {
  items: Placement[]; x: number; y: number; compact: boolean;
  degrees?: Record<string, number>; flash: Set<string>; flashKey: number;
} & Link) {
  const lineH = 17;
  const cols = compact && items.length > 3 ? 2 : 1;
  const rows = Math.ceil(items.length / cols);
  const top = y - ((rows - 1) * lineH) / 2;
  return (
    <>
      {items.map((p, i) => {
        const col = cols === 2 ? i % 2 : 0;
        const row = cols === 2 ? Math.floor(i / 2) : i;
        const px = cols === 2 ? x + (col === 0 ? -20 : 20) : x;
        const cls = ["planet",
          p.dignity === "exalted" ? "exalted" : "",
          p.dignity === "debilitated" ? "debilitated" : "",
          flash.has(p.code) ? "flash" : "",
          highlight === p.code ? "linked" : "",
          onHighlight ? "pickable" : ""].join(" ");
        const deg = degrees && degrees[p.code] !== undefined && cols === 1
          ? ` ${Math.floor(degrees[p.code])}°` : "";
        return (
          <text key={`${p.code}-${flash.has(p.code) ? flashKey : 0}`} x={px} y={top + row * lineH}
            className={cls} textAnchor="middle" dominantBaseline="middle"
            onMouseEnter={onHighlight && (() => onHighlight(p.code, false))}
            onMouseLeave={onHighlight && (() => onHighlight(null, false))}
            onClick={onHighlight && (() => onHighlight(p.code, true))}>
            {p.label}{deg}
            {p.retro && <tspan className="retro" dy={-5} fontSize="9">R</tspan>}
          </text>
        );
      })}
    </>
  );
}

export function ChartFigure({ style, lagnaSign, bySign, degrees, flash, flashKey, title, centre,
  highlight, onHighlight }: Props) {
  const lit = (sign: number) => highlight != null &&
    (highlight === "La" ? sign === lagnaSign : bySign[sign].some((p) => p.code === highlight));
  return (
    <svg viewBox="-2 -2 404 404" className="chart-svg" role="img"
      aria-label={`${title}, ${style === "north" ? "North" : "South"} Indian style`}>
      {style === "north" ? (
        <g>
          <rect x={0} y={0} width={400} height={400} className="chart-frame" />
          {NORTH_HOUSES.map((h, i) => {
            const sign = (lagnaSign + i) % 12;
            const isTriangle = i % 3 !== 0;
            return (
              <g key={i}>
                <polygon points={h.poly}
                  className={`${i === 0 ? "house lagna-house" : "house"}${lit(sign) ? " linked-house" : ""}`} />
                <text x={h.n[0]} y={h.n[1]} className="sign-num" textAnchor="middle"
                  dominantBaseline="middle">{sign + 1}</text>
                <PlanetLines items={bySign[sign]} x={h.c[0]} y={h.c[1]} compact={isTriangle}
                  degrees={degrees} flash={flash} flashKey={flashKey}
                  highlight={highlight} onHighlight={onHighlight} />
              </g>
            );
          })}
          {flash.has("La") && (
            <polygon key={`la-${flashKey}`} points={NORTH_HOUSES[0].poly} className="lagna-flash" />
          )}
        </g>
      ) : (
        <g>
          {SOUTH_CELL.map(([cx, cy], sign) => {
            const x = cx * 100, y = cy * 100;
            const isLagna = sign === lagnaSign;
            return (
              <g key={sign}>
                <rect x={x} y={y} width={100} height={100}
                  className={`${isLagna ? "house lagna-house" : "house"}${lit(sign) ? " linked-house" : ""}`} />
                <text x={x + 8} y={y + 14} className="sign-label">{SIGN_SHORT[sign]}</text>
                {isLagna && <line x1={x + 74} y1={y} x2={x + 100} y2={y + 26} className="lagna-mark" />}
                {isLagna && flash.has("La") && (
                  <rect key={`la-${flashKey}`} x={x} y={y} width={100} height={100} className="lagna-flash" />
                )}
                <PlanetLines items={bySign[sign]} x={x + 50} y={y + 56} compact={true}
                  degrees={degrees} flash={flash} flashKey={flashKey}
                  highlight={highlight} onHighlight={onHighlight} />
              </g>
            );
          })}
          <rect x={100} y={100} width={200} height={200} className="south-centre" />
          <text x={200} y={200} className="south-title" textAnchor="middle"
            dominantBaseline="middle">{centre}</text>
        </g>
      )}
    </svg>
  );
}
