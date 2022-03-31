# from typing import (
#     List,
#     Optional,
#     Dict,
#     Union,
# )

# from datetime import (
#     datetime,
#     timezone,
#     date,
# )

# from credmark.cmf.model import Model
# from credmark.cmf.model.errors import ModelRunError

# from credmark.dto import (
#     DTO,
#     DTOField,
# )

# from credmark.cmf.types import (
#     Portfolio,
#     Price,
#     Address,
# )

# from models.credmark.algorithms.risk import calc_var

# import numpy as np
# import pandas as pd


# class PriceList(DTO):
#     price: Price
#     token: Address


# class VaRInput(DTO):
#     # block_number: int
#     portfolio: Portfolio
#     window: str
#     intervals: List[str] = DTOField(...)
#     confidences: List[float] = DTOField(..., ge=0.0, le=1.0)  # accepts multiple values
#     asOfs: Optional[List[date]]
#     asOfsRange: Optional[bool] = DTOField(False)
#     debug: Optional[bool] = DTOField(False)

#     class Config:
#         validate_assignment = True


# class VaROutput(DTO):
#     window: str
#     # asOf/interval/confidence -> var
#     var: Dict[str, Dict[str, Dict[float, float]]]


# @Model.describe(slug='finance.var',
#                          version='1.0',
#                          display_name='Value at Risk',
#                          description='Value at Risk',
#                          input=VaRInput,
#                          output=VaROutput)
# class ValueAtRisk(Model):
#     def get_block_index(self):
#         data = []
#         for x in range(int(12e6), 14378699):
#             ts = self.context.web3.eth.get_block(x).timestamp
#             dt = datetime.fromtimestamp(ts, timezone.utc)
#             data.append((x, ts, dt))
#             if x // 1e5 == 0:
#                 self.logger.info(data[-1])
#         df = pd.DataFrame(data, columns=['block_number', 'timestamp', 'dt'])
#         return df

#     def get_history_price(self, token, starting_block):
#         data = []
#         for x in range(260):
#             block_past = starting_block-6500*x
#             price = self.context.run_model('uniswap-v3.get-average-price',
#                                            input=token,
#                                            block_number=block_past)
#             ts = self.context.web3.eth.get_block(block_past).timestamp
#             dt = datetime.fromtimestamp(ts, timezone.utc)
#             data.append([(block_past, price['price'], ts, dt)])
#         return data

#     def get_block_number_of_date(self, dt_in: Union[datetime, date]):
#         txn_blocks = self.context.ledger.Block.Columns
#         dt = datetime(dt_in.year, dt_in.month, dt_in.day, tzinfo=timezone.utc)
#         result = self.context.ledger.get_blocks(
#             [txn_blocks.TIMESTAMP, txn_blocks.NUMBER],
#             where=f"{txn_blocks.TIMESTAMP} >= {int(dt.timestamp())}",
#             order_by=f'{txn_blocks.TIMESTAMP} ASC',
#             limit='1')

#         rows = result.data
#         block_hist = rows[0].get(txn_blocks.NUMBER) if len(rows) else None

#         return block_hist

#     def get_date_of_block(self, block_hist: int):
#         txn_blocks = self.context.ledger.Block.Columns
#         result = self.context.ledger.get_blocks(
#             [txn_blocks.TIMESTAMP, txn_blocks.NUMBER],
#             where=f"{txn_blocks.NUMBER} = {int(block_hist)}",
#             order_by=f'{txn_blocks.TIMESTAMP} ASC',
#             limit='1')
#         rows = result.data
#         timestamp = rows[0].get(txn_blocks.TIMESTAMP) if len(rows) else None
#         if timestamp:
#             dt = datetime.fromtimestamp(timestamp, timezone.utc).date()
#         else:
#             raise ModelRunError(f'Can not get the timestamp for block={block_hist}')

#         return dt

#     def run(self, input: VaRInput) -> VaROutput:
#         """
#             Var takes in a portfolio object,
#             a price window, and
#             some intervals/confidences/asOfs
#             default value for asOf is the date of the input block.

#             It calculates the usd value of the portfolio for each of the blockstamps/timestamps.
#             It then calculates the change in value over the window period for each timestamp,
#             it returns the one that hits the input confidence levels.
#         """

#         current_block = self.context.block_number
#         if input.asOfs:
#             min_date = min(input.asOfs)
#             max_date = max(input.asOfs)
#             if input.asOfsRange:
#                 asOfs = [dt.to_pydatetime()  # .replace(tzinfo=timezone.utc)
#                          for dt in pd.date_range(min_date, max_date)]
#             else:
#                 asOfs = input.asOfs
#             block_hist = self.get_block_number_of_date(max_date)

#             if not block_hist:
#                 block_time = self.get_date_of_block(current_block)
#                 raise ModelRunError(
#                     (f'max(input.asOf)={max_date:%Y-%m-%d} is later than input block timestamp, '
#                      f'{current_block} on {block_time:%Y-%m-%d}.'))
#         else:
#             block_hist = current_block
#             min_date = self.get_date_of_block(block_hist)
#             max_date = min_date
#             asOfs = [min_date]

#         self.logger.info(
#             f'{min_date=:%Y-%m-%d} {max_date=:%Y-%m-%d} {input.asOfs=} {block_hist=}')

