// SPDX-License-Identifier: AGPL-3.0-or-later
"use client";

import { Yoga, YogaOptions } from "@/lib/api";
import { t } from "@/lib/i18n";
import { term, yogaName } from "@/lib/vocab";

export function YogaView({ yogas, options, onOptions }: {
  yogas: Yoga[]; options: YogaOptions; onOptions: (o: YogaOptions) => void;
}) {
  const active = yogas.filter((y) => y.present && !y.cancelled);
  const cancelled = yogas.filter((y) => y.present && y.cancelled);
  const groups = Array.from(new Set(active.map((y) => y.group)));
  return (
    <div className="yoga-view">
      <p className="view-lead">
        {t("{a} of {b} yogas form in this chart", { a: active.length, b: yogas.length })}
        {cancelled.length === 1 ? t("; 1 more forms but is cancelled") : cancelled.length ? t("; {n} more form but are cancelled", { n: cancelled.length }) : ""}.
        {" "}{t("Each shows why it fired and where the rule comes from. All rules are drafts awaiting expert review.")}
      </p>
      <div className="yoga-options">
        <label className="field inline">
          <span>{t("Strong Lagna lord (Lakshmi, Kahala)")}</span>
          <select value={options.strong_lord}
            onChange={(e) => onOptions({ ...options, strong_lord: e.target.value as YogaOptions["strong_lord"] })}>
            <option value="dignity">{t("By dignity and placement")}</option>
            <option value="shadbala">{t("By Shadbala (meets required rupas)")}</option>
          </select>
        </label>
        <label className="field inline">
          <span>{yogaName("gajakesari", "Gajakesari")}</span>
          <select value={options.gajakesari}
            onChange={(e) => onOptions({ ...options, gajakesari: e.target.value as YogaOptions["gajakesari"] })}>
            <option value="bphs">{t("BPHS (Jupiter in a kendra from the Moon)")}</option>
            <option value="phaladeepika">{t("Phaladeepika (also benefic aspect; not debilitated, combust or in an enemy sign)")}</option>
          </select>
        </label>
      </div>
      <div className="yoga-groups">
        {groups.map((g) => (
          <section key={g} className="yoga-group">
            <h3>{term(g)} <span className="count">{active.filter((y) => y.group === g).length}</span></h3>
            <ul>
              {active.filter((y) => y.group === g).map((y) => <YogaItem key={y.id} y={y} />)}
            </ul>
          </section>
        ))}
      </div>
      {cancelled.length > 0 && (
        <section className="yoga-group cancelled">
          <h3>{t("Formed but cancelled")} <span className="count">{cancelled.length}</span></h3>
          <ul>{cancelled.map((y) => <YogaItem key={y.id} y={y} />)}</ul>
        </section>
      )}
    </div>
  );
}

function YogaItem({ y }: { y: Yoga }) {
  return (
    <li className="yoga">
      <strong className="yoga-name">{yogaName(y.id, y.name)}</strong>
      <p>{y.summary}</p>
      <ul className="evidence">
        {y.evidence.map((e, i) => <li key={i}>{e}</li>)}
      </ul>
      <cite>{y.source.text}, {y.source.section}</cite>
    </li>
  );
}
