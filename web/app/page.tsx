// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useMemo, useState } from "react";
import { BirthForm } from "@/components/BirthForm";
import { ChartCard } from "@/components/ChartCard";
import { DashaPanel } from "@/components/DashaPanel";
import { PlanetTable } from "@/components/PlanetTable";
import { RECTIFY_RANGES, RibbonRange, TimeRibbon, TRANSIT_RANGES } from "@/components/TimeRibbon";
import { api, Birth, Chart } from "@/lib/api";
import { GRAHA_ORDER, placements } from "@/lib/jyotish";
import { PRESETS } from "@/lib/presets";
import { formatLocal, parseLocal, prettyDate, prettyLocal, toUtcIso } from "@/lib/time";
import { useLive } from "@/lib/useLive";
import type { ChartStyle } from "@/components/ChartFigure";

type Mode = "rectify" | "transit";

function degreesOf(c: Chart): Record<string, number> {
  return Object.fromEntries(GRAHA_ORDER.filter((k) => c.grahas[k]).map((k) => [k, c.grahas[k].degree]));
}

export default function Workbench() {
  const [name, setName] = useState(PRESETS[0].name);
  const [birth, setBirth] = useState<Birth>(PRESETS[0].birth);
  const [mode, setMode] = useState<Mode>("rectify");
  const [offset, setOffset] = useState(0);
  const [range, setRange] = useState<RibbonRange>(RECTIFY_RANGES[1]);
  const [varga, setVarga] = useState(9);
  const [style, setStyle] = useState<ChartStyle>("north");
  const [transitBase, setTransitBase] = useState(() => Date.now());
  const [eventDate, setEventDate] = useState(() => new Date().toISOString().slice(0, 10));

  const baseMs = mode === "rectify"
    ? parseLocal(birth.local_datetime)
    : transitBase + birth.utc_offset_hours * 3600_000;
  const momentMs = baseMs + offset * 1000;
  const moving: Birth = { ...birth, local_datetime: formatLocal(momentMs) };

  const live = useLive(JSON.stringify([moving, varga]), () => api.chart(moving, [1, varga]));
  const natal = useLive(mode === "transit" ? JSON.stringify([birth, varga]) : null,
    () => api.chart(birth, [1, varga]));
  const dashaAt = mode === "rectify" ? `${eventDate}T12:00:00` : toUtcIso(momentMs, birth.utc_offset_hours);
  const dasha = useLive(JSON.stringify([mode === "rectify" ? moving : birth, dashaAt.slice(0, 13)]),
    () => api.runningDasha(mode === "rectify" ? moving : birth, dashaAt), 250);
  const bounds = useLive(mode === "rectify" ? JSON.stringify([birth, varga]) : null,
    () => api.boundaries(birth, 120, [1, varga]));

  function switchMode(m: Mode) {
    setMode(m);
    setOffset(0);
    setRange(m === "rectify" ? RECTIFY_RANGES[1] : TRANSIT_RANGES[1]);
    if (m === "transit") setTransitBase(Date.now());
  }

  const chart = live.data;
  const left = useMemo(() => {
    const c = mode === "rectify" ? chart : natal.data;
    return c ? { ...placements(c, 1), degrees: degreesOf(c) } : null;
  }, [mode, chart, natal.data]);
  const right = useMemo(() => {
    if (!chart) return null;
    if (mode === "rectify") return placements(chart, varga);
    if (!natal.data) return null;
    // Gochara: today's planets in the natal houses.
    return { lagnaSign: natal.data.lagna.sign, bySign: placements(chart, 1).bySign };
  }, [mode, chart, natal.data, varga]);

  const error = live.error || natal.error;
  const nudges = mode === "rectify"
    ? [-600, -60, -10, 10, 60, 600]
    : range.id === "12y" ? [-30 * 86400, -86400, 86400, 30 * 86400] : [-86400, -3600, 3600, 86400];

  return (
    <main className="bench">
      <header className="bench-head">
        <div className="title-block">
          <p className="product">JyotishNet workbench</p>
          <h1>{name}</h1>
          <p className="birth-line">
            Born {prettyLocal(parseLocal(birth.local_datetime))} local time,
            {" "}{birth.latitude.toFixed(2)}° {birth.latitude >= 0 ? "N" : "S"},
            {" "}{Math.abs(birth.longitude).toFixed(2)}° {birth.longitude >= 0 ? "E" : "W"}
            {(mode === "rectify" ? chart : natal.data) &&
              <>, ayanamsa {(mode === "rectify" ? chart : natal.data)!.ayanamsa.toFixed(4)}° (Lahiri)</>}
          </p>
        </div>
        <BirthForm key={`${name}-${birth.local_datetime}`} name={name} birth={birth}
          onSubmit={(n, b) => { setName(n); setBirth(b); setOffset(0); }} />
      </header>

      <nav className="mode-bar" aria-label="What the slider moves">
        <div role="group" aria-label="Mode" className="segmented">
          <button type="button" aria-pressed={mode === "rectify"} onClick={() => switchMode("rectify")}>
            Rectify birth time
          </button>
          <button type="button" aria-pressed={mode === "transit"} onClick={() => switchMode("transit")}>
            Transits
          </button>
        </div>
        <div role="group" aria-label="Chart style" className="segmented quiet">
          <button type="button" aria-pressed={style === "north"} onClick={() => setStyle("north")}>North Indian</button>
          <button type="button" aria-pressed={style === "south"} onClick={() => setStyle("south")}>South Indian</button>
        </div>
      </nav>

      <TimeRibbon value={offset} onChange={setOffset} range={range}
        ranges={mode === "rectify" ? RECTIFY_RANGES : TRANSIT_RANGES}
        onRange={(r) => { setRange(r); setOffset((o) => Math.max(-r.seconds, Math.min(r.seconds, o))); }}
        momentMs={momentMs}
        boundaries={mode === "rectify" ? bounds.data?.changes ?? [] : []}
        highlightKeys={mode === "rectify"
          ? [{ key: "D1.lagna", label: "the Lagna", strong: true },
             { key: `D${varga}.lagna`, label: `the D${varga} Lagna`, strong: false }]
          : []}
        nudges={nudges} zeroLabel={mode === "rectify" ? "recorded time" : "now"} />

      {error && (
        <p className="service-error" role="alert">
          The calculation service did not answer ({error}). Start it with
          {" "}<code>uvicorn jyotishnet_api.main:app --port 8000</code> and try again.
        </p>
      )}

      <section className="charts" aria-live="off">
        {left && (
          <ChartCard title={mode === "rectify" ? "Rasi (D1)" : "Birth chart (D1)"} style={style}
            lagnaSign={left.lagnaSign} bySign={left.bySign} degrees={left.degrees} centre="Rasi" />
        )}
        {right && (
          mode === "rectify" ? (
            <ChartCard title={`D${varga}`} style={style} lagnaSign={right.lagnaSign} bySign={right.bySign}
              varga={varga} onVarga={setVarga} centre={`D${varga}`} />
          ) : (
            <ChartCard title="Transits over the birth chart" style={style} lagnaSign={right.lagnaSign}
              bySign={right.bySign} note={prettyDate(toUtcIso(momentMs, birth.utc_offset_hours) + "Z")}
              centre="Gochara" />
          )
        )}
        {!left && !error && <p className="muted">Casting the chart…</p>}
      </section>

      <section className="details">
        {chart && (
          <div className="table-wrap">
            <h2>{mode === "rectify" ? "Positions at this birth time" : "Transit positions"}</h2>
            <PlanetTable chart={chart} varga={varga} />
          </div>
        )}
        <DashaPanel running={dasha.data?.running ?? null} loading={dasha.loading}
          date={mode === "rectify" ? eventDate : dashaAt.slice(0, 10)}
          onDate={mode === "rectify" ? setEventDate : undefined} />
      </section>
    </main>
  );
}
