# JyotishNet R1 release

Version 1.0.0 · released 27 November 2026 · tag `v1.0.0`

## What R1 is

JyotishNet 1.0.0 (R1) is a Vedic astrology workbench for astrologers, with rule-based readings, that runs privately on one computer. It covers milestones M1 to M3: a calculation core checked against Jagannatha Hora 8.0 (JHora), an HTTP API, and a web workbench. It is tagged `v1.0.0` in the repository VU3RAZ/jyotishnet under the AGPL-3.0-or-later licence.

Not in R1: hosting and accounts (M4), the neural network (phases 2 to 5), and the other branches (KP, Tajika, Prashna, Muhurta, match-making). Every yoga, reading and rectification rule is still a draft awaiting the Jyotish reviewer.

## Running it

One command starts everything; nothing leaves the computer.

- **Start:** `./scripts/start.sh` on macOS or Linux, `scripts\start.bat` on Windows. Needs Python 3.11+ and Node.js 20+.
- **First run** installs the Python and web packages and builds the workbench (a few minutes). Later runs start in seconds and rebuild only what changed after a `git pull`.
- **Privacy:** the API and the web app listen on 127.0.0.1 only. Saved charts, notes and life events sit in a local SQLite file (`~/.local/share/jyotishnet/jyotishnet.db` by default, owner-only permissions).
- **Tested:** a fresh clone on Linux installs, builds and starts with no manual step, and the browser smoke test passes against it. The Windows launcher has not been tried on Windows.

## Chart calculations

Positions come from Swiss Ephemeris and follow JHora's defaults, with each school choice available as a setting.

| Capability | What R1 does | Checked against |
| --- | --- | --- |
| Planets and Lagna | Nine grahas and the ascendant, with speed and retrogression; true (geometric) positions by default, apparent as an option | JHora: within 2.2" on 55 golden charts |
| Ayanamsa | Lahiri (default), Raman, KP, True Chitra, Yukteshwar, Fagan-Bradley | — |
| Nodes | Mean (default) or true Rahu and Ketu | — |
| Houses | Whole-sign (default), Sripati, Placidus, Koch, Equal, Porphyry | — |
| Vargas | All 22 divisional charts JHora draws: D1 to D60, D81, D108, D144, with varga longitudes. D2 as Uma-Shambhu (default) or Parashari hora; D11 Rath; D108 navamsa-based | JHora's charts on 55 golden charts; PyJHora: 0 hard mismatches in 23 million placements |
| Nadiamsa | D150 number and name (Chandra Kala Nadi division) | JHora |
| Nakshatra and pada | For every graha and the Lagna | JHora |
| Dignity | Exaltation, debilitation, moolatrikona, own, friend, neutral, enemy; vargottama | JHora |
| Aspects | Parashari graha drishti; optional Rahu/Ketu 5th and 9th | — |
| Speed | Full chart with all 16 Shodashavarga about 8 ms on the API; about 0.4 ms in the browser for the slider | — |

## Dashas

R1 has 3 graha dashas and 19 Jaimini rasi dashas. The dasha year is the Sun's sidereal solar year by default, as in JHora; other year lengths are settings.

| Dasha | Levels | Checked against |
| --- | --- | --- |
| Vimshottari | Maha, antar, pratyantar | JHora: 584 of 648 antardashas exact, all within 1 day |
| Ashtottari | Maha, antar, pratyantar; tells whether it applies to the chart | PyJHora: sequence exact on 100,000 charts, starts within 1.6 days (PyJHora counts a tropical year) |
| Yogini | Maha, antar | JHora: within 1 day |
| 19 rasi dashas | Maha and antar: Narayana, Lagnamsaka, Padanaathamsa, Sudasa, Drig, Lagna Kendradi, Atma Karaka Kendradi, Trikona, Chara (K. N. Rao, Parashara, Iranganti Rangacharya), Yogardha, Shoola, Niryana Shoola, Brahma, Sthira, Mandooka, Navamsa, Varnada | JHora 8.0 with its default settings on the golden charts |

## Strengths

R1 computes six strength measures, matching JHora to its printed precision apart from two decided differences in Shadbala.

