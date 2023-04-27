# pylint:disable=line-too-long

import json
import math
import os

from cmf_test import CMFTest


def compare_dict(a, b):
    if isinstance(a, list):
        for i, v in enumerate(a):
            if not compare_dict(v, b[i]):
                return False
        return True
    elif isinstance(a, dict) and isinstance(b, dict):
        for k, v in a.items():
            if isinstance(v, dict):
                if not compare_dict(v, b[k]):
                    return False
            elif isinstance(v, list):
                return compare_dict(sorted(v, key=lambda x: list(x.keys()) if isinstance(x, dict) else [x]),
                                    sorted(b[k], key=lambda x: list(x.keys()) if isinstance(x, dict) else [x]))
            elif k not in b:
                print(k, v, b[k])
                return False
            else:
                return compare_dict(v, b[k])

        return True
    elif isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-4)
    return a == b


class TestTLSBatch(CMFTest):
    def test_batch(self):
        block_number = 16795830
        # read the file from tmp/all_tokens.txt
        if os.path.exists('tmp/all_tokens.txt'):
            with open('tmp/all_tokens.txt', 'r') as f:
                _addresses = f.read().splitlines()
                for addr in _addresses:
                    tls_score = self.run_model_with_output(
                        'tls.score', {"address": addr}, block_number=block_number)
                    with open(f'tmp/all_tokens_score/{addr}_{block_number}.txt', 'a') as f:
                        f.write(json.dumps(tls_score['output']))


