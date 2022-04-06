from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError

from credmark.dto import (
    EmptyInput,
)


from models.credmark.protocols.lending.compound.compound_v2 import (
    CompoundV2PoolValues,
    CompoundV2PoolInfos,
)

from models.credmark.algorithms.risk import (
    Plan,
    HistoricalBlockPlan
)

import os
import pandas as pd
import numpy as np


class CompoundValueHistoricalPlan(Plan[CompoundV2PoolValues, CompoundV2PoolValues]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs,
                         chef_return_type=CompoundV2PoolValues,
                         plan_return_type=CompoundV2PoolValues)

    def define(self) -> CompoundV2PoolValues:
        method = 'run_model'
        slug = 'compound.all-pools-values'
        pool_infos = self._input_to_plan['pool_infos']
        block_number = self._input_to_plan['block_number']

        recipe = self.create_recipe(
            cache_keywords=[method, slug, block_number],
            method=method,
            input={'slug': slug,
                   'input': pool_infos,
                   'block_number': block_number})

        return self.chef.cook(recipe)


class CompoundInfoHistoricalPlan(Plan[CompoundV2PoolInfos, CompoundV2PoolInfos]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs,
                         chef_return_type=CompoundV2PoolInfos,
                         plan_return_type=CompoundV2PoolInfos)

    def define(self) -> CompoundV2PoolInfos:
        method = 'run_model'
        slug = 'compound.all-pools-info'
        block_number = self._input_to_plan['block_number']

        recipe = self.create_recipe(
            cache_keywords=[method, slug, block_number],
            method=method,
            input={'slug': slug,
                   'block_number': block_number})
        return self.chef.cook(recipe)


@Model.describe(slug="compound.all-pools-values-historical-plan",
                version="1.0",
                display_name="Aave V2 token liquidity",
                description="Aave V2 token liquidity at a given block number",
                input=EmptyInput,
                output=None)
class CompoundV2AllPoolsValueHistoricalPlan(Model):
    def run(self, input: EmptyInput) -> None:
        window = '659 days'
        interval = '1 day'
        use_kitchen = True
        verbose = False
        dev_mode = False
        as_of_dt = self.context.block_number.timestamp_datetime

        block_plan = HistoricalBlockPlan(
            tag='eod',
            target_key=f'HistoricalBlock.{as_of_dt}.{window}.{interval}',
            use_kitchen=use_kitchen,
            context=self.context,
            verbose=verbose,
            as_of=as_of_dt,
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

            value_plan = CompoundInfoHistoricalPlan(
                tag='eod',
                target_key=f'CompoundInfoHistoricalPlan.{block_number}',
                use_kitchen=use_kitchen,
                context=self.context,
                verbose=verbose,
                block_number=block_number,
            )
            pool_infos = value_plan.execute()

            if dev_mode:
                ts_str = f'{self.context.block_number.timestamp_datetime:%Y%m%d_%H%M%S}'
                pd.DataFrame(pool_infos.dict()['infos']).to_excel(
                    f'compound_infos_{ts_str}.xlsx')

            value_plan = CompoundValueHistoricalPlan(
                tag='eod',
                target_key=f'CompoundValueHistoricalPlan.{block_number}',
                use_kitchen=use_kitchen,
                context=self.context,
                verbose=verbose,
                reset_cache=reset_cache_value,
                pool_infos=pool_infos,
                block_number=block_number,
            )
            reset_cache_value = False
            pool_values = value_plan.execute()

            if dev_mode:
                ts_str = f'{self.context.block_number.timestamp_datetime:%Y%m%d_%H%M%S}'
                pd.DataFrame(pool_infos.dict()['values']).to_excel(
                    f'compound_value_{ts_str}.xlsx')

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
            if 'total' not in token_series:
                token_series['total'] = block_table
            table_to_fill = token_series['total']
            for k, v in summary.items():
                table_to_fill.loc[table_to_fill.blockNumber == block_number, k] = v

        fp_out = os.path.join('tmp', 'compound_v2_assets_history.xlsx')
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
