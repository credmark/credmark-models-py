# pylint:disable=line-too-long

from cmf_test import CMFTest


class TestTLS(CMFTest):
    def test(self):
        result = self.run_model_with_output(
            'tls.score', {"address": "0x0000000000000000000000000000000000000348"}, block_number=16583473)
        self.assertEqual(
            result['output'],
            {"address": "0x0000000000000000000000000000000000000348",
             "score": None,
             "items": [{"name": "Fiat currency code USD", "impact": "!"}]})

        result = self.run_model_with_output(
            'tls.score', {"address": "0x0000000000000000000000000000000000000349"}, block_number=16583473)
        self.assertEqual(
            result['output'],
            {"address": "0x0000000000000000000000000000000000000349",
             "score": None,
             "items": [{"name": "Not an EOA", "impact": "!"}]})

        # 0x208A9C9D8E1d33a4f5b371Bf1864AA125379Ba1B: No source code, or not EOA for earlier block
        result = self.run_model_with_output('tls.score', {"address": "0x208A9C9D8E1d33a4f5b371Bf1864AA125379Ba1B"})
        self.assertEqual(
            result['output'],
            {"address": "0x208a9c9d8e1d33a4f5b371bf1864aa125379ba1b",
             "score": None,
             "items": [{"name": "Not an EOA", "impact": "!"}]})

        result = self.run_model_with_output(
            'tls.score', {"address": "0x208A9C9D8E1d33a4f5b371Bf1864AA125379Ba1B"}, block_number=16583473)
        self.assertEqual(
            result['output'],
            {"address": "0x208a9c9d8e1d33a4f5b371bf1864aa125379ba1b",
             "score": None,
             "items": [{"name": "EOA", "impact": "0"}, {"name": "No ABI from EtherScan", "impact": "!"}]})

        # Comptroller 0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B
        result = self.run_model_with_output(
            'tls.score', {"address": "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"}, block_number=16583473)
        self.assertEqual(
            result['output'],
            {"address": "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",
             "score": None,
             "items": [{"name": "EOA", "impact": "0"}, {"name": "Proxy contract", "impact": "0"}, {"name": "Found ABI from EtherScan", "impact": "+"}, {"name": "Not an ERC20 Token", "impact": "!"}]})

        # Unikey.finance 0x0AdD679A421f63455372B57530e614B6CD77d2Fe scam
        result = self.run_model_with_output(
            'tls.score', {"address": "0x0AdD679A421f63455372B57530e614B6CD77d2Fe"}, block_number=16583473)
        self.assertEqual(
            result['output'],
            {"address": "0x0add679a421f63455372b57530e614b6cd77d2fe",
             "score": 3.0,
             "items": [{"name": "EOA", "impact": "0"}, {"name": "Not a proxy contract", "impact": "0"}, {"name": "Found ABI from EtherScan", "impact": "+"}, {"name": "ERC20 Token", "impact": "0"}, {"name": "There is no liquidity in 1 pools for 0x0add679a421f63455372b57530e614b6cd77d2fe.", "impact": "!"}, {"name": "No transfer during during last 24h (16576315 to 16583473) or (2023-02-07 10:29:59+00:00 to 2023-02-08 10:29:59+00:00)", "impact": "!"}]})

        # AAVE 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9
        result = self.run_model_with_output(
            'tls.score', {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}, block_number=16583473)
        self.assertEqual(
            result['output'],
            {"address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",
             "score": 7,
             "items": [
                 {"name": "EOA", "impact": "0"},
                 {"name": "Proxy contract", "impact": "0"},
                 {"name": "Found ABI from EtherScan", "impact": "+"},
                 {"name": "ERC20 Token", "impact": "0"},
                 {"name": "Has price from DEX: {'src': 'uniswap-v2,sushiswap,uniswap-v3|Non-zero:10|Zero:1|4.0', 'price': 88.86499599495042, 'quoteAddress': '0x0000000000000000000000000000000000000348'}", "impact": "+"},
                 {"name": "974 transfers during during last 24h (16576315 to 16583473) or (2023-02-07 10:29:59+00:00 to 2023-02-08 10:29:59+00:00)", "impact": "+"}]
             })
