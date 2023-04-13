# pylint:disable=locally-disabled,line-too-long

from cmf_test import CMFTest


class TestCompose(CMFTest):
    def test(self):
        self.title('Compose')

        self.run_model('compose.map-block-time-series',
                       {"modelSlug": "price.quote",
                        "modelInput": {"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}},
                        "endTimestamp": 1645446694,
                        "interval": 86400,
                        "count": 3,
                        "exclusive": True})

        self.run_model('compose.map-blocks',
                       {"modelSlug": "price.quote",
                        "modelInput": {"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}},
                        "blockNumbers": [14249443, 14219443, 14209443]})

        self.run_model('compose.map-inputs',
                       {"modelSlug": "price.quote",
                        "modelInputs": [
                            {"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}},
                            {"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}}]})

        self.run_model('price.quote-historical-multiple',
                       {"some": [{"base": {"symbol": "AAVE"}}], "interval": 86400, "count": 20, "exclusive": True})

        self.run_model('price.multiple-maybe',
                      {"slug": "price.dex-maybe", "some": [{"base": "USDC"}, {"base": "AAVE", "quote": "JPY"}]})

        self.run_model('series.block-window-interval',
                       {"modelSlug": "token.balance",
                        "modelInput": {
                            "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                            "account": "0x55FE002aefF02F77364de339a1292923A15844B8"
                        }, "window": 20000, "interval": 10000})
