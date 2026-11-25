// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

// Saved charts and notes (M3.1). Charts live in a SQLite file next to the API on
// this computer; nothing is sent anywhere else.

import { FormEvent, useCallback, useEffect, useState } from "react";
import { Birth, library, LifeEvent, SavedChart } from "@/lib/api";
import { parseLocal, prettyLocal } from "@/lib/time";

type Props = {
  name: string;
  birth: Birth;
  events: LifeEvent[];
  savedId: number | null;
  onOpen: (c: SavedChart) => void;
  onSaved: (c: SavedChart) => void;
  onForget: () => void;
};

const sameBirth = (a: Birth, b: Birth) =>
  a.local_datetime === b.local_datetime && a.latitude === b.latitude &&
  a.longitude === b.longitude && a.utc_offset_hours === b.utc_offset_hours;

export function LibraryPanel({ name, birth, events, savedId, onOpen, onSaved, onForget }: Props) {
  const [charts, setCharts] = useState<SavedChart[] | null>(null);
  const [query, setQuery] = useState("");
  const [current, setCurrent] = useState<SavedChart | null>(null);
  const [draft, setDraft] = useState("");
  const [editing, setEditing] = useState<{ id: number; text: string } | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(() => {
    library.list(query).then((r) => setCharts(r.charts)).catch((e) => setError(String(e.message ?? e)));
  }, [query]);
  useEffect(() => { const t = setTimeout(refresh, 150); return () => clearTimeout(t); }, [refresh]);
  useEffect(() => {
    if (savedId === null) { setCurrent(null); return; }
    library.get(savedId).then(setCurrent).catch(() => setCurrent(null));
  }, [savedId]);

  const dirty = current !== null && (current.name !== name || !sameBirth(current.birth, birth));

  async function run(f: () => Promise<unknown>) {
    setError("");
    try { await f(); } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }

  const saveNew = () => run(async () => {
    const c = await library.create({ name, birth, events });
    setCurrent(c); onSaved(c); refresh();
  });
  const saveChanges = () => run(async () => {
    if (!current) return;
    const c = await library.update(current.id, { name, birth });
    setCurrent(c); onSaved(c); refresh();
  });
  const open = (id: number) => run(async () => {
    const c = await library.get(id);
    setCurrent(c); onOpen(c);
  });
  const remove = (c: SavedChart) => run(async () => {
    if (!window.confirm(`Delete the saved chart "${c.name}" and its notes?`)) return;
    await library.remove(c.id);
    if (current?.id === c.id) { setCurrent(null); onForget(); }
    refresh();
  });
  const addNote = (e: FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!current || !text) return;
    run(async () => {
      await library.addNote(current.id, text);
      setDraft("");
      setCurrent(await library.get(current.id)); refresh();
    });
  };
  const saveNote = () => run(async () => {
    if (!current || !editing || !editing.text.trim()) return;
    await library.updateNote(editing.id, editing.text.trim());
    setEditing(null);
    setCurrent(await library.get(current.id));
  });
  const removeNote = (id: number) => run(async () => {
    if (!current) return;
    await library.removeNote(id);
    setCurrent(await library.get(current.id)); refresh();
  });

  return (
    <details className="library">
      <summary>Saved charts and notes{current ? `: ${current.name}` : ""}</summary>
      <div className="library-head">
        <div className="library-actions">
          {current ? (
            <>
              <span className="muted">Saved as “{current.name}”{dirty ? " (changed)" : ""}</span>
              {dirty && <button type="button" className="primary" onClick={saveChanges}>Save changes</button>}
              <button type="button" className="quiet-button" onClick={saveNew}>Save as new</button>
            </>
          ) : (
            <button type="button" className="primary" onClick={saveNew}>Save this chart</button>
          )}
        </div>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}

      <div className="library-body">
        <div>
          <label className="field">
            Find a saved chart
            <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Name or place" />
          </label>
          {charts === null ? <p className="muted">Loading…</p> : charts.length === 0 ? (
            <p className="muted">{query ? "No saved chart matches." : "No saved charts yet."}</p>
          ) : (
            <ul className="library-list">
              {charts.map((c) => (
                <li key={c.id} aria-current={c.id === current?.id ? "true" : undefined}>
                  <button type="button" className="library-open" onClick={() => open(c.id)}>
                    <strong>{c.name}</strong>
                    <span className="muted">{prettyLocal(parseLocal(c.birth.local_datetime))}
                      {c.note_count ? ` · ${c.note_count} note${c.note_count > 1 ? "s" : ""}` : ""}</span>
                  </button>
                  <button type="button" className="link-button" aria-label={`Delete ${c.name}`} onClick={() => remove(c)}>
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="notes">
          <h3>Notes{current ? ` on ${current.name}` : ""}</h3>
          {!current ? <p className="muted">Save the chart to keep notes and life events with it.</p> : (
            <>
              <ul className="note-list">
                {(current.notes ?? []).map((n) => (
                  <li key={n.id}>
                    {editing?.id === n.id ? (
                      <>
                        <textarea aria-label="Edit note" value={editing.text}
                          onChange={(e) => setEditing({ id: n.id, text: e.target.value })} rows={3} />
                        <button type="button" className="link-button" onClick={saveNote}>Save</button>{" "}
                        <button type="button" className="link-button" onClick={() => setEditing(null)}>Cancel</button>
                      </>
                    ) : (
                      <>
                        <p>{n.text}</p>
                        <span className="muted note-meta">{n.updated.slice(0, 10)}</span>{" "}
                        <button type="button" className="link-button" onClick={() => setEditing({ id: n.id, text: n.text })}>Edit</button>{" "}
                        <button type="button" className="link-button" onClick={() => removeNote(n.id)}>Delete</button>
                      </>
                    )}
                  </li>
                ))}
              </ul>
              <form onSubmit={addNote} className="note-form">
                <textarea aria-label="New note" value={draft} onChange={(e) => setDraft(e.target.value)} rows={3}
                  placeholder="A note on this chart" />
                <button type="submit" className="primary" disabled={!draft.trim()}>Add note</button>
              </form>
            </>
          )}
        </div>
      </div>
    </details>
  );
}
