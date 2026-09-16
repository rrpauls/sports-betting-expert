# Markets, coupons and live positions

## Read the actual ticket

Capture the sport, competition, participants, date/time and timezone if shown, chosen side, exact market, handicap or total, covered period, odds, stake, payout and placement status. The selected side may differ from the first-listed team. An old score beside a market may be the placement score or handicap reference rather than the current score.

Quote ambiguous labels and identify the missing distinction. Continue with readable legs instead of silently substituting a familiar event, team, line or price. Avoid repeating ticket IDs or account details unless they are necessary.

## Settlement distinctions

The actual operator rules control settlement. Verify them when an exception affects the decision.

| Market | Key distinction |
|---|---|
| Football 1X2 | Usually 90 minutes plus stoppage time; qualification, extra time and penalties are separate markets. |
| 1X / X2 / 12 | Overlapping double-chance selections; not a mutually exclusive three-way set for normalization. |
| DNB / Asian handicap 0 | Win pays, draw refunds, loss loses for the stated period. |
| Asian whole/half line | Whole lines can push; half lines cannot tie with integer scoring. |
| Asian quarter line | Split stake over adjacent whole and half lines; enumerate half-win and half-loss outcomes. |
| European handicap | The post-handicap draw is a separate outcome; do not use Asian refund rules. |
| Hockey/basketball winner | Confirm whether overtime or shootouts count. |
| Player props | Verify participation, minimum action and void conditions. |
| Early payout | Operator promotion with its own trigger and exclusions, not a forecast or cash-out. |
| Cash-out | A changing offer to settle some or all exposure, not a guaranteed amount. |

In an ordinary accumulator, a fully void leg commonly becomes a `1.00` multiplier. A quarter-line half win has multiplier `(d+1)/2`; a half loss has multiplier `0.5`, assuming standard split-stake settlement. Verify promotions, builders and operator exceptions.

For live handicaps and totals, establish whether the line includes the current score, covers only remaining play or applies to a named period. A printed score does not resolve that question by itself.

## Correlation and construction

Check whether legs share a match, team, player, competition path, weather condition or tactical event. Team win and team total, or player scoring and team total, are generally dependent. Use the actual builder quote and a defensible joint model, reduce overlap, or state that combined value is unknown. Never report a product of marginal probabilities as a measured joint success rate without justifying independence.

## Already placed and live

Confirm whether the user wants commentary, reassessment, a new selection or a cash-out/hedge comparison. Preserve accepted prices as historical facts. Do not treat a past stake as a reason to add another bet.

For a live snapshot, record source and observation time, score, elapsed state and sport-specific context: innings/wickets/overs/target for cricket; set/game/server for tennis; inning/outs/bases/pitchers for baseball; period, power play and goalie state for hockey.

Update probabilities conditional on verified current state. If a feed is delayed or conflicting, provide scenarios and mark them conditional. For a simple all-or-nothing remaining ticket, gross expected future payout is `P_joint_remaining * gross_full_win_payout`; compare that with a cash-out offer alongside uncertainty and the user's desire to reduce exposure. Treat the original stake as sunk for hold-versus-cash-out while reporting total profit/loss separately.

For a requested hedge, show the new stake, available odds, fees and net total profit or loss in every mutually exclusive outcome before using the word “locked.” Settlement mismatch can leave residual risk.

