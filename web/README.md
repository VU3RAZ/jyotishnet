# JyotishNet workbench (web)

Next.js + React + TypeScript front end for the JyotishNet API.

## What it does

- North and South Indian charts (SVG) for the Rasi and any divisional chart.
- **Rectify birth time**: a time ribbon moves the birth time within ±30 minutes by default (±20 minutes
  or ±2 hours on request).
  Charts, positions and dashas recompute as you drag (about 3 ms per API call),
  and marks on the ribbon show where the Lagna and the chosen varga's Lagna
  change sign (from `/v1/boundaries`). Planets or Lagnas that change sign
  flash briefly. The dasha panel shows the Vimshottari periods running on an
  event date you enter.
- **Transits**: the birth chart stays fixed; the ribbon moves the sky (±3 days,
  ±1 year, ±12 years) and shows today's planets in the birth houses, with the
  periods running on that date.
- The eight Jagannatha Hora reference charts are available as presets.

## Run it

```bash
# 1. API (from the repository root)
pip install -e .
uvicorn jyotishnet_api.main:app --port 8000

# 2. Web app (in web/)
npm ci
npm run dev        # http://localhost:3000
```

The app calls `/api/*`, which Next forwards to `JYOTISHNET_API_URL`
(default `http://127.0.0.1:8000`). For a separate deployment, the API also
accepts browser calls from the origins in `JYOTISHNET_CORS`.

## Next steps

1. Analysis canvas: several vargas side by side with linked highlighting.
2. Swiss Ephemeris compiled to WebAssembly in a Web Worker for offline,
   sub-millisecond scrubbing; BTR event helpers on the ribbon.
3. Client management and notes.
4. A TypeScript client generated from the API's OpenAPI spec.
