# Jagannatha Hora golden set

`jhora/*.txt` are Jagannatha Hora "Natal Chart" text exports: eight charts born
1836-1970, and 47 edge-case charts `edge_*` (below). `jhora_parser.py` reads them; `tests/test_jhora_golden.py` checks the
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
| Shadbala components (23 charts) | every component and Kala part to JHora's printed precision, except Yuddha and Cheshta | kranti table on sidereal + 23 deg (#13); Mercury by JHora's aspect rule (read from its code) |
| Shadbala totals | differ by Cheshta (#16) and Yuddha (BPHS; JHora applies none) | |

## Edge-case charts (phase 1 gate)

The design doc asks for about 50 golden charts chosen for edge cases. These 49
(47 passing, two kept in pending as a record) fill the gaps the first eight leave. None is a real person. Their inputs are in
`jhd/`; they were exported from JHora 8.0 under Wine on 24 November 2026 (see
`tools/jhora/README.md`; `tools/jhora/make_jhd.py` writes `.jhd` files from a list).

For 7-11 the zone is the historical offset, typed in: JHora's atlas gives
every Indian place 5:30 on any date (see below), so these check that the engine
matches JHora once both use the same offset. 17-20 (New Delhi, noon, 1984) were
chosen so that two candidate Abda/Masa day offsets give different lords.
21-24 (New Delhi, noon, 1990-03-21, 06-21, 09-23, 12-22) put the Sun near
the equinoxes and solstices, for Ayana bala (decision #13). 25-47 (M1.1) add
western and far-eastern zones, summer time, high and equatorial latitudes, 1800
to 2100, births at sunrise and sunset, a Mercury station and a nakshatra change;
48-50 were designed to find Mercury's rule in Shadbala (#23).

**Result:** all 47 live edge charts pass every check in `tests/test_jhora_golden.py`
(planets, Lagna, special lagnas, Navamsa, Ashtakavarga and pindas, Vimshottari,
Vimshopaka). Shadbala totals stay expected failures (Cheshta, #16).
`jhora_shadbala/` holds JHora's Shadbala breakdowns of the first three charts
and of 5, 6, 17-25, 32, 37, 41-43 and 47-50, and `jhora_shadbala/kala/` their
Kaala Bala tables, which `tests/test_jhora_shadbala.py` checks part by part;
all 23 pass. `jhora_bhavabala/` holds JHora's Bhava balas table for the same 23
charts (`tests/test_jhora_bhavabala.py`): Dig bala exact, Drik bala within 0.025
virupa (the Lagna's 17"), lord's bala equal to the lord's Shadbala total.
`jhora_avasthas/` holds JHora's Basic Avasthas table (age, alertness, mood in
D-1) for all 55 charts (`tests/test_jhora_avasthas.py`): all 495 planets match.
The parser also reads the 23 North Indian chart drawings in each export
(`JHoraChart.vargas`); `tests/test_jhora_vargas.py` checks all 22 vargas, skipping a
body only when it lies within its position tolerance of a part boundary (up to 11
of 550 in D81-D144, mostly the Lagna). `jhora_nadiamsa/` holds JHora's D-150 Amsa
rulers table (division, index, name; `tests/test_jhora_nadiamsa.py`).
The body table's special lagnas, upagrahas and Bhrigu Bindu are checked by
`tests/test_jhora_upagrahas.py` (tolerances from the position and sunrise
differences, explained there); `jhora_yogi/` holds JHora's Yogi, Sahayogi and
Avayogi table (`tests/test_jhora_yogi.py`). `jhora_transits/` holds JHora's Basic
Transit Results (Transits tab; right-click the table > Standard, then Ashtakavarga
related, Copy to clipboard each) for one transit date per chart, 24 November of a
year spread over 1990-2034 at 12:00, typed as 5:30 from GMT; JHora applies the
direction already in the chart's zone box, so charts at or west of GMT carry
-05:30 in the file header (`tests/test_jhora_transits.py`).

`jhora_rasi_dashas/` holds JHora's 19 rasi dashas per chart (Dasas tab > Rasi dasas;
right-click > dasha > Copy, then the antardashas of the first two mahadashas), made
from the raw exports by `tools/import_jhora_rasi_dashas.py`; JHora's chart view was
set to hide Mandi and the special lagnas so that its drawings show the arudha labels
for a visual check (`tests/test_jhora_rasi_dashas.py`). `jhora_arudhas.json` holds the
sign of each arudha label (AL, A2..A11, UL) read from those drawings for all 55 charts;
null where the label is hidden under other text (29 of 660; `tests/test_jhora_arudhas.py`).

`jhora_panchanga/` holds JHora's monthly panchanga of each chart's birth month at the
birth place (Miscellany tab > Panchanga sub-tab > right-click > "Copy monthly
panchanga"; recipe in `tools/jhora/README.md`), converted by
`tools/import_jhora_panchanga.py` to one entry per day with times in minutes from the
local midnight (`tests/test_jhora_panchanga.py`). JHora's print quirks, handled by the
importer: the last day or two of an export can come out with every time marked "*"
(next day) though they belong to that date, and are dropped; some days print "Moonset"
twice instead of the Moon's sign (`moon_sign` null, 17 days); at Reykjavik in June
the printed sunrise is the next day's (the kalas use the right one).
`pending/jhora_panchanga.json` lists single day fields the test skips, with a note
each: elements ending within seconds of sunrise (JHora and we put them on different
days), the same for a moonrise or moonset seconds after sunrise, the Reykjavik sunrise
print, high-latitude moon events, a few ends about 5 s early on the 1800 and 1836
charts (the 19th-century offset noted below), and three varjyas that JHora leaves out though they
overlap the day.

Files in `pending/` wait for the engine or a decision; the tests do not read
them (except `pending/jhora_panchanga.json`, the skip list above):

- `pending/jhora/edge_39_*`, `edge_40_*` (2050, 2100): JHora's Delta T for
  future dates is larger than Swiss Ephemeris's current model (about 48 s in
  2050, 125 s in 2100), so the Moon differs by 27" and 75" and Vimshottari dates
  by about 2 days. Decided (#22): we keep Swiss Ephemeris's model; these stay
  here as a record of the difference.
- `pending/jhora_rasi_dashas/edge_38_*` (1800, local mean time; the other nine
  dashas are tested): every sign and antardasha order matches, but ten of the 19 dashas have start dates 5.1-5.6 s
  from JHora's (1875-1936; limit 5 s). The difference wanders between 0 and 5.6 s
  from one solar return to the next rather than growing, which points at JHora's
  Delta T for the 19th century differing from Swiss Ephemeris's; not investigated.
- `pending/jhora_rasi_dashas/pandit_suryanarayan_rao.json` (Yogardha) and
  `ramakrishna_paramhansa.json` (Chara of Rangacharya, Padanaathamsa): signs and
  orders match; one start date each is 5.03-5.06 s from JHora's (1938, 1945).
  Over all charts the date differences before 2016 average 0.00 s (sd 1.34 s,
  948 dates) but each chart has its own offset of up to about 2.6 s; it does not
  follow the natal Sun's difference from JHora. Cause not found yet.

Chart 12 (Tromso, polar night) was dropped: polar births are out of scope
(`docs/DECISIONS.md`). JHora gave no usable reference for it either: it printed
"Sunrise: 13:00:00 (November 24)", a time on the day of the export.

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
| 13 | High latitude, short night | 1975-06-21 | 23:30:00 | Reykjavik | 64.15 N, 21.94 W | +0:00 |
| 14 | Southern hemisphere, summer time | 1988-01-26 | 09:00:00 | Sydney | 33.87 S, 151.21 E | +11:00 |
| 15 | Southern hemisphere | 1970-07-15 | 14:00:00 | Johannesburg | 26.20 S, 28.05 E | +2:00 |
| 16 | Southern and western hemispheres | 1965-10-10 | 20:00:00 | Buenos Aires | 34.60 S, 58.38 W | -3:00 |
| 25 | Western zone, summer time | 1965-07-04 | 21:30:00 | New York | 40.71 N, 74.01 W | -4:00 |
| 26 | Western zone | 1985-11-20 | 03:15:00 | Los Angeles | 34.05 N, 118.24 W | -8:00 |
| 27 | Western zone, tropics | 1970-03-15 | 14:00:00 | Mexico City | 19.43 N, 99.13 W | -6:00 |
| 28 | Southern, western; morning | 1995-08-10 | 06:05:00 | Lima | 12.05 S, 77.04 W | -5:00 |
| 29 | Southern summer time, near midnight | 2001-12-25 | 23:50:00 | Santiago | 33.45 S, 70.67 W | -3:00 |
| 30 | British Summer Time | 1953-06-02 | 11:00:00 | London | 51.51 N, 0.13 W | +1:00 |
| 31 | Europe, +3 | 1961-04-12 | 09:07:00 | Moscow | 55.76 N, 37.62 E | +3:00 |
| 32 | High latitude, midsummer midnight (Shadbala) | 1975-06-21 | 23:59:00 | Helsinki | 60.17 N, 24.94 E | +2:00 |
| 33 | High latitude, midwinter noon | 1990-12-21 | 12:00:00 | Anchorage | 61.22 N, 149.90 W | -9:00 |
| 34 | East Asia | 1989-01-08 | 05:00:00 | Tokyo | 35.68 N, 139.69 E | +9:00 |
| 35 | Southern, +8 | 2010-02-14 | 16:00:00 | Perth | 31.95 S, 115.86 E | +8:00 |
| 36 | +13 (summer time), just after midnight | 1980-01-01 | 00:05:00 | Auckland | 36.85 S, 174.76 E | +13:00 |
| 37 | Far south, midwinter (Shadbala) | 1998-06-21 | 12:00:00 | Ushuaia | 54.80 S, 68.30 W | -3:00 |
| 38 | 1800, local mean time | 1800-01-01 | 12:00:00 | Varanasi | 25.32 N, 83.01 E | +5:32:02 |
| 39 | 2050 (pending: future Delta T, #22) | 2050-06-15 | 08:00:00 | Bengaluru | 12.97 N, 77.59 E | +5:30 |
| 40 | 2100, midnight (pending: future Delta T, #22) | 2100-03-01 | 00:00:00 | New Delhi | 28.61 N, 77.21 E | +5:30 |
| 41 | 2 min after sunrise (special lagnas, Tribhaga; Shadbala) | 2000-03-21 | 06:29:46 | New Delhi | 28.61 N, 77.21 E | +5:30 |
| 42 | 2 min after sunset (Shadbala) | 1998-11-10 | 17:38:21 | Chennai | 13.08 N, 80.27 E | +5:30 |
| 43 | 3 min before sunrise: the previous weekday's vara (Shadbala) | 2001-07-01 | 05:28:00 | New Delhi | 28.61 N, 77.21 E | +5:30 |
| 44 | Mercury stationary | 2020-02-17 | 06:30:00 | Mumbai | 19.08 N, 72.88 E | +5:30 |
| 45 | Moon 33" into Ashvini (Vimshottari lord change) | 2011-05-01 | 23:31:18 | Hyderabad | 17.39 N, 78.49 E | +5:30 |
| 46 | Equator, east | 1963-12-12 | 10:00:00 | Nairobi | 1.29 S, 36.82 E | +3:00 |
| 47 | Equator, west; Mercury-Venus war (Shadbala) | 1979-09-23 | 18:00:00 | Quito | 0.18 S, 78.47 W | -5:00 |
| 48 | Venus 15.5 deg from Mercury, nothing else within 21 deg (Mercury's nature, #23) | 1982-03-03 | 12:00:00 | New Delhi | 28.61 N, 77.21 E | +5:30 |
| 49 | Venus 16.4 deg from Mercury (#23) | 1992-07-13 | 12:00:00 | New Delhi | 28.61 N, 77.21 E | +5:30 |
| 50 | Venus 17.3 deg from Mercury (#23) | 1978-01-04 | 12:00:00 | New Delhi | 28.61 N, 77.21 E | +5:30 |

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
