from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError

from credmark.dto import (
    EmptyInput,
)

from credmark.cmf.types import (
    Contract,
)


from models.credmark.protocols.lending.compound.compound_v2 import (
    CompoundV2PoolValues,
    CompoundV2PoolInfos,
)

from models.credmark.algorithms.risk import (
    HistoricalBlockPlan,
    GeneralHistoricalPlan,
    kitchen,
)

import os
from datetime import (
    date,
    datetime,
    timezone,
)
import pandas as pd
import numpy as np


@Model.describe(slug="compound-v2.all-pools-values-historical-plan",
                version="1.0",
                display_name="Compound pools value history",
                description="Compound pools value history",
                input=EmptyInput,
                output=None)
class CompoundV2AllPoolsValueHistoricalPlan(Model):
    def run(self, input: EmptyInput) -> None:
        start_dt = datetime.combine(date(2020, 6, 15),
                                    datetime.max.time(),
                                    tzinfo=timezone.utc)
        end_dt = self.context.block_number.timestamp_datetime

        start_dt = datetime.combine(date(2021, 9, 28),
                                    datetime.max.time(),
                                    tzinfo=timezone.utc)
        end_dt = datetime.combine(date(2021, 10, 2),
                                  datetime.max.time(),
                                  tzinfo=timezone.utc)

        interval = (end_dt - start_dt).days

        window = f'{interval} days'
        interval = '1 day'
        use_kitchen = True
        verbose = True
        dev_mode = False

        block_plan = HistoricalBlockPlan(
            tag='eod',
            target_key=f'HistoricalBlock.{end_dt}.{window}.{interval}',
            use_kitchen=use_kitchen,
            context=self.context,
            verbose=verbose,
            as_of=end_dt,
            window=window,
            interval=interval)

        pre_plan_results = block_plan.execute()

        block_numbers = pre_plan_results['block_numbers']
        block_table = pre_plan_results['block_table']

        reset_cache_value = False

        token_series = {}
        for block_number in sorted(block_numbers):
            block_time = block_table.query('blockNumber == @block_number')['blockTime'].to_list()[0]
            self.logger.info(f'{block_time=}')

            comptroller_plan = GeneralHistoricalPlan(
                tag='eod',
                target_key=f'CompoundComptrollerHistoricalPlan.{block_number}',
                name='compound-v2.get-comptroller',
                use_kitchen=use_kitchen,
                chef_return_type=Contract,
                plan_return_type=Contract,
                context=self.context,
                verbose=verbose,
                method='run_model',
                slug='compound-v2.get-comptroller',
                block_number=block_number,
                input_keys=[],
            )
            comptroller = comptroller_plan.execute()

            if 'comptroller' not in token_series:
                token_series['comptroller'] = block_table.copy()
            table_to_fill = token_series['comptroller']
            table_to_fill.loc[table_to_fill.blockNumber == block_number,
                              'comptroller'] = comptroller.address

            value_plan = GeneralHistoricalPlan(
                tag='eod',
                target_key=f'CompoundInfoHistoricalPlan.{block_number}',
                name='compound-v2.all-pools-info',
                use_kitchen=use_kitchen,
                chef_return_type=CompoundV2PoolInfos,
                plan_return_type=CompoundV2PoolInfos,
                context=self.context,
                verbose=verbose,
                method='run_model',
                slug='compound-v2.all-pools-info',
                block_number=block_number,
                input_keys=[],
            )
            pool_infos = value_plan.execute()

            if dev_mode:
                ts_str = f'{self.context.block_number.timestamp_datetime:%Y%m%d_%H%M%S}'
                pd.DataFrame(pool_infos.dict()['infos']).to_excel(
                    f'compound_infos_{ts_str}.xlsx')

            value_plan = GeneralHistoricalPlan(
                tag='eod',
                target_key=f'CompoundValueHistoricalPlan.{block_number}',
                name='compound-v2.all-pools-values',
                use_kitchen=use_kitchen,
                chef_return_type=CompoundV2PoolValues,
                plan_return_type=CompoundV2PoolValues,
                context=self.context,
                verbose=verbose,
                reset_cache=reset_cache_value,
                method='run_model',
                slug='compound-v2.all-pools-values',
                input=pool_infos,
                block_number=block_number,
                input_keys=[pl.cToken.address for pl in pool_infos]
            )
            reset_cache_value = False
            pool_values = value_plan.execute()

            if dev_mode:
                ts_str = f'{self.context.block_number.timestamp_datetime:%Y%m%d_%H%M%S}'
                pd.DataFrame(pool_infos.dict()['values']).to_excel(
                    f'compound_value_{ts_str}.xlsx')

            if 'total' not in token_series:
                token_series['total'] = block_table.copy()

            df_values = pd.DataFrame(pool_values.dict()['values'])
            df_values.cTokenAddress = df_values.cTokenAddress.str[:5]
            df_values.loc[:, 'tokenId'] = df_values.cTokenSymbol + '.' + df_values.cTokenAddress
            df_values.drop(columns=['cTokenSymbol', 'cTokenAddress'], inplace=True)

            summary = {}
            for _, r in df_values.iterrows():
                tokenId = r['tokenId']
                if tokenId not in token_series:
                    token_series[tokenId] = block_table.copy()
                table_to_fill = token_series[tokenId]
                for k, v in r.iteritems():
                    table_to_fill.loc[table_to_fill.blockNumber == block_number, k] = v
                    if k in ['cash', 'borrow', 'liability', 'reserve', 'net',
                             'qty_cash', 'qty_borrow', 'qty_liability', 'qty_reserve', 'qty_net']:
                        if k not in summary:
                            summary[k] = 0
                        summary[k] += v

            table_to_fill = token_series['total']
            for k, v in summary.items():
                table_to_fill.loc[table_to_fill.blockNumber == block_number, k] = v

        fp_out = os.path.join('tmp', f'compound_v2_assets_history_{start_dt:%Y%m%d}_{end_dt:%Y%m%d}.xlsx')
        with pd.ExcelWriter(fp_out, engine='xlsxwriter') as writer:  # pylint: disable=abstract-class-instantiated
            for s_name, vv in token_series.items():
                if isinstance(vv, pd.DataFrame):
                    dt_cols = vv.select_dtypes(include=['datetime64[ns, UTC]']).columns
                    for dt_col in dt_cols:
                        vv[dt_col] = (pd.to_datetime(vv[dt_col], unit='ms')
                                        .dt.tz_localize(None))
                    vv.to_excel(writer, sheet_name=s_name, index=False)
                elif isinstance(vv, pd.Series):
                    vv.to_excel(writer, sheet_name=s_name, index=False)
                elif isinstance(vv, np.ndarray):
                    pd.DataFrame(vv).to_excel(writer, sheet_name=s_name, index=False)
                else:
                    raise ModelRunError(f'Unknown sub-type {type(vv)=} {vv=}')

        kitchen.save_cache()
