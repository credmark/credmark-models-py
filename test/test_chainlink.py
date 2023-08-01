# pylint:disable=locally-disabled,line-too-long

from datetime import datetime, timezone

from cmf_test import CMFTest

from models.credmark.price.data.chainlink_feeds import CHAINLINK_OVERRIDE_FEED


class TestChainlink(CMFTest):
    block_number: int = 15000109

    def run_model_chainlink(self, *args):
        self.run_model(*args, block_number=self.block_number)

    def test_ens(self):
        self.title('Chainlink - ENS')

        self.run_model_chainlink('chainlink.price-by-ens',
                                 {"domain": "eth-usd.data.eth"})
        self.run_model_chainlink('chainlink.price-by-ens',
                                 {"domain": "comp-eth.data.eth"})
        self.run_model_chainlink('chainlink.price-by-ens',
                                 {"domain": "avax-usd.data.eth"})
        self.run_model_chainlink('chainlink.price-by-ens',
                                 {"domain": "bnb-usd.data.eth"})
        self.run_model_chainlink('chainlink.price-by-ens',
                                 {"domain": "sol-usd.data.eth"})

    def test_price_by_registry(self):
        self.title('Chainlink - registry')

        # AAVE 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9
        # no quote
        # chainlink.get-feed-registry
        self.run_model_chainlink('chainlink.price-by-registry',
                                 {"base": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}})

        self.run_model_chainlink('chainlink.price-by-registry',
                                 {"base": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"},
                                  "quote": {"address": "0x0000000000000000000000000000000000000348"}})
        self.run_model_chainlink('chainlink.price-by-registry',
                                 {"base": {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"},
                                  "quote": {"address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"}})
        self.run_model_chainlink('chainlink.price-from-registry-maybe',
                                 {"base": {"address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"}})

    def test_price_quote(self):
        self.title('Chainlink - price quote')

        self.run_model_chainlink('price.cex', {"base": {"symbol": "AAVE"}})
        self.run_model_chainlink('price.cex', {"base": {"symbol": "WETH"}})
        self.run_model_chainlink('price.cex', {"base": {"symbol": "WBTC"}})
        self.run_model_chainlink('price.cex',
                                 {"base": {"address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"}})
        self.run_model_chainlink('price.cex',
                                 {"base": {"address": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"}})
        self.run_model_chainlink('price.cex',
                                 {"base": {"address": "0xD31a59c85aE9D8edEFeC411D448f90841571b89c"}})

        self.run_model_chainlink('price.cex', {"base": {"symbol": "WBTC"}})
        self.run_model_chainlink('price.cex', {"base": {"symbol": "BTC"}})
        self.run_model_chainlink('price.cex', {"base": {"symbol": "WETH"}})
        self.run_model_chainlink('price.cex', {"base": {"symbol": "ETH"}})
        self.run_model_chainlink('price.cex', {"base": {"symbol": "AAVE"}})
        self.run_model_chainlink('price.cex', {"base": {"symbol": "USD"}})

    def test_oracle_chainlink(self):
        self.title('Chainlink - Oracle')

        self.run_model_chainlink('price.oracle-chainlink',
                                 {"base": {"address": "0xD31a59c85aE9D8edEFeC411D448f90841571b89c"}})
        self.run_model_chainlink('price.oracle-chainlink',
                                 {"base": {"address": "0x1a4b46696b2bb4794eb3d4c26f1c55f9170fa4c5"}})
        self.run_model_chainlink('price.oracle-chainlink',
                                 {"base": {"address": "0x64aa3364F17a4D01c6f1751Fd97C2BD3D7e7f1D5"}})
        self.run_model_chainlink('price.oracle-chainlink',
                                 {"base": {"address": "0x383518188C0C6d7730D91b2c03a03C837814a899"}})
        self.run_model_chainlink('price.oracle-chainlink',
                                 {"base": {"symbol": "AAVE"}})
        self.run_model_chainlink('price.oracle-chainlink',
                                 {"base": {"symbol": "WETH"}})
        self.run_model_chainlink('price.oracle-chainlink',
                                 {"base": {"symbol": "WBTC"}})
        self.run_model_chainlink('price.oracle-chainlink',
                                 {"base": {"address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"}})
        self.run_model_chainlink('price.oracle-chainlink',
                                 {"base": {"address": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"}})

    def test_price_by_feed(self):
        self.title('Chainlink - Feed')

        self.run_model_chainlink('chainlink.price-by-feed',
                                 {"address": "0x37bC7498f4FF12C19678ee8fE19d713b87F6a9e6"})  # simple feed
        self.run_model_chainlink('chainlink.price-by-feed',
                                 {"address": "0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419"})  # aggregator

    def test_override(self):
        self.title('Chainlink - Override')
        test_time = datetime(2023, 7, 31, tzinfo=timezone.utc)

        for chain_id, address_book in CHAINLINK_OVERRIDE_FEED.items():
            test_block_number = self.run_model_with_output(
                'chain.get-block',
                {'timestamp': int(test_time.timestamp())},
                chain_id=chain_id)['output']['block_number']

            for address in address_book:
                self.run_model('price.oracle-chainlink',
                               {"base": address},
                               chain_id=chain_id,
                               block_number=test_block_number)
