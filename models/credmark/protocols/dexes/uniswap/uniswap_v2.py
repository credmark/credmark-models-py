from typing import List

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (Address, BlockNumber, Contract, Contracts,
                                Maybe, Network, Portfolio, Position, Price,
                                Some, Token, Tokens)
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.cmf.types.compose import MapInputsOutput
from credmark.cmf.types.series import BlockSeries, BlockSeriesRow
from credmark.cmf.types.token import get_token_from_configuration
from credmark.dto import DTO
from models.credmark.tokens.token import fix_erc20_token
from models.dtos.price import DexPoolPriceInput, PoolPriceInfo
from models.dtos.tvl import TVLInfo
from models.dtos.volume import (TokenTradingVolume, VolumeInput,
                                VolumeInputHistorical)
from models.tmp_abi_lookup import (CURVE_VYPER_POOL, UNISWAP_V2_POOL_ABI,
                                   UNISWAP_V3_POOL_ABI)
from web3.exceptions import ABIFunctionNotFound, BadFunctionCallOutput


class UniswapV2PoolMeta:
    PRIMARY_TOKENS = {
        Network.Mainnet:
        [Address(get_token_from_configuration('1', 'USDC')['address']),  # type: ignore
         Address(get_token_from_configuration('1', 'WETH')['address']),  # type: ignore
         Address(get_token_from_configuration('1', 'DAI')['address'])]  # type: ignore
    }

    @staticmethod
    def get_uniswap_pools(context, model_input, factory_addr) -> Contracts:
        factory = Contract(address=factory_addr)
        contracts = []
        try:
            for token_address in UniswapV2PoolMeta.PRIMARY_TOKENS[context.network]:
                if token_address == model_input.address:
                    continue
                if model_input.address.to_int() < token_address.to_int():
                    token_pair = model_input.address.checksum, token_address.checksum
                else:
                    token_pair = token_address.checksum, model_input.address.checksum
                pair_address = factory.functions.getPair(*token_pair).call()
                if not Address(pair_address).is_null():
                    cc = Contract(address=pair_address)
                    try:
                        _ = cc.abi
                    except BlockNumberOutOfRangeError:
                        continue
                    except ModelDataError as _err:
                        pass
                    contracts.append(cc)

            return Contracts(contracts=contracts)
        except (BadFunctionCallOutput, BlockNumberOutOfRangeError):
            # Or use this condition: if self.context.block_number < 10000835 # Uniswap V2
            # Or use this condition: if self.context.block_number < 10794229 # SushiSwap
            return Contracts(contracts=[])


@Model.describe(slug='uniswap-v2.get-pools',
                version='1.5',
                display_name='Uniswap v2 Token Pools',
                description='The Uniswap v2 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v2',
                input=Token,
                output=Contracts)
class UniswapV2GetPoolsForToken(Model, UniswapV2PoolMeta):
    # For mainnet, Ropsten, Rinkeby, Görli, and Kovan
    UNISWAP_V2_FACTORY_ADDRESS = {
        k: '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
        for k in
        [Network.Mainnet, Network.Ropsten, Network.Rinkeby, Network.Görli, Network.Kovan]}

    def run(self, input: Token) -> Contracts:
        addr = self.UNISWAP_V2_FACTORY_ADDRESS[self.context.network]
        return self.get_uniswap_pools(self.context, input, Address(addr))


@Model.describe(slug='uniswap-v2.get-pool-price-info',
                version='1.8',
                display_name='Uniswap v2 Token Pool Price Info',
                description='Gather price and liquidity information from pool',
                category='protocol',
                subcategory='uniswap-v2',
                input=DexPoolPriceInput,
                output=Maybe[PoolPriceInfo])
