import credmark.model
from credmark.types import Token, Position
from credmark.types.models.ledger import TokenTransferTable, ReceiptTable, LedgerModelOutput


class TokenExpanded(Token):
    totalSupply: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        self.totalSupply = self.total_supply()

@credmark.model.describe(
    slug="contrib.walkthrough-1",
    version="1.0",
    input=None,
    output=TokenExpanded,
    developer='neilz.eth'
    )
class WalkthroughModelOne(credmark.model.Model):
    def run(self, input):
        return TokenExpanded(address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

@credmark.model.describe(
    slug="contrib.walkthrough-2",
    version="1.0",
    input=Token,
    output=LedgerModelOutput,
    developer='neilz.eth'
    )
class WalkthroughModelTwo(credmark.model.Model):
    def run(self, input: Token):
        token_transfers = self.context.ledger.get_erc20_transfers([TokenTransferTable.Columns.VALUE],
            where=f"{TokenTransferTable.Columns.BLOCK_NUMBER}={self.context.block_number} and {TokenTransferTable.Columns.TOKEN_ADDRESS}= '{input.address}'")
        return token_transfers

@credmark.model.describe(
    slug="contrib.walkthrough-3",
    version="1.0",
    input=None,
    output=Position,
    developer='neilz.eth')
class WalkthroughModelThree(credmark.model.Model):
    def run(self, input) ->dict:
        token = self.context.run_model('contrib.walkthrough-1', return_type=Token)

        transfers_on_this_block = self.context.run_model('contrib.walkthrough-2', token, return_type=LedgerModelOutput)

        result = Position(amount = sum([t['value'] for t in transfers_on_this_block]) / (10 ** token.decimals), token=token)

        return result

@credmark.model.describe(
    slug="contrib.walkthrough-4",
    version="1.0",
    input=None,
    output=dict,
    developer='neilz.eth')
class WalkthroughModelFour(credmark.model.Model):
    def run(self, input) :
        historical_result = self.context.historical.run_model_historical_blocks('contrib.walkthrough-3', window=100, interval=20)
        return {"result": [{
            "block":r.blockNumber,
            "totalSupply": r.output['token']['totalSupply'],
            "volume": r.output['amount']
        } for r in historical_result
        ]}
        