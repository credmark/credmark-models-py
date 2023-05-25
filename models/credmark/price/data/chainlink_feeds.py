# pylint: disable=line-too-long

from credmark.cmf.types import Network

from models.credmark.price.data.chainlink_feeds_arbitrum_one import CHAINLINK_OVERRIDE_FEED_ARBITRUM_ONE
from models.credmark.price.data.chainlink_feeds_avalanche import CHAINLINK_OVERRIDE_FEED_AVALANCHE
from models.credmark.price.data.chainlink_feeds_bsc import CHAINLINK_OVERRIDE_FEED_BSC
from models.credmark.price.data.chainlink_feeds_fantom import CHAINLINK_OVERRIDE_FEED_FANTOM
from models.credmark.price.data.chainlink_feeds_mainnet import CHAINLINK_OVERRIDE_FEED_MAINNET
from models.credmark.price.data.chainlink_feeds_optimism import CHAINLINK_OVERRIDE_FEED_OPTIMISM
from models.credmark.price.data.chainlink_feeds_polygon import CHAINLINK_OVERRIDE_FEED_POLYGON

# The native token on other chain, give a direct address of feed.
# TODO: find the token address so to find the feed in Chainlink's registry
CHAINLINK_OVERRIDE_FEED = {
    Network.Mainnet: CHAINLINK_OVERRIDE_FEED_MAINNET,
    Network.BSC: CHAINLINK_OVERRIDE_FEED_BSC,
    Network.Polygon: CHAINLINK_OVERRIDE_FEED_POLYGON,
    Network.ArbitrumOne: CHAINLINK_OVERRIDE_FEED_ARBITRUM_ONE,
    Network.Optimism: CHAINLINK_OVERRIDE_FEED_OPTIMISM,
    Network.Avalanche: CHAINLINK_OVERRIDE_FEED_AVALANCHE,
    Network.Fantom: CHAINLINK_OVERRIDE_FEED_FANTOM,
}
