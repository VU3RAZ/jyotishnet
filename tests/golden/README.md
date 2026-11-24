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
