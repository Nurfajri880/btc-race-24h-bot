"""Dip-buy trading bot for the Make.fun competition btc-race-24h-20261117-0603.

Strategy (one asset, cbBTC/USDC, 1-minute bars, $1,000 paper money, long only):
  Buy a real dip, take a real profit, cut a real loss. Nothing else.

  * Entry -- when flat and at least LOOKBACK closes are known, buy the whole
    cash balance if the latest close has fallen DIP_BPS below the highest
    close of the previous LOOKBACK minutes. A dip that deep only happens
    after a genuine pullback, not on one-minute noise (per-minute noise is
    ~6 bps; a 150 bps dip is a ~2.5-sigma move over an hour).
  * Exit (take-profit) -- sell the whole position when the close rises
    TAKE_PROFIT_BPS above the entry close. Bank the move; do not ride it
    back down.
  * Exit (stop-loss) -- sell the whole position when the close falls
    STOP_LOSS_BPS below the entry close. A dip that keeps falling is a
    downtrend, not a bargain; the stop caps the loss on any one trade at
    about 1% of equity and keeps maximum drawdown far below the 25% guardrail.
  * End of window -- any position still open is flattened by the harness at
    the last close.

Why this shape: on the frozen dev window the price path is a slow grind down
to a trough, a sharp spike, then a choppy grind up and a late decline. Fast
trend followers whipsaw on the chop (every round trip costs ~34 bps in fee,
slippage and price impact, so frequent trading loses), and mean-reversion
oscillators fire too often. Buying only a deep dip and selling only on a
take-profit keeps the trade count tiny (3 buys on the dev window) and lets
each trade capture a multi-hour move. The same parameters are profitable on
both 12-hour halves of the dev window independently, and on the whole
neighbourhood around them, so the choice is a plateau, not a spike.

No look-ahead: every decision uses only closes already delivered in a batch
(the current bar's close and earlier ones). The reference high excludes the
current bar. No wall clock, no network, no files, no randomness -- all
arithmetic is integer (raw price units), so two runs on the same data produce
identical orders. Standard library only, via the vendored kit SDK shim.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"

# Minutes of history the reference high is taken over.
LOOKBACK = 360
# Buy when the close is this far (basis points) below the LOOKBACK-minute high.
DIP_BPS = 150
# Sell when the close is this far above the entry close.
TAKE_PROFIT_BPS = 150
# Sell when the close is this far below the entry close.
STOP_LOSS_BPS = 100
# Slippage guard on every order (basis points vs the latest close).
MAX_SLIPPAGE_BPS = 100

_BPS = 10_000


class DipBuyer:
    """Keeps the close history and the entry price of the open position."""

    def __init__(self):
        self.closes = []
        self.entry_close = None

    def on_batch(self, state, batch):
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        holding = state.positions.get(SYMBOL)
        if holding is not None:
            return self._maybe_exit(state, close, holding)
        return self._maybe_enter(state, close)

    def _maybe_exit(self, state, close, holding):
        # Defensive: a held position with no recorded entry (cannot happen in
        # a single uninterrupted run, but never crash the bot on it). Treat
        # the current close as the entry so the stops are measured from here.
        if self.entry_close is None:
            self.entry_close = close
            return []
        # Stop-loss first: protect the downside before checking profit.
        if close * _BPS <= self.entry_close * (_BPS - STOP_LOSS_BPS):
            return self._sell_all(state, holding)
        if close * _BPS >= self.entry_close * (_BPS + TAKE_PROFIT_BPS):
            return self._sell_all(state, holding)
        return []

    def _sell_all(self, state, holding):
        self.entry_close = None
        return state.to_orders([{
            "side": "sell",
            "symbol": SYMBOL,
            "qty": holding.qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }])

    def _maybe_enter(self, state, close):
        # Need a full LOOKBACK of earlier closes before the first trade.
        if len(self.closes) <= LOOKBACK:
            return []
        # Highest close of the LOOKBACK minutes before this bar (not this bar).
        reference_high = max(self.closes[-LOOKBACK - 1:-1])
        if close * _BPS < reference_high * (_BPS - DIP_BPS):
            self.entry_close = close
            return state.to_orders([{
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": state.cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }])
        return []


_BOT = DipBuyer()


def on_batch(state, batch):
    return _BOT.on_batch(state, batch)


makefun_bars.run(on_batch)
