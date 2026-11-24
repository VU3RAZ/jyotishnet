# Decisions

## Open

| # | Decision | Current default in code | Needed by |
| --- | --- | --- | --- |
| 1 | House system for the model's frame | Whole-sign; others selectable | Phase 1, week 1 |
| 3 | Chara dasha method and Narayana dasha | Chara: K. N. Rao (start at Lagna, direction by the 9th; lord count; +1 exalted / -1 debilitated, none when the lord is in the sign; second cycle 12 minus first; antardasha table as PyJHora). PVN Rao (Parashara) and Iranganti variants not yet; Narayana not yet | Before phase 2, expert |
| 4 | Gender-dependent rules | Not yet implemented; the yoga engine has no gender input yet | Before phase 4 |
| 12 | Shadbala: Kendra bala houses | Whole-sign houses (option: Sripati bhava) | Phase 1, expert |
| 13 | Shadbala: Ayana bala | Ephemeris declination (BPHS uses kranti tables) | Phase 1, golden set |
| 15 | Shadbala: Sun/Moon Cheshta | Undoubled Ayana (Sun) and Paksha (Moon) bala | Phase 1, expert |
| 17 | Yuddha bala: winner and orb | BPHS: within 1 deg; the planet with more Sthana + Dig + Kala (to Hora) wins; amount = difference / disc-diameter difference. Evidence (Nov 2026): JHora 8.0 applies no Yuddha bala on golden charts edge_05 (Mars-Jupiter 0.15 deg) and edge_06 (Mercury-Saturn 0.25 deg); ours adds 0.74 and 1.27 virupas, inside the Kala tolerance. Options: keep BPHS (note the JHora difference) or add a "none" setting as default to match JHora | User
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
| Shadbala benefics | Moon benefic from Shukla to Krishna Ashtami (at least 90 deg from the Sun). Mercury by majority (PVR Narasimha Rao; JHora): malefic when the Sun, Mars, Saturn, Rahu, Ketu or a malefic Moon in its sign outnumber Jupiter, Venus and a benefic Moon; a tie stays benefic. Matches all 5 JHora Shadbala charts (edge_05: Mercury with the Sun alone is malefic; Aurobindo: with the Sun and Venus, benefic). The yoga engine uses the same rule |
| Shadbala Abda/Masa | Kali ahargana - 13 days: the only offset (mod 360) that gives JHora's year and month lords on all 5 golden Shadbala charts. The earlier +1 matched the first three by chance and failed edge_06 (1990-01-10). More charts in the disputed part of the 30-day cycle would confirm it |
| Moon's Cheshta | Distance from the Sun / 3 (JHora) |
| D2 (Hora) scheme | Uma-Shambhu (parivritti, even signs reversed), as JHora's D-2 and Saptavargaja (21/21 exact); Parashari Leo/Cancer hora optional |
| Cheshta bala | Astronomical mean positions (modern orbital elements), not JHora's tables. Known difference from JHora (RMS 16 virupas on 3 charts); show a note in the UI. Revisit later |
| Test oracle | PyJHora in a separate environment (AGPL; never imported) |
| Yoga rule format | YAML files of predicates (all/any/not) with `source: {text, section}`, `status`, `notes` and optional `cancelled_by`; results carry evidence strings |
| Ashtottari | Lords Su, Mo, Ma, Me, Sa, Ju, Ra, Ve from Ardra; balance by the Moon's progress through the lord's whole nakshatra run; antardashas from the dasha lord (JHora/PyJHora) |
| Front-end stack | Next.js + React + TypeScript, plain CSS; fonts Martel and Hind (Latin + Devanagari); the slider calls the API (latest-wins) until the WebAssembly engine exists |
| Yuddha bala (#17) | Keep BPHS: within 1 deg, the planet with more Sthana + Dig + Kala (to Hora) wins; amount = difference / disc-diameter difference. Known difference from JHora 8.0, which applies none (golden charts edge_05, edge_06: 0.74 and 1.27 virupas, inside the Kala tolerance). Decided by the user, 24 Nov 2026 |
