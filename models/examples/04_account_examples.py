from credmark.cmf.model import Model
from credmark.cmf.types import Account, Accounts, Address
from credmark.dto import DTO
from models.examples.example_dtos import ExampleModelOutput


class _AccountInput(DTO):
    address_1: Address = Address('0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf')
    address_2: Address = Address('0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB')


@Model.describe(
    slug='example.account',
    version='1.0',
    display_name='Account Usage Examples',
    description='This model gives examples of the functionality available on the Account class',
    developer='Credmark',
    input=_AccountInput,
    output=ExampleModelOutput)
class ExampleAccount(Model):
    def run(self, input: _AccountInput) -> ExampleModelOutput:
        output = ExampleModelOutput(
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/04_account_examples.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/reference/credmark.cmf.types.account.html"
        )

        output.log("This model demonstrates the functionality of the Account class.")

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
