// SPDX-License-Identifier: AGPL-3.0-or-later
// Web Worker hosting the browser engine (M3.5): charts, running Vimshottari periods
// and the ribbon's boundary scan, computed locally so the slider needs no API.
import { buildChart, jdUt } from "./chart.ts";
import { boundaryMap } from "./boundaries.ts";
import { runningVimshottari } from "./dasha.ts";
import { Swe } from "./swe.ts";
import type { EngineRequest } from "./client.ts";

const swe = Swe.load(fetch("/engine/swe.wasm"));

self.onmessage = async (e: MessageEvent<EngineRequest>) => {
  const { id, op } = e.data;
  let s: Swe;
  try {
    s = await swe;
  } catch (err) {
    // The WebAssembly could not load: tell the page to use the API from now on.
    self.postMessage({ id, ok: false, fatal: true, error: String(err) });
    return;
  }
  try {
    let value: unknown;
    if (op === "chart") {
      value = buildChart(s, e.data.birth, e.data.vargas);
    } else if (op === "running") {
      const at = jdUt(s, { local_datetime: e.data.atUtc, latitude: 0, longitude: 0, utc_offset_hours: 0 });
      value = { running: runningVimshottari(s, e.data.birth, at) };
    } else {
      value = { changes: boundaryMap(s, e.data.birth, e.data.windowMin, 10, e.data.vargas) };
    }
    self.postMessage({ id, ok: true, value });
  } catch (err) {
    self.postMessage({ id, ok: false, error: err instanceof Error ? err.message : String(err) });
  }
};
