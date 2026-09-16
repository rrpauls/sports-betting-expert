# Sources and methods

## Source selection and freshness

Use official event pages and competition, club, team or player channels for schedules, confirmed lineups, injuries and results. Use a reputable score provider as a cross-check, preserving its timestamp and provisional status. Prefer a full source page over a search snippet for decisive claims.

For offered prices, prioritize the user's named bookmaker or exchange. An odds aggregator may help compare history, but it does not prove that the user can obtain a price. Record operator, jurisdiction/version when relevant, market, line and observation time. Do not infer line movement from different bookmakers or different lines.

Provider access changes. Treat provider names as starting points rather than promises of free access. If a source is unavailable, change sources or disclose the gap; never reconstruct missing current statistics from memory.

## Sport-specific evidence

| Sport | Decision-relevant checks | Useful starting points beyond official news |
|---|---|---|
| Football | Opponent-adjusted xG/xGA; home/away; lineups; rest; tactics; set pieces; match format | FBref, Understat, WhoScored; Transfermarkt as roster context with confirmation elsewhere |
| Basketball | Pace; possession-adjusted offense/defense; availability; minutes/usage; rest/travel; rotation | Official league stats, Basketball-Reference, SofaScore |
| Tennis | Surface and level; hold/break performance; fitness; workload; match format; serve/return matchup | ATP, WTA, ITF, official tournament data, TennisExplorer |
| Ice hockey | Confirmed goalie; shot quality; even-strength play; special teams; rest; regulation vs overtime | Official league stats, EliteProspects for roster context |
| Baseball | Confirmed starter/lineup; workload; bullpen availability; platoon splits; park/weather; F5 vs full game | MLB, Baseball Savant, FanGraphs, Baseball-Reference |
| Cricket | Format; squad; venue/pitch; toss/innings; weather/dew; wickets/run rates; DLS conditions | ICC, boards and tournament scorecards, ESPNcricinfo, Cricbuzz |

For player props, establish role, expected opportunities and participation rules before using a historical hit rate. A short-run hit rate is not a forecast probability. Identify any model's source, sample window and assumptions; never claim to have run a model that was not run.

## Probability and value

Use decimal odds `d > 1`. Convert American odds `A` with `d = 1 + A/100` for positive `A`, and `d = 1 + 100/abs(A)` for negative `A`. Fractional `a/b` becomes `d = 1 + a/b`.

For a complete, mutually exclusive and exhaustive market from one operator and one snapshot:

- raw implied probability: `q_i = 1/d_i`
- overround: `sum(q_i) - 1`
- proportional normalized benchmark: `q_i / sum(q_j)`

Normalization is an approximate margin-removal method, not true probability. Do not normalize overlapping double-chance selections, incomplete outcome sets, alternative totals together or prices from different books. Push markets need a separate push estimate; quarter lines need full settlement scenarios.

For full win/loss with independent probability estimate `p`:

- break-even probability: `1/d`
- expected net return per unit: `p*d - 1`
- fair odds: `1/p`

For probabilities `p_w + p_v + p_l = 1` covering win, void/push and loss:

- `EV = p_w*(d-1) - p_l`
- `fair_price = (1-p_v)/p_w` when `p_w > 0`

For partial settlements, enumerate mutually exclusive outcomes. Net returns per unit are `d-1` for full win, `(d-1)/2` for half win, `0` for push, `-0.5` for half loss and `-1` for full loss. Calculate `EV = sum(probability * net_return)`.

For an exchange back bet with commission `c` on winnings, isolated effective odds are `1 + (d-1)*(1-c)`. A portfolio settled on net market winnings needs market-level calculation.

## Accumulators

For an ordinary unboosted binary ticket, indicative combined odds are `D = product(d_i)`. Full-win gross return for stake `s` is `s*D`; net profit is `s*(D-1)`. Break-even joint probability is `1/D` and `EV = P_joint*D - 1`. Only under an explicit independence assumption may `P_joint = product(p_i)`. Correlation, pushes, partial outcomes, boosts and builders require their actual joint prices and payouts.

## Calculator usage

`scripts/bet_math.py` performs arithmetic on supplied assumptions. It does not retrieve prices or predict outcomes.

```bash
python3 scripts/bet_math.py market --odds 1.91 1.91
python3 scripts/bet_math.py single --odds 1.90 --win 0.45 --push 0.25 --stake 10
python3 scripts/bet_math.py parlay --odds 1.80 2.00 1.75 --probabilities 0.60 0.55 0.60 --assume-independent
python3 scripts/bet_math.py settlement --odds 1.90 --probabilities 0.40 0.20 0 0.10 0.30
```

## Staking and performance

For win/loss with credible `p`, full Kelly is `(p*d-1)/(d-1)`, floored at zero when shorting is unavailable. With pushes, divide EV by `(d-1)*(p_w+p_l)`. Fractional Kelly scales the model result but does not remove estimation risk. Prefer agreed flat stakes or conservative fractional sizing with exposure caps; avoid recovery systems.

Track date/time, event, exact market/line, operator, taken odds, stake, pre-bet estimate/method, result, net profit and a comparable closing line. Realized ROI is total net profit divided by total staked. Closing-line movement is a process diagnostic, not proof of profit; assess calibration and sample uncertainty too.
