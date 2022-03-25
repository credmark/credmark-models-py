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
from credmark.dto import DTO

import pandas as pd


class ValueAtRiskBase(credmark.model.Model):
    def eod_block(self, dt):
        dt_eod = datetime.combine(dt, datetime.max.time(), tzinfo=timezone.utc)
        return self.context.block_number.from_timestamp(int(dt_eod.timestamp()))

    def set_window(self, input):
        current_block = self.context.block_number
        current_block_date = self.context.block_number.to_datetime().date()
        if input.asOfs:
            min_date = min(input.asOfs)
            max_date = max(input.asOfs)

            if max_date >= current_block_date:
                raise ModelRunError(
                    (f'max(input.asOf)={max_date:%Y-%m-%d} shall be earlier than the input block, '
                     f'{current_block} on {current_block_date:%Y-%m-%d}.'))

            if input.asOf_is_range:
                asOfs = [dt.to_pydatetime().replace(tzinfo=timezone.utc)
                         for dt in pd.date_range(min_date, max_date)][::-1]
            else:
                asOfs = input.asOfs
        else:
            min_date = current_block_date - timedelta(days=1)
            max_date = min_date
            asOfs = [min_date]

        window = input.window

        # FIXME: pending for time range fix
        # current_to_asOf_range = f'{(current_block_date - max_date).days} days'
        # window_from_current = [..., current_to_asOf_range]
        if min_date == max_date:
            window_from_max_asOf = [window]
        else:
            asOf_range = f'{(max_date - min_date).days} days'
            window_from_max_asOf = [window, asOf_range]

        block_max_asOf = self.eod_block(max_date)
        self.logger.info(
            f'{min_date=:%Y-%m-%d} {max_date=:%Y-%m-%d} {input.asOfs=} {current_block_date=:%Y-%m-%d} {window_from_max_asOf=} {block_max_asOf=}')

        return {
            'asOfs': asOfs,
            'block_max_asOf': block_max_asOf,
            'window_from_max_asOf': window_from_max_asOf,
        }

    @abstractmethod
    def run(self, input: Union[dict, DTO]) -> Union[dict, DTO]:
        return super().run(input)
