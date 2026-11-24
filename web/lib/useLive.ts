// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Runs `run` whenever `key` changes, never more than one request at a time:
 * while one is in flight, further changes collapse into a single follow-up
 * with the latest inputs. Suits a slider that moves faster than the network.
 */
export function useLive<T>(key: string | null, run: () => Promise<T>, debounceMs = 0) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const latest = useRef(run);
  const busy = useRef(false);
  const dirty = useRef(false);
  latest.current = run;

  useEffect(() => {
    if (key === null) return;
    const kick = async () => {
      dirty.current = true;
      if (busy.current) return;
      busy.current = true;
      setLoading(true);
      while (dirty.current) {
        dirty.current = false;
        try {
          setData(await latest.current());
          setError(null);
        } catch (e) {
          setError(e instanceof Error ? e.message : String(e));
        }
      }
      busy.current = false;
      setLoading(false);
    };
    if (debounceMs > 0) {
      const t = setTimeout(kick, debounceMs);
      return () => clearTimeout(t);
    }
    void kick();
  }, [key, debounceMs]);

  return { data, error, loading };
}
