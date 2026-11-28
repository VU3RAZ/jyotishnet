# What BPHS and Phaladeepika say about timing events with dashas

Research note, 27 November 2026, for the Jyotish reviewer (decision #20).
Question: is the rectification and indicative-period logic in
`src/jyotishnet_engine/rules/btr_events.yaml` classical, and if not, what does
Brihat Parashara Hora Shastra actually give?

**Source.** The Sanskrit text with an English translation at
<https://enjoylearningsanskrit.com/scriptures/parashara/>, chapters 47, 48 and 52–60
in that site's numbering. Verse pages are at `.../chapter-N/verse-M/`. The points
below are paraphrased, not quoted. Caveats:

- This is one online translation. In places the site's English disagrees with the
  Sanskrit; for example, ch. 52 v. 13 translates *dāyeśa* (the dasha lord) as
  "6th lord".
- The fetches of chapters 52–60 were cut off after about verse 50, so later
  verses were read only in summary. Below they are marked *(unverified)*.
- Chapter numbers differ between editions. Santhanam's translation, for one,
  numbers them differently.
- Everything here needs checking against a printed edition before a rule is
  signed off.

## 1. Our current rule is not in BPHS

Our rule says a dasha lord is "linked" to an event if, in D1 or the event's
varga, it lords or occupies the event house or is the karaka. An event then
counts as indicated when both the mahadasha lord and the antardasha lord are
linked. I found no verse that states this.

- **No house-based marriage rule.** No verse says marriage comes in the dasha or
  antardasha of the 7th lord. On the 7th lord's dasha, ch. 48 v. 5 says the
  opposite: suffering to the spouse, and fear of death, because the 7th lord is
  a maraka.
- **No varga-based timing rule.** No verse says a lord linked to a house in
  D7, D9 or D10 gives that house's results in its dasha. The vargas enter the
  antardasha chapters only as a strength test: own, exalted or friendly navamsa.
- **No double transit.** The Jupiter–Saturn double transit we score is not in
  these chapters. It comes from modern teaching.

The citations in `btr_events.yaml`, such as "Effects of the 7th house;
Navamsa", name the topic but no verse. They read as if BPHS supports the rule,
and it does not.

## 2. What BPHS gives instead

### a. The dasha of a house lord gives that house's results (ch. 48 vv. 2–7)

| Lord whose dasha runs | Result given (paraphrase) | Verse |
| --- | --- | --- |
| 1st | reputation, bodily comfort | 48.2 |
| 4th | home and land | 48.3 |
| 5th | learning, happiness from children | 48.4 |
| 7th | distress to the spouse; maraka | 48.5 |
| 8th | fear of death, loss | 48.5 |
| 9th | gain, fame | 48.6 |
| 10th | honour from rulers | 48.6 |
| 11th, 12th | obstacles, illness | 48.7 |

Other verses in ch. 48 add to this:

- **Lords combining.**
  - 48.9–11: the 10th lord with the 5th lord is good; with the 9th lord it is very good.
  - 48.17–18: when the 10th lord is in the Lagna and the Lagna lord in the 10th, their dashas bring a rise to power.
- **Kendra and trikona lords.** 48.12–14: a trikona lord in a kendra, or a kendra lord in a trikona, gives a good dasha.
- **Maraka houses.** 48.19–20: even a benefic gives bad results in a maraka house, with a maraka lord, or in the 8th.

### b. A dasha planet joined with a house lord gives that house's results (ch. 47)

- **47.9:** joined with the 5th lord, it gives a son.
- **47.10:** with the lord of wealth it gives wealth; with the lord of vehicles, vehicles.
- **47.6–7:** results are good when the planet is in a kendra, a trikona or the 11th, in its own, exalted or mooltrikona sign, or joined with the 9th or 10th lord. They are bad when it is in the 6th, 8th or 12th, debilitated, combust or in an enemy sign.
- **47.3–4: timing within a dasha.** The planet's drekkana decides when in the dasha its results come:
  - first drekkana: the beginning;
  - second: the middle;
  - third: the end;
  - reversed when the planet is retrograde.

### c. Antardasha results (ch. 52–60)

Each chapter takes one mahadasha and goes through its nine antardashas. The
pattern is the same throughout:

- **Good antardasha.** The antardasha lord is:
  - in a kendra, a trikona or the 11th from the Lagna (sometimes the 3rd or 2nd);
  - or in a kendra, trikona, 3rd or 11th from the mahadasha lord;
  - or exalted, in its own or mooltrikona sign, or in its own or exalted navamsa;
  - or joined or aspected by benefics, the Lagna lord, the 9th and 10th lords, or a yogakaraka.
- **Bad antardasha.** The antardasha lord is:
  - in the 6th, 8th or 12th from the Lagna or from the mahadasha lord;
  - or debilitated, combust or in an enemy sign;
  - or joined with malefics.

  As the 2nd or 7th lord it is a maraka; for us that is check-only.

- **What a good antardasha promises.** One bundle of good things: marriage, a son,
  royal favour or position, house, land, vehicles. Which items appear depends
  mostly on the two planets, not on the houses they rule. Verses that name
  marriage in a good antardasha:

  | Mahadasha | Antardasha | Verses |
  | --- | --- | --- |
  | Sun | Moon | 52.4 |
  | Sun | Jupiter | 52.32 |
  | Sun | Saturn | 52.41–42 |
  | Rahu | Saturn | 55.21–22 |
  | Jupiter | Saturn | 56.8 (a wife) |
  | Saturn | Venus | 57.23 |
  | Mercury | Moon | 58.26 |
  | Mars | Moon | 54.72 *(unverified)* |
  | Jupiter | Mars | 56.65 *(unverified)* |

  Children appear in the same verses or the next. Examples: Sun–Jupiter 52.33,
  Mars–Mars 54.3, Mercury–Mars 58.38, Ketu–Sun 59.21. Position and career appear
  wherever the 9th and 10th lords are involved, for example 52.34, 54.17 and
  59.51–52.

- **Specific house lords as conditions.** A few verses do name one:
  - the 9th and 10th lords, for position;
  - the lord of vehicles, for vehicles (54.17, 59.1);
  - the Lagna lord (54.2, 58.36).

## 3. What this means for JyotishNet

1. **BPHS's model is good and bad periods, not event matching.** It judges an
   antardasha by where its lord stands and how dignified it is, and a good one
   brings several good things at once. Only for the 4th, 5th, 9th and 10th, and
   for the house lords a dasha planet is joined with, does it tie a house to a
   period's results.
2. **Marriage gets no house-based rule in BPHS.** The 7th lord's dasha is a
   warning for the spouse. A classical marriage indicator would come from the
   antardasha verses (good placement or dignity, with Venus and the Moon often
   involved). Another text could also supply one: Phaladeepika, Jataka
   Parijata, or later works such as Uttara Kalamrita. Those are not read here.
3. **The vargas count for dignity, not for linking a planet to an event.** Our
   D7, D9 and D10 house links are a modern addition. They are also the part
   that changes every few minutes and adds chance matches.
4. **A rule set closer to BPHS** would score an antardasha on two classical
   axes:
   - **quality:** the antardasha lord's place from the Lagna and from the
     mahadasha lord, its dignity, and its associations;
   - **house:** 48.2–7 and 47.9–10, that is, the lord of 4, 5, 9 or 10 running,
     or a dasha lord joined with that lord.

   Each rule would carry its verse. Which of these to adopt, and how to treat
   marriage, is the reviewer's decision.
5. **Until then,** the current rules stay as drafts and the release documents
   should not call them classical.

## 4. Phaladeepika (the marriage rule BPHS lacks)

Source: Mantreswara's Phaladeepika in V. Subrahmanya Sastri's translation (2nd
edition, 1950), read on wisdomlib
(<https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation>;
chapter 10 is `d/doc1621582.html`, 12 `doc1621584.html`, 19 `doc1621591.html`,
20 `doc1621592.html`, 21 `doc1621593.html` and 26 `doc1621598.html`). The pages
are unproofread OCR; ch. 21 after about verse 64 and ch. 26 after about verse 43
were only read in summary.

| Event | Rule (paraphrase) | Verse |
| --- | --- | --- |
| Marriage | in the dasha of a planet in the 7th, aspecting the 7th, or owning the 7th | 10.13 |
| Marriage | also when the Lagna lord in transit reaches the 7th sign | 10.13 |
| Marriage | when Venus or the 7th lord transits a trine to the sign or navamsa of the Lagna lord | 10.12 |
| Marriage | in the dasha of the strongest of Venus, the Moon and the lords of the 7th lord's sign and navamsa, when Jupiter transits a trine to the 7th lord's sign or navamsa | 10.14 |
| Marriage | the 7th lord's dasha brings marriages in the family | 20.8 |
| Marriage | Venus's dasha: acquisition of a wife | 19.26 |
| Children | in the dasha or bhukti of the Lagna lord, 7th lord, 5th lord, Jupiter, a planet in the 5th or a planet aspecting the 5th | 12.25 |
| Children | in the dasha of the stronger of the 5th lord and Jupiter, or of their sign or navamsa lords | 12.28 |
| Children | Jupiter transiting the 5th or 11th from the Moon | 26.19-20 |
| Children | the 5th lord's dasha: birth of a son | 20.6 |
| Career | the 10th lord's dasha: success, renown, a lasting position | 20.11 |
| Property | the 4th lord's dasha: vehicles, land, house, promotion | 20.5 |
| General | strong lords (own, exalted, friendly sign, not in 6, 8, 12) give their houses' results; weak ones the reverse | 20.14-20 |
| General | the bhukti lord in the 6th, 8th or 12th from the dasha lord gives unhappy results | 20.29 |
| General | strength by dignity: exalted full, moolatrikona 3/4, own 1/2, friend 1/4, enemy or debilitated nil | 20.30 |

So for marriage the texts differ: BPHS 48.5 makes the 7th lord's dasha a maraka
for the spouse, while Phaladeepika 10.13 and 20.8 give it marriage. Phaladeepika is
the later and more specific text on timing.

Uttara Kalamrita and Jataka Parijata were not found in a free online
translation; they are not used.

## 5. What JyotishNet does now

The rectification helpers have two rule sets, chosen in the Life events panel and
by `rule_set` in the API. **classical** is the default
(`src/jyotishnet_engine/rules/btr_classical.yaml`, every condition citing its verse);
**modern** keeps the R1 rules.

Classical scoring, per event:

- **The period's lords** (+1 antardasha lord, +0.5 mahadasha lord). A lord counts
  if it gives the event by the cited conditions:
  - marriage: 7th lord, in the 7th, aspects the 7th, Venus (PD 10.13, 19.26, 20.8);
  - children: lords of 1, 5, 7, in or aspecting the 5th, Jupiter, joined with the 5th lord (PD 12.25; BPHS 47.9, 48.4);
  - career: the 10th lord, joined with the 9th or 10th lord (BPHS 48.6, 48.9-11, 52.34; PD 20.11);
  - relocation and vehicles: the 4th lord, joined with the 4th lord (BPHS 47.10, 48.3; PD 20.5);
  - finance: the 9th lord, joined with the 2nd lord (BPHS 47.10, 48.6);
  - education: the 5th lord (BPHS 48.4).
- **The antardasha's quality** (+0.5 good, +0.25 mixed). Good means the antardasha lord is:
  - in a kendra, trikona or the 11th;
  - or exalted, moolatrikona or in its own sign;
  - or in a kendra, trikona, 3rd or 11th from the mahadasha lord.

  Bad means it is in the 6th, 8th or 12th from the Lagna or from the mahadasha
  lord, debilitated, in an enemy sign, or combust (BPHS 47.6-7, ch. 52-60;
  PD 20.14, 20.29). Check-only events (death, illness) score the reverse, on
  quality alone; no death-timing rule is used.
- **Jupiter's transit** (+0.5), where a text gives one:
  - marriage: a trine to the 7th lord's sign or navamsa (PD 10.14);
  - children: the 5th or 11th from the Moon (PD 26.19-20).
- **Events without a classical rule.** Sibling and spiritual events have no timing
  rule in the chapters read, so they are scored on quality alone.

Indicative periods (classical): antardashas whose lord gives the matter and whose
quality is good.

Measured on random charts (27 Nov 2026):

| | classical | modern |
| --- | --- | --- |
| Share of the 9 grahas that give a marriage | 38% | 40% |
| Share of the 9 grahas that give a child | 58% | 40% |
| Share of the 9 grahas that give a career event | 30% | 40% |
| How much the fit curve moves on random events across ±30 min (mean of max - min) | 0.9 | 2.7 |
| Random-event charts flagged "unlikely by chance" (p ≤ 0.05) | 2.5% | 3.3% |
| Indicative periods, share of ages 18-60, marriage / child / career / relocation | 18 / 21 / 10 / 7% | 20 / 19 / 20 / 16% |

The classical rules use only D1 and the navamsa sign of the 7th lord, which change
far more slowly than D7, D10 or D24. So the curve has fewer chance peaks. It is also
flatter: within ±30 minutes it often moves only with the dasha dates.

Not yet used, and open for the reviewer:

- PD 10.14's choice of the strongest of four planets;
- PD 12.28 (the stronger of the 5th lord and Jupiter);
- PD 10.12 and 10.13's transit rules for the Lagna lord and Venus;
- the drekkana timing within a dasha (BPHS 47.3-4);
- BPHS 48.5 against PD 20.8 on the 7th lord;
- the strength fractions of PD 20.30;
- an age window for indicative periods: decided by the user on 28 Nov 2026, the lists start at age 16
  (`min_age_years`; the texts give no age limit).
