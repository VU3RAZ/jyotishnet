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
| 0. Verified calculation core | Ephemeris, vargas, dashas, special lagnas, yogas (YAML rules), boundary map; deterministic and tested | **In progress (this repo)** |
| 1. Uncertainty-aware input | Birth-time window, 16-chart ensemble, stability scores, reliability gates | Planned |
| 2. Encoders | Relational graph transformer over 37 nodes per chart (9 grahas, 4 Lagna-type, 12 bhavas, 12 rashis), 10 edge types incl. a free edge; shared encoder over 13 vargas; temporal encoder for dashas and transits | Planned |
| 3. De-confounding | Cohort adversary (gradient reversal), covariate baseline | Planned (research mode) |
| 4. Heads | Yoga, strength, timing (research mode), query head for the AI assistant, grounded reading generator with verifier and safety filter | Planned |

About 11.4M core parameters; exported as two ONNX graphs (natal encoder, cached;
temporal encoder and heads, re-run as time moves).

## Real-time slider and rectification

The calc engine also runs in the browser (WebAssembly build of Swiss Ephemeris)
so the time slider recalculates every frame. The boundary map splits a birth
window into segments where nothing time-sensitive changes; the model runs once
per segment. Rectification helpers score known life events against dasha and
transit rules for each candidate time.

## Build phases

1. Calculation core + golden tests (now)
2. Synthetic data and pretraining
3. Uncertainty layer
4. Interpretation heads, reading generator, workbench
5. Research mode (optional, preregistered)

## Safety rules that apply everywhere

- Never predict the sex of a child or foetus (PCPNDT Act, India).
- AI drafts never state timing of death, serious illness, accidents or pregnancy
  outcomes; the workbench shows the technical factors to the astrologer only.
