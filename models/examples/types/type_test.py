import credmark.model
from credmark.types import DTO, DTOField
from credmark.types.financial.portfolio import Portfolio


class PortfolioSummary(DTO):
    num_tokens: int = DTOField(..., description='Number of different tokens')


@credmark.model.describe(slug='type-test-1',
                         version='1.0',
                         display_name='Test Model',
                         description='SDK Test Model',
                         input=Portfolio,
                         output=PortfolioSummary)
class TestModel(credmark.model.Model):

    def run(self, input: Portfolio) -> PortfolioSummary:
        return PortfolioSummary(num_tokens=len(input.positions))


@credmark.model.describe(slug='type-test-2',
                         version='1.0',
                         display_name='Test Model',
                         description='SDK Test Model',
                         input=Portfolio,
                         output=PortfolioSummary)
class TestModel2(credmark.model.Model):

    def run(self, input: Portfolio) -> PortfolioSummary:
        # return PortfolioSummary(num_tokens=len(input.positions))
        return {'xx': 'ss'}  # error
