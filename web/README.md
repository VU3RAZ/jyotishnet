# JyotishNet workbench (web)

Next.js + React + TypeScript front end for the JyotishNet API.

## What it does

- North and South Indian charts (SVG) for the Rasi and any divisional chart.
- **Rectify birth time**: a time ribbon moves the birth time within ±30 minutes by default (±20 minutes
  or ±2 hours on request).
  Charts, positions and dashas recompute as you drag, and marks on the ribbon
  show where the Lagna and the chosen varga's Lagna change sign. Planets or Lagnas that change sign
  flash briefly. The dasha panel shows the Vimshottari periods running on an
  event date you enter.
- **Life events** (rectify mode): enter dated events; each is scored for the
  birth time on the ribbon (dasha lords, links, double transit, verdict, and
  whether it helps decide). The ribbon draws the total fit across the window
  with a "Jump to best fit" button, and a panel lists indicative periods for
  marriage, children, career and relocation. Events are kept per chart in
  this browser only.
- **Analysis tabs**: Positions, Yogas (grouped, with the evidence for each and
  its source text; cancelled ones listed apart; settings for the strong Lagna lord
  and Gajakesari's conditions), Ashtakavarga (bindus in house
  order, by reduction stage, with pindas), Strengths (Shadbala components in rupas and
  each planet's ratio to the required strength, Bhava bala, avasthas, and Vimshopaka
  bala in four schemes with BPHS or JHora Saptavarga weights), and Dashas (a lifetime
  timeline for Vimshottari, Ashtottari, Yogini or Chara, opening on the event
  or transit date, with antardashas and pratyantars). In rectify mode they
  follow the birth time on the ribbon.
- **Transits**: the birth chart stays fixed; the ribbon moves the sky (±3 days,
  ±1 year, ±12 years) and shows today's planets in the birth houses, with the
  periods running on that date.
- The eight Jagannatha Hora reference charts are available as presets.
- **Vargas tab**: several divisional charts side by side (Shadvarga, Saptavarga,
  Dashavarga, Shodashavarga or any choice). Hover a planet to light it up in every
  chart; click it, or its chip, to keep it lit, with its sign in each varga below.
  The charts follow the time ribbon.
- **Readings tab**: pick one of 18 topics (career, marriage, children for fertility
  only, health as technical factors only, ...) and see the factors the classical
  rules weigh for it, ranked, with whether each supports or obstructs it, plus a
  short draft in which every sentence cites the engine facts it rests on (hover a
  sentence to light up its factor and facts). Scope: the natal promise, or also the
  Vimshottari lords running on the event or transit date. Factors resting on a
  varga Lagna that changes sign within 5 minutes of the birth time are marked
  uncertain. Accept or reject each factor; the choices are kept in the local chart
  store as future training labels. All topics are drafts awaiting expert review.
- **Saved charts and notes**: save the chart on screen, find saved charts by name,
  reopen them, keep dated notes and the life events with each one, delete them.
  They are stored by the API in a SQLite file on this computer
  (`JYOTISHNET_DB`, default `~/.local/share/jyotishnet/jyotishnet.db`). Life events of
  a chart that is not saved stay in this browser, as before.

## Run it

```bash
# 1. API (from the repository root)
pip install -e .
uvicorn jyotishnet_api.main:app --port 8000

# 2. Web app (in web/)
npm ci
npm run dev        # http://localhost:3000
```

**Browser engine.** The slider's calculations (charts with all vargas, special
lagnas, upagrahas and Jaimini points; the running Vimshottari periods; the ribbon's
boundary marks) run in the browser: Swiss Ephemeris compiled to WebAssembly
(`public/engine/swe.wasm`, built by `tools/build_swe_wasm.sh` from the same C sources
the API uses) with a TypeScript port of the chart code (`lib/engine/`) in a Web Worker.
A chart takes about 0.5 ms, so the slider updates every frame and works with the API
stopped. The header says "computed in this browser"; if the worker cannot start, the
app falls back to the API. `e2e/engine_parity.py` checks the results equal the API's
(about 700 charts, every field), and `e2e/offline.py` drives the slider with no API.
Everything else (yogas, strengths, readings, saved charts...) still comes from the API.

The app calls `/api/*`, which Next forwards to `JYOTISHNET_API_URL`
(default `http://127.0.0.1:8000`). For a separate deployment, the API also
accepts browser calls from the origins in `JYOTISHNET_CORS`.

## Next steps

1. Design pass over the analysis tabs (M3.6).
2. A TypeScript client generated from the API's OpenAPI spec.
