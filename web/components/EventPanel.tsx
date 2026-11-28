// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { FormEvent, useState } from "react";
import { EventCheck, EventRule, LifeEvent, RuleSet } from "@/lib/api";
import { N, t } from "@/lib/i18n";
import { eventName, grahaName } from "@/lib/vocab";
import { prettyDate } from "@/lib/time";

type Props = {
  rules: EventRule[];
  events: LifeEvent[];
  checks: EventCheck[] | null;
  helps: boolean[] | null;
  loading: boolean;
  ruleSet: RuleSet;
  onRuleSet: (r: RuleSet) => void;
  onAdd: (e: LifeEvent) => void;
  onRemove: (i: number) => void;
  /** The saved chart the events are kept with; null: kept in this browser only. */
  storedWith: string | null;
  saveError: string;
};

function linkText(links: string[], ruleSet: RuleSet): string {
  return links.length ? links.join(", ") : ruleSet === "classical" ? t("does not give it") : t("not linked");
}

const RULE_SET_LABEL: Record<RuleSet, string> = {
  classical: N("Classical (BPHS, Phaladeepika)"),
  modern: N("Modern (R1 links)"),
};

function qualityText(c: EventCheck): string {
  if (!c.quality) return "–";
  return t({ good: N("good antardasha"), mixed: N("mixed antardasha"), bad: N("bad antardasha") }[c.quality]);
}

export function EventPanel({ rules, events, checks, helps, loading, ruleSet, onRuleSet, onAdd, onRemove,
  storedWith, saveError }: Props) {
  const [type, setType] = useState("marriage");
  const [date, setDate] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    if (!date) return;
    onAdd({ type, date });
    setDate("");
  }

  return (
    <section className="events" aria-busy={loading}>
      <div className="events-head">
        <h2>{t("Life events")}</h2>
        <p className="muted">
          {t("Enter dated events the person is sure of. Each is checked against the dasha and transits for the birth time on the ribbon; the curve on the ribbon adds them up.")}
        </p>
        <p className="muted events-stored">
          {storedWith !== null
            ? t("Kept with the saved chart “{name}”.", { name: storedWith })
            : t("Kept in this browser only. Save the chart (Saved charts and notes) to keep them with it.")}
        </p>
        {saveError && <p className="form-error" role="alert">{saveError}</p>}
        <div role="group" aria-label={t("Rectification rules")} className="segmented quiet">
          {(Object.keys(RULE_SET_LABEL) as RuleSet[]).map((r) => (
            <button key={r} type="button" aria-pressed={ruleSet === r} onClick={() => onRuleSet(r)}>
              {t(RULE_SET_LABEL[r])}
            </button>
          ))}
        </div>
      </div>

      <form className="event-form" onSubmit={submit}>
        <label className="field"><span>{t("Event")}</span>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {rules.map((r) => (
              <option key={r.id} value={r.id}>{eventName(r.id, r.name)}{r.check_only ? ` (${t("check only")})` : ""}</option>
            ))}
          </select>
        </label>
        <label className="field"><span>{t("Date")}</span>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </label>
        <button type="submit" className="primary">{t("Add event")}</button>
      </form>

      {events.length === 0 ? (
        <p className="muted">{t("No events yet. Add well-dated events (marriage, first child, first job); the more there are, the better. The ribbon says whether together they point to a birth time or could fit as well by chance.")}</p>
      ) : (
        <div className="table-wrap">
          <table className="event-table">
            <thead>
              <tr>
                <th scope="col">{t("Event")}</th>
                <th scope="col">{t("Dasha then")}</th>
                <th scope="col">{ruleSet === "classical" ? t("Gives the event") : t("Links")}</th>
                <th scope="col">{ruleSet === "classical" ? t("Period and transit") : t("Jupiter and Saturn")}</th>
                <th scope="col">{t("Fit")}</th>
                <th scope="col"><span className="visually-hidden">{t("Remove")}</span></th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev, i) => {
                const c = checks?.[i];
                const rule = rules.find((r) => r.id === ev.type);
                return (
                  <tr key={`${ev.type}-${ev.date}-${i}`}>
                    <th scope="row">
                      {rule ? eventName(rule.id, rule.name) : ev.type}
                      <span className="event-date">{prettyDate(`${ev.date}T00:00:00Z`)}</span>
                    </th>
                    <td>{c ? `${c.mahadasha ? grahaName(c.mahadasha) : "–"} / ${c.antardasha ? grahaName(c.antardasha) : "–"}` : "…"}</td>
                    <td className="links">
                      {c && <>
                        <span><b>{grahaName(c.antardasha ?? "")}</b>: {linkText(c.antar_links, c.rule_set)}</span>
                        <span><b>{grahaName(c.mahadasha ?? "")}</b>: {linkText(c.maha_links, c.rule_set)}</span>
                      </>}
                    </td>
                    {c?.rule_set === "classical" ? (
                      <td className="links">
                        <span title={c.quality_reasons.join("\n")}>
                          <span className={`tag quality-${c.quality ?? "none"}`}>{qualityText(c)}</span>
                          {c.quality_reasons.length > 0 && <small> {c.quality_reasons.join("; ")}</small>}
                        </span>
                        {c.transit.length > 0 && <span>{c.transit.join(", ")}</span>}
                      </td>
                    ) : (
                      <td>{c ? (c.double_transit_houses.length
                        ? t("Both on house {h}", { h: c.double_transit_houses.join(", ") }) : t("No double transit")) : ""}</td>
                    )}
                    <td>
                      {c && <span className={`verdict ${c.verdict}`}>{t({ strong: N("strong"), partial: N("partial"), weak: N("weak") }[c.verdict])} ({t("{a} of {b}", { a: c.score, b: c.max_score })})</span>}
                      {helps?.[i] && <span className="helps" title={t("The verdict changes within the window, so this event helps choose a time")}> {t("helps decide")}</span>}
                    </td>
                    <td>
                      <button type="button" className="link-button" onClick={() => onRemove(i)}
                        aria-label={t("Remove {what}", { what: rule ? eventName(rule.id, rule.name) : ev.type })}>{t("Remove")}</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {ruleSet === "classical" ? (
        <p className="rules-note">{t("Scoring: antardasha lord gives the event +1, mahadasha lord +0.5 (by the cited rules, e.g. Phaladeepika 10.13 for marriage, 12.25 for children, BPHS 48 for house lords); antardasha good +0.5, mixed +0.25 (or bad, for check-only events); Jupiter's transit +0.5 where a text gives one. Strong from 75% of the event's maximum, partial from 37.5%. Events with no classical timing rule are scored on the period alone. Every rule cites its verse; all are drafts awaiting expert review.")}</p>
      ) : (
        <p className="rules-note">{t("Scoring: antardasha lord linked +1, mahadasha lord +0.5, double transit +0.5; strong from 1.5, partial from 0.75. Links count lordship, occupancy or natural karaka in D1 and the event's varga. These are modern rules, not stated in BPHS; drafts awaiting expert review.")}</p>
      )}
    </section>
  );
}