#         window = input.window
#         w_k, w_i = self.context.historical.parse_timerangestr(window)
#         w_seconds = self.context.historical.range_timestamp(w_k, w_i)

#         if min_date == max_date:
#             new_window = [window]
#         else:
#             asOf_range = f'{(max_date - min_date).days} days'
#             new_window = [asOf_range, window]

#         parsed_intervals = [
#             self.context.historical.parse_timerangestr(ii) for ii in input.intervals]
#         interval_keys, interval_nums = zip(*parsed_intervals)
#         unique_ivl_keys = list(set(interval_keys))
#         if unique_ivl_keys.__len__() != 1:
#             raise ModelRunError(
#                 f'There is more than one type of interval in input intervals={input.intervals}')

#         minimal_interval = f'1 {unique_ivl_keys[0]}'

#         df_hist = pd.DataFrame()
#         key_cols = []

#         for pos in input.portfolio.positions:
#             if not pos.token.address:
#                 raise ModelRunError(f'Input position is invalid, {input}')

#             key_col = (pos.token.address, pos.token.symbol)
#             if key_col in df_hist:
#                 continue

#             historical = self.context.run_model(
#                 'uniswap-v3.get-historical-price',
#                 input={
#                     'token': pos.token,
#                     'window': new_window,
#                     'interval': minimal_interval,
#                 },
#                 block_number=block_hist)

#             for p in historical['series']:
#                 p['price'] = p['output']['price']
#                 del p['output']

#             df_tk = (pd.DataFrame(historical['series'])
#                      .sort_values(['blockNumber'], ascending=False)
#                      .rename(columns={'price': key_col})
#                        .reset_index(drop=True))

#             df_tk.loc[:, 'blockTime'] = df_tk.blockTimestamp.apply(
#                 lambda x: datetime.fromtimestamp(x, timezone.utc))
#             df_tk.loc[:, 'sampleTime'] = df_tk.sampleTimestamp.apply(
#                 lambda x: datetime.fromtimestamp(x, timezone.utc))

#             if df_hist.empty:
#                 df_hist = df_tk
#             else:
#                 df_hist = df_hist.merge(df_tk, on=['blockNumber',
#                                                    'blockTimestamp',
#                                                    'sampleTimestamp',
#                                                    'blockTime',
#                                                    'sampleTime'], how='outer')
#                 for col in df_hist.columns:
#                     assert df_hist.loc[:, col].isnull().sum() == 0

#             key_cols.append(key_col)
#             if input.debug:
#                 self.logger.info(df_hist)
#                 df_hist.to_csv('df_hist.csv', index=False)

#         var = {}
#         res_arr = []
#         for asOf in asOfs:
#             asOf_str = asOf.strftime('%Y-%m-%d')
#             var[asOf_str] = {}
#             asOf_last = datetime(asOf.year, asOf.month, asOf.day,
#                                  23, 59, 59, tzinfo=timezone.utc)
#             idx_last = df_hist.index.get_loc(
#                 df_hist.index[df_hist['blockTime'] <= asOf_last][0])  # type: ignore
#             df_current = df_hist.loc[:, key_cols].iloc[idx_last, :]
#             dict_current = df_current.to_dict()

#             for ivl_k, ivl_n, ivl_str in zip(interval_keys, interval_nums, input.intervals):
#                 ivl_seconds = self.context.historical.range_timestamp(
#                     ivl_k, ivl_n)  # type: ignore
#                 n_ivl = int(np.floor(w_seconds / ivl_seconds))

#                 df_hist_ivl = df_hist.iloc[idx_last:(idx_last+n_ivl):ivl_n].copy()  # type: ignore

#                 df_hist_ivl_p_only = df_hist_ivl.loc[:, key_cols]

#                 df_ret = df_hist_ivl_p_only.iloc[:-1, :].reset_index(drop=True) / \
#                     df_hist_ivl_p_only.iloc[1:, :].reset_index(drop=True)

#                 df_ret = df_ret.apply(lambda x: x - 1)

#                 var[asOf_str][ivl_str] = {}
#                 df_value = pd.DataFrame()
#                 for pos in input.portfolio.positions:
#                     key_col = (pos.token.address, pos.token.symbol)
#                     ret = df_ret[key_col].to_numpy()
#                     current_value = pos.amount * dict_current[key_col]
#                     value_changes = ret * current_value
#                     if key_col not in df_value:
#                         df_value.insert(0, (key_col), value_changes)
#                     else:
#                         df_value[key_col] += value_changes
#                 ppl = df_value.sum(axis=1).to_numpy()

#                 for conf in input.confidences:
#                     v = calc_var(ppl, conf)
#                     var[asOf_str][ivl_str][conf] = v
#                     res_arr.append((ivl_str, conf, asOf_str, v))

#                 if input.debug:
#                     df_current.to_csv('df_current.csv')
#                     df_hist_ivl.to_csv('df_hist_ivl.csv')
#                     df_ret.to_csv('df_ret.csv')

#         result = VaROutput(window=window, var=var)

#         df_res = (pd.DataFrame(res_arr, columns=['asOf', 'interval', 'confidence', 'var'])
#                     .sort_values(by=['interval', 'confidence', 'asOf', 'var'],
#                                  ascending=[True, True, False, True]))
#         df_res.to_csv('df_res.csv')

#         return result
