# Changelog

## 1.0.0 (R1): astrologer workbench with rule-based readings

The first release: milestones M1 to M3 of the plan. JyotishNet runs privately on
your own computer (`scripts/start.sh`, or `scripts\start.bat` on Windows); both
servers listen on 127.0.0.1 only and saved charts stay in a local SQLite file.
Hosting and accounts (M4) and the neural network (phases 2-5) are not part of R1.
The full list of capabilities, with how each was checked, is in
[docs/RELEASE-R1.md](docs/RELEASE-R1.md).

### What is in it

- **Calculation core (Layer 0)**, verified against Jagannatha Hora 8.0 on 55
  golden charts and against PyJHora on 100,000 random charts per check:
  - positions;
  - all 22 JHora vargas and the D150 nadiamsa;
  - Vimshottari, Ashtottari and Yogini dashas, plus 19 Jaimini rasi dashas;
  - chara karakas and arudhas;
  - Ashtakavarga with both reductions and the pindas;
  - Shadbala with Ishta and Kashta phala, Bhava bala and avasthas;
  - Vimshopaka bala in four schemes;
  - special lagnas, upagrahas and the Yogi;
  - the panchanga;
  - transits: gochara, vedha, tara, murthi, kakshya and Sade Sati.
- **Yogas:** 56 cited rules, with evidence, cancellation and strength settings.
- **Rectification helpers:**
  - a boundary map refined to 1 second;
  - 12 event rules;
  - an event check table;
  - a fit curve over the birth window;
  - indicative periods.
- **Rule-based readings:** 18 topics. For each, a fact sheet from the engine,
  ranked factors, and a short draft in which every sentence cites the engine facts
  it rests on. Each draft passes a verifier and a safety filter. Accept/reject
  labels are kept locally for later training.
- **Workbench:**
  - charts:
    - North and South Indian charts for any varga;
    - a multi-varga canvas with linked highlighting;
  - the time ribbon:
    - rectification and transit modes;
    - runs every frame in the browser, from Swiss Ephemeris compiled to
      WebAssembly, and works with the API stopped;
  - analysis tabs:
    - positions, yogas, readings, Ashtakavarga, strengths, dashas and transits;
    - every tab usable at phone width;
  - saved charts with notes and life events.
- **API:** every calculation over HTTP (FastAPI); see README.md for the endpoints.

### Verification at release

Every check below runs in CI on every push, apart from the 100,000-chart PyJHora
run, which runs on version tags:

- `pytest` (unit, property, API and golden tests);
- PyJHora cross-checks (100,000 charts per check on version tags);
- web type-check and build;
- the browser smoke test, including phone width;
- the browser engine's parity with the API on about 700 charts;
- the offline slider test;
- a byte-for-byte rebuild of `swe.wasm`.

The README's "Verification" section gives the numbers.

### Still draft or open

These need a person, usually the Jyotish reviewer. The code runs on the default
recorded in `docs/DECISIONS.md`:

- **Drafts awaiting the Jyotish reviewer:**
  - the 56 yoga rules (#18);
  - the 18 reading topics and their factor weights (#24);
  - the 12 rectification event rules (#20).

  The app labels all of them as drafts.
- **Open decisions:**
  - house system for the model's frame (#1);
  - which Chara/Narayana dasha to lead with (#3);
  - gender-dependent rules, not implemented, gender never asked (#4);
  - Kendra bala houses (#12);
  - Sun/Moon Cheshta (#15);
  - Mercury in Virgo in Chara dasha (#19);
  - Mercury in the 10th in transit vedha, where JHora differs from the
    published table;
  - Sudasa's "sign 12";
  - the Moon's moolatrikona range.

### Known limits

- Polar births (beyond ±66° latitude) are refused: there is no sunrise to base the
  special lagnas, Tribhaga, vara and hora on.
- Bombay Time and Calcutta Time are not modelled. The birth form warns when a
  date and place fall in them so the offset can be entered by hand.
- Dates after 2016 can drift from JHora by its future Delta T (#22).
- Shadbala keeps two decided differences from JHora: Yuddha bala as BPHS, and
  Cheshta bala from astronomical mean motions.
- The browser engine covers the time ribbon (charts, running periods, boundary
  marks) at the default settings. The other tabs still ask the local API.
- The Windows launcher (`scripts/start.bat`) has not been tested on Windows.
- The workbench never predicts a child's sex. It never gives the timing of death,
  serious illness or accidents: those events are check-only in rectification.
