// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Yoga } from "@/lib/api";

export function YogaView({ yogas }: { yogas: Yoga[] }) {
  const active = yogas.filter((y) => y.present && !y.cancelled);
  const cancelled = yogas.filter((y) => y.present && y.cancelled);
  const groups = Array.from(new Set(active.map((y) => y.group)));
  return (
    <div className="yoga-view">
      <p className="view-lead">
        {active.length} of {yogas.length} yogas form in this chart
        {cancelled.length === 1 ? "; 1 more forms but is cancelled" : cancelled.length ? `; ${cancelled.length} more form but are cancelled` : ""}.
        Each shows why it fired and where the rule comes from. All rules are drafts awaiting expert review.
      </p>
      {groups.map((g) => (
        <section key={g} className="yoga-group">
          <h3>{g}</h3>
          <ul>
            {active.filter((y) => y.group === g).map((y) => <YogaItem key={y.id} y={y} />)}
          </ul>
        </section>
      ))}
      {cancelled.length > 0 && (
        <section className="yoga-group cancelled">
          <h3>Formed but cancelled</h3>
          <ul>{cancelled.map((y) => <YogaItem key={y.id} y={y} />)}</ul>
        </section>
      )}
    </div>
  );
}

function YogaItem({ y }: { y: Yoga }) {
  return (
    <li className="yoga">
      <div className="yoga-title">
        <strong>{y.name}</strong>
        <cite>{y.source.text}, {y.source.section}</cite>
      </div>
      <p>{y.summary}</p>
      <ul className="evidence">
        {y.evidence.map((e, i) => <li key={i}>{e}</li>)}
      </ul>
    </li>
  );
}
