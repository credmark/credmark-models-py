# pylint: disable=line-too-long

import sys
from typing import Any, cast

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelEngineError, ModelRunError
from credmark.cmf.types import BlockNumberOutOfRangeError, Contract, Maybe, Network, Price, PriceWithQuote
from credmark.dto import DTO, DTOField
from ens import ENS
from web3.exceptions import ContractLogicError

from models.dtos.price import PriceInput
from models.tmp_abi_lookup import CHAINLINK_AGG


@Model.describe(slug='chainlink.get-feed-registry',
                version="1.0",
                display_name="Chainlink - Feed registry",
                description="Supports multi-chain",
                category='protocol',
                subcategory='chainlink',
                output=Contract)
class ChainLinkFeedRegistry(Model):
    CHAINLINK_REGISTRY = {
        Network.Mainnet: '0x47Fb2585D2C56Fe188D0E6ec628a38b74fCeeeDf',
        Network.Kovan: '0xAa7F6f7f507457a1EE157fE97F6c7DB2BEec5cD0'
    }

    def run(self, _) -> Contract:
        registry = Contract(
            address=self.CHAINLINK_REGISTRY[self.context.network])
        _ = registry.abi
        return registry


class ENSDomainName(DTO):
    domain: str = DTOField(description='ENS Domain nam')

    class Config:
        schema_extra = {'examples': [{"domain": "eth-usd.data.eth"}]}


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
            # type: ignore # pylint: disable=no-member
            ns = ENS.from_web3(self.context.web3)
        except AttributeError:
            # type: ignore  # pylint: disable=no-member
            ns = cast(Any, ENS).from_web3(self.context.web3)

        feed_address = ns.address(input.domain)
        if feed_address is None:
            raise ModelRunError(
                'Unable to resolve ENS domain name {input.domain}')
        return self.context.run_model(
            'chainlink.price-by-feed', input={'address': feed_address},
            return_type=Price, local=True)


class ChainlinkFeedContract(Contract):
    class Config:
        schema_extra = {'examples':
                        [{"address": "0x37bC7498f4FF12C19678ee8fE19d713b87F6a9e6"},
                         {"address": "0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419"}]}


@Model.describe(slug='chainlink.price-by-feed',
                version="1.4",
                display_name="Chainlink - Price by feed",
                description="Input a Chainlink valid feed",
                category='protocol',
                subcategory='chainlink',
                input=ChainlinkFeedContract,
                output=Price)
class ChainLinkPriceByFeed(Model):
    def run(self, input: ChainlinkFeedContract) -> Price:
        feed_contract = input
        try:
            _ = feed_contract.abi
        except (ModelDataError, ModelEngineError):
            feed_contract = feed_contract.set_abi(
                CHAINLINK_AGG, set_loaded=True)

        (_roundId, answer, _startedAt, _updatedAt, _answeredInRound) = cast(
            tuple[int, int, int, int, int], feed_contract.functions.latestRoundData().call())
        decimals = cast(int, feed_contract.functions.decimals().call())
        description = cast(str, feed_contract.functions.description().call())
        version = cast(int, feed_contract.functions.version().call())

        feed = input.address
        if feed_contract.abi is not None and 'aggregator' in feed_contract.abi.functions:
            try:
                feed = feed_contract.functions.aggregator().call()
            except Exception:
                # Exception might occur when ABI is set manually
                pass

        isFeedEnabled = None

        time_diff = self.context.block_number.timestamp - _updatedAt
        round_diff = _answeredInRound - _roundId
        return Price(price=answer / (10 ** decimals),
                     src=(f'{self.slug}|{description}|{feed}|v{version}|'
                          f'{isFeedEnabled}|t:{time_diff}s|r:{round_diff}'))


class PriceInputWithRegistry(PriceInput):
    class Config:
        schema_extra = {'example': {"base": {"symbol": "CRV"}}}


@Model.describe(slug='chainlink.price-from-registry-maybe',
                version="1.4",
                display_name="Chainlink - Price by Registry",
                description="Looking up Registry for two tokens' addresses",
                category='protocol',
                subcategory='chainlink',
                input=PriceInputWithRegistry,
                output=Maybe[PriceWithQuote])
class ChainLinkFeedFromRegistryMaybe(Model):
    def run(self, input: PriceInputWithRegistry) -> Maybe[PriceWithQuote]:
        try:
            pq = self.context.run_model(
                'chainlink.price-by-registry', input=input,
                return_type=PriceWithQuote, local=True)
            return Maybe[PriceWithQuote](just=pq)
        except BlockNumberOutOfRangeError:
            return Maybe.none()
        except ModelRunError:
            try:
                pq = self.context.run_model(
                    'chainlink.price-by-registry', input=input.inverse(),
                    return_type=PriceWithQuote, local=True)
                return Maybe[PriceWithQuote](just=pq.inverse(input.quote.address))
            except ModelRunError:
                return Maybe.none()


@Model.describe(slug='chainlink.price-by-registry',
                version="1.7",
                display_name="Chainlink - Price by Registry",
                description="Looking up Registry for two tokens' addresses",
                category='protocol',
                subcategory='chainlink',
                input=PriceInputWithRegistry,
                output=PriceWithQuote)
class ChainLinkPriceByRegistry(Model):
    def run(self, input: PriceInputWithRegistry) -> Price:
        base_address = input.base.address
        quote_address = input.quote.address

        registry = self.context.run_model(
            'chainlink.get-feed-registry', {}, return_type=Contract, local=True)
        try:
            sys.tracebacklimit = 0
            feed = registry.functions.getFeed(
                base_address, quote_address).call()
            (_roundId, answer, _startedAt, _updatedAt, _answeredInRound) = cast(
                tuple[int, int, int, int, int],
                registry.functions.latestRoundData(base_address, quote_address).call())
            decimals = cast(int, registry.functions.decimals(base_address, quote_address).call())
            description = cast(str, registry.functions.description(base_address, quote_address).call())
            version = cast(int, registry.functions.version(base_address, quote_address).call())
            isFeedEnabled = cast(bool, registry.functions.isFeedEnabled(feed).call())

            time_diff = self.context.block_number.timestamp - _updatedAt
            round_diff = _answeredInRound - _roundId
            return PriceWithQuote(price=answer / (10 ** decimals),
                                  src=(f'{self.slug}|{description}|{feed}|v{version}|'
                                       f'{isFeedEnabled}|t:{time_diff}s|r:{round_diff}'),
                                  quoteAddress=quote_address)
        except ContractLogicError as err:
            if 'Feed not found' in str(err):
                self.logger.debug(
                    f'No feed found for {base_address}/{quote_address}')
                raise ModelRunError(
                    f'No feed found for {base_address}/{quote_address}') from err
            raise err
        finally:
            del sys.tracebacklimit
