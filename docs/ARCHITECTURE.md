# Architecture summary

The full design document ("JyotishNet v2 — Revised Architecture") is maintained
separately; this is the short version for contributors.

## Product

A professional workbench for practising astrologers covering all major branches
of Jyotish (Parashari, Jaimini, KP, Tajika/Varshaphal, Prashna, Muhurta,
match-making, optional Nadi), released in stages R1-R3. A smaller consumer
edition uses the same API with a stricter output profile.

## Five layers

| Layer | Role | Status |
| --- | --- | --- |
| 0. Verified calculation core | Ephemeris, vargas, dashas, special lagnas, yogas (YAML rules), boundary map; deterministic and tested | **Largely built (this repo)**; see status below |
| 1. Uncertainty-aware input | Birth-time window, 16-chart ensemble, stability scores, reliability gates | Planned |
| 2. Encoders | Relational graph transformer over 37 nodes per chart (9 grahas, 4 Lagna-type, 12 bhavas, 12 rashis), 10 edge types incl. a free edge; shared encoder over 13 vargas; temporal encoder for dashas and transits | Planned |
| 3. De-confounding | Cohort adversary (gradient reversal), covariate baseline | Planned (research mode) |
| 4. Heads | Yoga, strength, timing (research mode), query head for the AI assistant, grounded reading generator with verifier and safety filter | Planned |

About 11.4M core parameters; exported as two ONNX graphs (natal encoder, cached;
temporal encoder and heads, re-run as time moves).

## Status (November 2026)

Built and tested in Layer 0:

- Positions, houses, all 16 vargas, nakshatras, dignities, aspects, special
  lagnas, boundary map.
- Dashas: Vimshottari, Ashtottari (with applicability), Yogini, Chara
  (K. N. Rao) on a Jaimini module (rasi drishti, stronger co-lord).
- Ashtakavarga and Shadbala, including Yuddha bala.
- Yoga engine: 56 YAML rules citing text and section, with evidence strings
  and cancellation; all marked `draft` until an expert reviews them.

Verification: 8 Jagannatha Hora exports are golden tests; PyJHora runs as an
external oracle for vargas, Ashtakavarga, Shadbala, yogas and dashas.
Remaining differences are documented in the README and in DECISIONS.md.

Workbench UI v0 (`web/`, built ahead of phase 4 so the engine can be used and
reviewed): charts, the rectification and transit time ribbon, positions,
running dashas.

Not yet: Narayana and other Jaimini dashas, Tajika, KP, Prashna, Muhurta,
match-making, Panchanga; strength conditions inside some yogas; Layers 1-4.

## Real-time slider and rectification

The slider currently calls the API: one D1 + varga request takes about 3 ms,
and the UI keeps at most one request in flight, so dragging stays smooth on a
local or nearby server. The planned next step is the calc engine in the
browser (WebAssembly build of Swiss Ephemeris in a Web Worker) for offline,
every-frame recalculation. The boundary map splits a birth window into
segments where nothing time-sensitive changes; the ribbon already marks the
Lagna changes, and the model will run once per segment. Rectification helpers
will score known life events against dasha and transit rules for each
candidate time; the UI already shows the periods running on an event date.

## Build phases

1. Calculation core + golden tests (largely done; workbench UI v0 started)
2. Synthetic data and pretraining
3. Uncertainty layer
4. Interpretation heads, reading generator, workbench
5. Research mode (optional, preregistered)

## Safety rules that apply everywhere

- Never predict the sex of a child or foetus (PCPNDT Act, India).
- AI drafts never state timing of death, serious illness, accidents or pregnancy
  outcomes; the workbench shows the technical factors to the astrologer only.
