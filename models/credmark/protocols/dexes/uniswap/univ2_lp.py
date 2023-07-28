# pylint: disable=too-many-lines, unsubscriptable-object
import math
from typing import List

import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import Address, Position, Records, Token
from credmark.dto import DTO, DTOField

from models.credmark.chain.contract import ContractEventsInput, ContractEventsOutput
from models.credmark.protocols.dexes.uniswap.types import PositionWithFee
from models.tmp_abi_lookup import UNISWAP_V2_POOL_ABI


class UniswapV2LPInput(DTO):
    pool: Token
    lp: Address = DTOField(description='Account')

    class Config:
        schema_extra = {
            "examples": [{"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc",
                          "lp": "0x2344f131b07e6afd943b0901c55898573f0d1561"}]
        }


class UniswapV2LPOutput(DTO):
    lp: Position
    tokens: List[Position]


class UniswapV2LPFeeOutput(DTO):
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


class UniswapV2LPQuantityInput(DTO):
    pool: Token
    lp_balance: float

    class Config:
        schema_extra = {
            "examples": [
                {"pool": "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc", "lp_balance": 10000}
            ]
        }


@Model.describe(slug='uniswap-v2.lp-pos',
                version='0.3',
                display_name='Uniswap v2 (SushiSwap) LP Position (inclusive of fee) for liquidity',
                description='Returns position (inclusive of fee) for the amount of liquidity',
                category='protocol',
                subcategory='uniswap-v2',
                input=UniswapV2LPQuantityInput,
                output=UniswapV2LPOutput)
class UniswapV2LPQuantity(Model):
    def run(self, input: UniswapV2LPQuantityInput) -> UniswapV2LPOutput:
        pool = input.pool
        lp_balance = input.lp_balance

        try:
            _ = pool.abi
        except ModelDataError:
            pool.set_abi(UNISWAP_V2_POOL_ABI)

        reserves = pool.functions.getReserves().call()
        lp_total_supply = pool.functions.totalSupply().call()

        token0_addr = pool.functions.token0().call()
        token1_addr = pool.functions.token1().call()

        try:
            token0 = Token(address=Address(token0_addr)
                           ).as_erc20(set_loaded=True)
            scaled_reserve0 = token0.scaled(reserves[0])
        except OverflowError:
            token0 = Token(address=Address(token0_addr)).as_erc20()
            scaled_reserve0 = token0.scaled(reserves[0])

        try:
            token1 = Token(address=Address(token1_addr)
                           ).as_erc20(set_loaded=True)
            scaled_reserve1 = token1.scaled(reserves[1])
        except OverflowError:
            token1 = Token(address=Address(token1_addr)).as_erc20()
            scaled_reserve1 = token1.scaled(reserves[1])

        if math.isclose(lp_balance, 0):
            return UniswapV2LPOutput(
                lp=Position(amount=lp_balance, asset=pool),
                tokens=[Position(amount=0, asset=token0), Position(amount=0, asset=token1)])

        lp_token0 = scaled_reserve0 * lp_balance / lp_total_supply
        lp_token1 = scaled_reserve1 * lp_balance / lp_total_supply

        lp_position = Position(amount=pool.scaled(lp_balance), asset=pool)
        position0 = Position(amount=lp_token0, asset=token0)
        position1 = Position(amount=lp_token1, asset=token1)

        out = UniswapV2LPOutput(lp=lp_position, tokens=[position0, position1])
        return out


@Model.describe(slug='uniswap-v2.lp',
                version='0.4',
                display_name='Uniswap v2 (SushiSwap) LP Position (inclusive of fee) for account',
                description='Returns position (inclusive of fee) for account',
                category='protocol',
                subcategory='uniswap-v2',
                input=UniswapV2LPInput,
                output=UniswapV2LPOutput)
class UniswapV2LP(Model):
    def run(self, input: UniswapV2LPInput) -> UniswapV2LPOutput:
        pool = input.pool
        lp = input.lp
        lp_balance = pool.functions.balanceOf(lp).call()

        return self.context.run_model(
            'uniswap-v2.lp-pos',
            input=UniswapV2LPQuantityInput(pool=input.pool, lp_balance=lp_balance),
            return_type=UniswapV2LPOutput)


