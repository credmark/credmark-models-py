from typing import (
    List,
    Tuple,
    Optional,
    Dict,
)

from datetime import datetime, timezone, date

import credmark.model

from credmark.model import ModelRunError

from credmark.types.dto import (
    DTO,
    DTOField,
)

from credmark.types import (
    Portfolio,
    Price,
    Address,
    BlockNumber,
    BlockSeries,
)

import numpy as np
import pandas as pd


class PriceList(DTO):
    price: Price
    token: Address


class VaRInput(DTO):
    # block_number: int
    portfolio: Portfolio
    windows: List[str]
    intervals: List[str] = DTOField(...)
    confidences: List[float] = DTOField(..., gt=0.0, lt=1.0)  # accepts multiple values
    asOf: Optional[date]
    outputPrice: Optional[bool] = DTOField(False)
    debug: Optional[bool] = DTOField(False)

    class Config:
        validate_assignment = True


class VaROutput(DTO):
    asOf: str
    var: Dict[str, Dict[str, Dict[float, float]]]


CREDMARK_ADDRESS = "0x68CFb82Eacb9f198d508B514d898a403c449533E"


@credmark.model.describe(slug='finance.var',
                         version='1.0',
                         display_name='Value at Risk',
                         description='Value at Risk',
                         input=VaRInput,
                         output=VaROutput)
class ValueAtRisk(credmark.model.Model):
    @staticmethod
    def calc_var(ppl, lvl):
        ppl_d = ppl.copy()
        ppl_d.sort()
        len_ppl_d = ppl_d.shape[0]
        pos_f = lvl * (len_ppl_d - 1)
        lower = int(np.floor(pos_f))
        upper = int(np.ceil(pos_f))
        return ppl_d[lower] * (upper - pos_f) + ppl_d[upper] * (pos_f - lower)

    def run(self, input: VaRInput) -> VaROutput:
        """
            Var takes in a portfolio object,
            a list of prices per token into the past,
            a price window,
            and a worst case percentage.

            It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
            It then calculates the change in value over the window period for each timestamp,
            it returns the one that hits the input percentage.
        """

        # 2021 Jun 21st
        # 10 day.

        txn_blocks = self.context.ledger.Block.Columns

        if input.asOf:
            dt = datetime(input.asOf.year, input.asOf.month, input.asOf.day, tzinfo=timezone.utc)

            result = self.context.ledger.get_blocks(
                [txn_blocks.TIMESTAMP, txn_blocks.NUMBER],
                where=f"{txn_blocks.TIMESTAMP} >= {int(dt.timestamp())}",
                order_by=f'{txn_blocks.TIMESTAMP} ASC',
                limit='1')

            rows = result.data
            block_hist = rows[0].get(txn_blocks.NUMBER) if len(rows) else None
            print('rows', rows, input.asOf, block_hist)
        else:
            block_hist = self.context.block_number

            result = self.context.ledger.get_blocks(
                [txn_blocks.TIMESTAMP, txn_blocks.NUMBER],
                where=f"{txn_blocks.NUMBER} = {int(block_hist)}",
                order_by=f'{txn_blocks.TIMESTAMP} ASC',
                limit='1')

            rows = result.data
            timestamp = rows[0].get(txn_blocks.TIMESTAMP) if len(rows) else None
            if timestamp:
                input.asOf = datetime.fromtimestamp(timestamp, timezone.utc).date()
            else:
                raise ModelRunError(f'Can not get the timestamp for block={block_hist}')
            print('rows', rows, input.asOf, block_hist)

        var = {}

        for window in input.windows:
            var[window] = {}

            _ = self.context.historical.parse_timerangestr(window)
            parsed_intervals = [
                self.context.historical.parse_timerangestr(ii) for ii in input.intervals]
            interval_keys, interval_nums = zip(*parsed_intervals)
            unique_keys = list(set(interval_keys))
            if unique_keys.__len__() != 1:
                raise ModelRunError(
                    f'There is more than one type of interval in input intervals={input.intervals}')

            minimal_interval = f'1 {unique_keys[0]}'

            df_ret = pd.DataFrame()
            dict_price = {}
            dict_hist = {}
            dict_ret = {}
            for pos in input.portfolio.positions:
                if pos.token.symbol in df_ret:
                    continue

                if not pos.token.symbol:
                    raise ModelRunError(f'Input position is invalid, {input}')

                data = []
                for x in range(int(12e6), 14378699):
                    ts = self.context.web3.eth.get_block(x).timestamp
                    dt = datetime.fromtimestamp(ts, timezone.utc)
                    data.append((x, ts, dt))
                    if x // 1e5 == 0:
                        print(data[-1])
                df = pd.DataFrame(data, columns=['block_number', 'timestamp', 'dt'])
                df.to_pickle('block_index_12m_14m.pkl.gz')
                breakpoint()

                data = []
                for x in range(260):
                    block_past = block_hist-6500*x
                    price = self.context.run_model('uniswap-v3.get-average-price',
                                                   input=pos.token, block_number=block_past)
                    ts = self.context.web3.eth.get_block(block_past).timestamp
                    dt = datetime.fromtimestamp(ts, timezone.utc)
                    data.append([(block_past, price['price'], ts, dt)])

                breakpoint()

                df_hist.loc[:, 'blockTime'] = df_hist.blockTimestamp.apply(
                    lambda x: datetime.fromtimestamp(x, timezone.utc).date())
                df_hist.loc[:, 'sampleTime'] = df_hist.sampleTimestamp.apply(
                    lambda x: datetime.fromtimestamp(x, timezone.utc).date())

                ret = df_hist.price[:-1].to_numpy() / df_hist.price[1:].to_numpy()

                df_ret.loc[:, pos.token.symbol] = ret

                # The last block_number in df may not equal to the input block_number.
                # specify block_number=df.blockNumber.max() with run_model() to get the match price.
                current = self.context.run_model(
                    'price', pos.token, return_type=Price, block_number=block_hist)

                dict_price[pos.token.symbol] = current.price

                dict_hist[window] = df_hist
                dict_ret[window] = df_ret
                if input.debug:
                    print(df_hist)
                    print(df_ret)

            for ivl, ivl_str in zip(interval_nums, input.intervals):
                var[window][ivl_str] = {}
                df_ret_n = df_ret.copy().rolling(ivl).agg(lambda x: x.prod()) - 1
                # assert np.all(df_ret.copy().rolling(1).agg(lambda x : x.prod()) == df_ret.copy())
                for conf in input.confidences:
                    df_value = pd.DataFrame()
                    for pos in input.portfolio.positions:
                        ret = df_ret_n[pos.token.symbol]
                        current_value = pos.amount * dict_price[pos.token.symbol]
                        value_changes = ret * current_value
                        if pos.token.symbol not in df_value:
                            df_value.loc[:, pos.token.symbol] = value_changes
                        else:
                            df_value.loc[:, pos.token.symbol] += value_changes
                    ppl = df_value.sum(axis=1).to_numpy()
                    var[window][ivl_str][conf] = self.calc_var(ppl, conf)

        result = VaROutput(asOf=input.asOf.strftime('%Y-%m-%d'), var=var)

        return result
