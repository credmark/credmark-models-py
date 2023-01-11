# pylint: disable=too-many-lines
import math
from typing import List

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (Address, BlockNumber, Contract, Contracts,
                                Maybe, Portfolio, Position, Price,
                                PriceWithQuote, Some, Token, Tokens,
                                Records)
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.cmf.types.compose import MapInputsOutput
from credmark.cmf.types.series import BlockSeries, BlockSeriesRow
from credmark.dto import DTO, EmptyInput, DTOField
from models.credmark.price.dex import get_primary_token_tuples
from models.credmark.protocols.dexes.uniswap.constant import V2_FACTORY_ADDRESS
from models.credmark.protocols.dexes.uniswap.types import PositionWithFee
from models.dtos.price import (DexPricePoolInput, DexPriceTokenInput)
from models.dtos.pool import PoolPriceInfo
from models.dtos.tvl import TVLInfo
from models.dtos.volume import (TokenTradingVolume, VolumeInput,
                                VolumeInputHistorical)
from models.tmp_abi_lookup import (CURVE_VYPER_POOL, UNISWAP_V2_POOL_ABI,
                                   UNISWAP_V3_POOL_ABI)
from web3.exceptions import ABIFunctionNotFound, BadFunctionCallOutput


class UniswapV2PoolMeta:
    @staticmethod
    def get_uniswap_pools(context, input_address: Address, factory_addr: Address) -> Contracts:
        factory = Contract(address=factory_addr)
        token_pairs = get_primary_token_tuples(context, input_address)
        contracts = []
        try:
            for token_pair in token_pairs:
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

    @staticmethod
    def get_uniswap_pools_ledger(context, input_address: Address, _gw: Contract) -> Contracts:
        token_pairs = get_primary_token_tuples(context, input_address)

        with _gw.ledger.events.PairCreated as q:
            tp = token_pairs[0]
            eq_conds = q.EVT_TOKEN0.eq(tp[0]).and_(q.EVT_TOKEN1.eq(tp[1])).parentheses_()
            for tp in token_pairs[1:]:
                new_eq = q.EVT_TOKEN0.eq(tp[0]).and_(q.EVT_TOKEN1.eq(tp[1])).parentheses_()
                eq_conds = eq_conds.or_(new_eq)

            df_ts = []
            offset = 0
            while True:
                df_tt = q.select(columns=[q.EVT_PAIR, q.BLOCK_NUMBER],
                                 where=eq_conds,
                                 order_by=q.BLOCK_NUMBER,
                                 limit=5000,
                                 offset=offset).to_dataframe()

                if df_tt.shape[0] > 0:
                    df_ts.append(df_tt)
                if df_tt.shape[0] < 5000:
                    break
                offset += 5000

            all_df = pd.concat(df_ts, axis=0)

        evt_pair = all_df['evt_pair']  # type: ignore

        return Contracts(contracts=[Contract(c) for c in evt_pair])


@Model.describe(slug='uniswap-v2.get-pools',
                version='1.7',
                display_name='Uniswap v2 Token Pools',
                description='The Uniswap v2 pools that support a token contract',
                category='protocol',
                subcategory='uniswap-v2',
                input=Token,
                output=Contracts)
class UniswapV2GetPoolsForToken(Model, UniswapV2PoolMeta):
    def run(self, input: Token) -> Contracts:
        addr = V2_FACTORY_ADDRESS[self.context.network]
        return self.get_uniswap_pools(self.context, input.address, Address(addr))


@Model.describe(slug='uniswap-v2.get-pools-ledger',
                version='0.1',
                display_name='Uniswap v2 Token Pools',
                description='The Uniswap v2 pools that support a token contract - use ledger',
                category='protocol',
                subcategory='uniswap-v2',
                input=Token,
                output=Contracts)
class UniswapV2GetPoolsForTokenLedger(Model, UniswapV2PoolMeta):
    def run(self, input: Token) -> Contracts:
        gw = Contract(V2_FACTORY_ADDRESS[self.context.network])
        return self.get_uniswap_pools_ledger(self.context, input.address, gw)


