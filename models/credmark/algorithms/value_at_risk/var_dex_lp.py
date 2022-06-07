from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError, ModelDataError

from credmark.cmf.types import Contract, Token, Price

import numpy as np
import pandas as pd

from models.credmark.algorithms.value_at_risk.dto import UniswapPoolVaRInput

from models.credmark.algorithms.value_at_risk.risk_method import calc_var


from models.tmp_abi_lookup import (
    UNISWAP_V3_POOL_ABI,
)


@Model.describe(slug="finance.var-dex-lp",
                version="1.1",
                display_name="VaR for liquidity provider to Pool with IL adjustment to portfolio",
                description="Working for UniV2, V3 and Sushiswap pools",
                input=UniswapPoolVaRInput,
                output=dict)
class UniswapPoolVaR(Model):
    """
    This model takes a UniV2/Sushi/UniV3 pool to extract its token information.
    It then calculate the LP position's VaR from both price change and quantity change from IL
    for a portfolio worth of $1.
    """

    def run(self, input: UniswapPoolVaRInput) -> dict:
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
        current_ratio = bal1 / bal0

        _token0_price = self.context.run_model(input.price_model, input=token0)
        _token1_price = self.context.run_model(input.price_model, input=token1)

        token0_historical_price = (self.context.historical
                                   .run_model_historical(
                                       model_slug=input.price_model,
                                       model_input=token0,
                                       window=input.window,
                                       model_return_type=Price)
                                   .to_dataframe(fields=[('price', lambda p:p.price)])
                                   .sort_values('blockNumber', ascending=False)
                                   .reset_index(drop=True))

        token1_historical_price = (self.context.historical
                                   .run_model_historical(
                                       model_slug=input.price_model,
                                       model_input=token1,
                                       window=input.window,
                                       model_return_type=Price)
                                   .to_dataframe(fields=[('price', lambda p:p.price)])
                                   .sort_values('blockNumber', ascending=False)
                                   .reset_index(drop=True))

        df = pd.DataFrame({
            'TOKEN0/USD': token0_historical_price.price.to_numpy(),
            'TOKEN1/USD': token1_historical_price.price.to_numpy(),
        })

        df.loc[:, 'ratio_0_over_1'] = df['TOKEN0/USD'] / df['TOKEN1/USD']
        ratio_init = df.ratio_0_over_1[:-input.interval].to_numpy()
        ratio_tail = df.ratio_0_over_1[input.interval:].to_numpy()
        ratio_change_0_over_1 = ratio_init / ratio_tail

        df.loc[:, 'ratio_1_over_0'] = df['TOKEN1/USD'] / df['TOKEN0/USD']
        ratio_init = df.ratio_1_over_0[:-input.interval].to_numpy()
        ratio_tail = df.ratio_1_over_0[input.interval:].to_numpy()
        _ratio_change_1_over_0 = ratio_init / ratio_tail

        token0_init = df['TOKEN0/USD'][:-input.interval].to_numpy()
        token0_tail = df['TOKEN0/USD'][input.interval:].to_numpy()
        _token0_change = token0_init / token0_tail

        token1_init = df['TOKEN1/USD'][:-input.interval].to_numpy()
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

        if impermenant_loss_type == 'V2':
            impermenant_loss_vector = 2*np.sqrt(ratio_change)/(1+ratio_change) - 1
        else:
            impermenant_loss_vector = ((2*np.sqrt(ratio_change) - 1 - ratio_change) /
                                       (1 + ratio_change - np.sqrt(1-input.lower_range) -
                                           ratio_change * np.sqrt(1 / (1 + input.upper_range))))

        # IL check
        # import matplotlib.pyplot as plt
        # plt.scatter(1 / ratio_change - 1, impermenant_loss_vector_v2); plt.show()
        # plt.scatter(1 / ratio_change - 1, impermenant_loss_vector_v3); plt.show()
        # Or,
        # plt.scatter(ratio_change - 1, impermenant_loss_vector_v2); plt.show()
        # plt.scatter(ratio_change - 1, impermenant_loss_vector_v3); plt.show()

        # Count in both portfolio PnL and IL for the total Pnl vector
        total_pnl_vector = (1 + portfolio_pnl_vector) * (1 + impermenant_loss_vector) - 1
        total_pnl_without_il_vector = portfolio_pnl_vector
        total_pnl_il_vector = impermenant_loss_vector

        var = {}
        var_without_il = {}
        var_il = {}
        conf = input.confidence
        var_result = calc_var(total_pnl_vector, conf)
        var = {
            'var': var_result.var,
            'scenarios': (token0_historical_price.blockTime
                          .iloc[var_result.unsorted_index, ].to_list()),
            'ppl': total_pnl_vector[var_result.unsorted_index].tolist(),
            'weights': var_result.weights
        }

        var_result_without_il = calc_var(total_pnl_without_il_vector, conf)
        var_without_il = {
            'var': var_result_without_il.var,
            'scenarios': (token0_historical_price.blockTime
                          .iloc[var_result_without_il.unsorted_index, ].to_list()),
            'ppl': total_pnl_vector[var_result_without_il.unsorted_index].tolist(),
            'weights': var_result_without_il.weights
        }

        var_result_il = calc_var(total_pnl_il_vector, conf)
        var_il = {
            'var': var_result_il.var,
            'scenarios': (token0_historical_price.blockTime
                          .iloc[var_result_il.unsorted_index, ].to_list()),
            'ppl': total_pnl_vector[var_result_il.unsorted_index].tolist(),
            'weights': var_result_il.weights
        }

        # For V3, as existing assumptions, we need to cap the loss at -100%.
        if impermenant_loss_type == 'V3':
            var['var'] = np.max([-1, var['var']])
            var_without_il['var'] = np.max([-1, var_without_il['var']])
            var_il['var'] = np.max([-1, var_il['var']])

        return {
            'pool': input.pool,
            'tokens_address': [token0.address, token1.address],
            'tokens_symbol': [token0.symbol, token1.symbol],
            'ratio': current_ratio,
            'IL_type': impermenant_loss_type,
            'range': ([] if impermenant_loss_type == 'V2'
                      else [input.lower_range, input.upper_range]),
            'var': var,
            'var_without_il': var_without_il,
            'var_il': var_il,
        }
