from credmark.cmf.model import Model
from credmark.cmf.types import Accounts, Portfolio
from credmark.dto import DTOField

# Next Steps:

# Set the slug, display_name, and description for your model below.
# Add code to the run() method.


class AccountsWithOffset(Accounts):
    offset: int = DTOField(200, description='Block_number offset')

    class Config:
        schema_extra = {
            'example': {'address': '0x388c818ca8b9251b393131c08a736a67ccb19297', 'offset': 200}
        }


@Model.describe(slug='contrib.exploited-value',
                version='1.0',
                display_name='My Model',
                description="Description of the model.",
                input=AccountsWithOffset,
                output=dict)
class ExploitedValue(Model):
    """
    If the description is not set in the decorator above,
    this doc string is used as the model description.
    """

    def run(self, input: Accounts) -> dict:

        # Add your model code here.

        # Access utilities with self.context
        # Log using self.logger

        # Input:
        # If you require input, use an existing DTO class or
        # create your own and set the class as the "input" arg
        # in the decorator and set the "input" arg type in this function.

        # Output:
        # It is recommended to use an existing DTO class or
        # create your own to use as the model output (return value.)
        # Set the "output" arg in the decorator and the return type
        # of this function. Then change this function to return an
        # instance of the DTO class.

        portfolio_now = self.context.models.accounts.portfolio(input=input,
                                                               return_type=Portfolio)

        portfolio_two_blocks_ago: Portfolio = self.context.models.accounts.portfolio(
            input=input,
            return_type=Portfolio,
            block_number=self.context.block_number - 200)  # type: ignore

        value_diff = portfolio_two_blocks_ago.get_value() - \
            portfolio_now.get_value()  # type: ignore

        return {"exploited_value": value_diff}
