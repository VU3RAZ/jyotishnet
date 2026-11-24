# Decisions

## Open

| # | Decision | Current default in code | Needed by |
| --- | --- | --- | --- |
| 1 | House system for the model's frame | Whole-sign; others selectable | Phase 1, week 1 |
| 3 | Narayana and Chara dashas as model token streams | Not yet implemented | Before phase 2 |
| 4 | Gender-dependent rules | Not yet implemented (rules engine pending) | Before phase 4 |
| 12 | Shadbala: Kendra bala houses | Whole-sign houses (option: Sripati bhava) | Phase 1, expert |
| 13 | Shadbala: Ayana bala | Ephemeris declination (BPHS uses kranti tables) | Phase 1, golden set |
| 16 | Shadbala vs Jagannatha Hora | Against JHora's component table (3 charts): Naisargika exact, Dig within 2.8, Kala within 5.4, Drik within 7.3 virupas. Sthana (RMS 13, steps of Saptavargaja grades) and Cheshta (RMS 16; JHora uses its own mean-longitude tables) still differ | JHora's Sthana sub-components (Uchcha, Saptavargaja, Ojayugma, Kendra, Drekkana) for 1-2 charts |
| 15 | Shadbala: Sun/Moon Cheshta | Undoubled Ayana (Sun) and Paksha (Moon) bala | Phase 1, expert |

## Decided

| Decision | Choice |
| --- | --- |
| Product scope | Astrologer workbench first, all branches over R1-R3; consumer edition later on the same API |
| Calculation location | Deterministic Layer 0 outside the network |
| Zodiac frame | Lagna rotated to 0 deg for the model |
| Vargas encoded by the model | 13: D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D30, D60 |
| D2 method | Traditional Parashari hora (Leo/Cancer) as default; variants to be added as options |
| Golden reference | Jagannatha Hora exports in `tests/golden/jhora` (8 charts) |
| Ayanamsa, nodes, positions | Lahiri, mean nodes, true (geometric) positions: JHora match within 2.2" |
| Sunrise for special lagnas | Disc centre, no refraction (JHora) |
| Ashtakavarga | PVR variant; seven grahas occupy in Ekadhipatya; Virgo multiplier 5 (JHora: all pindas exact) |
| Vimshottari year | Solar year by the Sun's sidereal motion (JHora: 584/648 exact, rest within 1 day); fixed years optional |
| Pranapada formula | Sun-modality offset, one sign per 6 minutes (JHora match within 7.6', from a ~1 s sunrise difference) |
| Shadbala benefics | Moon benefic from Shukla to Krishna Ashtami (at least 90 deg from the Sun); Mercury malefic in a sign with a malefic Moon, Mars, Saturn, Rahu or Ketu (JHora component match) |
| Shadbala Abda/Masa | Kali ahargana + 1 day (JHora's year and month lords) |
| Moon's Cheshta | Distance from the Sun / 3 (JHora) |
| Test oracle | PyJHora in a separate environment (AGPL; never imported) |
