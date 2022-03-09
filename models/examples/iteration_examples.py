import credmark.model
from credmark.types import Account, Accounts, Address


@credmark.model.describe(slug='example.iteration',
                         version='1.0',
                         display_name='Example Iteration',
                         description="A test model for iteration",
                         output=Accounts)
class EchoModel(credmark.model.Model):
    """
    """

    def run(self, input) -> Accounts:

        # You can create an account with address as string
        account = Account(address="0x99cfb82eacb9f198d508b514d898a403c449533e")  # type: ignore
        assert isinstance(account.address, Address)

        # Or with an Address instance
        account2 = Account(address=Address("0x68cfb82eacb9f198d508b514d898a403c449533e"))
        assert isinstance(account.address, Address)

        accounts = Accounts(accounts=[
            account,
            account2,
            Account(address=Address("0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"))])

        more_accounts = Accounts(
            accounts=[Account(address=Address("0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3"))])

        for a in accounts:
            if a.address == "0x68cfb82eacb9f198d508b514d898a403c449533e":
                more_accounts.append(a)
        return more_accounts
