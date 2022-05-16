from typing import List, Union

from credmark.cmf.model import Model
from credmark.cmf.types.series import BlockSeries

from credmark.dto import (
    DTO
)

from models.credmark.algorithms.risk import (
    HistoricalBlockPlan,
    GeneralHistoricalPlan,
)


from datetime import date, datetime, timezone


class GenericHistoricalInput(DTO):
    model_slug: str
    model_input: dict
    input_keys: List[str]
    asOf: date
    window: str
    interval: str
    save_file: Union[None, str]


@Model.describe(slug="finance.historical-plan",
                version="1.0",
                display_name="Run model historical",
                description="Customizable input",
                input=GenericHistoricalInput,
                output=None)
class GenericHistoricalPlan(Model):
    def run(self, input: GenericHistoricalInput) -> None:
        verbose = False
        use_kitchen = True
        end_dt = datetime.combine(input.asOf,
                                  datetime.max.time(),
                                  tzinfo=timezone.utc)
        window = input.window
        interval = input.interval
        model_slug = input.model_slug
        model_input = input.model_input
        input_keys = input.input_keys

        block_plan = HistoricalBlockPlan(
            tag='eod',
            target_key=f'HistoricalBlock.{end_dt}.{window}.{interval}',
            use_kitchen=use_kitchen,
            context=self.context,
            verbose=verbose,
            as_of=end_dt,
            window=window,
            interval=interval)

        block_plan_results = block_plan.execute()

        block_numbers = block_plan_results['block_numbers']
        block_table = block_plan_results['block_table']
        df_table = block_table.copy()

        hp_plan = GeneralHistoricalPlan(
            tag='eod',
            target_key=f'GeneralHistoricalPlan.{model_slug}.{end_dt}.{window}.{interval}',
            name=model_slug,
            use_kitchen=use_kitchen,
            chef_return_type=BlockSeries[dict],
            plan_return_type=dict,
            context=self.context,
            verbose=verbose,
            slug=model_slug,
            input=model_input,
            block_numbers=block_numbers,
            input_keys=input_keys,
        )
        hp = hp_plan.execute()

        for block_numbers, result in hp['data']:
            for k, v in result.items():
                df_table.loc[df_table.blockNumber == block_numbers, k] = v

        if input.save_file is not None and isinstance(input.save_file, str):
            df_table.to_csv(input.save_file)
            self.logger.info(f'Saved result({df_table.shape}) to {input.save_file}')

        return df_table.to_dict()
