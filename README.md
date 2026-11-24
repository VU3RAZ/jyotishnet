# JyotishNet

A professional Vedic astrology workbench for astrologers, with a smaller
consumer edition planned on the same platform. This repository starts with
**phase 1: the verified calculation core (Layer 0)** and its HTTP API.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the five-layer design and
[docs/DECISIONS.md](docs/DECISIONS.md) for open decisions.

## What works now

| Area | Status |
| --- | --- |
| Planets, ascendant, house cusps | Swiss Ephemeris; Lahiri, Raman, KP, True Chitra, Yukteshwar, Fagan-Bradley ayanamsas; mean or true nodes; apparent or true positions |
| House systems | Whole-sign (default), Sripati, Placidus, Koch, Equal, Porphyry |
| Vargas | All 16 Parashari Shodashavarga (D1-D60), with varga longitudes |
| Nakshatra, pada, dignity | Exaltation, moolatrikona, own, natural relationship; vargottama |
| Aspects | Parashari graha drishti; optional Rahu/Ketu 5th/9th |
| Special lagnas | Bhava, Hora, Ghati Lagna and Pranapada (sunrise mode configurable) |
| Dashas | Vimshottari (3 levels), Yogini (2 levels); configurable year length |
| Ashtakavarga | BAV with prastara, SAV, Trikona and Ekadhipatya shodhana, Shodhya pinda; BPHS and PVR variants |
| Shadbala | Sthana (5 parts), Dig, Kala (Nathonnatha, Paksha, Tribhaga, Abda, Masa, Vara, Hora, Ayana), Cheshta, Naisargika, Drik; rupas and required minimums. Yuddha bala pending |
| Boundary map (BTR) | Every Lagna, Moon-varga, special-lagna and Moon-pada change in a window, refined to 1 second, plus segments |
| API | FastAPI: `/v1/chart`, `/v1/dasha`, `/v1/ashtakavarga`, `/v1/shadbala`, `/v1/boundaries` |

A full chart takes about 8 ms; a +/-60 minute boundary map about 0.1 s.

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
- **Unit and property tests**: `pytest` (Hypothesis checks varga invariants).
- **Jagannatha Hora golden set**: `tests/golden/`, to be filled by hand.

## Quick start

```bash
pip install -e ".[dev]"
pytest -q
uvicorn jyotishnet_api.main:app --reload
```

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
tools/                   PyJHora cross-check
docs/                    architecture summary and decisions
web/                     workbench front end (next)
```
