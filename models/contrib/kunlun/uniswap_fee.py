from datetime import datetime, timezone

import pandas as pd
from credmark.cmf.model import Model, ModelContext
from credmark.cmf.types import Address, BlockNumber, Contract, Token
from credmark.dto import DTO, DTOField


def get_dt(year: int, month: int, day: int, hour=0, minute=0, second=0, microsecond=0):
    """Get a datetime for date and time values"""
    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)


def get_block(in_dt: datetime):
    """Get the BlockNumber instance at or before the datetime timestamp."""
    return BlockNumber.from_timestamp(in_dt.replace(tzinfo=timezone.utc).timestamp())


class UniswapFeeInput(DTO):
    interval: int = DTOField(gt=0, description='Block interval to gather the fees')
    pool_address: Address = Address('0xcbcdf9626bc03e24f779434178a73a0b4bad62ed')


class UniswapFeeOutput(UniswapFeeInput):
    block_start: int
    block_end: int
    block_start_time: datetime
    block_end_time: datetime
    tx_number: int
    fee_rate: float
    total_fee: float
    total_tx_in_value: float
    total_tx_out_value: float

    @classmethod
    def default(cls, input: UniswapFeeInput):
        context = ModelContext.current_context()
        block_end = context.block_number
        block_start = context.block_number-input.interval
        return cls(**input.dict(),
                   block_start=block_start,
                   block_end=block_end,
                   block_start_time=BlockNumber(block_start).timestamp_datetime,
                   block_end_time=BlockNumber(block_end).timestamp_datetime,
                   tx_number=0,
                   fee_rate=0,
                   total_fee=0,
                   total_tx_in_value=0,
                   total_tx_out_value=0)


@Model.describe(slug='contrib.uniswap-fee',
                version='1.0',
                display_name='Calculate fee from swaps in Uniswap V3 pool',
                description="Ledger",
                input=UniswapFeeInput,
                output=UniswapFeeOutput)
class UniswapFee(Model):

    def run(self, input: UniswapFeeInput) -> UniswapFeeOutput:
        # pylint:disable=invalid-name
        uni_pool_addr = input.pool_address
        univ3_btcweth_pool = Contract(address=uni_pool_addr)
        t0 = Token(address=univ3_btcweth_pool.functions.token0().call())
        t1 = Token(address=univ3_btcweth_pool.functions.token1().call())
        t0_addr = t0.address
        t1_addr = t1.address
        fee = univ3_btcweth_pool.functions.fee().call()

        # get block numbers on the dates
        block_end = self.context.block_number
        block_start = block_end - input.interval

        # Query the ledger for the token transfers
        with self.context.ledger.TokenBalance as q:
            df_tx = q.select(
                columns=[q.BLOCK_NUMBER,
                         q.TOKEN_ADDRESS,
                         q.TRANSACTION_HASH,
                         q.FROM_ADDRESS,
                         q.TO_ADDRESS,
                         q.TRANSACTION_VALUE],
                where=(q.BLOCK_NUMBER.gt(block_start).and_(q.BLOCK_NUMBER.le(block_end))
                       .and_(q.ADDRESS.eq(uni_pool_addr))),
                order_by=q.BLOCK_NUMBER
            ).to_dataframe()

        if df_tx.empty:
            return UniswapFeeOutput.default(input)

        df_tx_total = df_tx.query('token_address in [@t0_addr, @t1_addr]')

        # Only keep those swap transactions
        df_groupby_hash = (df_tx_total.groupby('transaction_hash', as_index=False)
                           .token_address.count())
        _df_tx_non_swap = (df_tx_total.merge(
            df_groupby_hash.loc[(df_groupby_hash.token_address != 2), :],
            on='transaction_hash',
            how='inner'))

        # Use the swap transactions hashes to filter all transactions
        df_tx_swap = df_tx_total.merge(df_groupby_hash.loc[(
            df_groupby_hash.token_address == 2), ['transaction_hash']], how='inner')

        self.logger.info(f'{df_tx_swap.shape, df_tx_swap.block_number.min(), df_tx_swap.block_number.max()}')
        # Summarize the swap transaction from two rows to one row
        full_tx = []
        for dfg, df in df_tx_swap.groupby('transaction_hash', as_index=False):
            assert df.shape[0] == 2
            if df.transaction_value.product() < 0:
                t0_amount = t0.scaled(df.loc[df.token_address == t0_addr,
                                             'transaction_value'].to_list()[0])  # type: ignore
                t1_amount = t1.scaled(df.loc[df.token_address == t1_addr,
                                             'transaction_value'].to_list()[0])  # type: ignore
                if df.to_address.to_list()[0] == uni_pool_addr:
                    full_tx.append((dfg, df.block_number.to_list()[0],
                                    df.from_address.to_list()[0], df.to_address.to_list()[1],
                                    t0_amount, t1_amount, t1_amount / t0_amount))
                elif df.to_address.to_list()[1] == uni_pool_addr:
                    full_tx.append((dfg, df.block_number.to_list()[0],
                                    df.from_address.to_list()[1], df.to_address.to_list()[0],
                                    t0_amount, t1_amount, t1_amount / t0_amount))
                else:
                    raise ValueError('Cannot match tradeas\' from and to')

        df_tx_swap_one_line = pd.DataFrame(full_tx,
                                           columns=['transaction_hash',
                                                    'block_number',
                                                    'from', 'to',
                                                    't0_amount', 't1_amount',
                                                    't1/t0'])

        # Fee model: take the incoming amount's X.X% from pool's fee value.
        # TODO: my rough idea of how the fee is collected. I might be wrong.

        def calculate_fee(r, models, t0, t1, fee):
            t0_price = models(r['block_number']).price.quote(base=t0)['price']
            t1_price = models(r['block_number']).price.quote(base=t1)['price']
            if r['t0_amount'] > 0:
                in_value = t0_price * r['t0_amount']
                out_value = t1_price * r['t1_amount']
            else:
                in_value = t1_price * r['t1_amount']
                out_value = t0_price * r['t0_amount']
            return in_value, out_value, in_value / (1 + fee / 1_000_000) * fee / 1_000_000

        df_new_cols = df_tx_swap_one_line.apply(
            lambda r, self=self, t0=t0, t1=t1, fee=fee:
            calculate_fee(r, self.context.models, t0, t1, fee), axis=1, result_type='expand')

        df_new_cols.columns = pd.Index(['in_value', 'out_value', 'fee'])

        df_tx_swap_one_line = pd.concat([df_tx_swap_one_line, df_new_cols], axis=1)

        df_tx_swap_one_line.in_value.sum()

        output = UniswapFeeOutput.default(input)
        output.tx_number = df_tx_swap_one_line.shape[0]
        output.fee_rate = fee
        output.total_fee = df_tx_swap_one_line.fee.sum()
        output.total_tx_in_value = df_tx_swap_one_line.in_value.sum()
        output.total_tx_out_value = df_tx_swap_one_line.out_value.sum()

        return output
