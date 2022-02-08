from credmark.model import Model


class LaunchDateCmk(Model):

    def run(self, _input) -> dict:
        txs = self.context.ledger.get_transactions(
            ["nonce"], {"min": "block_time"})
        return txs
