from credmark import Model


class LaunchDateCmk(Model):

    def run(self, data):
        txs = self.context.ledger.get_transactions(["nonce"], {"min":"block_time"})
        return txs

