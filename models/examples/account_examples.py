# pylint: disable=line-too-long
from credmark.cmf.model import Model, EmptyInput
from credmark.cmf.types import Account, Accounts, Address
from .example_dtos import ExampleModelOutput


@Model.describe(
    slug='example.account',
    version='1.0',
    display_name='Account Usage Examples',
    description='This model gives examples of the functionality available on the Account class',
    developer='Credmark',
    input=EmptyInput,
    output=ExampleModelOutput)
class ExampleAccount(Model):
    def run(self, input) -> ExampleModelOutput:
        """
            This model demonstrates the functionality of the Account class.
        """

        example = ExampleModelOutput(
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/account_examples.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/reference/credmark.cmf.types.account.html"
            )

        account_1 = Account(address=Address('0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf'))
        account_2 = Account(address=Address('0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB'))
        accounts = Accounts(accounts=[account_1, account_2])

        example.log(
            "Account is the base Data Transfer Object for classes Contract and Token.")

        example.log(
            "You initialize an Account with an address.")

        example.log(
            f"Account(address='0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf') : {account_1.dict()}")

        example.log(
            "There is also an iterable Accounts Data Transfer Object,"
            " initialized with a list of accounts")
        
        example.log(
            f"Accounts(accounts=[account_1, account_2]) : {accounts.dict()}")

        return example
