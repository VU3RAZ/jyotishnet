# Jagannatha Hora golden set

`jhora/*.txt` are Jagannatha Hora "Natal Chart" text exports (eight charts, born
1836-1970). `jhora_parser.py` reads them; `tests/test_jhora_golden.py` checks the
engine against them; `tools/compare_jhora.py` compares candidate settings.

## Adding a chart

In Jagannatha Hora, open the chart and export the natal chart report as text,
then save it here as `firstname_lastname.txt`. The parser reads the date, time,
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
| Shadbala totals | differ by up to ~100 virupas | open: needs JHora's component table |

## Charts wanted (phase 1 gate)

The design doc asks for about 50 golden charts chosen for edge cases. These
fill the gaps the first eight leave. None needs to be a real person; enter the
data as given. For each, save the natal chart text export to `jhora/`; for 5
and 6, also save the Shadbala tables to `jhora_shadbala/` (same format as the
existing three).

For 7-11, **let JHora's atlas fill the time zone** instead of typing it, and
note in the file name or a comment what offset JHora chose: that tells us which
historical convention JHora follows, which `tests/test_timeutil.py` then pins.

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
| 7 | War time (IANA: +6:30) | 1943-06-01 | 12:00:00 | Kolkata | 22.57 N, 88.36 E | JHora atlas |
| 8 | The 1942 break in war time (IANA: +5:30 from May 15 to Sep 1) | 1942-07-01 | 12:00:00 | Chennai | 13.08 N, 80.27 E | JHora atlas |
| 9 | Bombay Time (+4:51 until 1955; IANA: +5:30) | 1950-03-01 | 10:00:00 | Mumbai | 19.08 N, 72.88 E | JHora atlas |
| 10 | Calcutta Time (+5:53:20 until 1948; IANA: +5:30) | 1946-05-10 | 10:00:00 | Kolkata | 22.57 N, 88.36 E | JHora atlas |
| 11 | Madras railway time (IANA: +5:21:10) | 1890-01-15 | 12:00:00 | Chennai | 13.08 N, 80.27 E | JHora atlas |
| 12 | Polar night: no sunrise (special lagnas, Tribhaga, vara). The engine raises here today (`tests/test_high_latitude.py`) | 1980-12-21 | 12:00:00 | Tromso | 69.65 N, 18.96 E | +1:00 |
| 13 | High latitude, short night | 1975-06-21 | 23:30:00 | Reykjavik | 64.15 N, 21.94 W | +0:00 |
| 14 | Southern hemisphere, summer time | 1988-01-26 | 09:00:00 | Sydney | 33.87 S, 151.21 E | +11:00 |
| 15 | Southern hemisphere | 1970-07-15 | 14:00:00 | Johannesburg | 26.20 S, 28.05 E | +2:00 |
| 16 | Southern and western hemispheres | 1965-10-10 | 20:00:00 | Buenos Aires | 34.60 S, 58.38 W | -3:00 |