class V2LPInput(DTO):
    pool: Token
    lp: Address = DTOField(description='Account')


class V2LPOutput(DTO):
    lp: Position
    tokens: List[Position]


class V2LPFeeOutput(DTO):
    lp: Position
    tokens: List[PositionWithFee]

    @classmethod
    # pylint: disable=invalid-name
    def zero(cls, lp, token0, token1):
        lp_pos = Position(amount=0, asset=lp)
        token0_pos = PositionWithFee(amount=0, fee=0, asset=token0)
        token1_pos = PositionWithFee(amount=0, fee=0, asset=token1)
        return cls(lp=lp_pos,
                   tokens=[token0_pos, token1_pos])


class V2LPQuantityInput(DTO):
    pool: Token
    lp_balance: float


@Model.describe(slug='uniswap-v2.lp-pos',
                version='0.2',
                display_name='Uniswap v2 (Sushiswap) LP Position (inclusive of fee) for liquidity',
                description='Returns position (inclusive of fee) for the amount of liquidity',
                category='protocol',
                subcategory='uniswap-v2',
                input=V2LPQuantityInput,
                output=V2LPOutput)
class UniswapV2LPQuantity(Model):
    def run(self, input: V2LPQuantityInput) -> V2LPOutput:
        pool = input.pool
        lp_balance = input.lp_balance

        try:
            _ = pool.abi
        except ModelDataError:
            pool.set_abi(UNISWAP_V2_POOL_ABI)

        reserves = pool.functions.getReserves().call()
        lp_total_supply = pool.functions.totalSupply().call()

        token0 = Token(address=Address(pool.functions.token0().call()))
        token1 = Token(address=Address(pool.functions.token1().call()))
        token0 = token0.as_erc20()
        token1 = token1.as_erc20()
        scaled_reserve0 = token0.scaled(reserves[0])
        scaled_reserve1 = token1.scaled(reserves[1])

        if math.isclose(lp_balance, 0):
            return V2LPOutput(
                lp=Position(amount=lp_balance, asset=pool),
                tokens=[Position(amount=0, asset=token0), Position(amount=0, asset=token1)])

        lp_token0 = scaled_reserve0 * lp_balance / lp_total_supply
        lp_token1 = scaled_reserve1 * lp_balance / lp_total_supply

        lp_position = Position(amount=pool.scaled(lp_balance), asset=pool)
        position0 = Position(amount=lp_token0, asset=token0)
        position1 = Position(amount=lp_token1, asset=token1)

        out = V2LPOutput(lp=lp_position, tokens=[position0, position1])
        return out


@Model.describe(slug='uniswap-v2.lp',
                version='0.2',
                display_name='Uniswap v2 (Sushiswap) LP Position (inclusive of fee) for account',
                description='Returns position (inclusive of fee) for account',
                category='protocol',
                subcategory='uniswap-v2',
                input=V2LPInput,
                output=V2LPOutput)
class UniswapV2LP(Model):
    def run(self, input: V2LPInput) -> V2LPOutput:
        pool = input.pool
        lp = input.lp
        lp_balance = pool.functions.balanceOf(lp).call()

        return self.context.run_model(
            'uniswap-v2.lp-pos',
            input=V2LPQuantityInput(pool=input.pool, lp_balance=lp_balance),
            return_type=V2LPOutput)


