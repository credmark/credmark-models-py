# pylint:disable=locally-disabled,protected-access,line-too-long,unsubscriptable-object

from typing import List

import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (BlockNumber, Contract,
                                Some, Token)
from credmark.cmf.types.series import BlockSeries, BlockSeriesRow
from models.dtos.volume import (TokenTradingVolume, VolumeInput,
                                VolumeInputHistorical)
from models.tmp_abi_lookup import (CURVE_VYPER_POOL, UNISWAP_V3_POOL_ABI)


@Model.describe(slug='dex.pool-volume-block-range',
                version='1.0',
                display_name='Uniswap/Sushiswap/Curve Pool Swap Volumes - Historical',
                description=('The volume of each token swapped in a pool '
                             'during the block interval from the current - Historical'),
                category='protocol',
                subcategory='uniswap-v2',
                input=Contract,
                output=dict)
class DexPoolSwapBlockRange(Model):
    def run(self, input: Contract) -> dict:
        try:
            _ = input.abi
        except ModelDataError:
            input.set_abi(UNISWAP_V3_POOL_ABI)

        def _use_ledger():
            with input.ledger.events.Swap as q:
                df = (q
                      .select(
                          aggregates=[(q.BLOCK_NUMBER.count_distinct_(), 'count'),
                                      (q.BLOCK_NUMBER.min_(), 'min'),
                                      (q.BLOCK_NUMBER.max_(), 'max')])
                      .to_dataframe())

                return {'count': df['count'][0],
                        'min':   df['min'][0],
                        'max':   df['max'][0]}

        return _use_ledger()


def new_trading_volume(_tokens: List[Token]):
    return Some[TokenTradingVolume](
        some=[TokenTradingVolume.default(token=tok) for tok in _tokens]
    )


@Model.describe(slug='dex.pool-volume-historical',
                version='1.13',
                display_name='Uniswap/Sushiswap/Curve Pool Swap Volumes - Historical',
                description=('The volume of each token swapped in a pool '
                             'during the block interval from the current - Historical'),
                category='protocol',
                subcategory='uniswap-v2',
                input=VolumeInputHistorical,
                output=BlockSeries[Some[TokenTradingVolume]])
class DexPoolSwapVolumeHistorical(Model):
    def run(self, input: VolumeInputHistorical) -> BlockSeries[Some[TokenTradingVolume]]:
        if input.pool_info_model == 'curve-fi.pool-tvl':
            return self.context.run_model(
                'dex.pool-volume-historical-ledger',
                input,
                return_type=BlockSeries[Some[TokenTradingVolume]],
                block_number=self.context.block_number)

        count = input.count
        interval = input.interval

        # credmark-dev run pool.dex-db-latest -i '{"address": "0x795065dcc9f64b5614c407a6efdc400da6221fb0"}' -j
        last_result = self.context.run_model(
            'pool.dex-db-latest', input={"address": input.address}, return_type=dict)
        last_block_number = last_result['block_number']

        tokens = [Token(token_addr) for token_addr in [last_result['token0_address'], last_result['token1_address']]]

        pool_volume_history = BlockSeries(
            series=[BlockSeriesRow(blockNumber=0,
                                   blockTimestamp=0,
                                   sampleTimestamp=0,
                                   output=new_trading_volume(tokens))
                    for _ in range(input.count)],
            errors=None)

        data_vols = [{
            'token0_in': 0.0, 'token0_out': 0.0,
            'token1_in': 0.0, 'token1_out': 0.0,
            'token0_price': 0, 'token1_price': 0.0}]

        prev_block_numbers = [x for x in (self.context.block_number - c * interval for c in range(count, -1, -1))
                              if x < last_block_number]

        prev_results = {
            r['block_number']: r
            for r in self.context.run_model(
                'pool.dex-db-blocks', {"address": input.address, 'blocks': prev_block_numbers})['results']}

        token0_in = 0
        token0_out = 0
        token1_in = 0
        token1_out = 0
        for c in range(count, -1, -1):
            prev_block_number = self.context.block_number - c * interval
            prev_block_timestamp = int(BlockNumber(prev_block_number).timestamp)

            if prev_block_number < last_block_number:
                if prev_block_number in prev_results:
                    curr_result = prev_results[prev_block_number]
                else:
                    # When there was no data
                    curr_result = {
                        'token0_in': 0.0, 'token0_out': 0.0,
                        'token1_in': 0.0, 'token1_out': 0.0,
                        'token0_price': 0, 'token1_price': 0.0}
            else:
                # use last_result
                curr_result = last_result

            data_vols.append(curr_result)

            if c == count:
                token0_in = curr_result['token0_in']
                token0_out = curr_result['token0_out']
                token1_in = curr_result['token1_in']
                token1_out = curr_result['token1_out']
            else:
                pool_volume_history.series[count - c - 1].blockNumber = int(prev_block_number)
                pool_volume_history.series[count - c - 1].blockTimestamp = prev_block_timestamp
                pool_volume_history.series[count - c - 1].sampleTimestamp = prev_block_timestamp

                pool_volume_history.series[count - c - 1].output[0].sellAmount = curr_result['token0_in'] - token0_in
                pool_volume_history.series[count - c - 1].output[0].buyAmount = curr_result['token0_out'] - token0_out
                pool_volume_history.series[count - c - 1].output[0].sellValue = (
                    curr_result['token0_in'] - token0_in) * curr_result['token0_price']
                pool_volume_history.series[count - c - 1].output[0].buyValue = (
                    curr_result['token0_out'] - token0_out) * curr_result['token0_price']

                pool_volume_history.series[count - c - 1].output[1].sellAmount = curr_result['token1_in'] - token1_in
                pool_volume_history.series[count - c - 1].output[1].buyAmount = curr_result['token1_out'] - token1_out
                pool_volume_history.series[count - c - 1].output[1].sellValue = (
                    curr_result['token1_in'] - token1_in) * curr_result['token1_price']
                pool_volume_history.series[count - c - 1].output[1].buyValue = (
                    curr_result['token1_out'] - token1_out) * curr_result['token1_price']

                token0_in = curr_result['token0_in']
                token0_out = curr_result['token0_out']
                token1_in = curr_result['token1_in']
                token1_out = curr_result['token1_out']

        _df_vols = pd.DataFrame(data_vols)

        return pool_volume_history


