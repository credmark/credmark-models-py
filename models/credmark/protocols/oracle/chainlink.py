from credmark.cmf.model import Model
from credmark.cmf.types import Contract, Price, Token, Address
from credmark.dto import EmptyInput


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


@Model.describe(slug='chainlink.price-usd',
                version="1.0",
                display_name="Chainlink - Price for Token / USD pair",
                description="",
                input=Token,
                output=Price)
class ChainLinkFeedPrice(Model):
    ETH = Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE')
    BTC = Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB')

    USD = Address('0x{:040x}'.format(840))
    GBP = Address('0x{:040x}'.format(826))
    EUR = Address('0x{:040x}'.format(978))

    def run(self, input) -> Contract:
        registry = Contract(**self.context.models.chainlink.get_feed_registry())
        (_roundId, answer,
         _startedAt, _updatedAt,
         _answeredInRound) = registry.functions.latestRoundData(input.address, self.USD).call()
        decimals = registry.functions.decimals(input.address, self.USD).call()
        description = registry.functions.description(input.address, self.USD).call()
        version = registry.functions.version(input.address, self.USD).call()
        feed = registry.functions.getFeed(input.address, self.USD).call()
        isFeedEnabled = registry.functions.isFeedEnabled(feed).call()
        time_diff = self.context.block_number.timestamp - _updatedAt
        round_diff = _answeredInRound - _roundId
        return Price(price=answer / (10 ** decimals),
                     src=f'{self.slug}|{description}|{feed}|v{version}|{isFeedEnabled}|t:{time_diff}s|r:{round_diff}')
