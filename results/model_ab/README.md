# Opus 5.5 vs Sonnet 5.5, one battle each (2026-10-17)

A light check the user asked for: how much does the model matter when Claude plays a battle itself?
Three random-map problems, one battle per model, both players fresh (a workflow subagent each) and
given the same briefing, [context.md](context.md), and nothing else from past battles (cards,
journals, rows and PROCEDURES.md were off limits). Played through RimMolt with `tools/hands.py`
and `tools/run_human.py`, one at a time, alternating which model went first.

The problems were picked so that Claude's earlier play suggested about two wins and a loss, or three
wins with one costly: rand_130 (Claude won twice, badness 35.4 and 21.8), rand_058 (won, badness 47.3,
two lost) and rand_227 (five tries, two wins, badness 19.4 to 112.4). Those earlier plays were in one
long session with the case library and older helpers, so they only gauge the difficulty.

## Rows ([play.jsonl](play.jsonl))

| Problem | Opus 5.5 (`opus55_ab`) | Sonnet 5.5 (`sonnet55_ab`) |
|---|---|---|
| rand_130 | repelled, lost 0, downed 0, **badness 7.1**, 6,453 ticks | repelled, lost 0, downed 2, badness 17.6, 7,550 ticks |
| rand_058 | repelled, lost 1, downed 2, badness 34.3, 9,593 ticks | repelled, lost 0, downed 0, **badness 14.9**, 6,637 ticks |
| rand_227 | repelled, lost 1, downed 0, **badness 21.7**, 8,810 ticks | repelled, lost 0, downed 1 (7 permanent injuries), badness 26.7, 5,336 ticks |
| Total | 3 wins, lost 2, downed 2, badness 63.1 | 3 wins, lost 0, downed 3, badness 59.2 |

Order of play: a1 (130, Opus), b1 (130, Sonnet), b2 (058, Sonnet), a2 (058, Opus), a3 (227, Opus),
b3 (227, Sonnet). Each run's plan, notes and scratch scripts are in `runs/<run>/`, the traces in
`traces/`.

## What the players did (from their reports)

- **rand_130:** both swapped Rae's knife for Lady's revolver and held a line in the open, grenadiers
  first. Opus kept fighting at 18-25 cells and switched fire off the flak-armoured raider; Sonnet
  advanced the line to 10-17 cells after the grenadiers fell, lost two pawns to downed there, then
  threw the dead grenadiers' frag and molotov.
- **rand_058:** Opus walked the squad ~67 cells to a pocket by a rock outcrop for a corner ambush;
  a raider leaning out from a one-cell rock spur covered the pocket, and one pawn was killed while
  falling back. Sonnet held the start position and walked its three grenadiers up to throw at
  raiders who had stopped 15-24 cells out.
- **rand_227:** both gave the autopistols to the best shooters and moved to the same rock tip so the
  raid's bolt-action rifles (range 36.9) could not use their range. Opus lost one pawn to a raider
  leaning out from the granite tip; Sonnet had one pawn downed with an arm destroyed (7 permanent
  injuries, 14 of its 26.7).

Tool trouble both reported: "Tend (without medicine)" orders that ran for hundreds of ticks with no
visible effect; pawns showing "moving" without moving for 50-100 ticks under fire or with very short
waits; a fire order cancelling a move; Keeper state lost between short python processes.

## Cost and time

Harness wall time: Opus 64 min, Sonnet 59 min for the three battles. API-price estimate from the
subagent transcripts (input, cache reads and writes, output at list prices; output may be
under-counted in the transcripts): Opus about $18 (368 model calls, 71 M cache-read tokens), Sonnet
about $14 (310 calls, 60 M). Cache reads, which cost $0.20 per million tokens on both models,
dominate this kind of long tool loop, so Sonnet's half price per token saved about a quarter here.

One battle per problem: the spread between tries of the same problem (rand_227: 19 to 112) is much
larger than the difference between the two models here.

## Mixed hands on rand_227 (run c3, same day)

After rimcockpit 0.2.0 (time and observation; orders still only through RimMolt), a fresh Opus 5.5
played rand_227 once more with [tools/hands_rc.py](../../tools/hands_rc.py): `tools/hands.py` with
game time moved to rimcockpit's `advance` (wait at the normal pace, skip at batch, and through them
guard and wait_safe) and `st()`/`wait_safe()` reading its snapshot, while orders and the grenade
reflex's reads stayed on RimMolt. The briefing was [context_rc.md](context_rc.md): context.md with
only the helpers swapped. A smoke test before it (scratch results, no row) checked exact advances of
1, 120 and 180 ticks, 600 at batch in 0.9 s, snapshot ids equal to RimMolt's, and a RimMolt order
between advances.

| Run | Helpers | Result |
|---|---|---|
| a3 (Opus 5.5) | hands.py, RimMolt only | repelled, lost 1, downed 0, badness 21.7, 8,810 ticks |
| b3 (Sonnet 5.5) | hands.py, RimMolt only | repelled, lost 0, downed 1, badness 26.7, 5,336 ticks |
| c3 (Opus 5.5) | hands_rc.py, mixed | **decisive**, lost 0, downed 0, **badness 10.4**, 6,640 ticks |

c3 took the same rock as a3 and b3, stood the squad where the rifles had to come round the tip, and
fought the melee rush inside the group with the knife pawns. rimcockpit's advance never reported a
short or inexact step. The player's remarks on the helpers: no line-of-sight read on either side (it
probed `order_pawn` menus per pair, and its own grid check disagreed at rock corners); the snapshot
has no stagger or stance field, so pawns slowed by hits looked stalled; and hands_rc's st() printed
the raw game tick while hands.st() and the harness count from 383 (st() now prints both). One battle
again: the helpers are not shown to be the cause of the better result.
