# Decisions

## Open

| # | Decision | Current default in code | Needed by |
| --- | --- | --- | --- |
| 1 | House system for the model's frame | Whole-sign; others selectable | Phase 1, week 1 |
| 3 | Chara dasha method and Narayana dasha | Chara: K. N. Rao (start at Lagna, direction by the 9th; lord count; +1 exalted / -1 debilitated, none when the lord is in the sign; second cycle 12 minus first; antardasha table as PyJHora). PVN Rao (Parashara) and Iranganti variants not yet; Narayana not yet | Before phase 2, expert |
| 4 | Gender-dependent rules | Not yet implemented; the yoga engine has no gender input yet | Before phase 4 |
| 12 | Shadbala: Kendra bala houses | Whole-sign houses (option: Sripati bhava) | Phase 1, expert |
| 15 | Shadbala: Sun/Moon Cheshta | Undoubled Ayana (Sun) and Paksha (Moon) bala | Phase 1, expert |
| 18 | Yoga definitions | 56 rules marked `draft`; variant readings in each rule's `notes`. Not yet checked: strong Lagna lord (Lakshmi, Kahala), Gajakesari's extra conditions | Expert review of `rules/yogas/*.yaml` |
| 19 | Chara dasha: Mercury in Virgo | Counted as exalted (BPHS), so +1 year where it is the counted lord outside its own sign; PyJHora treats it as own sign | With #3 |
| 20 | Rectification event rules | 12 event types (design table), draft. A dasha lord is linked if, in D1 or the event's varga, it lords or occupies an event house or is the karaka; D2 and D30 add no house links; Rahu and Ketu link only by occupancy (no dispositor rule yet); double transit = Jupiter and Saturn both occupy or aspect an event house in D1 | Expert review of `rules/btr_events.yaml` |

## Decided

