# What BPHS says about timing events with Vimshottari dashas

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
