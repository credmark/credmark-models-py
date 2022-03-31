from credmark.cmf.model import Model, EmptyInput
from credmark.cmf.types import Account, Accounts, Address


@Model.describe(
    slug='example.account',
    version='1.0',
    display_name='Account Usage Examples',
    description='This model gives examples of the functionality available on the Account class',
    developer='Credmark',
    input=EmptyInput,
    output=dict)
class ExampleAccount(Model):
    def run(self, input) -> dict:
        """
            This model demonstrates the functionality of the Account class
        """
        account_1 = Account(address=Address('0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf'))
        self.logger.info(
            "Account is the base Data Transfer Object for classes Contract and Token.")
        self.logger.info(
            "You initialize an Account with an address.")
        self.logger.info(
            f"Account(address='0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf') : {account_1.dict()}")
        account_2 = Account(address=Address('0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB'))
        self.logger.info(
            "There is also an iterable Accounts Data Transfer Object,"
            " initialized with a list of accounts")
        accounts = Accounts(accounts=[account_1, account_2])
        self.logger.info(
            f"Accounts(accounts=[account_1, account_2]) : {accounts.dict()}")

        return {"message": "see https://github.com/credmark/credmark-models-py/blob/main/model"
                "s/examples/account_examples.py for examples of Account usage"}
