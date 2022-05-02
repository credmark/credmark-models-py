from credmark.cmf.model import Model
from credmark.cmf.types import Account, Accounts
from models.dtos.example import ExampleAccountInput, ExampleModelOutput


@Model.describe(
    slug='example.account',
    version='1.2',
    display_name='Example - Account',
    description='This model gives examples of the functionality available on the Account class',
    developer='Credmark',
    input=ExampleAccountInput,
    output=ExampleModelOutput)
class ExampleAccount(Model):
    def run(self, input: ExampleAccountInput) -> ExampleModelOutput:
        output = ExampleModelOutput(
            title="4. Example - Account",
            description="This model gives examples of the functionality available "
            "on the Account class",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_04_account.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "reference/credmark.cmf.types.account.html"
        )

        account_1 = Account(address=input.address_1)
        account_2 = Account(address=input.address_2)
        accounts = Accounts(accounts=[account_1, account_2])

        output.log("Account is the base Data Transfer Object for classes Contract and Token.")

        output.log("You initialize an Account with an address.")
        output.log_io(input=f"Account(address='{account_1.address}')", output=account_1.dict())
        output.log_io(input=f"Account(address='{account_2.address}')", output=account_2.dict())

        output.log("There is also an iterable Accounts Data Transfer Object, "
                   "initialized with a list of accounts")

        output.log_io(input="Accounts(accounts=[account_1, account_2])", output=accounts.dict())

        return output
