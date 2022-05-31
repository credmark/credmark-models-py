import sys
from ens import ENS
from web3.exceptions import ContractLogicError

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError, ModelDataError
from credmark.cmf.types import Contract, Price, Token, Account, Address
from credmark.dto import EmptyInput, DTO, DTOField

from models.dtos.price import PriceInput


@Model.describe(slug='chainlink.get-feed-registry',
                version="1.0",
                display_name="Chainlink - Feed registry",
                description="Supports multi-chain",
                input=EmptyInput,
                output=Contract)
class ChainLinkFeedRegistry(Model):
    CHAINLINK_REGISTRY = {
        1: '0x47Fb2585D2C56Fe188D0E6ec628a38b74fCeeeDf',
        42: '0xAa7F6f7f507457a1EE157fE97F6c7DB2BEec5cD0'
    }

    def run(self, _) -> Contract:
        return Contract(address=self.CHAINLINK_REGISTRY[self.context.chain_id])


class ENSDomainName(DTO):
    domain: str = DTOField(description='ENS Domain nam')


# TODO: implement shortest path
@Model.describe(slug='chainlink.price-by-ens',
                version="1.0",
                display_name="Chainlink - Price by ENS",
                description="Use ENS domain name for a token pair",
                input=ENSDomainName,
                output=Price)
class ChainLinkPriceByENS(Model):
    def run(self, input: ENSDomainName) -> Price:
        ns = ENS.fromWeb3(self.context.web3)
        feed_address = ns.address(input.domain)
        if feed_address is None:
            raise ModelRunError('Unable to resolve ENS domain name {input.domain}')
        return self.context.run_model('chainlink.price-by-feed',
                                      input=Account(address=Address(feed_address)),
                                      return_type=Price)


@ Model.describe(slug='chainlink.price-by-feed',
                 version="1.0",
                 display_name="Chainlink - Price by feed",
                 description="Input a Chainlink valid feed",
                 input=Account,
                 output=Price)
class ChainLinkPriceByFeed(Model):
    def run(self, input: Account) -> Price:
        feed_contract = Contract(address=input.address)
        (_roundId, answer,
            _startedAt, _updatedAt,
            _answeredInRound) = feed_contract.functions.latestRoundData().call()
        decimals = feed_contract.functions.decimals().call()
        description = feed_contract.functions.description().call()
        version = feed_contract.functions.version().call()
        feed = feed_contract.functions.aggregator().call()
        isFeedEnabled = None

        time_diff = self.context.block_number.timestamp - _updatedAt
        round_diff = _answeredInRound - _roundId
        return Price(price=answer / (10 ** decimals),
                     src=(f'{self.slug}|{description}|{feed}|v{version}|'
                          f'{isFeedEnabled}|t:{time_diff}s|r:{round_diff}'))


@ Model.describe(slug='chainlink.price-by-registry',
                 version="1.1",
                 display_name="Chainlink - Price by Registry",
                 description="Looking up Registry for two tokens\' addresses",
                 input=PriceInput,
                 output=Price)
class ChainLinkPriceByRegistry(Model):
    def run(self, input: PriceInput) -> Price:
        token0_address = input.base
        if input.quote is None:
            raise ModelDataError('quote must not be None.')
        token1_address = input.quote

        registry = self.context.run_model('chainlink.get-feed-registry',
                                          input=EmptyInput(),
                                          return_type=Contract)
        try:
            sys.tracebacklimit = 0
            feed = registry.functions.getFeed(token0_address, token1_address).call()
            (_roundId, answer,
                _startedAt, _updatedAt,
                _answeredInRound) = (registry.functions
                                     .latestRoundData(token0_address, token1_address)
                                     .call())
            decimals = registry.functions.decimals(token0_address, token1_address).call()
            description = registry.functions.description(token0_address, token1_address).call()
            version = registry.functions.version(token0_address, token1_address).call()
            isFeedEnabled = registry.functions.isFeedEnabled(feed).call()

            time_diff = self.context.block_number.timestamp - _updatedAt
            round_diff = _answeredInRound - _roundId
            return Price(price=answer / (10 ** decimals),
                         src=(f'{self.slug}|{description}|{feed}|v{version}|'
                              f'{isFeedEnabled}|t:{time_diff}s|r:{round_diff}'))
        except ContractLogicError as err:
            if 'Feed not found' in str(err):
                raise ModelRunError(f'No feed found for {token0_address}/{token1_address}')
            raise err
        finally:
            del sys.tracebacklimit


@Model.describe(slug='chainlink.price-usd',
                version="1.1",
                display_name="Chainlink - Price for Token / USD pair",
                description="Input a Token",
                input=Token,
                output=Price)
class ChainLinkFeedPriceUSD(Model):
    CONVERT_FOR_TOKEN_PRICE = {
        1: {
            Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'):
            Address('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'),
            Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'):
            Address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'),
        }
    }

    def run(self, input: Token) -> Price:
        try:
            return self.context.run_model('price.oracle-chainlink',
                                          input={'base': input.address,
                                                 'quote': 'USD'},
                                          return_type=Price)
        except ModelRunError:
            convert_token = (self.CONVERT_FOR_TOKEN_PRICE[self.context.chain_id]
                             .get(input.address, None))
            return self.context.run_model(
                'token.price',
                input=Token(address=convert_token) if convert_token is not None else input,
                return_type=Price)