class UniswapPoolPriceInfo(Model):
    """
    Model to be shared between Uniswap V2 and SushiSwap
    """

    def run(self, input: DexPoolPriceInput) -> Maybe[PoolPriceInfo]:
        pool = input.pool
        try:
            _ = pool.abi
        except ModelDataError:
            pool = Contract(address=input.pool.address, abi=UNISWAP_V2_POOL_ABI)

        weth_price = None
        reserves = pool.functions.getReserves().call()
        if reserves == [0, 0, 0]:
            return Maybe[PoolPriceInfo].none()

        token0 = Token(address=Address(pool.functions.token0().call()))
        token1 = Token(address=Address(pool.functions.token1().call()))
        token0 = fix_erc20_token(token0)
        token1 = fix_erc20_token(token1)
        scaled_reserve0 = token0.scaled(reserves[0])
        scaled_reserve1 = token1.scaled(reserves[1])

        # https://uniswap.org/blog/uniswap-v3-dominance
        # Appendix B: methodology
        if input.token.address == token0.address:
            _inverse = False
            price = scaled_reserve1 / scaled_reserve0
            liquidity = scaled_reserve0
            tick_liquidity = np.abs(1 / np.sqrt(1 + 0.0001) - 1) * liquidity
        elif input.token.address == token1.address:
            _inverse = True
            price = scaled_reserve0 / scaled_reserve1
            liquidity = scaled_reserve1
            tick_liquidity = (np.sqrt(1 + 0.0001) - 1) * liquidity
        else:
            raise ModelRunError('input token is not one of the pool tokens.')

        weth_multiplier = 1
        weth_address = Token('WETH').address
        if input.token.address != weth_address:
            if weth_address in (token1.address, token0.address):
                if weth_price is None:
                    weth_price = self.context.run_model(
                        input.price_slug,
                        {'address': weth_address},
                        return_type=Price,
                        local=True)
                    if weth_price.price is None:
                        raise ModelRunError('Can not retriev price for WETH')
                weth_multiplier = weth_price.price

        price *= weth_multiplier

        pool_price_info = PoolPriceInfo(src=self.slug,
                                        price=price,
                                        tick_liquidity=tick_liquidity,
                                        token0_address=token0.address,
                                        token1_address=token1.address,
                                        token0_symbol=token0.symbol,
                                        token1_symbol=token1.symbol,
                                        weth_multiplier=weth_multiplier,
                                        pool_address=input.pool.address)

        return Maybe[PoolPriceInfo](just=pool_price_info)


@Model.describe(slug='uniswap-v2.get-pool-info-token-price',
                version='1.10',
                display_name='Uniswap v2 Token Pools',
                description='Gather price and liquidity information from pools for a Token',
                category='protocol',
                subcategory='uniswap-v2',
                input=Token,
                output=Some[PoolPriceInfo])
class UniswapV2GetTokenPriceInfo(Model):
    def run(self, input: Token) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('uniswap-v2.get-pools',
                                       input,
                                       return_type=Contracts,
                                       local=True)

        model_slug = 'uniswap-v2.get-pool-price-info'
        model_inputs = [DexPoolPriceInput(token=input,
                                          pool=pool,
                                          price_slug='uniswap-v2.get-weighted-price')
                        for pool in pools]

        def _use_compose():
            pool_infos = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug,
                       'modelInputs': model_inputs},
                return_type=MapInputsOutput[dict, Maybe[PoolPriceInfo]])

            infos = []
            for pool_n, p in enumerate(pool_infos):
                if p.output is not None:
                    if p.output.just is not None:
                        infos.append(p.output.just)
                elif p.error is not None:
                    self.logger.error(p.error)
                    raise ModelRunError(
                        (f'Error with models({self.context.block_number}).' +
                         f'{model_slug.replace("-","_")}({model_inputs[pool_n]}). ' +
                         p.error.message))
                else:
                    raise ModelRunError('compose.map-inputs: output/error cannot be both None')
            return infos

        def _use_for():
            infos = []
            for minput in model_inputs:
                pi = self.context.run_model(model_slug,
                                            minput,
                                            return_type=Maybe[PoolPriceInfo])
                if pi.is_just():
                    infos.append(pi.just)
            return infos

        def _use_local():
            infos = []
            for minput in model_inputs:
                pi = self.context.run_model(model_slug,
                                            minput,
                                            return_type=Maybe[PoolPriceInfo],
                                            local=True)
                if pi.is_just():
                    infos.append(pi.just)
            return infos

        infos = _use_local()

        return Some[PoolPriceInfo](some=infos)


class UniswapV2PoolInfo(DTO):
    pool_address: Address
    tokens: Tokens
    tokens_name: List[str]
    tokens_symbol: List[str]
    tokens_decimals: List[int]
    tokens_balance: List[float]
    tokens_price: List[Price]
    ratio: float


@ Model.describe(slug="uniswap-v2.get-pool-info",
                 version="1.6",
                 display_name="Uniswap/Sushiswap get details for a pool",
                 description="Returns the token details of the pool",
                 category='protocol',
                 subcategory='uniswap-v2',
                 input=Contract,
                 output=UniswapV2PoolInfo)
