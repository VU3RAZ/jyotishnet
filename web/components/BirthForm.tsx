// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { FormEvent, useState } from "react";
import { Birth } from "@/lib/api";
import { PRESETS } from "@/lib/presets";

type Props = { name: string; birth: Birth; onSubmit: (name: string, b: Birth) => void };

export function BirthForm({ name, birth, onSubmit }: Props) {
  const [draftName, setDraftName] = useState(name);
  const [date, setDate] = useState(birth.local_datetime.slice(0, 10));
  const [time, setTime] = useState(birth.local_datetime.slice(11, 19));
  const [lat, setLat] = useState(String(birth.latitude));
  const [lon, setLon] = useState(String(birth.longitude));
  const [tz, setTz] = useState(String(birth.utc_offset_hours));
  const [error, setError] = useState("");

  function load(i: number) {
    const p = PRESETS[i];
    setDraftName(p.name);
    setDate(p.birth.local_datetime.slice(0, 10));
    setTime(p.birth.local_datetime.slice(11, 19));
    setLat(String(p.birth.latitude));
    setLon(String(p.birth.longitude));
    setTz(String(p.birth.utc_offset_hours));
    setError("");
    onSubmit(p.name, p.birth);
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    const la = Number(lat), lo = Number(lon), off = Number(tz);
    const t = time.length === 5 ? `${time}:00` : time;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !/^\d{2}:\d{2}:\d{2}$/.test(t)) {
      setError("Enter the date as YYYY-MM-DD and the time as HH:MM or HH:MM:SS.");
      return;
    }
    if (!(la >= -66 && la <= 66)) { setError("Latitude must be between −66 and 66 (north positive)."); return; }
    if (!(lo >= -180 && lo <= 180)) { setError("Longitude must be between −180 and 180 (east positive)."); return; }
    if (!(off >= -14 && off <= 14)) { setError("The UTC offset must be between −14 and +14 hours."); return; }
    setError("");
    onSubmit(draftName || "Untitled chart", {
      local_datetime: `${date}T${t}`, latitude: la, longitude: lo, utc_offset_hours: off,
    });
  }

  return (
    <form className="birth-form" onSubmit={submit}>
      <label className="field preset">
        <span>Reference chart</span>
        <select defaultValue="" onChange={(e) => e.target.value !== "" && load(Number(e.target.value))}>
          <option value="" disabled>Choose…</option>
          {PRESETS.map((p, i) => <option key={p.name} value={i}>{p.name}</option>)}
        </select>
      </label>
      <label className="field wide"><span>Name</span>
        <input value={draftName} onChange={(e) => setDraftName(e.target.value)} /></label>
      <label className="field"><span>Date</span>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required /></label>
      <label className="field"><span>Local time</span>
        <input type="time" step={1} value={time} onChange={(e) => setTime(e.target.value)} required /></label>
      <label className="field narrow"><span>Latitude</span>
        <input inputMode="decimal" value={lat} onChange={(e) => setLat(e.target.value)} /></label>
      <label className="field narrow"><span>Longitude</span>
        <input inputMode="decimal" value={lon} onChange={(e) => setLon(e.target.value)} /></label>
      <label className="field narrow"><span>UTC offset (h)</span>
        <input inputMode="decimal" value={tz} onChange={(e) => setTz(e.target.value)} /></label>
      <button type="submit" className="primary">Cast chart</button>
      {error && <p className="form-error" role="alert">{error}</p>}
    </form>
  );
}
