// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { BirthForm } from "@/components/BirthForm";
import { ChartCard } from "@/components/ChartCard";
import { DashaPanel } from "@/components/DashaPanel";
import { PlanetTable } from "@/components/PlanetTable";
import { GocharaView } from "@/components/GocharaView";
import { SpecialPoints } from "@/components/SpecialPoints";
import { JaiminiPoints } from "@/components/JaiminiPoints";
import { PanchangaPanel } from "@/components/PanchangaPanel";
import { LibraryPanel } from "@/components/LibraryPanel";
import { DEFAULT_CANVAS, VargaCanvas } from "@/components/VargaCanvas";
import { DEFAULT_RECTIFY_RANGE, RECTIFY_RANGES, RibbonRange, TimeRibbon, TRANSIT_RANGES } from "@/components/TimeRibbon";
import { analysis, api, Birth, btr, Chart, DashaSystem, DEFAULT_YOGA_OPTIONS, EventRule, library, LifeEvent, readings, ReadingTopic,
  SavedChart, YogaOptions } from "@/lib/api";
import { VimshopakaView } from "@/components/VimshopakaView";
import { EventPanel } from "@/components/EventPanel";
import { AnalysisTabs, TabId } from "@/components/AnalysisTabs";
import { YogaView } from "@/components/YogaView";
import { ReadingScope, ReadingView, Verdict } from "@/components/ReadingView";
import { AshtakavargaView } from "@/components/AshtakavargaView";
import { ShadbalaView } from "@/components/ShadbalaView";
import { DashaTimeline } from "@/components/DashaTimeline";
import { IndicativePanel } from "@/components/IndicativePanel";
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
  const [range, setRange] = useState<RibbonRange>(DEFAULT_RECTIFY_RANGE);
  const [varga, setVarga] = useState(9);
  const [style, setStyle] = useState<ChartStyle>("north");
  const [transitBase, setTransitBase] = useState(() => Date.now());
  const [eventDate, setEventDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [rules, setRules] = useState<EventRule[]>([]);
  const [tab, setTab] = useState<TabId>("positions");
  const [dashaSystem, setDashaSystem] = useState<DashaSystem>("vimshottari");
  const [events, setEvents] = useState<LifeEvent[]>([]);
  const [savedId, setSavedId] = useState<number | null>(null);
  const [canvasVargas, setCanvasVargas] = useState<number[]>(DEFAULT_CANVAS);
  const [yogaOptions, setYogaOptions] = useState<YogaOptions>(DEFAULT_YOGA_OPTIONS);
  const [vimWeights, setVimWeights] = useState<"bphs" | "jhora">("bphs");
  const [readingTopics, setReadingTopics] = useState<ReadingTopic[]>([]);
  const [readingTopic, setReadingTopic] = useState("career");
  const [readingScope, setReadingScope] = useState<ReadingScope>("period");
  const [verdicts, setVerdicts] = useState<Record<string, Verdict>>({});

  useEffect(() => { btr.events().then((r) => setRules(r.events)).catch(() => {}); }, []);
  useEffect(() => { readings.topics().then((r) => setReadingTopics(r.topics)).catch(() => {}); }, []);
  // Events belong to one person: kept with the saved chart, or per chart in this
  // browser for a chart that is not saved.
  const storeKey = `jyotishnet.events.${name}.${birth.local_datetime}`;
  useEffect(() => {
    if (savedId !== null) return;
    try { setEvents(JSON.parse(localStorage.getItem(storeKey) ?? "[]")); } catch { setEvents([]); }
  }, [storeKey, savedId]);
  function openSaved(c: SavedChart) {
    setSavedId(c.id); setName(c.name); setBirth(c.birth); setEvents(c.events); setOffset(0);
  }
  function saveEvents(next: LifeEvent[]) {
    const sorted = [...next].sort((a, b) => a.date.localeCompare(b.date));
    setEvents(sorted);
    if (savedId !== null) {
      library.update(savedId, { events: sorted }).catch(() => {});
      return;
    }
    try { localStorage.setItem(storeKey, JSON.stringify(sorted)); } catch { /* storage unavailable */ }
  }

  const baseMs = mode === "rectify"
    ? parseLocal(birth.local_datetime)
    : transitBase + birth.utc_offset_hours * 3600_000;
  const momentMs = baseMs + offset * 1000;
  const moving: Birth = { ...birth, local_datetime: formatLocal(momentMs) };

  const live = useLive(JSON.stringify([moving, varga]), () => api.chart(moving, [1, varga]));
  const chart_ = live.data;
  const natal = useLive(mode === "transit" ? JSON.stringify([birth, varga]) : null,
    () => api.chart(birth, [1, varga]));
  const dashaAt = mode === "rectify" ? `${eventDate}T12:00:00` : toUtcIso(momentMs, birth.utc_offset_hours);
  const dasha = useLive(JSON.stringify([mode === "rectify" ? moving : birth, dashaAt.slice(0, 13)]),
    () => api.runningDasha(mode === "rectify" ? moving : birth, dashaAt), 250);
  const bounds = useLive(mode === "rectify" ? JSON.stringify([birth, varga]) : null,
    () => api.boundaries(birth, 120, [1, varga]));

  const rectify = mode === "rectify";
  const evKey = JSON.stringify(events);
  const checks = useLive(rectify && events.length ? JSON.stringify([moving, evKey]) : null,
    () => btr.check(moving, events), 120);
  const windowMin = Math.min(range.seconds / 60, 120);
  const curve = useLive(rectify && events.length ? JSON.stringify([birth, evKey, windowMin]) : null,
    () => btr.curve(birth, events, windowMin, windowMin <= 30 ? 30 : 60), 300);
  const indicative = useLive(rectify ? JSON.stringify(moving) : null, () => btr.indicative(moving), 250);

  // Analysis views follow the chart on the ribbon in rectify mode, the birth chart in transit mode.
  const subject = rectify ? moving : birth;
  const subjectKey = JSON.stringify(subject);
  const yogas = useLive(tab === "yogas" ? JSON.stringify([subject, yogaOptions]) : null,
    () => analysis.yogas(subject, yogaOptions), 200);
  const av = useLive(tab === "ashtakavarga" ? subjectKey : null, () => analysis.ashtakavarga(subject), 200);
  const sb = useLive(tab === "shadbala" ? subjectKey : null, () => analysis.shadbala(subject), 200);
  const vim = useLive(tab === "shadbala" ? JSON.stringify([subject, vimWeights]) : null,
    () => analysis.vimshopaka(subject, vimWeights), 200);
  // The canvas follows the ribbon in rectify mode and shows the birth chart in transit mode.
  const canvas = useLive(tab === "vargas" ? JSON.stringify([subject, canvasVargas]) : null,
    () => api.chart(subject, canvasVargas));
  const panchanga = useLive(tab === "positions" ? subjectKey : null, () => analysis.panchanga(subject), 250);
  const transitAt: Birth = rectify ? { ...birth, local_datetime: `${eventDate}T12:00:00` } : moving;
  const gochara = useLive(tab === "transits" ? JSON.stringify([subject, transitAt]) : null,
    () => analysis.transits(subject, transitAt), 250);
  const dashas = useLive(tab === "dashas" ? JSON.stringify([subject, dashaSystem]) : null,
    () => analysis.dashas(subject, dashaSystem), 250);
  // Readings: the current-period scope uses the event date (rectify) or the ribbon's date (transit).
  const readingDate = rectify ? eventDate : formatLocal(momentMs).slice(0, 10);
  const reading = useLive(tab === "readings"
    ? JSON.stringify([subject, readingTopic, readingScope === "period" ? readingDate : null]) : null,
  () => readings.reading(subject, readingTopic, readingScope === "period" ? readingDate : null), 250);
  const verdictKey = (factor: string) => `${name}|${readingTopic}|${factor}`;
  function giveVerdict(factor: string, verdict: Verdict) {
    setVerdicts((v) => ({ ...v, [verdictKey(factor)]: verdict }));
    readings.feedback({ topic: readingTopic, factor, verdict, chart_id: savedId, birth: subject }).catch(() => {});
  }
  const subjectChart = rectify ? chart_ : natal.data;
  const birthUtc = toUtcIso(parseLocal(subject.local_datetime), subject.utc_offset_hours) + "Z";
  const refUtc = (rectify ? `${eventDate}T12:00:00` : toUtcIso(momentMs, birth.utc_offset_hours)) + "Z";

  function switchMode(m: Mode) {
    setMode(m);
    setOffset(0);
    setRange(m === "rectify" ? DEFAULT_RECTIFY_RANGE : TRANSIT_RANGES[1]);
    if (m === "transit") setTransitBase(Date.now());
  }

  const chart = live.data;
  const left = useMemo(() => {
    const c = mode === "rectify" ? chart : natal.data;
    const pl = c ? placements(c, 1) : null;
    return c && pl ? { ...pl, degrees: degreesOf(c) } : null;
  }, [mode, chart, natal.data]);
  // While a newly chosen varga loads, keep showing the last chart that could be drawn.
  const lastRight = useRef<{ mode: Mode; r: NonNullable<ReturnType<typeof placements>> } | null>(null);
  const right = useMemo(() => {
    let r: ReturnType<typeof placements> = null;
    if (chart && mode === "rectify") r = placements(chart, varga);
    else if (chart && natal.data) {
      // Gochara: today's planets in the natal houses.
      const pl = placements(chart, 1);
      r = pl ? { lagnaSign: natal.data.lagna.sign, bySign: pl.bySign } : null;
    }
    if (r) lastRight.current = { mode, r };
    return r ?? (lastRight.current?.mode === mode ? lastRight.current.r : null);
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
            {chart?.source && (
              <span className="engine-note" data-engine={chart.source}
                title={chart.source === "browser"
                  ? "Swiss Ephemeris running in this browser (WebAssembly); same results as the API"
                  : "The browser engine could not start; charts come from the API"}>
                {" "}· {chart.source === "browser" ? "computed in this browser" : "computed by the API"}
              </span>
            )}
          </p>
        </div>
        <BirthForm key={`${name}-${birth.local_datetime}`} name={name} birth={birth}
          onSubmit={(n, b) => { setName(n); setBirth(b); setOffset(0); }} />
      </header>

      <LibraryPanel name={name} birth={birth} events={events} savedId={savedId}
        onOpen={openSaved} onSaved={(c) => setSavedId(c.id)} onForget={() => setSavedId(null)} />

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
        nudges={nudges} zeroLabel={mode === "rectify" ? "recorded time" : "now"}
        curve={rectify && events.length ? curve.data : null} />

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

      {rectify && (
        <EventPanel rules={rules} events={events} loading={checks.loading || curve.loading}
          checks={events.length ? checks.data?.checks ?? null : null}
          helps={events.length ? curve.data?.helps_decide ?? null : null}
          onAdd={(e) => saveEvents([...events, e])}
          onRemove={(i) => saveEvents(events.filter((_, j) => j !== i))} />
      )}

      <AnalysisTabs tab={tab} onTab={setTab}
        busy={canvas.loading || yogas.loading || av.loading || sb.loading || vim.loading || dashas.loading || gochara.loading || reading.loading}>
        {tab === "positions" && (
          <div className="details">
            {chart && (
              <div className="table-wrap">
                <h2>{mode === "rectify" ? "Positions at this birth time" : "Transit positions"}</h2>
                <PlanetTable chart={chart} varga={varga} />
                <SpecialPoints chart={chart} />
                <JaiminiPoints chart={chart} />
                {panchanga.data && <PanchangaPanel p={panchanga.data} />}
              </div>
            )}
            <DashaPanel running={dasha.data?.running ?? null} loading={dasha.loading}
              date={mode === "rectify" ? eventDate : dashaAt.slice(0, 10)}
              onDate={mode === "rectify" ? setEventDate : undefined} />
          </div>
        )}
        {tab === "vargas" && (
          <VargaCanvas chart={canvas.data ?? null} vargas={canvasVargas} onVargas={setCanvasVargas} style={style} />
        )}
        {tab === "yogas" && (yogas.data
          ? <YogaView yogas={yogas.data.yogas} options={yogaOptions} onOptions={setYogaOptions} />
          : <p className="muted">Finding yogas…</p>)}
        {tab === "readings" && (
          <ReadingView topics={readingTopics} topic={readingTopic} onTopic={setReadingTopic}
            scope={readingScope} onScope={setReadingScope} dateLabel={prettyDate(`${readingDate}T12:00:00Z`)}
            reading={reading.data ?? null} loading={reading.loading}
            verdicts={Object.fromEntries((reading.data?.factors ?? []).filter((f) => verdicts[verdictKey(f.key)])
              .map((f) => [f.key, verdicts[verdictKey(f.key)]]))}
            onVerdict={giveVerdict} />
        )}
        {tab === "ashtakavarga" && (av.data && subjectChart
          ? <AshtakavargaView av={av.data} lagnaSign={subjectChart.lagna.sign} />
          : <p className="muted">Counting bindus…</p>)}
        {tab === "shadbala" && (sb.data ? (
          <>
            <ShadbalaView sb={sb.data} />
            {vim.data && <VimshopakaView v={vim.data} weights={vimWeights} onWeights={setVimWeights} />}
          </>
        ) : <p className="muted">Working out strengths…</p>)}
        {tab === "transits" && (gochara.data
          ? <GocharaView tr={gochara.data} when={rectify ? `the event date (${eventDate})` : transitAt.local_datetime.replace("T", " ")} />
          : <p className="muted">Working out transits…</p>)}
        {tab === "dashas" && (dashas.data
          ? <DashaTimeline system={dashaSystem} onSystem={setDashaSystem} periods={dashas.data.periods}
              applicable={dashas.data.applicable} birthIso={birthUtc} refIso={refUtc}
              refLabel={rectify ? `the event date (${prettyDate(refUtc)})` : `the transit date (${prettyDate(refUtc)})`} />
          : <p className="muted">Laying out the periods…</p>)}
      </AnalysisTabs>
      {rectify && <IndicativePanel periods={indicative.data?.periods ?? null} loading={indicative.loading} />}
    </main>
  );
}
