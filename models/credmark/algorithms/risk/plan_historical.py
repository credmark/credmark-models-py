from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError

from credmark.dto import (
    DTO
)

from credmark.cmf.types import (
    Contract,
)

from models.credmark.algorithms.risk import (
    HistoricalBlockPlan,
    GeneralHistoricalPlan,
)


from datetime import date, datetime, timezone


class GenericHistoricalInput(DTO):
    model_slug: str
    model_input: dict
    asOf: date
    window: str
    interval: str


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

        for block_number in sorted(block_numbers):
            block_time = block_table.query('blockNumber == @block_number')['blockTime'].to_list()[0]
            self.logger.info(f'{block_time=}')

            hp_plan = GeneralHistoricalPlan(
                tag='eod',
                target_key=f'HistoricalPlan.{model_slug}.{block_number}',
                name=model_slug,
                use_kitchen=use_kitchen,
                chef_return_type=dict,
                plan_return_type=dict,
                context=self.context,
                verbose=verbose,
                method='run_model',
                slug=model_slug,
                input=model_input,
                block_number=block_number,
                input_keys=[],
            )
            hp = hp_plan.execute()
            print(hp, block_number)

            df_table.loc[df_table.blockNumber == block_number,
                         'result'] = hp
