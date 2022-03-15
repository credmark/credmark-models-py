import credmark.model
from credmark.types.dto import DTO, DTOField
from credmark.types import Portfolio


class PortfolioSummary(DTO):
    num_tokens: int = DTOField(..., description='Number of different tokens')


@credmark.model.describe(slug='example.type-test-1',
                         version='1.0',
                         display_name='Test Model',
                         description='Framework Test Model',
                         input=Portfolio,
                         output=PortfolioSummary)
class TestModel(credmark.model.Model):

    def run(self, input: Portfolio) -> PortfolioSummary:
        return PortfolioSummary(num_tokens=len(input.positions))


@credmark.model.describe(slug='example.type-test-2',
                         version='1.0',
                         display_name='Test Model',
                         description='Framework Test Model',
                         input=Portfolio,
                         output=PortfolioSummary)
class TestModel2(credmark.model.Model):

    def run(self, input: Portfolio) -> PortfolioSummary:
        # return PortfolioSummary(num_tokens=len(input.positions))

        # This will raise an error because we're not returning
        # the type PortfolioSummary that we set as "output"
        # in the describe() decorator above.
        return {'xx': 'ss'}  # type: ignore
