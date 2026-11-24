# Workbench front end (next step)

Planned: Next.js + React + TypeScript.

First milestones:

1. Chart components: North Indian (diamond), South Indian (grid) and later East
   Indian, rendered as SVG from the `/v1/chart` response.
2. Analysis canvas: several vargas side by side with linked highlighting.
3. Real-time slider: Swiss Ephemeris compiled to WebAssembly in a Web Worker,
   transit mode and birth-time mode with the boundary map and BTR helpers.
4. Client management and notes.

A TypeScript client will be generated from the API's OpenAPI spec.
