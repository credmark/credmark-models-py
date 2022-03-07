import credmark.model
from credmark.types import Account, Accounts


@credmark.model.describe(slug='example-iteration',
                         version='1.0',
                         display_name='Echo',
                         description="A test model to echo the message property sent in input.",
                         output=Accounts)
class EchoModel(credmark.model.Model):
    """
    This test simply echos back the input.
    The DTO message field defines a default value so that is
    used if no input is sent.
    """

    def run(self, input) -> dict:
        accounts = Accounts(accounts=[Account(address="0x68cfb82eacb9f198d508b514d898a403c449533e"),
                                      Account(address="0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3")])
        more_accounts = Accounts(
            accounts=[Account(address="0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3")])
        for a in accounts:
            if a.address == "0x68cfb82eacb9f198d508b514d898a403c449533e":
                more_accounts.append(a)
        return more_accounts