class TestTLS(CMFTest):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName, request_timeout=26400)

    def test_select(self):
        block_number = 16795830

        _latest_block = self.run_model_with_output(
            'rpc.get-latest-blocknumber', {})['output']['blockNumber']

        # AAVE: 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9
        # UNI: 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984
        # LINK: 0x514910771af9ca656af840dff83e8264ecf986ca
        # cDAI: 0x5d3a536e4d6dbd6114cc1ead35777bab948e3643
        # DAI: 0x6b175474e89094c44da98b954eedeac495271d0f
        for addr in [
            '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9',  # AAVE
            '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984',  # UNI
            '0x514910771af9ca656af840dff83e8264ecf986ca',  # LINK
            '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643',  # cDAI
            '0x6b175474e89094c44da98b954eedeac495271d0f',  # DAI
        ]:
            tls_score = self.run_model_with_output(
                'tls.score', {"address": addr}, block_number=block_number)
            print((addr, tls_score['output']['score'],
                  tls_score['output']['items']))

    def test_sample(self):
        result = self.run_model_with_output(
            'tls.score', {"address": "0x0000000000000000000000000000000000000348"}, block_number=16583473)
        self.assertEqual(
            result['output'],
            {"address": "0x0000000000000000000000000000000000000348",
             "name": None,
             "symbol": None,
             "score": None,
             "items": [{"name": "Fiat currency code USD", "impact": "!"}]})

        result = self.run_model_with_output(
            'tls.score', {"address": "0x0000000000000000000000000000000000000349"}, block_number=16583473)
        self.assertEqual(
            result['output'],
            {"address": "0x0000000000000000000000000000000000000349",
             "name": None,
             "symbol": None,
             "score": None,
             "items": [{"name": "Not an EOA", "impact": "!"}]})

        # 0x208A9C9D8E1d33a4f5b371Bf1864AA125379Ba1B: No source code, or not EOA for earlier block
        result = self.run_model_with_output(
            'tls.score', {"address": "0x208A9C9D8E1d33a4f5b371Bf1864AA125379Ba1B"})
        self.assertEqual(
            result['output'],
            {"address": "0x208a9c9d8e1d33a4f5b371bf1864aa125379ba1b",
             "name": None,
             "symbol": None,
             "score": None,
             "items": [{"name": "Not an EOA", "impact": "!"}]})

        result = self.run_model_with_output(
            'tls.score', {"address": "0x208A9C9D8E1d33a4f5b371Bf1864AA125379Ba1B"}, block_number=16583473)
        self.assertEqual(
            result['output'],
            {"address": "0x208a9c9d8e1d33a4f5b371bf1864aa125379ba1b",
             "name": None,
             "symbol": None,
             "score": None,
             "items": [{"name": "EOA", "impact": "0"}, {"name": "No ABI from EtherScan", "impact": "!"}]})

        # Comptroller 0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B
        result = self.run_model_with_output(
            'tls.score', {"address": "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"}, block_number=16583473)
        self.assertEqual(
            result['output'],
            {"address": "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",
             "name": None,
             "symbol": None,
             "score": None,
             "items": [{"name": "EOA", "impact": "0"}, {"name": "Proxy contract", "impact": "0"}, {"name": "Found ABI from EtherScan", "impact": "+"}, {"name": "Not an ERC20 Token", "impact": "!"}]})

        result = self.run_model_with_output(
            'tls.score', {"address": "0x0AdD679A421f63455372B57530e614B6CD77d2Fe"}, block_number=16583473)
        print(result)
        self.assertEqual(
            result['output'],
            {
                "address": "0x0add679a421f63455372b57530e614b6cd77d2fe",
                "name": "Unikey.finance",
                "symbol": "UNKY",
                "score": 3,
                "items": [
                    {
                        "name": "EOA",
                        "impact": "0"
                    },
                    {
                        "name": "Not a proxy contract",
                        "impact": "0"
                    },
                    {
                        "name": "Found ABI from EtherScan",
                        "impact": "+"
                    },
                    {
                        "name": "ERC20 Token",
                        "impact": "0"
                    },
                    {
                        "name": "There is no liquidity (<= 1e-8) in 1 pools for 0x0add679a421f63455372b57530e614b6cd77d2fe.",
                        "impact": "-"
                    },
                    {
                        "name": "No transfer during during last 24h (16576315 to 16583473) or (2023-02-07 10:29:59+00:00 to 2023-02-08 10:29:59+00:00)",
                        "impact": "!"
                    }
                ]
            })
        # {"name": "No transfer during during last 12h (16579888 to 16583473) or (2023-02-07 22:29:59+00:00 to 2023-02-08 10:29:59+00:00)", "impact": "!"}]})

        # AAVE 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9
        result = self.run_model_with_output(
            'tls.score', {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"}, block_number=16583473)

        print(result)
        self.assertTrue(
            compare_dict(result['output'],
                         {
                "address": "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",
                "name": "Aave Token",
                "symbol": "AAVE",
                "score": 7,
                "items": [
                    {
                        "name": "EOA",
                        "impact": "0"
                    },
                    {
                        "name": "Proxy contract",
                        "impact": "0"
                    },
                    {
                        "name": "Found ABI from EtherScan",
                        "impact": "+"
                    },
                    {
                        "name": "ERC20 Token",
                        "impact": "0"
                    },
                    {
                        "name": [
                            "DEX price",
                            {
                                "price": 88.85804532122681,
                                "src": "sushiswap,uniswap-v2,uniswap-v3",
                                "quoteAddress": "0x0000000000000000000000000000000000000348"
                            }
                        ],
                        "impact": "+"
                    },
                    {
                        "name": "974 transfers during during last 24h (16576315 to 16583473) or (2023-02-07 10:29:59+00:00 to 2023-02-08 10:29:59+00:00)",
                        "impact": "+"
                    }
                ]
            }))
        # 974

        # aWETH 0x030bA81f1c18d280636F32af80b9AAd02Cf0854e
        result = self.run_model_with_output(
            'tls.score', {"address": "0x030bA81f1c18d280636F32af80b9AAd02Cf0854e"}, block_number=16583473)

        print(result)
        self.assertTrue(
            compare_dict(result['output'], {
                "address": "0x030ba81f1c18d280636f32af80b9aad02cf0854e",
                "name": "Aave interest bearing WETH",
                "symbol": "aWETH",
                "score": 7,
                "items": [
                    {
                        "name": "EOA",
                        "impact": "0"
                    },
                    {
                        "name": "Proxy contract",
                        "impact": "0"
                    },
                    {
                        "name": "Found ABI from EtherScan",
                        "impact": "+"
                    },
                    {
                        "name": "ERC20 Token",
                        "impact": "0"
                    },
                    {
                        "name": [
                            "DEX price",
                            {
                                "price": 1670.95363668341,
                                "src": "sushiswap,uniswap-v2,uniswap-v3",
                                "quoteAddress": "0x0000000000000000000000000000000000000348"
                            }
                        ],
                        "impact": "+"
                    },
                    {
                        "name": [
                            "DEX price is taken from the underlying",
                            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                            {
                                "address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                                "name": "Wrapped Ether",
                                "symbol": "WETH",
                                "score": 7,
                                "items": [
                                    {
                                        "name": "EOA",
                                        "impact": "0"
                                    },
                                    {
                                        "name": "Not a proxy contract",
                                        "impact": "0"
                                    },
                                    {
                                        "name": "Found ABI from EtherScan",
                                        "impact": "+"
                                    },
                                    {
                                        "name": "ERC20 Token",
                                        "impact": "0"
                                    },
                                    {
                                        "name": [
                                            "DEX price",
                                            {
                                                "price": 1670.95363668341,
                                                "src": "sushiswap,uniswap-v2,uniswap-v3",
                                                "quoteAddress": "0x0000000000000000000000000000000000000348"
                                            }
                                        ],
                                        "impact": "+"
                                    },
                                    {
                                        "name": "266589 transfers during during last 24h (16576315 to 16583473) or (2023-02-07 10:29:59+00:00 to 2023-02-08 10:29:59+00:00)",
                                        "impact": "+"
                                    }
                                ]
                            }
                        ],
                        "impact": "0"
                    },
                    {
                        "name": "405 transfers during during last 24h (16576315 to 16583473) or (2023-02-07 10:29:59+00:00 to 2023-02-08 10:29:59+00:00)",
                        "impact": "+"
                    }
                ]
            }))