# pylint: disable=invalid-name
def calculate_v2_fee(context, pool, lp, block_number, transaction_value,
                     lp_prev_token0, lp_prev_token1):

    # Get the amount of tokens for a given amount of LP tokens.
    lp_in_out = context.run_model(
        'uniswap-v2.lp-pos',
        input=V2LPQuantityInput(pool=pool, lp_balance=1e18),
        return_type=V2LPOutput,
        block_number=block_number)

    ratio = lp_in_out.tokens[1].amount / lp_in_out.tokens[0].amount

    # Position implied from previous LP position (without fee)
    lp_il0 = (lp_prev_token0 * lp_prev_token1 / ratio) ** 0.5
    lp_il1 = lp_il0 * ratio

    # LP position at block_number from LP token (with fee)
    # $x = lp / lp_total_supply * token_x$
    # $y = lp / lp_total_supply * token_y$
    default_block = context.web3.eth.default_block
    context.web3.eth.default_block = block_number
    lp_balance = pool.functions.balanceOf(lp).call()
    context.web3.eth.default_block = default_block

    if lp_balance != 0:
        lp_pos_token0 = lp_in_out.tokens[0].amount * lp_balance / 1e18
        lp_pos_token1 = lp_in_out.tokens[1].amount * lp_balance / 1e18
    else:
        lp_pos_token0, lp_pos_token1 = 0.0, 0.0

    # LP position from recent deposit/withdraw (no contribution to fee)
    if transaction_value != 0:
        lp_in_out_amount0 = lp_in_out.tokens[0].amount * transaction_value / 1e18
        lp_in_out_amount1 = lp_in_out.tokens[1].amount * transaction_value / 1e18
    else:
        lp_in_out_amount0, lp_in_out_amount1 = 0.0, 0.0

    # fee = With fee - Without fee - Just-in
    # 1. "With fee" uses end-of-block lp token holding to calculate - up-to-date
    # 2. "Without fee" uses previous end-of-block holding to calculate - up-to-date
    # 3. "Just in" is calculated from the current end-of-block's ratio,
    #    which may not be the original amount put in due to other swaps inside the block.
    return dict(
        token0_lp=lp_pos_token0,
        token1_lp=lp_pos_token1,
        token0=try_zero(lp_in_out_amount0),
        token1=try_zero(lp_in_out_amount1),
        lp_il0=lp_il0,
        lp_il1=lp_il1,
        token0_fee=try_zero(lp_pos_token0 - lp_il0 - lp_in_out_amount0),
        token1_fee=try_zero(lp_pos_token1 - lp_il1 - lp_in_out_amount1),
    )


def try_zero(flt):
    if math.isclose(flt, 0):
        return 0
    return flt


def uniswap_v2_fee_sample_data():
    _df_sample = pd.DataFrame(
        columns=['block_number', 'log_index', 'from_address', 'to_address', 'transaction_value'],
        data=[(int(10109485), int(173),
              '0x0000000000000000000000000000000000000000',
               '0x76e2e2d4d655b83545d4c50d9521f5bc63bc5329',
               int(1885295466071170)),
              (int(10431987), int(27),
              '0x76e2e2d4d655b83545d4c50d9521f5bc63bc5329',
               '0x7fba4b8dc5e7616e59622806932dbea72537a56b',
               int(-357094337512011)),
              (int(10933740), int(178),
              '0x0000000000000000000000000000000000000000',
               '0x76e2e2d4d655b83545d4c50d9521f5bc63bc5329',
               int(75011156151825)), ])

    return _df_sample


#pylint: disable=line-too-long
@Model.describe(slug='uniswap-v2.lp-fee-history',
                version='0.8',
                display_name='Uniswap v2 (Sushiswap) LP Position and Fee history for account',
                description='Returns LP Position and Fee history for account',
                category='protocol',
                subcategory='uniswap-v2',
                input=V2LPInput,
                output=Records)
