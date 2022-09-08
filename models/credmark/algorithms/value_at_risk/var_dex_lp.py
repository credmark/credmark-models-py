import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Contract, Price, Some, Token
from credmark.cmf.types.compose import MapBlockTimeSeriesOutput
from models.credmark.algorithms.value_at_risk.dto import (DexVaR,
                                                          UniswapPoolVaRInput,
                                                          UniswapPoolVaROutput)
from models.credmark.algorithms.value_at_risk.risk_method import calc_var
from models.credmark.protocols.dexes.uniswap.uniswap_v3 import \
    UniswapV3PoolInfo
from models.tmp_abi_lookup import UNISWAP_V3_POOL_ABI

np.seterr(all='raise')


@Model.describe(slug="finance.var-dex-lp",
                version="1.6",
                display_name="VaR for liquidity provider to Pool with IL adjustment to portfolio",
                description="Working for UniV2, V3 and Sushiswap pools",
                category='protocol',
                subcategory='uniswap',
                tags=['var'],
                input=UniswapPoolVaRInput,
                output=UniswapPoolVaROutput)
class UniswapPoolVaR(Model):
    """
    This model takes a UniV2/Sushi/UniV3 pool to extract its token information.
    It then calculate the LP position's VaR from both price change and quantity change from IL
    for a portfolio worth of $1.
    """

    def run(self, input: UniswapPoolVaRInput) -> UniswapPoolVaROutput:
        pool = input.pool

        try:
            _ = pool.abi
        except ModelDataError:
            pool = Contract(address=input.pool.address, abi=UNISWAP_V3_POOL_ABI)

        if not isinstance(pool.abi, list):
            raise ModelRunError('Pool abi can not be loaded.')

        if 'slot0' in [x['name'] for x in pool.abi if 'name' in x]:
            impermenant_loss_type = 'V3'
        else:
            impermenant_loss_type = 'V2'

        # get token and balances
        token0 = Token(address=pool.functions.token0().call())
        token1 = Token(address=pool.functions.token1().call())
        bal0 = token0.scaled(token0.functions.balanceOf(pool.address).call())
        bal1 = token1.scaled(token1.functions.balanceOf(pool.address).call())

        # Current price
        if impermenant_loss_type == 'V2':
            p_0 = bal1 / bal0
        else:
            v3_info = self.context.run_model('uniswap-v3.get-pool-info',
                                             input=pool,
                                             return_type=UniswapV3PoolInfo)
            scale_multiplier = (10 ** (v3_info.token0.decimals - v3_info.token1.decimals))
            # p_0 = tick_price = token0 / token1
            p_0 = 1.0001 ** v3_info.current_tick * scale_multiplier

        t_unit, count = self.context.historical.parse_timerangestr(input.window)
        interval = self.context.historical.range_timestamp(t_unit, 1)

        token_hp = self.context.run_model(
            slug='price.quote-historical-multiple',
            input={'some': [{'base': token0}, {'base': token1}],
                   "interval": interval,
                   "count": count,
                   "exclusive": False},
            return_type=MapBlockTimeSeriesOutput[Some[Price]])

        token_historical_prices = [
            (token_hp.to_dataframe(fields=[('price', lambda p, n=tok_n:p.some[n].price)])
             .sort_values('blockNumber', ascending=False)
             .reset_index(drop=True))
            for tok_n in range(2)]

        historical_days = (token_historical_prices[0]
                           .blockTime)

        df = pd.DataFrame({
            'TOKEN0/USD': token_historical_prices[0].price.to_numpy(),
            'TOKEN1/USD': token_historical_prices[1].price.to_numpy(),
        })

        df.loc[:, 'ratio_0_over_1'] = df['TOKEN0/USD'] / df['TOKEN1/USD']
        ratio_init = df.ratio_0_over_1[: -input.interval].to_numpy()
        ratio_tail = df.ratio_0_over_1[input.interval:].to_numpy()
        ratio_change_0_over_1 = ratio_init / ratio_tail

        df.loc[:, 'ratio_1_over_0'] = df['TOKEN1/USD'] / df['TOKEN0/USD']
        ratio_init = df.ratio_1_over_0[: -input.interval].to_numpy()
        ratio_tail = df.ratio_1_over_0[input.interval:].to_numpy()
        _ratio_change_1_over_0 = ratio_init / ratio_tail

        token0_init = df['TOKEN0/USD'][: -input.interval].to_numpy()
        token0_tail = df['TOKEN0/USD'][input.interval:].to_numpy()
        _token0_change = token0_init / token0_tail

        token1_init = df['TOKEN1/USD'][: -input.interval].to_numpy()
        token1_tail = df['TOKEN1/USD'][input.interval:].to_numpy()
        token1_change = token1_init / token1_tail

        ratio_change = ratio_change_0_over_1

        # Assume we hold a set of tokens on time 0, we could become a LP provider or do nothing.
        # Case of Do nothing: we are only subject to price change
        # Case of LP: we are subjected to both price change quantity change from IL.
        # Impermanent loss is the loss relative to the holding's value of no quantity change.
        # The change in value from price change is counted in `portfolio_pnl_vector`.

        # For portfolio PnL vector, we need to match either
        # ratio_0_over_1 with Token1's price change, or
        # ratio_1_over_0 with Token1's price change.
        portfolio_pnl_vector = (1 + ratio_change_0_over_1) / 2 * token1_change - 1

        # Impermenant loss
        # If we change the order of token0 and token1 to obtain the ratio,
        # impermenant_loss_vector shall be very close to each other (invariant for the order)
        # i.e. For V2
        # np.allclose(
        #   2*np.sqrt(ratio_change)/(1+ratio_change)-1,
        #   2*np.sqrt(1/ratio_change)/(1+1/ratio_change)-1
        # )

        # Demo for extreme values
        # ratio_change[0] = 0.05
        # ratio_change[1] = 1000

        # V2
        impermenant_loss_vector_v2 = 2*np.sqrt(ratio_change)/(1+ratio_change) - 1

        # V3
        p_a = (1-input.lower_range) * p_0
        p_b = (1+input.upper_range) * p_0

        if np.isclose(p_a, 0):
            impermenant_loss_vector_under = np.zeros(ratio_change.shape)
        else:
            impermenant_loss_vector_under = (1 / np.sqrt(p_a) - 1 / np.sqrt(p_b)) / (
                (np.sqrt(p_b) - np.sqrt(p_0)) / (np.sqrt(p_0) * np.sqrt(p_b)) +
                (np.sqrt(p_0) - np.sqrt(p_a)) * 1 / (p_0 * ratio_change)) - 1

        impermenant_loss_vector_between = (
            (2*np.sqrt(ratio_change) - 1 - ratio_change) /
            (1 + ratio_change - np.sqrt(1-input.lower_range) -
                ratio_change * np.sqrt(1 / (1 + input.upper_range))))

        impermenant_loss_vector_above = (
            np.sqrt(p_b) - np.sqrt(p_a)) / (
            (np.sqrt(p_b) - np.sqrt(p_0)) / (
                np.sqrt(p_0) * np.sqrt(p_b)) * p_0 * ratio_change +
            (np.sqrt(p_0) - np.sqrt(p_a))) - 1

        impermenant_loss_vector_v3 = impermenant_loss_vector_between.copy()
        impermenant_loss_vector_v3[
            (ratio_change < 1 - input.lower_range)] = impermenant_loss_vector_under[
                (ratio_change < 1 - input.lower_range)]
        impermenant_loss_vector_v3[
            (ratio_change > 1 + input.upper_range)] = impermenant_loss_vector_above[
                (ratio_change > 1 + input.lower_range)]

        if impermenant_loss_type == 'V2':
            impermenant_loss_vector = impermenant_loss_vector_v2.copy()
        else:
            impermenant_loss_vector = impermenant_loss_vector_v3.copy()

        # IL check
        # import matplotlib.pyplot as plt
        # plt.scatter(1 / ratio_change - 1, impermenant_loss_vector_v2)
        # plt.scatter(1 / ratio_change - 1, impermenant_loss_vector_v3)
        # plt.title(f'Pool PPL for -{input.lower_range}/+{input.upper_range}')
        # plt.show()

        # Or,
        # plt.scatter(ratio_change - 1, impermenant_loss_vector_v2)
        # plt.scatter(ratio_change - 1, impermenant_loss_vector_v3)
        # plt.show()

        # Count in both portfolio PnL and IL for the total Pnl vector
        total_pnl_vector = (1 + portfolio_pnl_vector) * (1 + impermenant_loss_vector) - 1
        total_pnl_without_il_vector = portfolio_pnl_vector
        total_pnl_il_vector = impermenant_loss_vector

        var = {}
        var_without_il = {}
        var_il = {}
        conf = input.confidence
        var_result = calc_var(total_pnl_vector, conf)

        var = DexVaR(
            var=var_result.var,
            scenarios=historical_days.loc[var_result.unsorted_index].to_list(),
            ppl=total_pnl_vector[var_result.unsorted_index].tolist(),
            weights=var_result.weights)

        var_result_without_il = calc_var(total_pnl_without_il_vector, conf)
        var_without_il = DexVaR(
            var=var_result_without_il.var,
            scenarios=historical_days.loc[var_result_without_il.unsorted_index].to_list(),
            ppl=total_pnl_without_il_vector[var_result_without_il.unsorted_index].tolist(),
            weights=var_result_without_il.weights)

        var_result_il = calc_var(total_pnl_il_vector, conf)
        var_il = DexVaR(
            var=var_result_il.var,
            scenarios=historical_days.loc[var_result_il.unsorted_index].to_list(),
            ppl=total_pnl_il_vector[var_result_il.unsorted_index].tolist(),
            weights=var_result_il.weights)

        # For V3, as existing assumptions, we need to cap the loss at -100%.
        if impermenant_loss_type == 'V3':
            var.var = np.max([-1, var.var])
            var_without_il.var = np.max([-1, var_without_il.var])
            var_il.var = np.max([-1, var_il.var])

        return UniswapPoolVaROutput(
            pool=input.pool,
            tokens_address=[token0.address, token1.address],
            tokens_symbol=[token0.symbol, token1.symbol],
            ratio=p_0,
            IL_type=impermenant_loss_type,
            lp_range=(None if impermenant_loss_type == 'V2'
                      else (input.lower_range, input.upper_range)),
            var=var,
            var_without_il=var_without_il,
            var_il=var_il)