| Capability | What R1 does | Checked against |
| --- | --- | --- |
| Ashtakavarga | Bhinnashtakavarga with prastara, Sarvashtakavarga, Trikona and Ekadhipatya shodhana, Rasi, Graha and Shodhya pinda; BPHS and PVR variants | JHora: all pindas exact; PyJHora: all components match |
| Shadbala | Sthana (5 parts), Dig, Kala (Nathonnatha, Paksha, Tribhaga, Abda, Masa, Vara, Hora, Ayana, Yuddha), Cheshta, Naisargika, Drik; rupas, required minimum and ratio; planetary wars | JHora on 23 charts, every component to its printed precision except Yuddha (BPHS kept) and Cheshta (astronomical mean motions kept) |
| Ishta and Kashta phala | BPHS ch. 27 | JHora: Sun and Moon match on 55 charts |
| Bhava bala | Lord's Shadbala, Bhava dig bala and Bhava drik bala for the 12 houses | JHora on 23 charts: Dig exact, Drik within 0.025 virupa |
| Avasthas | Baladi (age), Jagradadi (alertness), Deeptadi and Lajjitadi moods for the nine grahas | JHora's Basic Avasthas table on the golden charts |
| Vimshopaka bala | Shadvarga, Saptavarga, Dashavarga, Shodashavarga; Saptavarga weights per BPHS (default) or JHora | JHora within 0.005 on 55 charts (JHora's weights) |

## Special points, Jaimini, panchanga and transits

All four match JHora 8.0 on the 55 golden charts.

| Capability | What R1 does |
| --- | --- |
| Special lagnas | Bhava, Hora, Ghati and Vighati Lagna, Pranapada, Varnada, Sree and Indu Lagna; sunrise by the disc centre without refraction, as JHora |
| Upagrahas | The Dhooma group (Dhooma, Vyatipata, Parivesha, Indrachapa, Upaketu) and the time upagrahas (Gulika, Maandi, Kaala, Mrityu, Artha Prahara, Yama Ghantaka) |
| Other points | Bhrigu Bindu; Yogi, Sahayogi and Avayogi |
| Jaimini | Eight chara karakas (seven, or Parashara's rule, as settings); bhava arudhas A1 to A12 with the arudha exceptions and node co-lords. All 631 readable arudha labels on JHora's 55 chart drawings match |
| Birth panchanga | Tithi, nakshatra, yoga and karana with lords and fraction left; weekday and hora lord; samvatsara; lunar month with Adhika/Nija; Janma ghatis |
| Day panchanga | Sunrise to sunrise: element end times, sunrise and sunset, moonrise and moonset, the Moon's sign, Rahu kala, Gulika kala, Yamaganda, durmuhurta, varjya. Matches JHora's monthly panchanga on about 1,700 days |
| Transits (gochara) | From the natal Moon: good houses, vedha, tara, murthi, kakshya, the graha's own Ashtakavarga and SAV scores |
| Saturn | Sade Sati (rising, peak, setting), Kantaka and Ashtama Shani, with dated spells |

## Yogas

R1 checks 56 yoga rules, written as YAML so that a reviewer can read and change them. Each rule cites its text and section, shows the evidence it fired on, and lists any cancellation. All 56 are `draft`.

| Group | Yogas |
| --- | --- |
| Chandra (9) | Sunapha, Anapha, Durudhara, Kemadruma, Gajakesari, Adhi, Chandra-Mangala, Shakata, Vasumati |
| Surya (4) | Vesi, Vosi, Ubhayachari, Budha-Aditya (Nipuna) |
| Pancha Mahapurusha (5) | Ruchaka, Bhadra, Hamsa, Malavya, Sasa |
| Raja (4) | Raja yoga (kendra-trikona), Dharma-Karmadhipati, Yogakaraka, Neecha Bhanga Raja |
| Viparita Raja (3) | Harsha, Sarala, Vimala |
| Parivartana (3) | Maha, Khala, Dainya |
| Dhana (3) | Dhana yoga (2nd and 11th lords), Dhana yoga (wealth and trikona lords), Lakshmi |
| Shubha (4) | Amala, Saraswati, Parvata, Kahala |
| Kartari (2) | Shubha Kartari, Papa Kartari (of the Lagna) |
| Nabhasa (19) | Sankhya: Vallaki, Damini, Pasha, Kedara, Shoola, Yuga, Gola. Ashraya: Rajju, Musala, Nala. Dala: Mala, Sarpa. Akriti: Gada, Shakata, Vihaga, Shringataka, Hala, Kamala, Vapi |

**Settings:** the strong Lagna lord for Lakshmi and Kahala can be judged by dignity and placement or by Shadbala. Gajakesari can follow BPHS/JHora or add Phaladeepika's conditions.

**Cross-check:** compared with PyJHora on 38 shared yogas, 24 agree on every chart; the rest differ by documented textual variants, recorded in each rule's notes.

## Birth-time rectification

R1 shows what changes as the birth time moves, and scores dated life events against each candidate time.

- **Boundary map:** every change of the Lagna, the Moon's varga signs, the special lagnas and the Moon's pada within the window, refined to 1 second. These are drawn as marks on the time ribbon.
- **12 event types** (draft, cited), each with its governing varga and karakas:
  - marriage (D9), birth of a child (D7), career (D10), relocation or property (D4);
  - finance (D2), sibling (D3), vehicle (D16), spiritual initiation (D20), education (D24);
  - father's death and mother's death (D12), surgery or serious illness (D30). These three are check-only and never predicted.
- **Event check table:** for each event, it shows:
  - the dasha lords running on the date;
  - how each lord links to the event: by lordship, occupancy or karaka, in D1 and in the event's varga;
  - the Jupiter-Saturn double transit;
  - a score and a verdict, and whether the event helps decide between times.
- **Fit curve:** the total fit across the birth window drawn on the ribbon, with a "Jump to best fit" button.
- **Indicative periods** for marriage, children, career and relocation.

## Rule-based readings

For 18 life topics, R1 lists the factors the classical rules weigh and ranks them. It then drafts a short text in which every sentence cites the engine facts it rests on. There is no neural network: the text comes from rules, so each claim can be traced.

**Topics:** personality and temperament; fame and reputation; earned income; accumulated wealth; career direction; business and partnerships; marriage quality; children (fertility only); father; mother; siblings; property and land; vehicles; school and higher education; foreign travel and settlement; litigation, enemies and competition; spiritual practice; health indicators (technical only, no draft text).

How a reading is built:

1. **Fact sheet:** the engine's facts for the chart, each with an id, such as the lord of the 10th, a graha's dignity, a yoga, or a Shadbala ratio.
2. **Ranked factors:** the house lord, occupants, aspects, karaka, yogas and the governing varga's lord. Each is weighted for the topic and marked as supporting, obstructing or mixed.
3. **Scope:** the natal promise alone, or also the Vimshottari lords running on a chosen date.
4. **Uncertainty:** factors that rest on a varga Lagna changing sign within 5 minutes of the birth time are marked uncertain.
5. **Cited draft:** a sentence for each factor, with links to the facts it cites. A verifier drops any sentence that fails one of three checks: every claim must rest on a cited fact, every claim is rechecked against the chart, and every graha, sign or house the sentence names must be one of its claims. Dropped sentences are listed with the reason.
6. **Safety filter:** it never states a child's sex, and never gives timing of death, serious illness or accidents. Health is technical factors only, with a disclaimer.
7. **Feedback:** you can accept or reject each factor. The choice is stored locally as a label for future training.

All 18 topics and their factor weights are `draft` (decision #24).

## The workbench

The workbench is a web app at http://localhost:3000, built around a time ribbon that moves the birth time or the sky.

- **Charts:** North or South Indian style for any varga, with exalted and debilitated grahas coloured and retrograde marked.
- **Time ribbon, rectify mode:**
  - moves the birth time by ±20 min, ±30 min (default) or ±2 h;
  - marks where the Lagna and the chosen varga's Lagna change sign;
  - flashes planets that change sign;
  - shows the Vimshottari periods running on an event date.
- **Time ribbon, transit mode:** the birth chart stays fixed while the sky moves (±3 days, ±1 year, ±12 years), with today's planets in the birth houses.
- **Computed in the browser:** Swiss Ephemeris compiled to WebAssembly runs in a Web Worker. Charts, running periods and boundary marks recompute every frame (about 0.4 ms a chart) and keep working with the API stopped. Results equal the API's on about 700 test charts.
- **Analysis tabs:**
  - **Positions**, with special lagnas, upagrahas, chara karakas, arudhas and the panchanga;
  - **Vargas**, a multi-varga canvas: Shadvarga to Shodashavarga side by side, with a planet lit in every chart on hover or click;
  - **Yogas**, as cards with evidence and source;
  - **Readings**;
  - **Ashtakavarga**, with a SAV-by-house chart and each reduction stage;
  - **Strengths**: Shadbala, Bhava bala, avasthas and Vimshopaka;
  - **Dashas**, a lifetime timeline with drill-down into antar and pratyantar;
  - **Transits**, with Sade Sati cycles.
- **Life events:** dated events with the event check table, the fit curve and indicative periods.
- **Saved charts and notes:** save, search by name, reopen, keep dated notes and life events, delete.
- **Presets:** the 8 JHora reference charts.
- **Phone width:** every tab fits a 420 px screen.

## API

Every calculation is available over HTTP from a FastAPI service, with interactive documentation at `/docs`. Calls from other origins are allowed only for those listed in `JYOTISHNET_CORS`.

| Area | Endpoints |
| --- | --- |
| Chart | `POST /v1/chart`, `POST /v1/birth/warnings` |
| Dashas | `POST /v1/dasha`, `GET /v1/dasha/systems` |
| Strengths | `POST /v1/ashtakavarga`, `/v1/shadbala` (with wars and Bhava bala), `/v1/vimshopaka`, `/v1/avasthas` |
| Panchanga and transits | `POST /v1/panchanga`, `POST /v1/transits` |
| Yogas | `POST /v1/yogas` |
| Rectification | `POST /v1/boundaries`, `GET /v1/btr/events`, `POST /v1/btr/check`, `/v1/btr/curve`, `/v1/btr/indicative` |
| Readings | `GET /v1/reading/topics`, `POST /v1/reading`, `POST /v1/reading/feedback` |
| Saved charts | `GET`/`POST /v1/charts`, `GET`/`PUT`/`DELETE /v1/charts/{id}`, `POST /v1/charts/{id}/notes`, `PUT`/`DELETE /v1/notes/{id}` |
| Health | `GET /health` |

The engine is also a Python library: `build_chart(BirthData(...))` returns the whole chart.

## How R1 was verified

The tagged code passed every check: unit and golden tests, CI on the release commit, a 100,000-chart cross-check, and a fresh install.

**Release cross-check against PyJHora** (run 27 Nov 2026 on `v1.0.0`; 100,000 charts per check from Indian cities, global latitudes to ±66°, and births placed on varga, nakshatra and pada boundaries; all 50 jobs passed):

| Check | Result |
| --- | --- |
| Varga signs (Lagna and nine grahas, 23 vargas) | 0 hard mismatches in 23,000,000 placements; 4,993 within 7" of a sign boundary (ephemeris noise) |
| Ashtakavarga (BAV, SAV, reductions, pindas) | All components match; 221 charts with a D1 sign on a boundary skipped |
| Shadbala (Uchcha, Tribhaga, Naisargika, in-range Paksha) | No mismatch beyond 0.1 virupa; 126 births within 3 min of a Tribhaga boundary skipped; PyJHora's out-of-range Dig and Paksha values reported, not compared |
| Ashtottari | 6,400,000 antardashas: sequence exact, starts within 1.58 days (PyJHora uses a tropical year) |
| Chara (K. N. Rao) | Antardasha order exact; 0.9% of 1,192,210 mahadashas differ in length, all from documented variants |
| Yogas (38 shared) | 24 agree on every chart; the rest differ by the textual variants recorded in each rule |

**Against Jagannatha Hora 8.0** (55 golden charts, 1800 to 2001, every continent, Lagna, nakshatra and sign edge cases): see the "Checked against" columns above.

**Tests and CI on the release commit:**

- pytest: 2,618 passed;
- web type-check and production build;
- browser smoke test of every tab, including phone width;
- browser engine parity: 698 of 698 charts equal to the API, plus 13 boundary scans with 2,520 sign changes;
- the slider test with the API stopped;
- `swe.wasm` rebuilt byte-for-byte.

**Fresh install:** a new clone on Linux ran `scripts/start.sh` from nothing to a working workbench, and the smoke test passed against it.

## Still draft or open

R1 runs on a recorded default for each item below. Each needs a person before it is final, mostly the Jyotish reviewer. Details are in `docs/DECISIONS.md`.

| # | Item | Default in R1 | Who decides |
| --- | --- | --- | --- |
| 18 | 56 yoga rules | `draft`; variant readings in each rule's notes | Jyotish reviewer |
| 24 | 18 reading topics and their factor weights | `draft`, BPHS sources | Jyotish reviewer |
| 20 | 12 rectification event rules | `draft`; Rahu/Ketu linked by occupancy only | Jyotish reviewer |
| 1 | House system for the model's frame | Whole-sign; others selectable | User |
| 3 | Which Chara/Narayana dasha to lead with | K. N. Rao's Chara; all 19 rasi dashas available | User and reviewer |
| 4 | Gender-dependent rules | Not implemented; gender never asked | User |
| 12 | Kendra bala houses | Whole-sign (as JHora) | Reviewer |
| 15 | Sun and Moon Cheshta bala | As JHora's code | User (reopen on request) |
| 19 | Mercury in Virgo in Chara dasha | Exalted (BPHS) | Reviewer |
| — | Mercury in the 10th in transit vedha | JHora's 7th, where the published table gives the 8th | Reviewer |
| — | Sudasa's "sign 12" | As JHora | User |
| — | Moon's moolatrikona | Taurus 4° to 20° (as JHora) | Reviewer |

## Known limits

- **Polar births** beyond ±66° latitude are refused: without a sunrise there is no base for the special lagnas, Tribhaga, vara and hora.
- **Bombay Time and Calcutta Time** (before 1955 and 1948) are not modelled. The birth form warns when a date and place fall in them, so the offset can be entered by hand.
- **Dates after 2016** can drift slightly from JHora, which uses its own projection of future Delta T (#22).
- **Shadbala** keeps two decided differences from JHora: Yuddha bala as BPHS, and Cheshta bala from astronomical mean motions.
- **Browser engine** covers the time ribbon at the default settings: charts, running periods and boundary marks. The other tabs still call the local API.
- **Windows** launcher not yet tested on Windows.
- **Never predicted:** a child's sex, or the timing of death, serious illness or accidents. Those events are check-only in rectification.
