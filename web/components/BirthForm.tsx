// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, Birth } from "@/lib/api";
import { PRESETS } from "@/lib/presets";
import { getLang, t } from "@/lib/i18n";

/** `preset`: true when a preset was picked (another person), false for an edit of this one. */
type Props = { name: string; birth: Birth; onSubmit: (name: string, b: Birth, preset: boolean) => void };

export function BirthForm({ name, birth, onSubmit }: Props) {
  const [draftName, setDraftName] = useState(name);
  const [date, setDate] = useState(birth.local_datetime.slice(0, 10));
  const [time, setTime] = useState(birth.local_datetime.slice(11, 19));
  const [lat, setLat] = useState(String(birth.latitude));
  const [lon, setLon] = useState(String(birth.longitude));
  const [tz, setTz] = useState(String(birth.utc_offset_hours));
  const [error, setError] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const lang = getLang();            // warnings come back in the interface language

  // Check the time zone as the user types (historical Indian zones, decision
  // "Historical Indian zones"): a warning only, the chart is never changed.
  useEffect(() => {
    const la = Number(lat), lo = Number(lon), off = Number(tz);
    const hms = time.length === 5 ? `${time}:00` : time;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !/^\d{2}:\d{2}:\d{2}$/.test(hms) ||
        !(la >= -66 && la <= 66) || !(lo >= -180 && lo <= 180) || !(off >= -14 && off <= 14)) {
      setWarnings([]);
      return;
    }
    const ctl = new AbortController();
    const timer = setTimeout(() => {
      api.birthWarnings({ local_datetime: `${date}T${hms}`, latitude: la, longitude: lo, utc_offset_hours: off },
        ctl.signal).then((r) => setWarnings(r.warnings)).catch(() => {});
    }, 300);
    return () => { clearTimeout(timer); ctl.abort(); };
  }, [date, time, lat, lon, tz, lang]);

  function load(i: number) {
    const p = PRESETS[i];
    setDraftName(p.name);
    setDate(p.birth.local_datetime.slice(0, 10));
    setTime(p.birth.local_datetime.slice(11, 19));
    setLat(String(p.birth.latitude));
    setLon(String(p.birth.longitude));
    setTz(String(p.birth.utc_offset_hours));
    setError("");
    onSubmit(p.name, p.birth, true);
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    const la = Number(lat), lo = Number(lon), off = Number(tz);
    const hms = time.length === 5 ? `${time}:00` : time;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !/^\d{2}:\d{2}:\d{2}$/.test(hms)) {
      setError(t("Enter the date as YYYY-MM-DD and the time as HH:MM or HH:MM:SS."));
      return;
    }
    if (!(la >= -66 && la <= 66)) { setError(t("Latitude must be between −66 and 66 (north positive).")); return; }
    if (!(lo >= -180 && lo <= 180)) { setError(t("Longitude must be between −180 and 180 (east positive).")); return; }
    if (!(off >= -14 && off <= 14)) { setError(t("The UTC offset must be between −14 and +14 hours.")); return; }
    setError("");
    onSubmit(draftName || t("Untitled chart"), {
      local_datetime: `${date}T${hms}`, latitude: la, longitude: lo, utc_offset_hours: off,
    }, false);
  }

  return (
    <form className="birth-form" onSubmit={submit}>
      <label className="field preset">
        <span>{t("Reference chart")}</span>
        <select defaultValue="" onChange={(e) => e.target.value !== "" && load(Number(e.target.value))}>
          <option value="" disabled>{t("Choose…")}</option>
          {PRESETS.map((p, i) => <option key={p.name} value={i}>{p.name}</option>)}
        </select>
      </label>
      <label className="field wide"><span>{t("Name")}</span>
        <input value={draftName} onChange={(e) => setDraftName(e.target.value)} /></label>
      <label className="field"><span>{t("Date")}</span>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required /></label>
      <label className="field"><span>{t("Local time")}</span>
        <input type="time" step={1} value={time} onChange={(e) => setTime(e.target.value)} required /></label>
      <label className="field narrow"><span>{t("Latitude")}</span>
        <input inputMode="decimal" value={lat} onChange={(e) => setLat(e.target.value)} /></label>
      <label className="field narrow"><span>{t("Longitude")}</span>
        <input inputMode="decimal" value={lon} onChange={(e) => setLon(e.target.value)} /></label>
      <label className="field narrow"><span>{t("UTC offset (h)")}</span>
        <input inputMode="decimal" value={tz} onChange={(e) => setTz(e.target.value)} /></label>
      <button type="submit" className="primary">{t("Cast chart")}</button>
      {error && <p className="form-error" role="alert">{error}</p>}
      {warnings.length > 0 && (
        <ul className="form-warning" role="status" aria-label={t("Time zone check")}>
          {warnings.map((w) => <li key={w}>{w}</li>)}
        </ul>
      )}
    </form>
  );
}