# pylint: disable=invalid-name
def calculate_v2_fee(context, pool, lp, block_number, transaction_value,
                     lp_prev_token0, lp_prev_token1):

    # Get the amount of tokens for a given amount of LP tokens.
    lp_in_out = context.run_model(
        'uniswap-v2.lp-pos',
        input=UniswapV2LPQuantityInput(pool=pool, lp_balance=1e18),
        return_type=UniswapV2LPOutput,
        block_number=block_number)

    ratio = lp_in_out.tokens[1].amount / lp_in_out.tokens[0].amount

    # Position implied from previous LP position (without fee)
    token0_lp_current = (lp_prev_token0 * lp_prev_token1 / ratio) ** 0.5
    token1_lp_current = token0_lp_current * ratio

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
        in_out_amount0 = lp_in_out.tokens[0].amount * transaction_value / 1e18
        in_out_amount1 = lp_in_out.tokens[1].amount * transaction_value / 1e18
    else:
        in_out_amount0, in_out_amount1 = 0.0, 0.0

    # fee = With fee - Without fee - Just-in
    # 1. "With fee" uses end-of-block lp token holding to calculate - up-to-date
    # 2. "Without fee" uses previous end-of-block holding to calculate - up-to-date
    # 3. "Just in" is calculated from the current end-of-block's ratio,
    #    which may not be the original amount put in due to other swaps inside the block.
    return {
        'token0_lp': lp_pos_token0,
        'token1_lp':  lp_pos_token1,
        'in_out_amount0': try_zero(in_out_amount0),
        'in_out_amount1': try_zero(in_out_amount1),
        'token0_lp_current':  token0_lp_current,
        'token1_lp_current': token1_lp_current,
        'token0_fee': try_zero(lp_pos_token0 - token0_lp_current - in_out_amount0),
        'token1_fee': try_zero(lp_pos_token1 - token1_lp_current - in_out_amount1),
    }


def try_zero(flt):
    if math.isclose(flt, 0):
        return 0
    return flt


