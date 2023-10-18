# pylint: disable = line-too-long

# LP Profit/loss = Rebalancing Profit/loss - LVR + Trading fee income

# The metric is c`alculated from a benchmark portfolio that matches the LP’s asset composition
# but is being traded on a CEX.
# The idea is that whenever the price changes, the CEX portfolio sells one of the assets
# and buys the other in order to remain in sync
# with the composition of the LP assets and mirror the market risk.

# Intuitively, the rebalancing strategy buys exactly the same quantity
# of the risky asset as the CFMM does,
# but does so at the external market price, rather than the CFMM price.

# $\text{LVR} = R_t - V_t$, where $R_t$ is rebalancing portfolio and
# $V_t$ is the CFMM portfolio value.

# $\text{LVR} = \frac{1}{2} \left( \frac{V_t}{P_t} - \frac{V_t}{P_t} \right) = 0$

# Under the same price move from $P_t$ to $P_t + d P_t$
# In DEX, we sold some risky asset $d_{x_t}$ with a mix of both prices
# In CEX, we can rebalance directly at price $P_t + d P_t$ and sell $d_{x_t}$


def calc_fee(amount, fee):
    return amount * fee


def calc_swap_price(row, fee, which_token):
    if which_token == 0:
        if row.amount1_scaled > 0:
            return row.amount1_scaled * (1 - fee) / - row.amount0_scaled
        else:
            return - row.amount1_scaled / row.amount0_scaled / (1 - fee)

    elif which_token == 1:
        if row.amount0_scaled > 0:
            return row.amount0_scaled * (1 - fee) / - row.amount1_scaled
        else:
            return - row.amount0_scaled / row.amount1_scaled / (1 - fee)
    raise ValueError("which_token must be 0 or 1")


def lvr(row, which_token):
    """
    let's do when amount0 is negative, it means pool is selling token0, we copy the trade
    LVR is the difference in value between the re-balancing portfolio (Rt) and the CFMM pool (Vt)
    LVR = (Rt - Vt)
    """
    if row.amount0_scaled <= 0:
        if which_token == 1:
            # sell token0 for token1
            return - row.amount0_scaled * (row.token0_price - row.swap0_price)
        if which_token == 0:
            # sell token0 for token1 * token1's price in token0
            return - row.amount0_scaled * (row.token0_price - row.swap0_price) * row.token1_price
        raise ValueError("which_token must be 0 or 1")

    if row.amount1_scaled < 0:
        if which_token == 0:
            return - row.amount1_scaled * (row.token1_price - row.swap1_price)
        if which_token == 1:
            return - row.amount1_scaled * (row.token1_price - row.swap1_price) * row.token0_price
        raise ValueError("which_token must be 0 or 1")

    raise ValueError(f"Unhandled amount0/amount1 {row.amount0_scaled}/{row.amount1_scaled}")
