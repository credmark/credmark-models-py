from abc import abstractmethod
from typing import (
    Union
)
from datetime import (
    datetime,
    timezone,
    timedelta,
)
from credmark.cmf.model import Model
from credmark.cmf.model.errors import (
    ModelRunError
)
from credmark.dto import (
    DTO,
)

import pandas as pd
import numpy as np

from .plan import (
    BlockFromTimePlan,
)


class ValueAtRiskBase(Model):
    def eod_block(self, dt_input: datetime, verbose=False) -> dict:
        block_plan = BlockFromTimePlan(tag='eod',
                                       target_key=f'BlockFromEODPlan.{dt_input}',
                                       use_kitchen=True,
                                       context=self.context,
                                       verbose=verbose,
                                       date=dt_input)
        result = block_plan.execute()
        result['datetime'] = datetime.fromtimestamp(result['timestamp'], tz=timezone.utc)
        return result

    def save_mkt_and_dict(self, mkt, dict_of_df, fp_out):
        with pd.ExcelWriter(fp_out, engine='xlsxwriter') as writer:  # pylint: disable=abstract-class-instantiated
            for (tag, k), v in mkt.items():
                if isinstance(v, dict):
                    for vk, vv in v.items():
                        s_name = f'{tag}.{k[:31-len(tag)-1-len(vk)-1]}_{vk}'
                        if isinstance(vv, pd.DataFrame):
                            dt_cols = vv.select_dtypes(include=['datetime64[ns, UTC]']).columns
                            for dt_col in dt_cols:
                                vv[dt_col] = (pd.to_datetime(vv[dt_col], unit='ms',
                                              utc=True).dt.to_pydatetime().replace(tzinfo=None))
                            vv.to_excel(writer, sheet_name=s_name, index=False)
                        elif isinstance(vv, pd.Series):
                            vv.to_excel(writer, sheet_name=s_name, index=False)
                        elif isinstance(vv, np.ndarray):
                            pd.DataFrame(vv).to_excel(writer, sheet_name=s_name, index=False)
                        else:
                            raise ModelRunError(f'Unknown sub-type {type(vv)=} {vv=}')
                else:
                    raise ModelRunError(f'Unknown type {type(v)=} {v=}')

            for vk, vv in dict_of_df.items():
                s_name = vk[:31]
                if isinstance(vv, pd.DataFrame):
                    dt_cols = vv.select_dtypes(include=['datetime64[ns, UTC]']).columns
                    for dt_col in dt_cols:
                        vv[dt_col] = (pd.to_datetime(vv[dt_col], unit='ms')
                                      .dt.to_pydatetime().replace(tzinfo=None))
                    if isinstance(vv.columns, pd.MultiIndex):
                        vv.to_excel(writer, sheet_name=s_name)
                    else:
                        vv.to_excel(writer, sheet_name=s_name, index=False)
                elif isinstance(vv, pd.Series):
                    vv.to_excel(writer, sheet_name=s_name, index=False)
                elif isinstance(vv, np.ndarray):
                    pd.DataFrame(vv).to_excel(writer, sheet_name=s_name, index=False)
                else:
                    raise ModelRunError(f'Unknown sub-type {type(vv)=} {vv=}')

    def set_window(self, input):
        current_block = self.context.block_number
        current_block_date = self.context.block_number.timestamp_datetime.date()
        if input.as_ofs:
            min_date = min(input.as_ofs)
            max_date = max(input.as_ofs)

            if max_date >= current_block_date:
                raise ModelRunError(
                    (f'max(input.as_of)={max_date:%Y-%m-%d} shall be earlier than the input block, '
                     f'{current_block} on {current_block_date:%Y-%m-%d}.'))

            if input.as_of_is_range:
                as_ofs = [dt.to_pydatetime().replace(tzinfo=timezone.utc)
                          for dt in pd.date_range(min_date, max_date)]
            else:
                as_ofs = input.as_ofs
        else:
            min_date = current_block_date - timedelta(days=1)
            max_date = min_date
            as_ofs = [min_date]

        window = input.window

        # TODO: pending for time range fix
        # current_to_as_of_range = f'{(current_block_date - max_date).days} days'
        # window_from_current = [..., current_to_as_of_range]
        if min_date == max_date:
            window_from_max_as_of = [window]
        else:
            as_of_range = f'{(max_date - min_date).days} days'
            window_from_max_as_of = [window, as_of_range]

        max_as_of_eod = self.eod_block(max_date, input.verbose)
        self.logger.info(
            f'{min_date=:%Y-%m-%d} {max_date=:%Y-%m-%d} {input.as_ofs=} '
            f'{current_block_date=:%Y-%m-%d} {window_from_max_as_of=} '
            f'{max_as_of_eod["block_number"]=}/{max_as_of_eod["timestamp"]=}')

        return {
            'as_ofs': as_ofs,
            'block_max_as_of': max_as_of_eod['block_number'],
            'timestamp_max_as_of': max_as_of_eod['timestamp'],
            'window_from_max_as_of': window_from_max_as_of,
            'min_date': min_date,
            'max_date': max_date,
        }

    def res_to_df(self, var_result):
        res_arr = []
        for as_of, v1 in var_result.items():
            for interval, v2 in v1.items():
                for confidence, var in v2.items():
                    res_arr.append((as_of, interval, confidence, var))

        df_res = pd.DataFrame(res_arr, columns=['as_of', 'interval', 'confidence', 'var'])
        df_res.loc[:, 'interval'] = df_res.interval.apply(
            self.context.historical.parse_timerangestr)
        df_res_p = (df_res.pivot(index=['as_of'],
                                 columns=['confidence', 'interval'],
                                 values='var')
                    .sort_values('as_of', ascending=False)
                    .sort_index(axis=1)
                    .reset_index(drop=False))
        return df_res_p

    @ abstractmethod
    def run(self, input: Union[dict, DTO]) -> Union[dict, DTO]:
        return super().run(input)
