# JyotishNet

A professional Vedic astrology workbench for astrologers, with a smaller
consumer edition planned on the same platform. This repository holds
**phase 1: the verified calculation core (Layer 0)**, its HTTP API, and a first
version of the **workbench UI** (charts, live time slider, transits).

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the five-layer design and
[docs/DECISIONS.md](docs/DECISIONS.md) for open decisions.

## What works now

| Area | Status |
| --- | --- |
| Planets, ascendant, house cusps | Swiss Ephemeris; Lahiri, Raman, KP, True Chitra, Yukteshwar, Fagan-Bradley ayanamsas; mean or true nodes; apparent or true positions |
| House systems | Whole-sign (default), Sripati, Placidus, Koch, Equal, Porphyry |
| Vargas | All 16 Parashari Shodashavarga (D1-D60), with varga longitudes; D2 as Uma-Shambhu (JHora default) or Parashari hora |
| Nakshatra, pada, dignity | Exaltation, moolatrikona, own, natural relationship; vargottama |
| Aspects | Parashari graha drishti; optional Rahu/Ketu 5th/9th |
| Special lagnas | Bhava, Hora, Ghati Lagna and Pranapada (sunrise mode configurable) |
| Dashas | Vimshottari (3 levels), Ashtottari (3 levels, with applicability check), Yogini (2 levels), Chara (K. N. Rao, 2 levels, two cycles; Jaimini rasi drishti and co-lord rules); configurable year length |
| Ashtakavarga | BAV with prastara, SAV, Trikona and Ekadhipatya shodhana, Shodhya pinda; BPHS and PVR variants |
| Shadbala | Sthana (5 parts), Dig, Kala (Nathonnatha, Paksha, Tribhaga, Abda, Masa, Vara, Hora, Ayana), Cheshta, Naisargika, Drik, Yuddha (planetary war, BPHS); rupas and required minimums; Ishta and Kashta phala (BPHS ch. 27; Sun and Moon match JHora on 55 charts). Matches Jagannatha Hora on 23 charts to its printed precision except Yuddha and Cheshta (decided differences) |
| Bhava bala | The twelve houses: lord's Shadbala, Bhava dig bala (by sign class) and Bhava drik bala (aspects on the house middle; Jupiter and Mercury in full), as Jagannatha Hora 8.0 computes them (read from its code); Dig and Drik match JHora on 23 charts (`src/jyotishnet_engine/bhavabala.py`) |
| Vargas | All 22 divisional charts Jagannatha Hora draws (D1-D60, D81, D108, D144), each matching JHora's charts on the 55 golden charts, and the D150 nadiamsa (number and name, JHora's Chandra Kala Nadi division) (`src/jyotishnet_engine/vargas.py`) |
| Special points | Vighati, Varnada, Sree and Indu lagnas, Bhrigu Bindu, the Dhooma group and the time upagrahas (Gulika, Maandi, Kaala, Mrityu, Artha Prahara, Yama Ghantaka), Yogi, Sahayogi and Avayogi, as Jagannatha Hora 8.0 (matched on the 55 golden charts; `src/jyotishnet_engine/upagrahas.py`) |
| Avasthas | Baladi (age), Jagradadi (alertness) and the mood states (Deeptadi and Lajjitadi) of the nine grahas, as Jagannatha Hora 8.0's code; matches JHora's Basic Avasthas table on the golden charts (`src/jyotishnet_engine/avasthas.py`) |
| Vimshopaka bala | Shadvarga, Saptavarga, Dashavarga and Shodashavarga schemes for the nine grahas; Saptavarga weights per BPHS by default, JHora's as an option; with that option matches Jagannatha Hora on all 31 golden charts (`docs/DECISIONS.md`) |
| Rectification helpers | 12 event types in YAML (`rules/btr_events.yaml`, cited, draft) with governing vargas and karakas; event check table (dasha lords linked by lordship, occupancy or karaka in D1 and the event varga, Jupiter-Saturn double transit, score and verdict), fit curve over the birth window with best fit, indicative periods for marriage, children, career and relocation. Death and illness are check-only, never predicted |
| Boundary map (BTR) | Every Lagna, Moon-varga, special-lagna and Moon-pada change in a window, refined to 1 second, plus segments |
| Yogas | 56 rules in YAML (`src/jyotishnet_engine/rules/yogas/`), each citing text and section, with evidence and cancellation: Pancha Mahapurusha, Chandra, Surya, Raja, Viparita, Neecha Bhanga, Parivartana, Dhana, Lakshmi, Amala, Saraswati, Parvata, Kahala, Kartari, Nabhasa (Sankhya, Ashraya, Dala, Akriti). All `draft` pending expert review |
| API | FastAPI: `/v1/chart`, `/v1/dasha` (vimshottari, ashtottari, yogini, chara), `/v1/ashtakavarga`, `/v1/shadbala` (with planetary wars and Bhava bala), `/v1/vimshopaka`, `/v1/avasthas`, `/v1/birth/warnings` (historical Indian time zones), `/v1/yogas`, `/v1/boundaries`, `/v1/btr/events|check|curve|indicative`; CORS via `JYOTISHNET_CORS` |
| Workbench UI | Next.js app in `web/`: North and South Indian charts for any varga; time ribbon for birth-time rectification (±30 min by default, ±20 min or ±2 h, with Lagna-change marks) and transits (±3 days to ±12 years); sign changes flash; positions table; Vimshottari periods on an event date; life events with the event check table, a fit curve and "jump to best fit" on the ribbon, and indicative periods; analysis tabs for yogas (with evidence and citations), Ashtakavarga (by reduction stage, with pindas), Shadbala (components, strength ratios, Bhava bala and avasthas) and a lifetime dasha timeline (Vimshottari, Ashtottari, Yogini, Chara) with antar and pratyantar drill-down; special lagnas, upagrahas and the Yogi under the positions table; the 8 JHora charts as presets. See [web/README.md](web/README.md) |

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
- **Dasha cross-check**: `tools/crosscheck_dashas.py` matches PyJHora's
  Ashtottari maha/antar sequence exactly; start dates within 1.5 days (PyJHora
  counts the dasha year by the tropical Sun, we by the sidereal Sun as JHora).
  Chara (K. N. Rao): antardasha order exact; mahadasha lengths agree except
  where PyJHora treats Mercury in Virgo as own sign rather than exalted, adds
  a year to a lord in its own sign, or picks a Scorpio/Aquarius co-lord by a
  rule-2 slip (it compares a planet number with a sign number).
- **Release run** (`.github/workflows/release-crosscheck.yml`, on version tags
  and on demand): every check above on 100,000 charts, drawn by
  `tools/sampling.py` from Indian cities, latitudes up to ±66° in both
  hemispheres, and births nudged onto varga, nakshatra and pada boundaries.
  Run of 24 November 2026: **0 hard mismatches in 16,000,000 varga placements**
  (3,432 within 7" of a boundary, ephemeris noise); Ashtakavarga all match
  (221 charts skipped with a D1 sign on a boundary); Shadbala no strict
  mismatches (126 births within 3 minutes of a Tribhaga boundary skipped);
  Ashtottari sequence exact, starts within 1.6 days; Chara antardasha order
  exact, mahadasha lengths differ in 0.9% (the variants above).
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
  Dig exact, Drik within 0.025 virupa. Kept in
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

CI runs the tests, the PyJHora cross-checks, and the web build and type-check
on every push.

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

- **Swiss Ephemeris** (via `pyswisseph`) is used under its AGPL licence option,
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
