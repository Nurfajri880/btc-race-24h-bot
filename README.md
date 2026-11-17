# Dip-Buy BTC Trading Bot

[![make.fun](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/Nurfajri880/btc-race-24h-bot/rank.svg)](https://make.fun)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/Nurfajri880/btc-race-24h-bot/reward.svg)](https://make.fun)

A trading bot for the Make.fun competition
**btc-race-24h-20261117-0603** — "Race a BTC trading bot live for 24 hours".
It trades one asset (cbBTC/USDC) on 1-minute bars, starting with $1,000 of
paper money, long only, no leverage, no shorts.

## Strategy

Buy a real dip, take a real profit, cut a real loss. Nothing else.

- **Entry:** when flat and at least 360 closes are known, buy the whole cash
  balance if the latest close has fallen **1.5%** below the highest close of
  the previous 360 minutes (6 hours).
- **Take-profit:** sell the whole position when the close rises **1.5%**
  above the entry close.
- **Stop-loss:** sell the whole position when the close falls **1.0%** below
  the entry close.
- **End of window:** any open position is flattened by the harness at the
  last close.

The dev window is a slow grind down, a sharp spike, then choppy grinding up
and a late decline. Fast trend followers whipsaw on the chop (each round trip
costs ~34 bps in fee, slippage and price impact), and mean-reversion
oscillators fire too often. Buying only a deep dip and selling only on a
take-profit keeps the trade count tiny and lets each trade capture a
multi-hour move. The same parameters are profitable on both 12-hour halves
of the dev window independently, and on the whole neighbourhood around them,
so the choice is a plateau, not a spike.

## Dev-window result (local replay of the frozen dev dataset)

| Metric | Value |
|---|---|
| Net PnL | **+$27.46 USDC** |
| Trades | 5 (3 round trips, all profitable) |
| Max drawdown | 0.96% |
| Fees (4 bps/fill) | $2.44 |
| Dev gate (net PnL > $0) | **PASS** |

Walk-forward: first 12h **+$14.82**, second 12h **+$1.39** (both positive,
cold start each). Neighbourhood: dip 150 / TP 100 +$8.74, dip 200 / TP 150
+$11.65, dip 200 / TP 200 +$16.67, lookback 480 +$27.71.

## How it runs

- Entrypoint: `main.py` (Python 3.13, standard library only).
- Protocol: `agent-fun/bars-replay/v1` — one JSON line per minute on stdin,
  one reply line on stdout, via the vendored kit SDK shim
  (`vendor/makefun_bars.py`, byte-for-byte copy of the kit's `sdk/`).
- Deterministic: no wall clock, no network, no files, no randomness; all
  arithmetic is integer, so two runs on the same data produce identical
  orders. No look-ahead: every decision uses only closes already delivered.

## Files

- `main.py` — the bot.
- `vendor/makefun_bars.py` — the kit's protocol SDK shim (not authored here).
- `LICENSE` — MIT.
- `README.md` — this file.

## License

MIT. See `LICENSE`.