class UniswapGetPoolInfo(Model):
    def run(self, input: Contract) -> UniswapV2PoolInfo:
        contract = input
        try:
            contract.abi
        except ModelDataError:
            contract = Contract(address=input.address, abi=UNISWAP_V2_POOL_ABI)

        token0 = Token(address=contract.functions.token0().call())
        token1 = Token(address=contract.functions.token1().call())
        # getReserves = contract.functions.getReserves().call()

        token0_balance = token0.balance_of_scaled(input.address)
        token1_balance = token1.balance_of_scaled(input.address)
        # token0_reserve = token0.scaled(getReserves[0])
        # token1_reserve = token1.scaled(getReserves[1])

        prices = self.context.run_model(
            'price.quote-multiple',
            input={'some': [{'base': token0}, {'base': token1}]},
            return_type=Some[Price]).some

        value0 = prices[0].price * token0_balance
        value1 = prices[1].price * token1_balance

        balance_ratio = value0 * value1 / (((value0 + value1)/2)**2)

        pool_info = UniswapV2PoolInfo(
            pool_address=input.address,
            tokens=Tokens(tokens=[token0, token1]),
            tokens_name=[token0.name, token1.name],
            tokens_symbol=[token0.symbol, token1.symbol],
            tokens_decimals=[token0.decimals, token1.decimals],
            tokens_balance=[token0_balance, token1_balance],
            tokens_price=prices,
            ratio=balance_ratio
        )

        return pool_info


@ Model.describe(slug='uniswap-v2.pool-tvl',
                 version='1.2',
                 display_name='Uniswap/Sushiswap Token Pool TVL',
                 description='Gather price and liquidity information from pools',
                 category='protocol',
                 subcategory='uniswap-v2',
                 input=Contract,
                 output=TVLInfo)
class UniswapV2PoolTVL(Model):
    def run(self, input: Contract) -> TVLInfo:
        pool_info = self.context.run_model('uniswap-v2.get-pool-info', input=input)
        positions = []
        prices = []
        tvl = 0.0

        prices = []
        for token_info, tok_price, bal in zip(pool_info['tokens']['tokens'],
                                              pool_info['tokens_price'],
                                              pool_info['tokens_balance']):
            prices.append(Price(**tok_price))
            tvl += bal * tok_price['price']
            positions.append(Position(asset=Token(**token_info), amount=bal))

        try:
            pool_name = input.functions.name().call()
        except (ABIFunctionNotFound, ModelDataError):
            pool_name = 'Uniswap V3'

        tvl_info = TVLInfo(
            address=input.address,
            name=pool_name,
            portfolio=Portfolio(positions=positions),
            tokens_symbol=pool_info['tokens_symbol'],
            prices=prices,
            tvl=tvl
        )

        return tvl_info


@ Model.describe(slug='dex.pool-volume-historical',
                 version='1.8',
                 display_name='Uniswap/Sushiswap/Curve Pool Swap Volumes - Historical',
                 description=('The volume of each token swapped in a pool '
                              'during the block interval from the current - Historical'),
                 category='protocol',
                 subcategory='uniswap-v2',
                 input=VolumeInputHistorical,
                 output=BlockSeries[Some[TokenTradingVolume]])
