from abc import abstractmethod
from typing import (
    Union
)
from datetime import (
    datetime,
    timezone,
    timedelta,
)
import credmark.model
from credmark.model import (
    ModelRunError
)
from credmark.dto import (
    DTO,
    EmptyInput,
)

import pandas as pd


@credmark.model.describe(slug='finance.get-one',
                         version='1.0',
                         display_name='Get Block History',
                         description='Get Block History',
                         output=dict)
class GetBlockHistory(credmark.model.Model):
    # TODO: better integrate with history_utils to only retrieve the list of block numbers/timestamp
    """
    We are only interested in past block numbers
    """

    def run(self, input: EmptyInput) -> dict:
        return {'x': 1}


class ValueAtRiskBase(credmark.model.Model):
    def eod_block(self, dt_input):
        dt_eod = datetime.combine(dt_input, datetime.max.time(), tzinfo=timezone.utc)
        eod_time_stamp = int(dt_eod.timestamp())
        eod_block = self.context.block_number.from_timestamp(eod_time_stamp)
        return {'block': eod_block,
                'timestamp': eod_time_stamp, }

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
                          for dt in pd.date_range(min_date, max_date)][::-1]
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

        max_as_of_eod = self.eod_block(max_date)
        self.logger.info(
            f'{min_date=:%Y-%m-%d} {max_date=:%Y-%m-%d} {input.as_ofs=} '
            f'{current_block_date=:%Y-%m-%d} {window_from_max_as_of=} '
            f'{max_as_of_eod["block"]=}/{max_as_of_eod["timestamp"]=}')

        return {
            'as_ofs': as_ofs,
            'block_max_as_of': max_as_of_eod['block'],
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
