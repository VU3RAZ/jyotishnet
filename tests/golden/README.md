# Jagannatha Hora golden set

`jhora/*.txt` are Jagannatha Hora "Natal Chart" text exports: eight charts born
1836-1970, and 15 edge-case charts `edge_*` (below). `jhora_parser.py` reads them; `tests/test_jhora_golden.py` checks the
engine against them; `tools/compare_jhora.py` compares candidate settings.

## Adding a chart

In Jagannatha Hora, open the chart and use Edit > Copy complete calculations,
then save the text here as `firstname_lastname.txt`. `tools/jhora/` does this
under Wine from `.jhd` files, with the settings the golden set needs. The parser reads the date, time,
time zone, place, ayanamsa, sunrise, body table, Ashtakavarga, pindas, Shadbala
totals and Vimshottari dasha. Useful additions: births near sign or nakshatra
boundaries, high latitudes, pre-1955 Indian zones, and the southern hemisphere.

## What the set confirmed (November 2026)

| Item | Result | Setting |
| --- | --- | --- |
| Ayanamsa | within 0.1" | Lahiri |
| Planets | within 2.2" | true (geometric) positions |
| Rahu/Ketu | within 0.1" | mean nodes |
| Lagna | within 17" | |
| Bhava/Hora/Ghati Lagna, Pranapada | within 0.1' / 0.4' / 1.9' / 7.6' | sunrise: disc centre, no refraction |
| Navamsa | 80/80 | |
| Ashtakavarga BAV, Sodhya/Rasi/Graha pinda | all exact | PVR variant, seven grahas occupy, Virgo x5 |
| Vimshottari antardasha starts | 584/648 exact, rest within 1 day | solar (Sun's sidereal motion) year |
| Shadbala components (13 charts) | within 0.05 virupa; Ayana within 0.73 | BPHS kranti table (#13); Mercury by bhava majority |
| Shadbala totals | differ by Cheshta (#16) and Yuddha (BPHS; JHora applies none) | |

## Edge-case charts (phase 1 gate)

The design doc asks for about 50 golden charts chosen for edge cases. These 24
fill the gaps the first eight leave. None is a real person. Their inputs are in
`jhd/`; they were exported from JHora 8.0 under Wine on 24 November 2026 (see
`tools/jhora/README.md`).

For 7-11 the zone is the historical offset, typed in: JHora's atlas gives
every Indian place 5:30 on any date (see below), so these check that the engine
matches JHora once both use the same offset. 17-20 (New Delhi, noon, 1984) were
chosen so that two candidate Abda/Masa day offsets give different lords.
21-24 (New Delhi, noon, 1990-03-21, 06-21, 09-23, 12-22) put the Sun near
the equinoxes and solstices, for Ayana bala (decision #13).

**Result:** 23 of 24 pass every check in `tests/test_jhora_golden.py` (planets,
Lagna, special lagnas, Navamsa, Ashtakavarga and pindas, Vimshottari), including
the boundary cases. Shadbala totals stay expected failures (Cheshta, #16).
`jhora_shadbala/` holds JHora's Shadbala breakdowns of the first three charts
and of 5, 6 and 17-24, and `jhora_shadbala/kala/` their Kaala Bala tables,
which `tests/test_jhora_shadbala.py` checks part by part; all 13 pass.

`pending/` holds a file that waits for the engine or a decision; the tests do
not read it:

- `pending/jhora/edge_12_polar_night_tromso.txt`: the engine cannot build a
  chart without a sunrise (`tests/test_high_latitude.py`). JHora's export is no
  reference for the sunrise-based items either: it prints "Sunrise: 13:00:00
  (November 24)", a time on the day of the export, not near the birth.

Boundary times below were found with the engine (Lahiri, mean nodes). Margins
are wider than the known JHora differences (Lagna 17", planets 2.2"), so a sign
flip here is a real disagreement, not noise.

| # | What it tests | Date | Time | Place | Lat, lon | Zone |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Lagna 54" into Aries | 1984-03-10 | 08:16:37 | New Delhi | 28.61 N, 77.21 E | +5:30 |
| 2 | Lagna 53" before Aquarius (a D1 and D9 boundary) | 1972-08-21 | 18:05:22 | Chennai | 13.08 N, 80.27 E | +5:30 |
| 3 | Moon 15" into Hasta | 1961-11-05 | 06:46:15 | Kolkata | 22.57 N, 88.36 E | +5:30 |
| 4 | Sun 21" into Aries (Mesha sankranti) | 1975-04-14 | 07:32:00 | Mumbai | 19.08 N, 72.88 E | +5:30 |
| 5 | Planetary war, Mars and Jupiter 0.15 deg apart (Yuddha bala, decision #17) | 1991-06-14 | 12:00:00 | New Delhi | 28.61 N, 77.21 E | +5:30 |
| 6 | Planetary war, Mercury and Saturn 0.25 deg apart | 1990-01-10 | 12:00:00 | New Delhi | 28.61 N, 77.21 E | +5:30 |
| 7 | War time | 1943-06-01 | 12:00:00 | Kolkata | 22.57 N, 88.36 E | +6:30 |
| 8 | The 1942 break in war time (IANA: May 15 to Sep 1) | 1942-07-01 | 12:00:00 | Chennai | 13.08 N, 80.27 E | +5:30 |
| 9 | Bombay Time (until 1955) | 1950-03-01 | 10:00:00 | Mumbai | 19.08 N, 72.88 E | +4:51 |
| 10 | Calcutta Time (until 1948) | 1946-05-10 | 10:00:00 | Kolkata | 22.57 N, 88.36 E | +5:53:20 |
| 11 | Madras railway time | 1890-01-15 | 12:00:00 | Chennai | 13.08 N, 80.27 E | +5:21:10 |
| 12 | Polar night: no sunrise (special lagnas, Tribhaga, vara). The engine raises here today (`tests/test_high_latitude.py`) | 1980-12-21 | 12:00:00 | Tromso | 69.65 N, 18.96 E | +1:00 |
| 13 | High latitude, short night | 1975-06-21 | 23:30:00 | Reykjavik | 64.15 N, 21.94 W | +0:00 |
| 14 | Southern hemisphere, summer time | 1988-01-26 | 09:00:00 | Sydney | 33.87 S, 151.21 E | +11:00 |
| 15 | Southern hemisphere | 1970-07-15 | 14:00:00 | Johannesburg | 26.20 S, 28.05 E | +2:00 |
| 16 | Southern and western hemispheres | 1965-10-10 | 20:00:00 | Buenos Aires | 34.60 S, 58.38 W | -3:00 |

## How Jagannatha Hora handles time zones (JHora 8.0, checked November 2026)

From the shipped files of `jh_full_install.exe` (SHA-256 `37df1209...4c2`):

- The atlas `jhcore/atlas/jhworld.adb` stores, per place, the longitude and
  latitude (degrees and minutes) and two signed bytes: the standard and summer
  offsets in 15-minute units. Every Indian place, Bombay, Calcutta and Madras
  included, carries `16 16`: +5:30 and +5:30. Checked against other places:
  Tromso `04 08` (+1/+2), Johannesburg `08 08` (+2), an Afghan place `12 12` (+4:30),
  New Zealand `30 34` (+12/+13).
- The record has no dates, so the atlas has no history: no war time, Bombay,
  Calcutta or Madras time, and no local mean time. `jhora.exe` names only a
  "Standard Timezone", a "Summer Timezone" and a "Daylight Saving" switch; no
  strings for war time or historical zones were found. (Inference: the code
  that reads the atlas was not traced.)
- The author's sample charts in `data/*.jhd` carry hand-entered local mean time
  for 19th-century births (Gandhi 1869: 4:39:27, Ramakrishna 1836: 5:51,
  Vivekananda 1863: 5:54), and 5:30 from 1906 on.

So a JHora user who takes the zone from the atlas gets 5:30 for a 1943 Kolkata
birth, where the engine's `Asia/Kolkata` gives war time, 6:30: an hour apart.