def uniswap_v2_fee_sample_data():
    _df_sample = pd.DataFrame(
        columns=['block_number', 'log_index', 'from_address',
                 'to_address', 'transaction_value'],
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


# pylint: disable=line-too-long
@Model.describe(slug='uniswap-v2.lp-fee-history',
                version='1.2',
                display_name='Uniswap v2 (SushiSwap) LP Position and Fee history for account',
                description='Returns LP Position and Fee history for account',
                category='protocol',
                subcategory='uniswap-v2',
                input=UniswapV2LPInput,
                output=Records)
class UniswapV2LPFeeHistory(Model):
    def run(self, input: UniswapV2LPInput) -> Records:
        pool = input.pool
        lp = input.lp

        try:
            _ = pool.abi
        except ModelDataError:
            pool.set_abi(UNISWAP_V2_POOL_ABI)

        token0 = Token(address=Address(pool.functions.token0().call()))
        token1 = Token(address=Address(pool.functions.token1().call()))
        token0 = token0.as_erc20(set_loaded=True)
        token1 = token1.as_erc20(set_loaded=True)

        with self.context.ledger.TokenBalance as q:
            q_cols = [q.TRANSACTION_HASH,
                      q.BLOCK_NUMBER,
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
            if len(df_ts) == 0:
                return _df

            return pd.concat(df_ts).drop_duplicates()

        def _use_model():
            return self.context.run_model('account.token-transfer',
                                          input={'address': lp,
                                                 'tokens': [pool.address]},
                                          return_type=Records).to_dataframe()

        # _df = _use_model().rename(columns={'value': 'transaction_value'})[q_cols]
        # _df.loc[1:, 'transaction_value'] = -1 * (_df.loc[0, 'transaction_value'])

        def _use_events():
            def _use_fetch_events():
                minted = pd.DataFrame(pool.fetch_events(
                    pool.events.Transfer,
                    argument_filters={'to': lp.checksum},
                    from_block=0,
                    to_block=self.context.block_number,
                    contract_address=pool.address.checksum))
                burnt = pd.DataFrame(pool.fetch_events(
                    pool.events.Transfer,
                    argument_filters={'from': lp.checksum},
                    from_block=0,
                    to_block=self.context.block_number,
                    contract_address=pool.address.checksum))
                if not minted.empty:
                    minted = minted.assign(
                        transactionHash=lambda r: r.transactionHash.apply(lambda x: x.hex()))
                if not burnt.empty:
                    burnt = burnt.assign(
                        transactionHash=lambda r: r.transactionHash.apply(lambda x: x.hex()))
                return minted, burnt

            def use_contract_events():
                assert pool.abi
                minted = self.context.run_model(
                    'contract.events',
                    ContractEventsInput(
                        address=pool.address,
                        event_name='Transfer',
                        event_abi=pool.abi.events.Transfer.raw_abi,
                        argument_filters={'to': str(lp.checksum)},
                        from_block=0),
                    return_type=ContractEventsOutput).records.to_dataframe()
                burnt = self.context.run_model(
                    'contract.events',
                    ContractEventsInput(
                        address=pool.address,
                        event_name='Transfer',
                        event_abi=pool.abi.events.Transfer.raw_abi,
                        argument_filters={'from': str(lp.checksum)},
                        from_block=0),
                    return_type=ContractEventsOutput).records.to_dataframe()
                return minted, burnt

            minted, burnt = use_contract_events()

            df_empty = pd.DataFrame(
                data=[],
                columns=['transactionHash', 'blockNumber', 'logIndex', 'from', 'to', 'value'])

            df_combined = (pd.concat(
                [minted.loc[:, ['transactionHash', 'blockNumber', 'logIndex', 'from', 'to', 'value']] if not minted.empty else df_empty,
                 (burnt.loc[:, ['transactionHash', 'blockNumber', 'logIndex', 'from', 'to', 'value']].assign(
                     value=lambda x: -x.value) if not burnt.empty else df_empty)
                 ])
                .sort_values(['blockNumber', 'logIndex'])
                .rename(columns={
                    'transactionHash': 'transaction_hash',
                    'blockNumber': 'block_number',
                    'logIndex': 'log_index',
                    'from': 'from_address',
                    'to': 'to_address',
                    'value': 'transaction_value'})
                .reset_index(drop=True))

            return df_combined

        # _df = _use_ledger()
        _df = _use_events()

        if _df.empty:
            return Records.from_dataframe(_df)

        if (_df["block_number"].tail(1) != int(self.context.block_number)).all():
            new_row = [('', int(self.context.block_number), -
                        1, input.lp, input.lp, 0)]
            _df = pd.concat(
                [_df, pd.DataFrame(new_row, columns=q_cols)]).reset_index(drop=True)

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
                       'in_out_amount0', 'in_out_amount1',
                       'token0_lp_current', 'token1_lp_current',
                       'token0_fee', 'token1_fee']:
                _df.loc[row_n, it] = try_zero(v2_fee[it])  # type: ignore

        return Records.from_dataframe(_df)


@Model.describe(slug='uniswap-v2.lp-fee',
                version='0.8',
                display_name='Uniswap v2 (SushiSwap) LP Position (split for fee) for account',
                description='Returns position (split for fee) for account. The fee is accumulated from last position change.',
                category='protocol',
                subcategory='uniswap-v2',
                input=UniswapV2LPInput,
                output=UniswapV2LPFeeOutput)
class UniswapV2LPFee(Model):
    def run(self, input: UniswapV2LPInput) -> UniswapV2LPFeeOutput:
        pool = input.pool
        lp = input.lp

        try:
            _ = pool.abi
        except ModelDataError:
            pool.set_abi(UNISWAP_V2_POOL_ABI)

        token0 = Token(address=Address(pool.functions.token0().call()))
        token1 = Token(address=Address(pool.functions.token1().call()))
        token0 = token0.as_erc20(set_loaded=True)
        token1 = token1.as_erc20(set_loaded=True)

        # Obtain the last 2 when the current block has mint/burn
        with self.context.ledger.TokenBalance as q:
            _df = q.select(
                aggregates=[
                    (q.TRANSACTION_VALUE.as_numeric().sum_(), 'sum_transaction_value')],
                order_by=q.BLOCK_NUMBER.desc(),
                where=(q.ADDRESS.eq(lp)
                        .and_(q.TOKEN_ADDRESS.eq(pool.address))
                       ),
                group_by=[q.BLOCK_NUMBER],
                bigint_cols=['sum_transaction_value', 'block_number'],
                limit=2
            ).to_dataframe()

        if _df.empty:
            return UniswapV2LPFeeOutput.zero(lp, token0, token1)

        prev_block_number = _df['block_number'].to_list()[0]
        prev_transaction_value = _df['sum_transaction_value'].to_list()[0]

        if prev_block_number == self.context.block_number:
            prev2_block_number = _df['block_number'].to_list()[1]
            lp_pos = self.context.run_model(
                'uniswap-v2.lp',
                input=UniswapV2LPInput(pool=input.pool, lp=input.lp),
                return_type=UniswapV2LPOutput,
                block_number=prev2_block_number)

            lp_prev_token0, lp_prev_token1 = lp_pos.tokens[0].amount, lp_pos.tokens[1].amount

            v2_fee = calculate_v2_fee(
                self.context, pool, lp, prev_block_number, prev_transaction_value,
                lp_prev_token0, lp_prev_token1)
        else:
            lp_pos = self.context.run_model(
                'uniswap-v2.lp',
                input=UniswapV2LPInput(pool=input.pool, lp=input.lp),
                return_type=UniswapV2LPOutput,
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

        return UniswapV2LPFeeOutput(lp=lp_position,
                                    tokens=[position0, position1])