class DexPoolSwapVolumeHistorical(Model):
    def run(self, input: VolumeInputHistorical) -> BlockSeries[Some[TokenTradingVolume]]:
        # pylint:disable=locally-disabled,protected-access,line-too-long
        pool = Contract(address=input.address)

        try:
            _ = pool.abi
        except ModelDataError:
            if input.pool_info_model == 'uniswap-v2.pool-tvl':
                pool._loaded = True  # pylint:disable=protected-access
                pool.set_abi(UNISWAP_V3_POOL_ABI)
            elif input.pool_info_model == 'curve-fi.pool-tvl':
                pool._loaded = True  # pylint:disable=protected-access
                pool.set_abi(CURVE_VYPER_POOL)
            else:
                raise

        if pool.abi is None:
            raise ModelRunError('Input contract\'s ABI is empty')

        pool_info = self.context.run_model(input.pool_info_model, input=input)
        tokens_n = len(pool_info['portfolio']['positions'])

        tokens = [Token(**token_info['asset'])
                  for token_info in pool_info['portfolio']['positions']]

        # initialize empty TradingVolume
        def new_trading_volume():
            return Some[TokenTradingVolume](some=[TokenTradingVolume.default(token=tok) for tok in tokens])

        pool_volume_history = BlockSeries(
            series=[BlockSeriesRow(blockNumber=0,
                                   blockTimestamp=0,
                                   sampleTimestamp=0,
                                   output=new_trading_volume())
                    for _ in range(input.count)],
            errors=None)

        if input.pool_info_model == 'uniswap-v2.pool-tvl':
            with pool.ledger.events.Swap as q:
                event_swap_args = [c for c in q.colnames if c.lower().startswith('amount')]
                df_all_swaps = (q.select(
                    aggregates=(
                        [(f'sum((sign({q[field]})+1) / 2 * {q[field]})', f'sum_pos_{q[field]}')
                         for field in event_swap_args] +
                        [(f'sum((sign({q[field]})-1) / 2 * {q[field]})', f'sum_neg_{q[field]}')
                         for field in event_swap_args] +
                        [(f'floor(({self.context.block_number} - {q.EVT_BLOCK_NUMBER}) / {input.interval}, 0)',
                            'interval_n')] +
                        [(q.EVT_BLOCK_NUMBER.func_(func), f'{func}_block_number')
                         for func in ['min', 'max', 'count']]),
                    where=q.EVT_BLOCK_NUMBER.gt(self.context.block_number - input.interval * input.count).and_(
                        q.EVT_BLOCK_NUMBER.le(self.context.block_number)),
                    group_by=['"interval_n"']
                ).to_dataframe())

            if len(df_all_swaps) == 0:
                return pool_volume_history

            df_all_swaps.columns = pd.Index([c.lower() for c in df_all_swaps.columns])

            event_swap_args_lower = sorted([c.lower() for c in event_swap_args])
            if event_swap_args_lower == sorted(['amount0in', 'amount1in', 'amount0out', 'amount1out']):
                df_all_swaps = (df_all_swaps.drop(
                    columns=([f'sum_neg_inp_amount{n}in' for n in range(tokens_n)] +  # type: ignore
                             [f'sum_neg_inp_amount{n}out' for n in range(tokens_n)]))  # type: ignore
                    .rename(columns=(
                        {f'sum_pos_inp_amount{n}in': f'inp_amount{n}_in' for n in range(tokens_n)} |
                        {f'sum_pos_inp_amount{n}out': f'inp_amount{n}_out' for n in range(tokens_n)}))
                    .sort_values('min_block_number')
                    .reset_index(drop=True))
            else:
                df_all_swaps = (df_all_swaps.rename(columns=(
                    {f'sum_pos_inp_amount{n}': f'inp_amount{n}_in' for n in range(tokens_n)} |
                    {f'sum_neg_inp_amount{n}': f'inp_amount{n}_out' for n in range(tokens_n)}))
                    .sort_values('min_block_number')
                    .reset_index(drop=True))

            for n in range(tokens_n):
                for col in [f'inp_amount{n}_in', f'inp_amount{n}_out']:
                    df_all_swaps.loc[:, col] = df_all_swaps.loc[:, col].astype(float)  # type: ignore

        elif input.pool_info_model == 'curve-fi.pool-tvl':
            df_all_swap_1 = pd.DataFrame()
            if 'TokenExchange' in pool.abi.events:
                try:
                    event_tokenexchange_args = [s.upper() for s in pool.abi.events.TokenExchange.args]
                    assert sorted(event_tokenexchange_args) == sorted(
                        ['BUYER', 'SOLD_ID', 'TOKENS_SOLD', 'BOUGHT_ID', 'TOKENS_BOUGHT'])

                    with pool.ledger.events.TokenExchange as q:
                        df_all_swap_1 = (q.select(
                            aggregates=(
                                [(f'sum({q[field]})', f'{q[field]}')
                                 for field in ['TOKENS_SOLD', 'TOKENS_BOUGHT']] +
                                [(f'floor(({self.context.block_number} - {q.EVT_BLOCK_NUMBER}) / {input.interval}, 0)',
                                  'interval_n')] +
                                [(f'{func}({q.EVT_BLOCK_NUMBER})', f'{func}_block_number')
                                 for func in ['min', 'max', 'count']]),
                            where=q.EVT_BLOCK_NUMBER.gt(self.context.block_number - input.interval * input.count).and_(
                                q.EVT_BLOCK_NUMBER.le(self.context.block_number)),
                            group_by=['"interval_n"',
                                      q.SOLD_ID,
                                      q.BOUGHT_ID])
                            .to_dataframe())
                except ModelDataError:
                    pass

            df_all_swap_2 = pd.DataFrame()
            if 'TokenExchangeUnderlying' in pool.abi.events:
                event_tokenexchange_args = [s.upper() for s in pool.abi.events.TokenExchangeUnderlying.args]
                assert sorted(event_tokenexchange_args) == sorted(
                    ['BUYER', 'SOLD_ID', 'TOKENS_SOLD', 'BOUGHT_ID', 'TOKENS_BOUGHT'])
                try:
                    with pool.ledger.events.TokenExchangeUnderlying as q:
                        df_all_swap_2 = (q.select(
                            aggregates=(
                                [(q[field].sum_().str(), f'{q[field]}')
                                    for field in ['TOKENS_SOLD', 'TOKENS_BOUGHT']] +
                                [(f'floor(({self.context.block_number} - {q.EVT_BLOCK_NUMBER}) / {input.interval}, 0)',
                                    'interval_n')] +
                                [(q.EVT_BLOCK_NUMBER.func_(func), f'{func}_block_number')
                                    for func in ['min', 'max', 'count']]),
                            where=q.EVT_BLOCK_NUMBER.gt(self.context.block_number - input.interval * input.count).and_(
                                q.EVT_BLOCK_NUMBER.le(self.context.block_number)),
                            group_by=['"interval_n"',
                                      q.SOLD_ID,
                                      q.BOUGHT_ID])
                            .to_dataframe())
                except ModelDataError:
                    pass

            df_all_swaps = pd.concat([df_all_swap_1, df_all_swap_2]).reset_index(drop=True)

            if len(df_all_swaps) == 0:
                return pool_volume_history

            df_all_swaps.columns = pd.Index([c.lower() for c in df_all_swaps.columns])

            for col in ['inp_tokens_bought', 'inp_tokens_sold']:
                df_all_swaps.loc[:, col] = df_all_swaps.loc[:, col].astype(float)  # type: ignore

            for n in range(tokens_n):
                # In: Sold to the pool
                # Out: Bought from the pool
                df_all_swaps.loc[:, f'inp_amount{n}_in'] = df_all_swaps.loc[:, 'inp_tokens_sold']       # type: ignore
                df_all_swaps.loc[:, f'inp_amount{n}_out'] = df_all_swaps.loc[:, 'inp_tokens_bought']    # type: ignore
                df_all_swaps.loc[df_all_swaps.inp_sold_id != n, f'inp_amount{n}_in'] = 0                # type: ignore
                df_all_swaps.loc[df_all_swaps.inp_bought_id != n, f'inp_amount{n}_out'] = 0             # type: ignore

            df_all_swaps = (df_all_swaps
                            .groupby(['interval_n'], as_index=False)
                            .agg({'min_block_number': ['min'],
                                 'max_block_number': ['max'],
                                  'count_block_number': ['sum']} |
                                 {f'inp_amount{n}_in': ['sum'] for n in range(tokens_n)} |
                                 {f'inp_amount{n}_out': ['sum'] for n in range(tokens_n)}))
            df_all_swaps.columns = pd.Index([a for a, _ in df_all_swaps.columns])
            df_all_swaps = df_all_swaps.sort_values('min_block_number').reset_index(drop=True)

        else:
            raise ModelRunError(f'Unknown pool info model {input.pool_info_model=}')

        df_all_swaps.loc[:, 'interval_n'] = input.count - df_all_swaps.loc[:, 'interval_n'] - 1
        df_all_swaps.loc[:, 'start_block_number'] = (
            int(self.context.block_number) - (df_all_swaps.interval_n + 1) * input.interval)
        df_all_swaps.loc[:, 'end_block_number'] = (
            int(self.context.block_number) - (df_all_swaps.interval_n) * input.interval)

        # TODO: get price for each block when composer model is ready
        # all_blocks = df_all_swaps.loc[:, ['evt_block_number']]  # type: ignore
        # for n in range(tokens_n):
        #     for n_row, row in all_blocks[::-1].iterrows():
        #         all_blocks.loc[n_row, f'token{n}_price'] = self.context.run_model(
        #             'price.quote',
        #             input=tokens[n], block_number=row.evt_block_number, return_type=Price).price

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
                token_out = df_swap_sel[f'inp_amount{n}_out'].sum()  # type: ignore
                token_in = df_swap_sel[f'inp_amount{n}_in'].sum()  # type: ignore

                pool_volume_history.series[cc].output[n].sellAmount = tokens[n].scaled(token_out)
                pool_volume_history.series[cc].output[n].buyAmount = tokens[n].scaled(token_in)
                pool_volume_history.series[cc].output[n].sellValue = tokens[n].scaled(token_out * token_price)
                pool_volume_history.series[cc].output[n].buyValue = tokens[n].scaled(token_in * token_price)

        return pool_volume_history


@ Model.describe(slug='dex.pool-volume',
                 version='1.10',
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
