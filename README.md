# JyotishNet

A professional Vedic astrology workbench for astrologers, with a smaller
consumer edition planned on the same platform. This repository holds **release R1:
an astrologer workbench with rule-based readings**, built on the verified
calculation core (phase 1, Layer 0) and its HTTP API. It runs privately on your own
computer. The neural network (phases 2-5) has not started. What is in R1 and what
is still draft is listed in [CHANGELOG.md](CHANGELOG.md); every capability of R1, with
how each was checked, is in [docs/RELEASE-R1.md](docs/RELEASE-R1.md).

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the five-layer design and
[docs/DECISIONS.md](docs/DECISIONS.md) for open decisions.

## What works now

| Area | Status |
| --- | --- |
| Planets, ascendant, house cusps | Swiss Ephemeris; Lahiri, Raman, KP, True Chitra, Yukteshwar, Fagan-Bradley ayanamsas; mean or true nodes; apparent or true positions |
| House systems | Whole-sign (default), Sripati, Placidus, Koch, Equal, Porphyry |
| Nakshatra, pada, dignity | Exaltation, moolatrikona, own, natural relationship; vargottama |
| Aspects | Parashari graha drishti; optional Rahu/Ketu 5th/9th |
| Special lagnas | Bhava, Hora, Ghati Lagna and Pranapada (sunrise mode configurable) |
| Dashas | Vimshottari (3 levels), Ashtottari (3 levels, with applicability check), Yogini (2 levels), Chara (K. N. Rao, 2 levels, two cycles; Jaimini rasi drishti and co-lord rules); configurable year length |
| Ashtakavarga | BAV with prastara, SAV, Trikona and Ekadhipatya shodhana, Shodhya pinda; BPHS and PVR variants |
| Shadbala | Sthana (5 parts), Dig, Kala (Nathonnatha, Paksha, Tribhaga, Abda, Masa, Vara, Hora, Ayana), Cheshta, Naisargika, Drik, Yuddha (planetary war, BPHS); rupas and required minimums; Ishta and Kashta phala (BPHS ch. 27; Sun and Moon match JHora on 55 charts). Matches Jagannatha Hora on 23 charts to its printed precision except Yuddha and Cheshta (decided differences) |
| Bhava bala | The twelve houses: lord's Shadbala, Bhava dig bala (by sign class) and Bhava drik bala (aspects on the house middle; Jupiter and Mercury in full), as Jagannatha Hora 8.0 computes them (read from its code); Dig and Drik match JHora on 23 charts (`src/jyotishnet_engine/bhavabala.py`) |
| Vargas | All 22 divisional charts Jagannatha Hora draws (D1-D60, D81, D108, D144), each matching JHora's charts on the 55 golden charts, with varga longitudes; D2 as Uma-Shambhu (JHora default) or Parashari hora; and the D150 nadiamsa (number and name, JHora's Chandra Kala Nadi division) (`src/jyotishnet_engine/vargas.py`) |
| Special points | Vighati, Varnada, Sree and Indu lagnas, Bhrigu Bindu, the Dhooma group and the time upagrahas (Gulika, Maandi, Kaala, Mrityu, Artha Prahara, Yama Ghantaka), Yogi, Sahayogi and Avayogi, as Jagannatha Hora 8.0 (matched on the 55 golden charts; `src/jyotishnet_engine/upagrahas.py`) |
| Jaimini | Chara karakas, bhava arudhas (AL..UL) and 19 rasi dashas (Narayana, Lagnamsaka, Padanaathamsa, Sudasa, Drig, Lagna and AK Kendradi, Trikona, three Chara dashas, Yogardha, Shoola, Niryana Shoola, Brahma, Sthira, Mandooka, Navamsa, Varnada) as Jagannatha Hora 8.0 computes them, matching it on the golden charts (`src/jyotishnet_engine/jaimini_jhora.py`, `/v1/dasha`, Dashas tab) |
| Panchanga | Birth panchanga (tithi, nakshatra, yoga, karana with lords and fraction left, weekday, hora lord, samvatsara, lunar month with Adhika/Nija, Janma ghatis) and the day panchanga from sunrise to sunrise (element end times, sunrise and sunset, Rahu kala, Gulika kala, Yamaganda, durmuhurta, varjya, moonrise and moonset, the Moon's sign), as Jagannatha Hora 8.0; matches its Key info on the 55 golden charts and its monthly panchanga on about 1,700 days (`src/jyotishnet_engine/panchanga.py`, `POST /v1/panchanga`, Positions tab) |
| Transits | Gochara from the natal Moon: good houses, vedha, tara, murthi, Ashtakavarga and SAV scores, kakshya; Sade Sati, Kantaka and Ashtama Shani with dated spells; matches Jagannatha Hora 8.0's Basic Transit Results on the 55 golden charts (`src/jyotishnet_engine/transits.py`, `POST /v1/transits`, Transits tab) |
| Avasthas | Baladi (age), Jagradadi (alertness) and the mood states (Deeptadi and Lajjitadi) of the nine grahas, as Jagannatha Hora 8.0's code; matches JHora's Basic Avasthas table on the golden charts (`src/jyotishnet_engine/avasthas.py`) |
| Vimshopaka bala | Shadvarga, Saptavarga, Dashavarga and Shodashavarga schemes for the nine grahas; Saptavarga weights per BPHS by default, JHora's as an option; with that option matches Jagannatha Hora on all 31 golden charts (`docs/DECISIONS.md`) |
| Rectification helpers | 12 event types in YAML (`rules/btr_events.yaml`, cited, draft) with governing vargas and karakas; event check table (dasha lords linked by lordship, occupancy or karaka in D1 and the event varga, Jupiter-Saturn double transit, score and verdict), classical event rules cited to BPHS and Phaladeepika (the R1 rules kept as "modern"), fit curve over the birth window with best fit and a significance test against random event dates (how often random dates fit as well), indicative periods for marriage, children, career and relocation. Death and illness are check-only, never predicted |
| Boundary map (BTR) | Every Lagna, Moon-varga, special-lagna and Moon-pada change in a window, refined to 1 second, plus segments |
| Yogas | 56 rules in YAML (`src/jyotishnet_engine/rules/yogas/`), each citing text and section, with evidence and cancellation: Pancha Mahapurusha, Chandra, Surya, Raja, Viparita, Neecha Bhanga, Parivartana, Dhana, Lakshmi, Amala, Saraswati, Parvata, Kahala, Kartari, Nabhasa (Sankhya, Ashraya, Dala, Akriti); strength conditions as settings (strong Lagna lord for Lakshmi and Kahala by dignity or Shadbala; Gajakesari as BPHS/JHora or with Phaladeepika's conditions). All `draft` pending expert review |
| Readings | 18 topics (career, marriage, children for fertility only, health as technical factors only, ...) in `rules/readings/topics.yaml`, cited and `draft`: a fact sheet from the engine, the factors the classical rules weigh for the topic ranked with whether each supports or obstructs it, and a short draft in which every sentence cites the facts it rests on and passes a verifier and safety filter (no child's sex, no timing of death, illness or accidents). Natal promise or the Vimshottari lords running on a date; factors that rest on a varga Lagna changing sign near the birth time are marked uncertain; accept/reject labels kept in the local store (`src/jyotishnet_engine/readings.py`) |
| Browser engine | Swiss Ephemeris compiled to WebAssembly (`web/public/engine/swe.wasm`, reproducible from `tools/build_swe_wasm.sh`) with a TypeScript port of the chart, running-dasha and boundary code in a Web Worker: the time slider runs every frame and works with the API stopped; equal to the API on about 700 charts (`web/e2e/engine_parity.py`) |
| API | FastAPI: `/v1/chart`, `/v1/dasha` (vimshottari, ashtottari, yogini and the rasi dashas of `/v1/dasha/systems`), `/v1/ashtakavarga`, `/v1/shadbala` (with planetary wars and Bhava bala), `/v1/panchanga`, `/v1/vimshopaka`, `/v1/avasthas`, `/v1/transits`, `/v1/birth/warnings` (historical Indian time zones), `/v1/yogas`, `/v1/boundaries`, `/v1/btr/events|check|curve|indicative`, `/v1/reading/topics`, `/v1/reading`, `/v1/reading/feedback`, saved charts `/v1/charts` (list, save, reopen, update, delete) with `/v1/charts/{id}/notes` and `/v1/notes/{id}`; CORS via `JYOTISHNET_CORS` |
| Saved charts | Charts with their life events and notes, in a local SQLite file (`$JYOTISHNET_DB`, default `~/.local/share/jyotishnet/jyotishnet.db`, owner-only permissions); nothing leaves the computer (`src/jyotishnet_api/store.py`) |
| Workbench UI | Next.js app in `web/`: saved charts and notes (save, find, reopen, annotate, delete); a multi-varga canvas (Shadvarga to Shodashavarga or any choice of vargas side by side, following the ribbon; hover or pin a planet to light it up in every chart, with its sign in each varga); North and South Indian charts for any varga; time ribbon for birth-time rectification (±30 min by default, ±20 min or ±2 h, with Lagna-change marks) and transits (±3 days to ±12 years); sign changes flash; positions table; Vimshottari periods on an event date; life events with the event check table, a fit curve and "jump to best fit" on the ribbon, and indicative periods; analysis tabs for yogas (with evidence and citations), Ashtakavarga (by reduction stage, with pindas), Strengths (Shadbala components, strength ratios, Bhava bala, avasthas and Vimshopaka bala) and a lifetime dasha timeline (Vimshottari, Ashtottari, Yogini and 19 Jaimini rasi dashas) with antar and pratyantar drill-down; special lagnas, upagrahas, the Yogi, chara karakas, arudhas and the panchanga under the positions table; a Readings tab (ranked factors with accept/reject and a cited draft); the slider computed in the browser; every tab usable at phone width; the 8 JHora charts as presets. See [web/README.md](web/README.md) |

A full chart with all 16 vargas takes about 8 ms; the D1 + one varga request
behind the slider about 3 ms; a ±60 minute boundary map about 0.1 s.

## Verification

- **PyJHora cross-check**: `tools/crosscheck_pyjhora.py` compares every
  Shodashavarga placement of the Lagna and nine grahas on random charts. Latest
  run: **0 mismatches in 64,000 placements (400 charts, 1900-2030, 8 Indian
  cities)**, with matching settings (Lahiri, true nodes, true positions,
  Parashari hora).
- **Ashtakavarga cross-check**: `tools/crosscheck_ashtakavarga.py` compares BAV,
  SAV, both reductions and Shodhya pinda with PyJHora: **all components match
  on 300 random charts** (PVR variant, PyJHora's occupancy rule).
- **Shadbala cross-check**: `tools/crosscheck_shadbala.py` matches PyJHora on
  Uchcha, Tribhaga, Naisargika and in-range Paksha bala (150 charts). PyJHora
  5.0.6 returns out-of-range Dig and Paksha values in many charts, so those and
  Drik bala are reported rather than checked; Shadbala needs the Jagannatha
  Hora golden set for absolute verification.
- **Yoga cross-check**: `tools/crosscheck_yogas.py` compares 38 yogas with
  PyJHora (PVR Narasimha Rao's definitions) on random charts. 24 agree on every
  chart; the rest differ by textual variant (for example B. V. Raman's Sunapha
  and Vesi do not need the opposite side empty), which each rule's `notes` record.
  `--strong-lord` and `--gajakesari` pick the yoga strength settings; Lakshmi
  agrees on 295 of 300 charts (PyJHora's node co-lords make the rest).
- **Dasha cross-check**: `tools/crosscheck_dashas.py` matches PyJHora's
  Ashtottari maha/antar sequence exactly; start dates within 1.5 days (PyJHora
  counts the dasha year by the tropical Sun, we by the sidereal Sun as JHora).
  Chara (K. N. Rao): antardasha order exact; mahadasha lengths agree except
  where PyJHora treats Mercury in Virgo as own sign rather than exalted, adds
  a year to a lord in its own sign, or picks a Scorpio/Aquarius co-lord by a
  rule-2 slip (it compares a planet number with a sign number). This check runs
  our Chara with K. N. Rao's book rules (`chara_exaltation_adjust`,
  `chara_co_lord_rule="knrao"`), as PyJHora; the default follows JHora 8.0, which
  the golden rasi dashas check.
- **Release run** (`.github/workflows/release-crosscheck.yml`, on version tags
  and on demand): every check above on 100,000 charts, drawn by
  `tools/sampling.py` from Indian cities, latitudes up to ±66° in both
  hemispheres, and births nudged onto varga, nakshatra and pada boundaries.
  Run on the v1.0.0 tag (27 November 2026): **0 hard mismatches in 23,000,000
  varga placements** (all 23 vargas; 4,993 within 7" of a boundary, ephemeris
  noise); Ashtakavarga all match (221 charts skipped with a D1 sign on a
  boundary); Shadbala no strict mismatches (126 births within 3 minutes of a
  Tribhaga boundary skipped); Ashtottari sequence exact, starts within 1.6 days;
  Chara antardasha order exact, mahadasha lengths differ in 0.9% (the variants
  above).
- **Unit and property tests**: `pytest` (Hypothesis checks varga invariants).
- **Jagannatha Hora golden set**: 55 JHora exports in `tests/golden/jhora`: 8
  real charts (1836-1970) and 47 edge cases (Lagna, nakshatra and sign
  boundaries, planetary wars, historical Indian time zones, Abda/Masa lords,
  solstices and equinoxes, births at sunrise and sunset, every continent's
  zones with summer time, latitudes from the equator to 61 deg, 1800-2001).
  Positions match within 2.2", Navamsa all, Ashtakavarga and all pindas
  exactly, Vimshottari antardashas within 1 day, Vimshopaka (four schemes, nine
  grahas, JHora's Saptavarga weights) within 0.005. Shadbala against JHora's
  breakdown (23 charts): every component and every Kala part
  (`tests/golden/jhora_shadbala/kala/`) to JHora's printed precision, except
  Yuddha (BPHS, which JHora omits) and Cheshta (#16). Bhava bala (23 charts):
  Dig exact, Drik within 0.025 virupa. Panchanga: Key info of all 55 charts, and
  JHora's monthly panchanga of each birth month to the minute it prints (ends
  truncated, other times rounded, 3 s margin), knife-edge days held in
  `tests/golden/pending/jhora_panchanga.json`. Kept in
  `tests/golden/pending/`: two future charts (2050, 2100) that differ by Delta T
  (decided, #22).

## Run the workbench on your computer

Needs Python 3.11+ and Node.js 20+. From the repository folder:

- macOS or Linux: `./scripts/start.sh`
- Windows: double-click `scripts\start.bat`

The first run installs everything (a few minutes); later runs start in seconds
and rebuild only what changed after a `git pull`. Your browser opens at
http://localhost:3000. Ctrl+C (or closing the window) stops it. Both servers
listen on 127.0.0.1 only, so nothing is reachable from other machines.

## Quick start

```bash
pip install -e ".[dev]"
pytest -q
uvicorn jyotishnet_api.main:app --reload
```

Workbench UI: with the API running on port 8000,

```bash
cd web && npm ci && npm run dev    # http://localhost:3000
```

CI runs the tests, the PyJHora cross-checks, the web build and type-check, the
browser smoke test (including phone width), the browser engine's parity and offline
tests, and a rebuild of `swe.wasm` that must match the committed file, on every push.

API and library examples:

```bash
curl -s localhost:8000/v1/chart -H 'content-type: application/json' -d '{
  "birth": {"local_datetime": "1990-01-15T06:30:00", "latitude": 28.61, "longitude": 77.21},
  "vargas": [1, 9, 10]
}'
```

```python
from datetime import datetime
from jyotishnet_engine import BirthData, build_chart, describe

chart = build_chart(BirthData(datetime(1990, 1, 15, 6, 30), 28.61, 77.21))
print(describe(chart))
```

## License

Copyright (C) 2026 Rahul Sathe.

JyotishNet is free software: you can redistribute it and/or modify it under the
terms of the **GNU Affero General Public License, version 3 or (at your option)
any later version**. See [LICENSE](LICENSE). Because it is the AGPL, anyone who
runs a modified version as a network service must offer its source code to that
service's users.

Notes:

- **Swiss Ephemeris** (via `pyswisseph`, and compiled to WebAssembly from the same
  sources for the browser engine, `web/public/engine/swe.wasm`) is used under its AGPL licence option,
  which requires the whole project to be AGPL-compatible. A closed-source edition
  would need the Swiss Ephemeris Professional Licence from Astrodienst.
- **PyJHora** (AGPL-3.0) is used only as an external test oracle in a separate
  environment and is not imported by the engine.
- **Trained model weights and datasets** are not covered by this repository's
  licence and are not included here.

## Layout

```
src/jyotishnet_engine/   Layer 0 calculation core
src/jyotishnet_api/      FastAPI service
tests/                   unit, property, API and golden tests
src/jyotishnet_engine/rules/yogas/   yoga rules (YAML, cited)
tools/                   PyJHora cross-checks (vargas, ashtakavarga, shadbala, yogas, dashas)
docs/                    architecture summary and decisions
web/                     workbench UI (Next.js + TypeScript)
```
