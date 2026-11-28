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
- **Fit curve:** the total score at each candidate birth time, drawn on the ribbon, with a "Jump to best fit" button (how the best fit is chosen is below).
- **Indicative periods** for marriage, children, career and relocation.

### How the best-fit time is chosen

*This describes the scoring in 1.0.0. After the release, research found these linking rules are not stated in BPHS. They are kept as the "modern" rule set, and the default is now a classical rule set (below).*

The best fit is the candidate birth time at which the most events find their dasha lords and Jupiter-Saturn transit linked to them. Ties go to the time nearest the one recorded.

1. **Candidate times:** the recorded time shifted across the ribbon's window, every 30 seconds for ±20 or ±30 min and every 60 seconds for ±2 h (121 candidates at ±30 min).
2. **Recompute:** at each candidate, the engine rebuilds the chart (D1 and the event vargas) and the Vimshottari periods from that time's Moon.
3. **Score each event** on its date, taken at local noon:

| Condition | Points |
| --- | --- |
| Antardasha lord linked to the event | +1 |
| Mahadasha lord linked to the event | +0.5 |
| Double transit: Jupiter and Saturn both occupy or aspect one of the event's D1 houses, counted from this candidate's Lagna | +0.5 |

A lord is linked when, in D1 or the event's varga, it lords or occupies one of the event's houses, or is the event's natural karaka. An event scores at most 2: strong at 1.5 or more, partial at 0.75 or more, otherwise weak.

4. **Total:** the event scores are added, up to 2 per event. Check-only events (deaths, illness) count like the others: they test a time and are never predicted.
5. **Best fit:** the candidate with the highest total. When several share it, the one nearest the recorded time wins; between two equally near, the earlier.
6. **Helps decide:** an event whose verdict changes somewhere in the window. An event with the same verdict everywhere adds the same points to every candidate and cannot move the best fit.

**Limits of this score.**

- Every event weighs the same, whatever its type.
- Only the Vimshottari mahadasha and antardasha count; pratyantars do not.
- The total moves in steps of 0.5, so the top is often a plateau several minutes wide. The button jumps to one point on it, the one nearest the recorded time; the curve on the ribbon shows how wide the plateau is, and that width is the real uncertainty.
- The event rules are drafts (#20).

### Is the best fit real? (added after 1.0.0)

A best fit is always found somewhere, even for made-up dates. So the ribbon also says whether the events point to a birth time at all, in one line under the "Jump to best fit" button.

**How it is checked.** The tool keeps the same chart and the same event types and gives the events 200 sets of random dates. Each date is drawn from the years the real events span, widened by five years each side and never before birth. For each set it finds the best total anywhere in the window, just as for the real events, and counts how many sets do at least as well as the real ones. That count, as a fraction, is the p-value: (1 + count) / 201. The random dates are seeded from the birth and the events, so the same input always gives the same answer.

**What the line says.**

| Line on the ribbon | p-value | Button | Meaning |
| --- | --- | --- | --- |
| Life-event fit unlikely by chance | 0.05 or less | Solid | The real events fit this chart much better than random dates do; the peak is worth taking seriously. |
| Weak life-event fit | above 0.05, up to 0.2 | Dashed | Some support, but random dates often come close. |
| No signal in the life events | above 0.2 | Dashed | Random dates fit about as well; the best fit says nothing about the birth time. |

The best-fit line on the curve follows the button: solid green only when the fit is unlikely by chance, dashed grey otherwise. The peak is always marked, so you can see where it is, but only a solid line is a suggested birth time.

An example: "random dates fit as well in 163 of 200 tries (p = 0.816)" means 163 of the 200 invented sets of dates scored as high as the real events, so the peak is what these rules give for almost any dates.

**When it says no signal:** add more events with exact dates (two or three rarely beat chance), prefer events dated to the day or month, and if it still says no signal, rely on the boundary marks and your own judgment rather than the curve.

**How well the check works.**

- On random event dates (150 charts) it flagged 3.3% at p 0.05 or less, about the 5% expected by chance.
- On events planted in periods the rules favour (60 charts) it flagged 98%.
- It says whether the events carry a signal under the current rules. It does not show that the rules are right; that needs charts with known birth times and dated events.

The curve and 200 random sets take under a second at ±30 min.

### Classical rules (added after 1.0.0)

The 1.0.0 rules link a dasha lord to an event through D1 and the event's varga, and score the Jupiter-Saturn double transit. Neither is stated in Brihat Parashara Hora Shastra. A new rule set, now the default, uses only conditions the texts give, each citing its verse (BPHS, and Phaladeepika in V. Subrahmanya Sastri's translation). The Life events panel switches between "Classical" and "Modern".

