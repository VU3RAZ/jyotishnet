# JyotishNet: notes for Claude Code

Start here:

- Handover (status, remaining work M1-M8, build order, lessons learned):
  https://claude.ai/artifact/LrioA6TqNfmGM4zra7zpa7
- Master design (the spec; propose changes as suggestions, not direct edits):
  https://claude.ai/artifact/1Co7313q1J8qVqvBkh91Yd
- In the repo: README.md, docs/DECISIONS.md (open and decided conventions),
  tests/golden/README.md (golden charts and JHora notes), web/README.md.

Every change:

1. `git pull`; small commits to `main`.
2. `pytest -q`. For web changes also, in `web/`: `npx tsc --noEmit`, `npx next build`,
   and `python e2e/smoke.py` against a running app (`scripts/start.sh`).
3. Engine changes to a verified quantity: run the matching `tools/crosscheck_*.py`
   in the separate PyJHora environment (PyJHora is AGPL; never import it).
4. Check CI after pushing.

Rules:

- School choices are settings (SchoolConfig / ShadbalaOptions) with the JHora
  convention as default where the golden set shows it; record each in DECISIONS.md.
  Open decisions belong to the user.
- Failing golden charts go to tests/golden/pending/ with a note; never loosen a
  tolerance to pass.
- Yoga and event rules cite their source and stay `status: draft` until the user's
  Jyotish reviewer signs them off.
- Never predict a child's sex; never state timing of death, serious illness or
  accidents as a prediction (death and illness events are check-only).
