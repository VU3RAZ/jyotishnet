# Decisions

## Open

| # | Decision | Current default in code | Needed by |
| --- | --- | --- | --- |
| 1 | House system for the model's frame | Whole-sign; others selectable | Phase 1, week 1 |
| 2 | Sunrise definition for special lagnas | Disc centre, no refraction | Phase 1, week 1 |
| 3 | Narayana and Chara dashas as model token streams | Not yet implemented | Before phase 2 |
| 4 | Gender-dependent rules | Not yet implemented (rules engine pending) | Before phase 4 |
| 5 | Apparent vs true planet positions | Apparent (`true_positions=False`); PyJHora uses true | Phase 1, week 1: match the JHora golden set |
| 6 | Pranapada formula convention | Sun-modality offset, 1 sign per 6 minutes; needs expert sign-off | Phase 1 |
| 7 | Mean vs true nodes default | Mean (PyJHora defaults to true) | Phase 1 |
| 8 | Ashtakavarga BAV variant | `bphs` (Raman's reading); `pvr` (PVR Narasimha Rao, PyJHora default) differs for Moon and Venus | Phase 1, with the expert reviewer |
| 9 | Ekadhipatya "occupied" signs | Seven grahas; options add Rahu/Ketu, or Rahu/Ketu and Lagna (PyJHora) | Phase 1, with the expert reviewer |
| 10 | Shodhya pinda Virgo multiplier | 5 (common references); 6 in PVR's book | Phase 1 |
| 11 | Shadbala: Mercury benefic or malefic | Malefic when sharing a sign with Mars, Saturn, Rahu or Ketu | Phase 1, expert |
| 12 | Shadbala: Kendra bala houses | Whole-sign houses (option: Sripati bhava) | Phase 1, expert |
| 13 | Shadbala: Ayana bala | Ephemeris declination (BPHS uses kranti tables) | Phase 1, golden set |
| 14 | Shadbala: Abda/Masa epoch | Kali Yuga epoch, 360-day years and 30-day months | Phase 1, golden set |
| 15 | Shadbala: Sun/Moon Cheshta | Undoubled Ayana (Sun) and Paksha (Moon) bala | Phase 1, expert |

## Decided

| Decision | Choice |
| --- | --- |
| Product scope | Astrologer workbench first, all branches over R1-R3; consumer edition later on the same API |
| Calculation location | Deterministic Layer 0 outside the network |
| Zodiac frame | Lagna rotated to 0 deg for the model |
| Vargas encoded by the model | 13: D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D30, D60 |
| D2 method | Traditional Parashari hora (Leo/Cancer) as default; variants to be added as options |
| Test oracle | PyJHora in a separate environment (AGPL; never imported) |