| Part of the score | Classical rule | Points |
| --- | --- | --- |
| The antardasha lord gives the event | e.g. marriage: lords, occupies or aspects the 7th, or is Venus (Phaladeepika 10.13, 19.26); children: lords of 1, 5 or 7, in or aspecting the 5th, or Jupiter (Phaladeepika 12.25); career: the 10th lord (BPHS 48.6); property: the 4th lord (BPHS 48.3) | +1 |
| The mahadasha lord gives the event | the same conditions | +0.5 |
| The antardasha is good | its lord in a kendra, trikona or the 11th, exalted or in its own sign, or well placed from the mahadasha lord, with nothing against it (BPHS ch. 52-60; Phaladeepika 20.14, 20.29). Mixed scores +0.25 | +0.5 |
| Jupiter's transit, where a text gives one | marriage: a trine to the 7th lord's sign or navamsa (Phaladeepika 10.14); children: the 5th or 11th from the Moon (Phaladeepika 26.19-20) | +0.5 |

- **Events with no classical timing rule** (sibling, spiritual) are scored on the period's quality alone.
- **Check-only events** (death, illness) also score on quality alone, the reverse way. No death-timing rule is used.
- **Strong and partial** are set at 75% and 37.5% of each event's maximum.

On random charts the classical curve has far fewer chance peaks than the 1.0.0 rules: it moves 0.9 points on average across ±30 minutes, against 2.7. The significance check flags 2.5% of random-event charts. The verse references, the measurements and the points still open for the reviewer are in `docs/research/BPHS-dasha-events.md`. All rules remain drafts (#20).

## Rule-based readings

For 18 life topics, R1 lists the factors the classical rules weigh and ranks them. It then drafts a short text in which every sentence cites the engine facts it rests on. There is no neural network: the text comes from rules, so each claim can be traced.

**Topics:** personality and temperament; fame and reputation; earned income; accumulated wealth; career direction; business and partnerships; marriage quality; children (fertility only); father; mother; siblings; property and land; vehicles; school and higher education; foreign travel and settlement; litigation, enemies and competition; spiritual practice; health indicators (technical only, no draft text).

How a reading is built:

1. **Fact sheet:** the engine's facts for the chart, each with an id, such as the lord of the 10th, a graha's dignity, a yoga, or a Shadbala ratio.
2. **Ranked factors:** the house lord, occupants, aspects, karaka, yogas and the governing varga's lord. Each is weighted for the topic and read as favouring the native, against the native, or mixed.
3. **Scope:** the natal promise alone, or also the Vimshottari lords running on a chosen date.
4. **Uncertainty:** factors that rest on a varga Lagna changing sign within 5 minutes of the birth time are marked uncertain.
5. **Cited draft:** a sentence for each factor, with links to the facts it cites. A verifier drops any sentence that fails one of three checks: every claim must rest on a cited fact, every claim is rechecked against the chart, and every graha, sign or house the sentence names must be one of its claims. Dropped sentences are listed with the reason.
6. **Safety filter:** it never states a child's sex, and never gives timing of death, serious illness or accidents. Health is technical factors only, with a disclaimer.
7. **Feedback:** you can accept or reject each factor. The choice is stored locally as a label for future training.

All 18 topics and their factor weights are `draft` (decision #24).

### Favours the native or against the native (added after 1.0.0)

Each factor now reads as **favours the native**, **against the native** or **mixed**, in every topic. In 1.0.0 the labels were "supports" and "obstructs". For litigation and enemies, that left it unclear whether "supports" meant more disputes or winning them. A line above the factor table names what the readings are for. For disputes, that is success over enemies, in disputes and in competition.

**The general rule** is unchanged for most topics:

- A natural benefic in a topic's house, or aspecting it, favours the native. A malefic is against.
- The house lord in a kendra or trikona favours the native, and in a dusthana is against.
- The planet's dignity, Shadbala and combustion adjust the reading.

**House rules from the texts.** Where a text gives a house its own rule, that rule replaces the general one, and the "Why" column cites the verse:

| Topic | Factor | Reads as | Source |
|---|---|---|---|
| Litigation, enemies and competition | Sun, Mars, Mercury, Jupiter, Venus or Ketu in the 6th | favours the native | Phaladeepika 8.3, 8.9, 8.12, 8.15, 8.18, 8.30 |
| Litigation, enemies and competition | Moon, Saturn or Rahu in the 6th | against the native | Phaladeepika 8.6, 8.22, 8.26 |
| Litigation, enemies and competition | A malefic aspecting the 6th, or the 6th lord in the 6th, 8th or 12th | favours the native | Phaladeepika 6.57, 6.63 (Harsha yoga) |
| Litigation, enemies and competition | A benefic aspecting the 6th, or the 6th lord in a kendra or trikona | mixed | no rule found |
| Foreign travel and settlement | Any planet in the 12th, or aspecting it | favours the native | BPHS 23.11–12 |
| Health indicators | The 6th or 8th lord in the 6th, 8th or 12th | favours the native | Phaladeepika 6.57, 6.63, 6.65 (Harsha, Sarala) |

In 1.0.0, the general rule read malefics in the 6th as against the native. It read the 6th lord in a dusthana the same way, which contradicted the Harsha yoga listed for the same topic. Three other topics were checked and agree with the general rule: siblings (BPHS 14.1, 14.14), gains (BPHS 22.11) and spiritual practice (BPHS 23.9–10). The 6th lord's dignity and strength still count: in a kendra, a strong 6th lord can read as favouring the native.

**The presets, for litigation, enemies and competition** (D1 factors):

| Preset | Favours the native | Against the native | Mixed |
|---|---|---|---|
| Mahatma Gandhi | Jupiter, the 6th lord, in the 7th; Mars (karaka); the Sun aspects the 6th | – | – |
| Sri Aurobindo | Jupiter, the 6th lord, in the 1st; Mars (karaka) | the Moon in the 6th; Saturn in the 6th | – |
| Ramakrishna Paramhansa | the Moon, the 6th lord, in the 1st; Mars and Saturn aspect the 6th | Mars (karaka) | – |
| B. V. Raman | the Moon, the 6th lord, in the 4th; Mars (karaka); the Sun in the 6th; Saturn aspects the 6th | – | Jupiter aspects the 6th |
| Suryanarayan Rao | Venus, the 6th lord, in the 8th; Harsha yoga; Ketu in the 6th; the Moon and Rahu aspect the 6th | – | Mars (karaka); Jupiter aspects the 6th |
| Maharshi Mahesh Yogi | Mercury, the 6th lord, in the 1st; Ketu in the 6th; Mars (karaka); Rahu and the Sun aspect the 6th | – | Venus aspects the 6th |
| Sanjay Rath | Mercury in the 6th | – | the Sun, the 6th lord, in the 5th; Mars (karaka); the Moon aspects the 6th |
| P. V. R. Narasimha Rao | Harsha yoga; Saturn, the 6th lord, in the 8th; Mars (karaka); Ketu aspects the 6th | the Moon in the 6th; Rahu in the 6th | Jupiter aspects the 6th |

**Open for the reviewer:**

- Phaladeepika disagrees with itself on the 6th, 8th and 12th houses. In 15.18 it quotes Satyacharya, who reverses the general rule there. In 15.19, Mantreswara's own view is that malefics in those houses increase their evils. Neither is used as a general rule; the per-planet verses of ch. 8 are used instead.
- BPHS ch. 17, on the 6th house, is about illness and wounds and gives no rule for enemies. The dispute rules rest on Phaladeepika alone.
- The 6th-house rules are also applied in the D6 chart, though the verses describe the birth chart.
- The verse numbers follow archive.org scans of V. Subrahmanya Sastri's translation (1950) and need checking against print.

The rules are in `rules/readings/topics.yaml` (`house_rules`). The decision is recorded as "Reading house rules" in `docs/DECISIONS.md`, and all of it stays draft (#24).

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
