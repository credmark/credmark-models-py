from credmark.cmf.model import Model
from credmark.cmf.types import Network


class CompoundV3Meta(Model):
    USDC_MARKETS = {
        Network.Mainnet: '0xc3d688B66703497DAA19211EEdff47f25384cdc3',
        Network.Polygon: '0xF25212E676D1F7F89Cd72fFEe66158f541246445',
        Network.ArbitrumOne: '0xA5EDBDD9646f8dFF606d7448e414884C7d905dCA',
    }

    WETH_MARKETS = {
        Network.Mainnet: '0xA17581A9E3356d9A858b789D68B4d866e593aE94',

    }

    def run(self, _):
        ...


# .baseToken / .baseScale,