| Decision | Choice |
| --- | --- |
| Product scope | Astrologer workbench first, all branches over R1-R3; consumer edition later on the same API |
| Calculation location | Deterministic Layer 0 outside the network |
| Zodiac frame | Lagna rotated to 0 deg for the model |
| Vargas encoded by the model | 13: D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D30, D60 |
| Golden reference | Jagannatha Hora exports in `tests/golden/jhora` (8 charts) |
| Ayanamsa, nodes, positions | Lahiri, mean nodes, true (geometric) positions: JHora match within 2.2" |
| Sunrise for special lagnas | Disc centre, no refraction (JHora) |
| Ashtakavarga | PVR variant; seven grahas occupy in Ekadhipatya; Virgo multiplier 5 (JHora: all pindas exact) |
| Vimshottari year | Solar year by the Sun's sidereal motion (JHora: 584/648 exact, rest within 1 day); fixed years optional |
| Pranapada formula | Sun-modality offset, one sign per 6 minutes (JHora match within 7.6', from a ~1 s sunrise difference) |
| Shadbala benefics | Moon benefic from Shukla to Krishna Ashtami (at least 90 deg from the Sun). Mercury by Jagannatha Hora 8.0's own rule, read from its code (jhora.exe, the function that fills the benefic table before Paksha and Drik bala; decision #23 closed): the Sun, Mars and Saturn score -1, Jupiter and Venus +1, the Moon +1 or -1 by the rule above; each adds its score when Mercury is within 15 deg of it or 165-195 deg from it, and 0.75 x its score when Mercury lies within 15 deg of its special aspect (Mars 90/210, Jupiter 120/240, Saturn 60/270 deg ahead). Malefic when the total is negative, or zero with any planet counted; benefic when positive or untouched. The nodes do not count. Matches all 23 golden Shadbala charts, including edge_48-50 designed for this. Earlier fitted rules (15-deg orb, equal bhava) are superseded. Options: `mercury_rule` bhava, majority (sign), any |
| Shadbala Abda/Masa | Kali ahargana - 13 days: the only offset (mod 360) that gives JHora's year and month lords on all 5 golden Shadbala charts. The earlier +1 matched the first three by chance and failed edge_06 (1990-01-10). More charts in the disputed part of the 30-day cycle would confirm it |
| Shadbala Dig and Nathonnatha | 10th point = Lagna - 90 deg, 4th = Lagna + 90 deg (not the meridian); Nathonnatha from the Sun's distance to Lagna - 90 deg (equals the Sun's Dig bala). Back-solved from JHora on golden charts edge_18-20; matches all 9 charts to 0.01 virupa. Meridian and clock-time versions are options |
| Drishti strength (Drik bala) | Straight lines between the BPHS values at every 30 deg (0, 15, 45, 30, 0, 60, 45, 30, 15, 0 from 30 to 300 deg), with special-aspect points raised to 60: Mars 90/210, Jupiter 120/240, Saturn 60/270. Measured from JHora (23 single-aspect points, all within 0.03); BPHS flat additions are an option |
| Moon's moolatrikona | Taurus 4-20 deg (JHora: golden charts put the end between 17.2 and 20.2 deg). Affects dignity labels, yogas and Saptavargaja |
| Ayana bala (#13) | Declination from the BPHS kranti table (24 deg maximum, 15-degree steps, linear between), ecliptic latitude ignored, on the sidereal longitude + a fixed 23 deg, as JHora does: the shift needed on 20 charts (1965-2001) was exactly the chart's ayanamsa - 23. Matches JHora within 0.005 on 119 values (was 0.86 with the true tropical longitude). Options: `ayana_fixed_ayanamsa=None` (true tropical), `ayana_declination="true"` (ephemeris) |
| Moon's Cheshta | Distance from the Sun / 3 (JHora) |
| D2 (Hora) scheme | Uma-Shambhu (parivritti, even signs reversed), as JHora's D-2 and Saptavargaja (21/21 exact); Parashari Leo/Cancer hora optional |
| Cheshta bala | Astronomical mean positions (modern orbital elements), not JHora's tables. Known difference from JHora (RMS 16 virupas on 3 charts); show a note in the UI. Revisit later |
| Test oracle | PyJHora in a separate environment (AGPL; never imported) |
| Yoga rule format | YAML files of predicates (all/any/not) with `source: {text, section}`, `status`, `notes` and optional `cancelled_by`; results carry evidence strings |
| Ashtottari | Lords Su, Mo, Ma, Me, Sa, Ju, Ra, Ve from Ardra; balance by the Moon's progress through the lord's whole nakshatra run; antardashas from the dasha lord (JHora/PyJHora) |
| Front-end stack | Next.js + React + TypeScript, plain CSS; fonts Martel and Hind (Latin + Devanagari); the slider calls the API (latest-wins) until the WebAssembly engine exists |
| Yuddha bala (#17) | Keep BPHS: within 1 deg, the planet with more Sthana + Dig + Kala (to Hora) wins; amount = difference / disc-diameter difference. Known difference from JHora 8.0, which applies none (golden charts edge_05, edge_06: 0.74 and 1.27 virupas, inside the Kala tolerance). Decided by the user, 24 Nov 2026 |
| Polar births | Out of scope: no sunrise in polar night or midnight sun, so the special lagnas, Tribhaga, vara and hora have no base. The API rejects latitudes beyond +/-66 deg; the JHora golden chart for Tromso was dropped. Decided by the user, 24 Nov 2026 |
| Bhava bala (M2.2) | As Jagannatha Hora 8.0's code (jhora.exe): equal houses with each middle at Lagna + 30 deg x n; Bhava dig bala by the class of the house's sign (human strongest in the 1st, water 4th, four-footed 10th, Scorpio 7th; 60 there, 10 less per house away), Sagittarius human and Capricorn four-footed while the Lagna is under 15 deg of its sign, otherwise four-footed and water; Bhava drik bala from Drik bala's aspect curve, Jupiter and Mercury in full (Mercury whatever its nature), Venus and a benefic Moon a quarter, malefics minus a quarter, nodes none; lord's bala = the lord's Shadbala total (ours includes Yuddha, JHora's has none). Dig and Drik match JHora on 23 charts |
| Vimshopaka bala | Own sign 20; otherwise compound relationship with the sign lord (18/15/10/7/5), temporal part within each varga; Shad-, Dasha- and Shodashavarga weights as BPHS. Rahu and Ketu own no sign; friends Venus, Saturn; neutral Mercury, Jupiter; enemies Sun, Moon, Mars (back-solved from JHora, the only fit among all own-sign and relationship combinations). Matches JHora on all 1,116 golden values. Saptavarga weights: BPHS by default (D7 2.5, D9 4.5, D12 2, D30 1; the user's decision, 24 Nov 2026); option `saptavarga_weights="jhora"` gives JHora 8.0's D7 1, D9 2.5, D12 4.5, D30 2, which fit all 31 golden charts within 0.005 and look like BPHS's shifted by one varga |
| Historical Indian zones (M1.3) | Not modelled; the birth form warns instead (`zone_warnings` in timeutil, `POST /v1/birth/warnings`, also in `/v1/chart`). India before 1956: Bombay Time UTC+4:51 within 250 km of Bombay (1906 to about 1955), Calcutta Time UTC+5:53:20 within 150 km of Calcutta (1906-1948), the tz database's official time (war time +6:30) from 1906, local mean time or Madras time before 1906. A warning never changes the chart. Decided by the user, 24 Nov 2026 |
| Delta T for future dates (#22) | Swiss Ephemeris's current model (Stephenson et al. 2016 with its extrapolation). JHora 8.0's is larger by about 48 s in 2050 and 125 s in 2100 (an older extrapolation): the Moon differs by 27" and 75", Vimshottari dates by about 2 days. Future Delta T is unknowable; the current model is the better estimate. Golden charts edge_39 (2050) and edge_40 (2100) stay in tests/golden/pending/ as a record of the difference. Decided by the user, 24 Nov 2026 |
