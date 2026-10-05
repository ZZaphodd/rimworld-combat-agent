# Case library: battles to look back on while playing

Claude plays battles directly — strategic, tactical and micro, through `tools/hands.py`. The
Python agents stay as they are; they are the baseline (`results/night/router.jsonl`).

The library keeps **what happened, not rules**. The user's reading (2026-10-05): the choice in
a battle moves around in something like 20–30 dimensions as the situation changes, too many to
write down as rules, but Claude's own records, read again, carry it well. So each battle is
kept as a card and a journal, and the closest ones are fetched for the next battle. Lessons are
not written from single battles. The user decides what generalizes.

The procedure is PROCEDURES §16. Start there after a context compaction.

## Files

| file | what |
|---|---|
| `cards/<id>.md` | one card per problem: situation tags, sides, every play of it (agent, human, Claude) with results, **scenes** (moment → tags → what was done → what followed), what the play stood on |
| `journals/<id>_claude_<date>.md` | Claude's own battles: plan, then each decision as seen at the time (format below) |
| `sheets/<id>_<moment>.md` | what retrieval returned for a battle (start, or a turning point) |
| `sites.md` | sites on the shared night map with coordinates; a site from one problem is a candidate in all |
| `tags.md` | the tag vocabulary (situation, moment, play); it grows from play |
| `img/` | the site map and journal frames |

## Cards

| card | arena | ours vs raid | situation | best play so far | badness: agent / human / Claude |
|---|---|---|---|---|---|
| [rand_107](cards/rand_107.md) | open | low-skill gunners vs 3 grenadiers | `raid-throwers` `us-low-skill` | forest-edge hold (lost 4) | 142.2 / 96.4 / – |
| [rand_067](cards/rand_067.md) | forest | tribal bows vs clubs + boar | `raid-melee` `us-bows` | kite, fight on arrival (lost 1) | 130.5 / 58.7 / – |
| [rand_030](cards/rand_030.md) | forest | short guns + throwables vs mixed, outranged | `raid-outranges` `us-short` `top-threat` | loadout + rock-hill corner ambush | 128.0 / 21.1 / 38.8 |
| [rand_084](cards/rand_084.md) | open | low-skill gunners + 2 brawlers vs sniper + 2 grenadiers | `raid-sniper` `raid-throwers` | loadout + west notch + gap slip | 124.9 / 1.8 / 20.5 |
| [rand_127](cards/rand_127.md) | forest | savage bows + ikwas vs Neanderthal melee | `raid-melee` `raid-strong-1v1` | loadout + breach + nook mouth + rotation | 116.9 / 26.0 / 10.8 |
| [rand_065](cards/rand_065.md) | open | civil outlanders vs Empire troopers | `raid-armoured` `raid-outranges` | walled room (squad down, ≈ draw) | 114.3 / 64.4 / – |
| [rand_029](cards/rand_029.md) | open | tribal bows vs 4 throwers | `raid-throwers` `us-bows` | loadout + spaced line + chase the carriers | 110.0 / 55.6 / – |
| [rand_039](cards/rand_039.md) | forest | low-skill gunners vs civil mixed with throwers | `raid-throwers` `top-threat` | loadout + small ruin + stepped withdrawal | 108.0 / 8.0 / 48.4 |

Comparing rows: the worst-list agent rows stopped at squad down (old rule); rows since
2026-10-05 run until the raid is gone (`end_rule: raid_gone`), so a battle where the whole
squad went down compares by `squad_down.missing` (EVAL_SPEC §3).

## Retrieval (a subagent, so the main context stays small)

**At the start**, after the battle card is written (PROCEDURES §16 step 3), launch a
general-purpose subagent with:

> You find past battles that resemble a new one, for a RimWorld combat study. Read
> `results/cases/README.md`, `tags.md`, `sites.md`, every card in `results/cases/cards/` and
> every journal in `results/cases/journals/`. The new battle: <the battle card: arena, the raid's
> edge and distance, both sides with shooting/melee, weapons, armour, traits; situation tags>.
> Pick the **3** past battles closest to it in situation (matchup, sites reachable before
> contact, where the raid will walk), not in outcome. For each: why it is close (tags and
> numbers in common); what differs and whether that difference matters; what could be borrowed
> (loadout, a site from sites.md with its distance from our start and from the raid's likely
> path, the play, timings); what went wrong there. Also list any site in sites.md that suits
> this battle even if its card is not in the three. Do not write general rules. Write the
> result to `results/cases/sheets/<id>_start.md` (at most 70 lines) and reply with the three
> card ids and one line each.

**At a turning point** (a moment the start sheet did not cover: first contact, first of ours
down, a kidnapping, a thrower close, the raid splitting or flanking, a stalemate), the game is
paused between decisions, so a lookup costs no game time:

> Read the Scenes sections of every card in `results/cases/cards/` and every journal in
> `results/cases/journals/`. Current moment of <id> at t<tick>: <what is where, health, who
> holds what, the raid's state; tags>. Find the **3** scenes most like it. For each: the scene
> (card, tick), what was done, what followed, and what differs from now. No general rules.
> Write to `results/cases/sheets/<id>_t<tick>.md` (at most 40 lines) and reply in 3 lines.

The sheet is advice, not orders: the journal says which parts were used and how they went.

## Journal format (`journals/<id>_claude_<date>.md`)

Written after the battle, while it is still in context (a battle interrupted by a context
compaction is discarded and replayed, not resumed).

```
# <id> — Claude, <date>
Trace … · row … · result: <grade>, lost …, downed …, permanent …, badness … (agent …)
Sheets: sheets/<id>_start.md (cards A, B, C: what was used) · sheets/<id>_t….md

## Card at the start
<sides, raid edge, situation tags, the plan and why>

## Scenes
### t<tick> `<situation tags>` → `<play tags>`
saw: <positions, health, what the raid was doing>
options: <what I weighed>
chose: <orders> because <reason>
followed: <what happened by the next decision>
![](../img/<id>_t<tick>.jpg)      (key moments only: hands.shot(..., keep="<id>_t<tick>.jpg"))

## What the play stood on (observed)
## New tags / sites (for the user to look at)
```

Then the card for the problem gets the Claude row and its scenes (shorter), and new sites go
into `sites.md`.