class UniswapV2LPFeeHistory(Model):
    def run(self, input: V2LPInput) -> Records:
        pool = input.pool
        lp = input.lp

        try:
            _ = pool.abi
        except ModelDataError:
            pool.set_abi(UNISWAP_V2_POOL_ABI)

        token0 = Token(address=Address(pool.functions.token0().call()))
        token1 = Token(address=Address(pool.functions.token1().call()))
        token0 = token0.as_erc20()
        token1 = token1.as_erc20()

        with self.context.ledger.TokenBalance as q:
            q_cols = [q.BLOCK_NUMBER,
                      q.LOG_INDEX,
                      q.FROM_ADDRESS,
                      q.TO_ADDRESS,
                      q.TRANSACTION_VALUE]

        def _use_ledger():
            with self.context.ledger.TokenBalance as q:
                df_ts = []
                offset = 0

                q_cols = [q.BLOCK_NUMBER,
                          q.LOG_INDEX,
                          q.FROM_ADDRESS,
                          q.TO_ADDRESS,
                          q.TRANSACTION_VALUE]
                while True:
                    df_tt = q.select(
                        columns=q_cols,
                        order_by=q.BLOCK_NUMBER,
                        where=(q.ADDRESS.eq(lp)
                               .and_(q.TOKEN_ADDRESS.eq(pool.address))
                               )
                    ).to_dataframe()

                    if df_tt.shape[0] > 0:
                        df_ts.append(df_tt)
                    if df_tt.shape[0] < 5000:
                        break
                    offset += 5000

            _df = pd.DataFrame()
            if len(df_ts) > 0:
                _df = pd.concat(df_ts).drop_duplicates()
            return _df

        def _use_model():
            return self.context.run_model('account.token-transfer',
                                          input={'address': lp, 'tokens': [pool.address]},
                                          return_type=Records).to_dataframe()

        # _df = _use_model().rename(columns={'value': 'transaction_value'})[q_cols]
        # _df.loc[1:, 'transaction_value'] = -1 * (_df.loc[0, 'transaction_value'])

        def _use_events():
            minted = pd.DataFrame(pool.fetch_events(pool.events.Transfer, argument_filters={
                'to': lp.checksum}, from_block=0, contract_address=pool.address.checksum))
            burnt = pd.DataFrame(pool.fetch_events(pool.events.Transfer, argument_filters={
                'from': lp.checksum}, from_block=0, contract_address=pool.address.checksum))
            df_combined = (pd.concat(
                [minted.loc[:, ['blockNumber', 'logIndex', 'from', 'to', 'value']],
                 (burnt.loc[:, ['blockNumber', 'logIndex', 'from', 'to', 'value']].assign(value=lambda x: -x.value))
                 ])
                .sort_values(['blockNumber', 'logIndex'])
                .rename(columns={
                    'blockNumber': 'block_number',
                    'logIndex': 'log_index',
                    'from': 'from_address',
                    'to': 'to_address',
                    'value': 'transaction_value'})
                .reset_index(drop=True))

            return df_combined

        _df = _use_events()

        new_data = [(int(self.context.block_number), -1, input.lp, input.lp, 0)]

        if _df.empty or (_df["block_number"].tail(1) != int(self.context.block_number)).all():
            _df = pd.concat([_df, pd.DataFrame(new_data, columns=q_cols)]).reset_index(drop=True)

        lp_prev_token0 = 0
        lp_prev_token1 = 0

        for row_n, row_data in _df.iterrows():
            # Uniswap V2 has compounding effect for the fee
            # fee = current lp position - IL'ed position from previous lp position - current addition/removal
            block_number = row_data['block_number']
            transaction_value = row_data['transaction_value']

            v2_fee = calculate_v2_fee(
                self.context, pool, lp, block_number, transaction_value,
                lp_prev_token0, lp_prev_token1)

            lp_prev_token0 = v2_fee['token0_lp']
            lp_prev_token1 = v2_fee['token1_lp']

            for it in ['token0_lp', 'token1_lp',
                       'token0', 'token1',
                       'lp_il0', 'lp_il1',
                       'token0_fee', 'token1_fee']:
                _df.loc[row_n, it] = try_zero(v2_fee[it])  # type: ignore

        return Records.from_dataframe(_df)


@Model.describe(slug='uniswap-v2.lp-fee',
                version='0.6',
                display_name='Uniswap v2 (Sushiswap) LP Position (split for fee) for account',
                description='Returns position (split for fee) for account',
                category='protocol',
                subcategory='uniswap-v2',
                input=V2LPInput,
                output=V2LPFeeOutput)
