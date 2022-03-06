import credmark.model
from credmark.types import Wallet, Wallets


@credmark.model.describe(slug='example-iteration',
                         version='1.0',
                         display_name='Echo',
                         description="A test model to echo the message property sent in input.",
                         output=Wallets)
class EchoModel(credmark.model.Model):
    """
    This test simply echos back the input.
    The DTO message field defines a default value so that is
    used if no input is sent.
    """

    def run(self, input) -> dict:
        wallets = Wallets(wallets=[Wallet(address="0x68cfb82eacb9f198d508b514d898a403c449533e"),
                                   Wallet(address="0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3")])
        more_wallets = Wallets(
            wallets=[Wallet(address="0x59e1f901b5c33ff6fae15b61684ebf17cca7b9b3")])
        for w in wallets:
            if w.address == "0x68cfb82eacb9f198d508b514d898a403c449533e":
                more_wallets.append(w)
        return more_wallets