@Model.describe(slug='dex.pool-volume-historical-ledger',
                version='1.11',
                display_name='Uniswap/Sushiswap/Curve Pool Swap Volumes - Historical',
                description=('The volume of each token swapped in a pool '
                             'during the block interval from the current - Historical'),
                category='protocol',
                subcategory='uniswap-v2',
                input=VolumeInputHistorical,
                output=BlockSeries[Some[TokenTradingVolume]])
class DexPoolSwapVolumeHistoricalLedger(Model):
    def run(self, input: VolumeInputHistorical) -> BlockSeries[Some[TokenTradingVolume]]:
        pool = Contract(address=input.address)

        try:
            _ = pool.abi
        except ModelDataError:
            if input.pool_info_model == 'uniswap-v2.pool-tvl':
                pool.set_abi(UNISWAP_V3_POOL_ABI, set_loaded=True)
            elif input.pool_info_model == 'curve-fi.pool-tvl':
                pool.set_abi(CURVE_VYPER_POOL, set_loaded=True)
            else:
                raise

        if pool.abi is None:
            raise ModelRunError('Input contract\'s ABI is empty')

        pool_info = self.context.run_model(input.pool_info_model, input=input)
        tokens_n = len(pool_info['portfolio']['positions'])

        tokens = [Token(**token_info['asset'])
                  for token_info in pool_info['portfolio']['positions']]

        pool_volume_history = BlockSeries(
            series=[BlockSeriesRow(blockNumber=0,
                                   blockTimestamp=0,
                                   sampleTimestamp=0,
                                   output=new_trading_volume(tokens))
                    for _ in range(input.count)],
            errors=None)

        if input.pool_info_model == 'uniswap-v2.pool-tvl':
            with pool.ledger.events.Swap as q:
                event_swap_args = [c for c in q.colnames if c.lower().startswith('evt_amount')]
                df_all_swaps = (q.select(
                    aggregates=(
                        [(f'sum((sign({q[field]})+1) / 2 * {q[field]})', f'sum_pos_{q[field]}')
                         for field in event_swap_args] +
                        [(f'sum((sign({q[field]})-1) / 2 * {q[field]})', f'sum_neg_{q[field]}')
                         for field in event_swap_args] +
                        [(f'floor(({self.context.block_number} - {q.BLOCK_NUMBER}) / {input.interval}, 0)',
                            'interval_n')] +
                        [(q.BLOCK_NUMBER.func_(func), f'{func}_block_number')
                         for func in ['min', 'max', 'count']]),
                    where=q.BLOCK_NUMBER.gt(self.context.block_number - input.interval * input.count).and_(
                        q.BLOCK_NUMBER.le(self.context.block_number)),
                    group_by=['"interval_n"']
                ).to_dataframe())

            if len(df_all_swaps) == 0:
                return pool_volume_history

            df_all_swaps.columns = pd.Index([c.lower() for c in df_all_swaps.columns])  # type: ignore

            event_swap_args_lower = sorted([c.lower() for c in event_swap_args])
            if event_swap_args_lower == sorted(['evt_amount0in', 'evt_amount1in', 'evt_amount0out', 'evt_amount1out']):
                # Pool uses In/Out to represent
                df_all_swaps = (df_all_swaps.drop(
                    columns=([f'sum_neg_evt_amount{n}in' for n in range(tokens_n)] +  # type: ignore
                             [f'sum_neg_evt_amount{n}out' for n in range(tokens_n)]))  # type: ignore
                    .rename(columns=(
                        {f'sum_pos_evt_amount{n}in': f'evt_amount{n}_in' for n in range(tokens_n)} |
                        {f'sum_pos_evt_amount{n}out': f'evt_amount{n}_out' for n in range(tokens_n)}))
                    .sort_values('min_block_number')
                    .reset_index(drop=True))
            else:
                # Pool uses two records per Swap (+/-) sign.
                df_all_swaps = (df_all_swaps.rename(columns=(
                    {f'sum_pos_evt_amount{n}': f'evt_amount{n}_in' for n in range(tokens_n)} |
                    {f'sum_neg_evt_amount{n}': f'evt_amount{n}_out' for n in range(tokens_n)}))
                    .sort_values('min_block_number')
                    .reset_index(drop=True))

            for n in range(tokens_n):
                for col in [f'evt_amount{n}_in', f'evt_amount{n}_out']:
                    df_all_swaps[col] = df_all_swaps.loc[:, col].astype(float)  # type: ignore

        elif input.pool_info_model == 'curve-fi.pool-tvl':
            df_all_swap_1 = pd.DataFrame()
            if 'TokenExchange' in pool.abi.events:
                try:
                    event_tokenexchange_args = ['EVT_' + s.upper() for s in pool.abi.events.TokenExchange.args]
                    assert sorted(event_tokenexchange_args) == sorted(
                        ['EVT_BUYER', 'EVT_SOLD_ID', 'EVT_TOKENS_SOLD', 'EVT_BOUGHT_ID', 'EVT_TOKENS_BOUGHT'])

                    with pool.ledger.events.TokenExchange as q:
                        df_all_swap_1 = (q.select(
                            aggregates=(
                                [(q[field].as_integer().sum_(), q[field])
                                 for field in ['EVT_TOKENS_SOLD', 'EVT_TOKENS_BOUGHT']] +
                                [(f'floor(({self.context.block_number} - {q.BLOCK_NUMBER}) / {input.interval}, 0)',
                                  'interval_n')] +
                                [(f'{func}({q.BLOCK_NUMBER})', f'{func}_block_number')
                                 for func in ['min', 'max', 'count']]),
                            where=q.BLOCK_NUMBER.gt(self.context.block_number - input.interval * input.count).and_(
                                q.BLOCK_NUMBER.le(self.context.block_number)),
                            group_by=['"interval_n"',
                                      q.EVT_SOLD_ID,
                                      q.EVT_BOUGHT_ID])
                            .to_dataframe())
                except ModelDataError:
                    pass

            df_all_swap_2 = pd.DataFrame()
            if 'TokenExchangeUnderlying' in pool.abi.events:
                event_tokenexchange_args = ['EVT_' + s.upper() for s in pool.abi.events.TokenExchangeUnderlying.args]
                assert sorted(event_tokenexchange_args) == sorted(
                    ['EVT_BUYER', 'EVT_SOLD_ID', 'EVT_TOKENS_SOLD', 'EVT_BOUGHT_ID', 'EVT_TOKENS_BOUGHT'])
                try:
                    with pool.ledger.events.TokenExchangeUnderlying as q:
                        df_all_swap_2 = (q.select(
                            aggregates=(
                                [(q[field].as_integer().sum_().str(), f'{q[field]}')
                                    for field in ['EVT_TOKENS_SOLD', 'EVT_TOKENS_BOUGHT']] +
                                [(f'floor(({self.context.block_number} - {q.BLOCK_NUMBER}) / {input.interval}, 0)',
                                    'interval_n')] +
                                [(q.BLOCK_NUMBER.func_(func), f'{func}_block_number')
                                    for func in ['min', 'max', 'count']]),
                            where=q.BLOCK_NUMBER.gt(self.context.block_number - input.interval * input.count).and_(
                                q.BLOCK_NUMBER.le(self.context.block_number)),
                            group_by=['"interval_n"',
                                      q.EVT_SOLD_ID,
                                      q.EVT_BOUGHT_ID])
                            .to_dataframe())
                except ModelDataError:
                    pass

            df_all_swaps = pd.concat([df_all_swap_1, df_all_swap_2]).reset_index(drop=True)

            if len(df_all_swaps) == 0:
                return pool_volume_history

            df_all_swaps.columns = pd.Index([c.lower() for c in df_all_swaps.columns])  # type: ignore

            for col in ['evt_tokens_bought', 'evt_tokens_sold']:
                df_all_swaps[col] = df_all_swaps.loc[:, col].astype(float)  # type: ignore

            for n in range(tokens_n):
                # In: Sold to the pool
                # Out: Bought from the pool
                df_all_swaps[f'evt_amount{n}_in'] = df_all_swaps.loc[:, 'evt_tokens_sold']       # type: ignore
                df_all_swaps[f'evt_amount{n}_out'] = df_all_swaps.loc[:, 'evt_tokens_bought']    # type: ignore
                df_all_swaps.loc[df_all_swaps.evt_sold_id != n, f'evt_amount{n}_in'] = 0                # type: ignore
                df_all_swaps.loc[df_all_swaps.evt_bought_id != n, f'evt_amount{n}_out'] = 0             # type: ignore

            df_all_swaps = (df_all_swaps
                            .groupby(['interval_n'], as_index=False)
                            .agg({'min_block_number': ['min'],
                                 'max_block_number': ['max'],
                                  'count_block_number': ['sum']} |
                                 {f'evt_amount{n}_in': ['sum'] for n in range(tokens_n)} |
                                 {f'evt_amount{n}_out': ['sum'] for n in range(tokens_n)}))  # type: ignore

            df_all_swaps.columns = pd.Index([a for a, _ in df_all_swaps.columns])  # type: ignore
            df_all_swaps = df_all_swaps.sort_values('min_block_number').reset_index(drop=True)
        else:
            raise ModelRunError(f'Unknown pool info model {input.pool_info_model=}')

        df_all_swaps['interval_n'] = input.count - df_all_swaps.loc[:, 'interval_n'] - 1
        df_all_swaps['start_block_number'] = (
            int(self.context.block_number) - (df_all_swaps.interval_n + 1) * input.interval)
        df_all_swaps['end_block_number'] = (
            int(self.context.block_number) - (df_all_swaps.interval_n) * input.interval)

        # TODO: get price for each block when composer model is ready
        # all_blocks = df_all_swaps.loc[:, ['evt_block_number']]  # type: ignore
        # for n in range(tokens_n):
        #     for n_row, row in all_blocks[::-1].iterrows():
        #         all_blocks.loc[n_row, f'token{n}_price'] = self.context.run_model(
        #             'price.quote',
        #             input=tokens[n], block_number=row.BLOCK_NUMBER, return_type=Price).price

        # df_all_swaps = df_all_swaps.merge(all_blocks, on=['evt_block_number'], how='left')

        # Use current block's price, instead.
        for cc in range(input.count):
            df_swap_sel = df_all_swaps.loc[df_all_swaps.interval_n == cc, :]

            if df_swap_sel.empty:  # type: ignore
                block_number = self.context.block_number + (cc - input.count + 1) * input.interval
                pool_volume_history.series[cc].blockNumber = int(block_number)
                pool_volume_history.series[cc].blockTimestamp = int(BlockNumber(block_number).timestamp)
                pool_volume_history.series[cc].sampleTimestamp = BlockNumber(block_number).timestamp
                continue

            block_number = df_swap_sel.max_block_number.to_list()[0]  # type: ignore
            pool_volume_history.series[cc].blockNumber = int(block_number)
            pool_volume_history.series[cc].blockTimestamp = int(BlockNumber(block_number).timestamp)
            pool_volume_history.series[cc].sampleTimestamp = BlockNumber(block_number).timestamp

            pool_info_past = self.context.run_model(input.pool_info_model, input=input, block_number=block_number)
            for n in range(tokens_n):
                token_price = pool_info_past['prices'][n]['price']  # type: ignore
                token_out = df_swap_sel[f'evt_amount{n}_out'].sum()  # type: ignore
                token_in = df_swap_sel[f'evt_amount{n}_in'].sum()  # type: ignore

                pool_volume_history.series[cc].output[n].sellAmount = tokens[n].scaled(token_out)
                pool_volume_history.series[cc].output[n].buyAmount = tokens[n].scaled(token_in)
                pool_volume_history.series[cc].output[n].sellValue = tokens[n].scaled(token_out * token_price)
                pool_volume_history.series[cc].output[n].buyValue = tokens[n].scaled(token_in * token_price)

        return pool_volume_history


@Model.describe(slug='dex.pool-volume',
                version='1.11',
                display_name='Uniswap/Sushiswap/Curve Pool Swap Volumes',
                description=('The volume of each token swapped in a pool '
                             'during the block interval from the current'),
                category='protocol',
                subcategory='uniswap-v2',
                input=VolumeInput,
                output=Some[TokenTradingVolume])
class DexPoolSwapVolume(Model):
    def run(self, input: VolumeInput) -> Some[TokenTradingVolume]:
        input_historical = VolumeInputHistorical(**input.dict(), count=1)
        volumes = self.context.run_model('dex.pool-volume-historical',
                                         input=input_historical,
                                         return_type=BlockSeries[Some[TokenTradingVolume]],
                                         local=True)
        return volumes.series[0].output