class UniswapV2LPFee(Model):
    def run(self, input: V2LPInput) -> V2LPFeeOutput:
        pool = input.pool
        lp = input.lp

        try:
            _ = pool.abi
        except ModelDataError:
            pool.set_abi(UNISWAP_V2_POOL_ABI)

        token0 = Token(address=Address(pool.functions.token0().call()))
        token1 = Token(address=Address(pool.functions.token1().call()))
        token0 = token0.as_erc20()
        token1 = token1.as_erc20()

        # Obtain the last 2 when the current block has mint/burn
        with self.context.ledger.TokenBalance as q:
            _df = q.select(
                aggregates=[(q.TRANSACTION_VALUE.sum_(), 'sum_transaction_value')],
                order_by=q.BLOCK_NUMBER.desc(),
                where=(q.ADDRESS.eq(lp)
                        .and_(q.TOKEN_ADDRESS.eq(pool.address))
                       ),
                group_by=[q.BLOCK_NUMBER],
                limit=2
            ).to_dataframe()

        if _df.empty:
            return V2LPFeeOutput.zero(lp, token0, token1)

        prev_block_number = _df['block_number'].to_list()[0]
        prev_transaction_value = _df['sum_transaction_value'].to_list()[0]

        if prev_block_number == self.context.block_number:
            prev2_block_number = _df['block_number'].to_list()[1]
            lp_pos = self.context.run_model(
                'uniswap-v2.lp',
                input=V2LPInput(pool=input.pool, lp=input.lp),
                return_type=V2LPOutput,
                block_number=prev2_block_number)

            lp_prev_token0, lp_prev_token1 = lp_pos.tokens[0].amount, lp_pos.tokens[1].amount

            v2_fee = calculate_v2_fee(
                self.context, pool, lp, prev_block_number, prev_transaction_value,
                lp_prev_token0, lp_prev_token1)
        else:
            lp_pos = self.context.run_model(
                'uniswap-v2.lp',
                input=V2LPInput(pool=input.pool, lp=input.lp),
                return_type=V2LPOutput,
                block_number=prev_block_number)

            lp_prev_token0, lp_prev_token1 = lp_pos.tokens[0].amount, lp_pos.tokens[1].amount

            v2_fee = calculate_v2_fee(
                self.context, pool, lp, self.context.block_number, 0,
                lp_prev_token0, lp_prev_token1)

        lp_balance = pool.functions.balanceOf(lp).call()

        lp_position = Position(amount=pool.scaled(lp_balance), asset=pool)
        position0 = PositionWithFee(
            amount=v2_fee['token0_lp'] - v2_fee['token0_fee'],
            fee=v2_fee['token0_fee'],
            asset=token0)
        position1 = PositionWithFee(
            amount=v2_fee['token1_lp'] - v2_fee['token1_fee'],
            fee=v2_fee['token1_fee'],
            asset=token1)

        return V2LPFeeOutput(lp=lp_position,
                             tokens=[position0, position1])


@Model.describe(slug='uniswap-v2.get-pool-price-info',
                version='1.12',
                display_name='Uniswap v2 Token Pool Price Info',
                description='Gather price and liquidity information from pool',
                category='protocol',
                subcategory='uniswap-v2',
                input=DexPricePoolInput,
                output=Maybe[PoolPriceInfo])
