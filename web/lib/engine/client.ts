// SPDX-License-Identifier: AGPL-3.0-or-later
// Main-thread side of the browser engine. Each call goes to the worker; if the worker
// or its WebAssembly cannot start (old browser, blocked file), `ok` turns false and
// callers fall back to the API.
import type { EngineBirth } from "./chart.ts";

export type EngineRequest = { id: number } & (
  | { op: "chart"; birth: EngineBirth; vargas: number[] }
  | { op: "running"; birth: EngineBirth; atUtc: string }
  | { op: "boundaries"; birth: EngineBirth; windowMin: number; vargas: number[] });
type Pending = { resolve: (v: unknown) => void; reject: (e: Error) => void };
type Op = EngineRequest extends infer R ? R extends { id: number } ? Omit<R, "id"> : never : never;

let worker: Worker | null = null;
let broken = false;
let nextId = 1;
const pending = new Map<number, Pending>();

function start(): Worker | null {
  if (broken || typeof Worker === "undefined") return null;
  if (worker) return worker;
  try {
    worker = new Worker(new URL("./worker.ts", import.meta.url), { type: "module" });
  } catch {
    broken = true;
    return null;
  }
  worker.onmessage = (e: MessageEvent<{ id: number; ok: boolean; value?: unknown; error?: string; fatal?: boolean }>) => {
    if (e.data.fatal) broken = true;
    const p = pending.get(e.data.id);
    if (!p) return;
    pending.delete(e.data.id);
    if (e.data.ok) p.resolve(e.data.value);
    else p.reject(new Error(e.data.error));
  };
  worker.onerror = () => {
    broken = true;
    for (const p of pending.values()) p.reject(new Error("browser engine failed to start"));
    pending.clear();
    worker?.terminate();
    worker = null;
  };
  return worker;
}

export function engineCall<T>(req: Op): Promise<T> {
  const w = start();
  if (!w) return Promise.reject(new Error("browser engine unavailable"));
  const id = nextId++;
  return new Promise<T>((resolve, reject) => {
    pending.set(id, { resolve: resolve as (v: unknown) => void, reject });
    w.postMessage({ ...req, id });
  });
}

/** Whether the browser engine is usable (true until it fails to start). */
export const engineOk = () => !broken;
