from credmark.cmf.model import Model
from credmark.cmf.types import Address, BlockNumber, Maybe, Price, Token
from credmark.dto import EmptyInput


@Model.describe(
    slug='contrib.neilz-redacted-votium-cashflow',
    version='1.2',
    display_name='Redacted Cartel Votium Cashflow',
    description='Redacted Cartel Votium Cashflow',
    category='protocol',
    subcategory='votium',
    input=EmptyInput,
    output=dict
)
class RedactedVotiumCashflow(Model):
    def run(self, _: EmptyInput) -> dict:
        votium_claim_address = Address("0x378Ba9B73309bE80BF4C2c027aAD799766a7ED5A")
        redacted_multisig_address = Address("0xA52Fd396891E7A74b641a2Cb1A6999Fcf56B077e")
        with self.context.ledger.TokenTransfer as q:
            transfers = q.select(columns=[
                q.BLOCK_NUMBER,
                q.VALUE,
                q.TOKEN_ADDRESS,
                q.TRANSACTION_HASH
            ], where=q.TO_ADDRESS.eq(redacted_multisig_address).and_(
                q.FROM_ADDRESS.eq(votium_claim_address)))

        for transfer in transfers:
            token = Token(address=transfer['token_address'])
            try:
                transfer['price'] = self.context.run_model(
                    'price.quote',
                    input={'base': token},
                    block_number=transfer['block_number'])['price']
            except Exception:
                transfer['price'] = 0
            if transfer['price'] is None:
                transfer['price'] = 0
            transfer['value_usd'] = transfer['price'] * \
                float(transfer['value']) / (10 ** token.decimals)
            transfer['block_time'] = str(BlockNumber(transfer['block_number']).timestamp_datetime)
            transfer['token_symbol'] = token.symbol
        return transfers.dict()


@Model.describe(
    slug='contrib.neilz-redacted-convex-cashflow',
    version='1.3',
    display_name='Redacted Cartel Convex Cashflow',
    description='Redacted Cartel Convex Cashflow',
    category='protocol',
    subcategory='votium',
    input=EmptyInput,
    output=dict)
class RedactedConvexCashflow(Model):
    CONVEX_ADDRESSES = [
        Address("0x72a19342e8F1838460eBFCCEf09F6585e32db86E"),
        Address("0xD18140b4B819b895A3dba5442F959fA44994AF50"),
    ]
    REDACTED_MULTISIG_ADDRESS = Address("0xA52Fd396891E7A74b641a2Cb1A6999Fcf56B077e")

    def run(self, _: EmptyInput) -> dict:
        with self.context.ledger.TokenTransfer as q:
            transfers = q.select(columns=[
                q.BLOCK_NUMBER,
                q.VALUE,
                q.TOKEN_ADDRESS
            ], where=q.TO_ADDRESS.eq(self.REDACTED_MULTISIG_ADDRESS).and_(
                q.FROM_ADDRESS.in_(self.CONVEX_ADDRESSES))
            )
        for transfer in transfers:
            token = Token(address=transfer['token_address'])
            transfer['price'] = (self.context.run_model(
                'price.quote-maybe',
                input={'base': token},
                block_number=transfer['block_number'],
                return_type=Maybe[Price])
                .get_just(Price(price=0.0, src='NA'))
                .price)
            transfer['value_usd'] = transfer['price'] * token.scaled(float(transfer['value']))
            transfer['block_time'] = str(BlockNumber(transfer['block_number']).timestamp_datetime)
            transfer['token_symbol'] = token.symbol
        return transfers.dict()