class UniswapPoolPriceInfo(Model):
    """
    Model to be shared between Uniswap V2 and SushiSwap
    """

    def run(self, input: DexPricePoolInput) -> Maybe[PoolPriceInfo]:
        pool = input
        try:
            _ = pool.abi
        except ModelDataError:
            pool = Contract(address=input.address, abi=UNISWAP_V2_POOL_ABI)

        primary_tokens = self.context.run_model('dex.primary-tokens',
                                                input=EmptyInput(),
                                                return_type=Some[Address],
                                                local=True).some
        # Count WETH-pool as primary pool
        primary_tokens.append(Token('WETH').address)

        reserves = pool.functions.getReserves().call()
        if reserves == [0, 0, 0]:
            return Maybe[PoolPriceInfo].none()

        token0 = Token(address=Address(pool.functions.token0().call()))
        token1 = Token(address=Address(pool.functions.token1().call()))
        token0 = token0.as_erc20()
        token1 = token1.as_erc20()
        scaled_reserve0 = token0.scaled(reserves[0])
        scaled_reserve1 = token1.scaled(reserves[1])

        # https://uniswap.org/blog/uniswap-v3-dominance
        # Appendix B: methodology
        try:
            tick_price0 = scaled_reserve1 / scaled_reserve0
            tick_price1 = 1 / tick_price0
        except (FloatingPointError, ZeroDivisionError):
            tick_price0 = 0
            tick_price1 = 0

        full_tick_liquidity0 = scaled_reserve0
        one_tick_liquidity0 = np.abs(1 / np.sqrt(1 + 0.0001) - 1) * full_tick_liquidity0

        full_tick_liquidity1 = scaled_reserve1
        one_tick_liquidity1 = (np.sqrt(1 + 0.0001) - 1) * full_tick_liquidity1

        is_primary_pool = token0.address in primary_tokens and token1.address in primary_tokens

        if token0.address in primary_tokens:
            primary_address = token0.address
        elif token1.address in primary_tokens:
            primary_address = token1.address
        else:
            primary_address = Address.null()

        ref_price = 1.0
        weth_address = Token('WETH').address

        # 1. If both are stablecoins (non-WETH): do nothing
        # 2. If SB-WETH: use SB to price WETH
        # 3. If WETH-X: use WETH to price
        # 4. If SB-X: use SB to price

        if is_primary_pool:
            if token0.address == weth_address:
                ref_price = self.context.run_model(
                    slug=input.price_slug,
                    input=DexPriceTokenInput(
                        **token1.dict(),
                        weight_power=input.weight_power,
                        debug=input.debug),
                    return_type=Price,
                    local=True).price
            if token1.address == weth_address:
                ref_price = self.context.run_model(
                    slug=input.price_slug,
                    input=DexPriceTokenInput(
                        **token0.dict(),
                        weight_power=input.weight_power,
                        debug=input.debug),
                    return_type=Price,
                    local=True).price
        else:
            if not primary_address.is_null():
                ref_price = self.context.run_model(
                    slug=input.price_slug,
                    input=DexPriceTokenInput(
                        address=primary_address,
                        weight_power=input.weight_power,
                        debug=input.debug),
                    return_type=Price,
                    local=True).price
                if ref_price is None:
                    raise ModelRunError(f'Can not retriev price for '
                                        f'{Token(address=primary_address)}')

        pool_price_info = PoolPriceInfo(src=input.price_slug,
                                        price0=tick_price0,
                                        price1=tick_price1,
                                        one_tick_liquidity0=one_tick_liquidity0,
                                        one_tick_liquidity1=one_tick_liquidity1,
                                        full_tick_liquidity0=full_tick_liquidity0,
                                        full_tick_liquidity1=full_tick_liquidity1,
                                        token0_address=token0.address,
                                        token1_address=token1.address,
                                        token0_symbol=token0.symbol,
                                        token1_symbol=token1.symbol,
                                        ref_price=ref_price,
                                        pool_address=input.address,
                                        tick_spacing=1)

        return Maybe[PoolPriceInfo](just=pool_price_info)


@Model.describe(slug='uniswap-v2.get-pool-info-token-price',
                version='1.12',
                display_name='Uniswap v2 Token Pools',
                description='Gather price and liquidity information from pools for a Token',
                category='protocol',
                subcategory='uniswap-v2',
                input=DexPriceTokenInput,
                output=Some[PoolPriceInfo])
