import sys

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError, ModelEngineError
from credmark.cmf.types import Contract, Maybe, Network, Price, PriceWithQuote
from credmark.cmf.types.block_number import BlockNumberOutOfRangeError
from credmark.dto import DTO, DTOField, EmptyInput
from ens import ENS
from models.dtos.price import PriceInput
from models.tmp_abi_lookup import CHAINLINK_AGG
from web3.exceptions import ContractLogicError


@Model.describe(slug='chainlink.get-feed-registry',
                version="1.0",
                display_name="Chainlink - Feed registry",
                description="Supports multi-chain",
                category='protocol',
                subcategory='chainlink',
                input=EmptyInput,
                output=Contract)
class ChainLinkFeedRegistry(Model):
    CHAINLINK_REGISTRY = {
        Network.Mainnet: '0x47Fb2585D2C56Fe188D0E6ec628a38b74fCeeeDf',
        Network.Kovan: '0xAa7F6f7f507457a1EE157fE97F6c7DB2BEec5cD0'
    }

    def run(self, _) -> Contract:
        registry = Contract(address=self.CHAINLINK_REGISTRY[self.context.network])
        _ = registry.abi
        return registry


class ENSDomainName(DTO):
    domain: str = DTOField(description='ENS Domain nam')


# TODO: implement shortest path
@Model.describe(slug='chainlink.price-by-ens',
                version="1.2",
                display_name="Chainlink - Price by ENS",
                description="Use ENS domain name for a token pair",
                category='protocol',
                subcategory='chainlink',
                input=ENSDomainName,
                output=Price)
class ChainLinkPriceByENS(Model):
    def run(self, input: ENSDomainName) -> Price:
        try:
            ns = ENS.fromWeb3(self.context.web3)  # type: ignore # pylint: disable=no-member
        except AttributeError:
            ns = ENS.from_web3(self.context.web3)  # type: ignore  # pylint: disable=no-member

        feed_address = ns.address(input.domain)
        if feed_address is None:
            raise ModelRunError('Unable to resolve ENS domain name {input.domain}')
        return self.context.run_model('chainlink.price-by-feed',
                                      input={'address': feed_address},
                                      return_type=Price,
                                      local=True)


@Model.describe(slug='chainlink.price-by-feed',
                version="1.3",
                display_name="Chainlink - Price by feed",
                description="Input a Chainlink valid feed",
                category='protocol',
                subcategory='chainlink',
                input=Contract,
                output=Price)
class ChainLinkPriceByFeed(Model):
    def run(self, input: Contract) -> Price:
        feed_contract = input
        try:
            feed_contract.abi
        except ModelEngineError:
            feed_contract.set_abi(CHAINLINK_AGG, set_loaded=True)

        (_roundId, answer,
            _startedAt, _updatedAt,
            _answeredInRound) = feed_contract.functions.latestRoundData().call()
        decimals = feed_contract.functions.decimals().call()
        description = feed_contract.functions.description().call()
        version = feed_contract.functions.version().call()

        feed = input.address
        if feed_contract.abi is not None:
            if 'aggregator'.lower() in feed_contract.abi.functions:
                feed = feed_contract.functions.aggregator().call()
        isFeedEnabled = None

        time_diff = self.context.block_number.timestamp - _updatedAt
        round_diff = _answeredInRound - _roundId
        return Price(price=answer / (10 ** decimals),
                     src=(f'{self.slug}|{description}|{feed}|v{version}|'
                          f'{isFeedEnabled}|t:{time_diff}s|r:{round_diff}'))


@Model.describe(slug='chainlink.price-from-registry-maybe',
                version="1.3",
                display_name="Chainlink - Price by Registry",
                description="Looking up Registry for two tokens' addresses",
                category='protocol',
                subcategory='chainlink',
                input=PriceInput,
                output=Maybe[PriceWithQuote])
class ChainLinkFeedFromRegistryMaybe(Model):
    def run(self, input: PriceInput) -> Maybe[PriceWithQuote]:
        try:
            pq = self.context.run_model('chainlink.price-by-registry',
                                        input=input,
                                        return_type=PriceWithQuote,
                                        local=True)
            return Maybe[PriceWithQuote](just=pq)
        except BlockNumberOutOfRangeError:
            return Maybe.none()
        except ModelRunError as _err:
            try:
                pq = self.context.run_model('chainlink.price-by-registry',
                                            input=input.inverse(),
                                            return_type=PriceWithQuote,
                                            local=True)
                return Maybe[PriceWithQuote](just=pq.inverse(input.quote.address))
            except ModelRunError as _err2:
                return Maybe.none()


@Model.describe(slug='chainlink.price-by-registry',
                version="1.5",
                display_name="Chainlink - Price by Registry",
                description="Looking up Registry for two tokens' addresses",
                category='protocol',
                subcategory='chainlink',
                input=PriceInput,
                output=PriceWithQuote)
class ChainLinkPriceByRegistry(Model):
    def run(self, input: PriceInput) -> Price:
        base_address = input.base.address
        quote_address = input.quote.address

        registry = self.context.run_model('chainlink.get-feed-registry',
                                          input=EmptyInput(),
                                          return_type=Contract,
                                          local=True)
        try:
            sys.tracebacklimit = 0
            feed = registry.functions.getFeed(base_address, quote_address).call()
            (_roundId, answer,
                _startedAt, _updatedAt,
                _answeredInRound) = (registry.functions
                                     .latestRoundData(base_address, quote_address)
                                     .call())
            decimals = registry.functions.decimals(base_address, quote_address).call()
            description = registry.functions.description(base_address, quote_address).call()
            version = registry.functions.version(base_address, quote_address).call()
            isFeedEnabled = registry.functions.isFeedEnabled(feed).call()

            time_diff = self.context.block_number.timestamp - _updatedAt
            round_diff = _answeredInRound - _roundId
            return PriceWithQuote(price=answer / (10 ** decimals),
                                  src=(f'{self.slug}|{description}|{feed}|v{version}|'
                                       f'{isFeedEnabled}|t:{time_diff}s|r:{round_diff}'),
                                  quoteAddress=quote_address)
        except ContractLogicError as err:
            if 'Feed not found' in str(err):
                self.logger.debug(f'No feed found for {base_address}/{quote_address}')
                raise ModelRunError(f'No feed found for {base_address}/{quote_address}') from err
            raise err
        finally:
            del sys.tracebacklimit
