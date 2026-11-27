// SPDX-License-Identifier: AGPL-3.0-or-later
// Runs the browser engine under Node for web/e2e/engine_parity.py:
//   node web/lib/engine/cli.ts < cases.json > results.json
// Input: [{birth, vargas, at_jd?, bounds?: [window_min, step_s, vargas]}];
// output: [{chart, running?, changes?} | {error}].
import { readFileSync } from "node:fs";
import { buildChart } from "./chart.ts";
import { boundaryMap } from "./boundaries.ts";
import { runningVimshottari } from "./dasha.ts";
import { Swe } from "./swe.ts";

const wasm = readFileSync(new URL("../../public/engine/swe.wasm", import.meta.url));
const swe = await Swe.load(wasm);
const cases = JSON.parse(readFileSync(0, "utf8"));
type Case = { birth: never; vargas: number[]; at_jd?: number; bounds?: [number, number, number[]] };
const out = cases.map((c: Case) => {
  try {
    return {
      chart: buildChart(swe, c.birth, c.vargas),
      ...(c.at_jd !== undefined ? { running: runningVimshottari(swe, c.birth, c.at_jd) } : {}),
      ...(c.bounds ? { changes: boundaryMap(swe, c.birth, ...c.bounds) } : {}),
    };
  } catch (e) {
    return { error: String(e) };
  }
});
process.stdout.write(JSON.stringify(out));