class UniswapV2GetTokenPriceInfo(Model):
    def run(self, input: DexPriceTokenInput) -> Some[PoolPriceInfo]:
        pools = self.context.run_model('uniswap-v2.get-pools',
                                       input,
                                       return_type=Contracts,
                                       local=True)

        model_slug = 'uniswap-v2.get-pool-price-info'
        model_inputs = [
            DexPricePoolInput(
                address=pool.address,
                price_slug='uniswap-v2.get-weighted-price',
                weight_power=input.weight_power,
                debug=input.debug)
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

        def _use_for(local):
            infos = []
            for minput in model_inputs:
                pi = self.context.run_model(model_slug,
                                            minput,
                                            return_type=Maybe[PoolPriceInfo],
                                            local=local)
                if pi.is_just():
                    infos.append(pi.just)
            return infos

        infos = _use_for(local=True)

        return Some[PoolPriceInfo](some=infos)


class UniswapV2PoolInfo(DTO):
    pool_address: Address
    tokens: Tokens
    tokens_name: List[str]
    tokens_symbol: List[str]
    tokens_decimals: List[int]
    tokens_balance: List[float]
    tokens_price: List[PriceWithQuote]
    ratio: float


@Model.describe(slug="uniswap-v2.get-pool-info",
                version="1.8",
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

        token0_balance = token0.balance_of_scaled(input.address.checksum)
        token1_balance = token1.balance_of_scaled(input.address.checksum)
        # token0_reserve = token0.scaled(getReserves[0])
        # token1_reserve = token1.scaled(getReserves[1])

        prices = self.context.run_model(
            'price.quote-multiple',
            input={'some': [{'base': token0}, {'base': token1}]},
            return_type=Some[PriceWithQuote]).some

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


@Model.describe(slug='uniswap-v2.pool-tvl',
                version='1.5',
                display_name='Uniswap/Sushiswap Token Pool TVL',
                description='Gather price and liquidity information from pools',
                category='protocol',
                subcategory='uniswap-v2',
                input=Contract,
                output=TVLInfo)
class UniswapV2PoolTVL(Model):
    def run(self, input: Contract) -> TVLInfo:
        pool_info = self.context.run_model('uniswap-v2.get-pool-info',
                                           input=input,
                                           return_type=UniswapV2PoolInfo)
        positions = []
        prices = []
        tvl = 0.0

        prices = []
        for token_info, tok_price, bal in zip(pool_info.tokens,
                                              pool_info.tokens_price,
                                              pool_info.tokens_balance):
            prices.append(tok_price)
            tvl += bal * tok_price.price
            positions.append(Position(asset=token_info, amount=bal))

        try:
            pool_name = input.functions.name().call()
        except (ABIFunctionNotFound, ModelDataError):
            pool_name = 'Uniswap V3'

        tvl_info = TVLInfo(
            address=input.address,
            name=pool_name,
            portfolio=Portfolio(positions=positions),
            tokens_symbol=pool_info.tokens_symbol,
            prices=prices,
            tvl=tvl
        )

        return tvl_info


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

        with input.ledger.events.Swap as q:
            df = q.select(aggregates=[(q.BLOCK_NUMBER.count_distinct_(), 'count'),
                                      (q.BLOCK_NUMBER.min_(), 'min'),
                                      (q.BLOCK_NUMBER.max_(), 'max')]).to_dataframe()

            return {'count': df['count'][0],
                    'min':   df['min'][0],
                    'max':   df['max'][0]}


def new_trading_volume(_tokens: List[Token]):
    return Some[TokenTradingVolume](
        some=[TokenTradingVolume.default(token=tok) for tok in _tokens]
    )


@Model.describe(slug='dex.pool-volume-historical',
                version='1.12',
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

        data_vols = [dict(
            token0_in=0.0, token0_out=0.0,
            token1_in=0.0, token1_out=0.0,
            token0_price=0, token1_price=0.0)]

        token0_in = 0
        token0_out = 0
        token1_in = 0
        token1_out = 0
        for c in range(count, -1, -1):
            prev_block_number = self.context.block_number - c * interval
            prev_block_timestamp = int(BlockNumber(prev_block_number).timestamp)

            if prev_block_number < last_block_number:
                try:
                    curr_result = self.context.run_model(
                        'pool.dex-db', {"address": input.address}, block_number=prev_block_number)
                except ModelDataError as _err:
                    # When there was no data
                    curr_result = dict(
                        token0_in=0.0, token0_out=0.0,
                        token1_in=0.0, token1_out=0.0,
                        token0_price=0, token1_price=0.0)
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
                version='1.10',
                display_name='Uniswap/Sushiswap/Curve Pool Swap Volumes - Historical',
                description=('The volume of each token swapped in a pool '
                             'during the block interval from the current - Historical'),
                category='protocol',
                subcategory='uniswap-v2',
                input=VolumeInputHistorical,
                output=BlockSeries[Some[TokenTradingVolume]])
class DexPoolSwapVolumeHistoricalLedger(Model):
    def run(self, input: VolumeInputHistorical) -> BlockSeries[Some[TokenTradingVolume]]:
        # pylint:disable=locally-disabled,protected-access,line-too-long,unsubscriptable-object
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
