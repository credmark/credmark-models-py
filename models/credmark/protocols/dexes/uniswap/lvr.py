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
