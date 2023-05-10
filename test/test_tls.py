# pylint:disable=line-too-long, too-many-return-statements, invalid-name

import math
import os

from cmf_test import CMFTest
from credmark.dto.encoder import json_dumps


def compare_dict(value_a, value_b):
    if isinstance(value_a, list):
        for i, v in enumerate(value_a):
            if not compare_dict(v, value_b[i]):
                return False
        return True
    elif isinstance(value_a, dict) and isinstance(value_b, dict):
        for k, v in value_a.items():
            if isinstance(v, dict):
                if not compare_dict(v, value_b[k]):
                    return False
            elif isinstance(v, list):
                return compare_dict(sorted(v, key=lambda x: list(x.keys()) if isinstance(x, dict) else [x]),
                                    sorted(value_b[k], key=lambda x: list(x.keys()) if isinstance(x, dict) else [x]))
            elif k not in value_b:
                print(k, v, value_b[k])
                return False
            else:
                return compare_dict(v, value_b[k])

        return True
    elif isinstance(value_a, float) and isinstance(value_b, float):
        return math.isclose(value_a, value_b, rel_tol=1e-4)
    return value_a == value_b


class TestTLSBatch(CMFTest):
    pass


def run_tls_for_token(self, _addr, _block_number):
    tls_score = self.run_model_with_output(
        'tls.score', {"address": _addr}, block_number=_block_number)
    with open(f'tmp/all_tokens_score/{_addr}_{_block_number}.txt', 'w') as f:
        f.write(json_dumps(tls_score))


def add_test(_class, _addresses, _block_number, _token_added_n):
    for addr in _addresses:
        if addr == '0x0000000000000000000000000000000000000000':
            continue
        if addr.startswith('%% '):
            addr = addr[3:]
        _token_added_n += 1
        print((_token_added_n, addr[:42], _block_number))
        setattr(_class, f'test_{_class.__name__}_{_token_added_n:05d}',
                lambda self, addr=addr[:42], _block_number=_block_number:
                run_tls_for_token(self, _addr=addr, _block_number=_block_number))
    return _token_added_n


def init_tls_batch():
    block_number = 17170231
    token_list_files = ['../price_api/scripts/all_tokens.txt', '../price_api/scripts/all_tokens_junk.txt']
    token_added_n = 0
    for token_list_fp in token_list_files:
        if os.path.exists(token_list_fp):
            with open(token_list_fp, 'r') as f:
                _addresses = f.read().splitlines()
                token_added_n = add_test(TestTLSBatch, _addresses, block_number, token_added_n)
    print(f'Added {token_added_n} tokens to TestTLSBatch')


class TestTLSAll(CMFTest):
    def init_tls_all(self, page, page_end, page_limit):
        assert page <= page_end
        assert page_limit <= 5000
        block_number = 17170231
        token_result_page1 = self.run_model_with_output('token.all', {'limit': page_limit}, block_number=block_number)
        token_count = token_result_page1['output']['total']
        limit = token_result_page1['output']['limit']

        if page < 1:
            return

        token_added_n = 0
        if page == 1:
            addresses = [x['address'] for x in token_result_page1['output']['result']['some']]
            token_added_n = add_test(TestTLSAll, addresses, block_number, token_added_n)

        for page_n in range(2, token_count // limit + 1):
            if page <= page_n <= page_end:
                tokens_result = self.run_model_with_output(
                    'token.all', {'page': page_n, 'limit': page_limit}, block_number=block_number)
                addresses = [x['address'] for x in tokens_result['output']['result']['some']]
                token_added_n = add_test(TestTLSAll, addresses, block_number, token_added_n)


class TestTLS(CMFTest):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName, request_timeout=26400)

    def test_select(self):
        block_number = 16795830

        _latest_block = self.run_model_with_output(
            'rpc.get-latest-blocknumber')['output']['blockNumber']

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
            tls_score = self.run_model_with_output('tls.score', {"address": addr}, block_number=block_number)
            print((addr, tls_score['output']['score'],
                  tls_score['output']['items']))

    def test_sample(self):
        result = self.run_model_with_output(
            'tls.score', {"address": "0x0000000000000000000000000000000000000348"}, block_number=16583473)
        self.assertTrue(
            compare_dict(result['output'],
                         {"address": "0x0000000000000000000000000000000000000348",
                          "name": None,
                          "symbol": None,
                          "score": None,
                          "items": [{"name": "Fiat currency code USD", "impact": "!"}]}))

        result = self.run_model_with_output(
            'tls.score', {"address": "0x0000000000000000000000000000000000000349"}, block_number=16583473)
        self.assertTrue(
            compare_dict(result['output'],
                         {"address": "0x0000000000000000000000000000000000000349",
                          "name": None,
                          "symbol": None,
                          "score": None,
                          "items": [{"name": "Not an EOA", "impact": "!"}]}))

        # 0x208A9C9D8E1d33a4f5b371Bf1864AA125379Ba1B: No source code, or not EOA for earlier block
        result = self.run_model_with_output(
            'tls.score', {"address": "0x208A9C9D8E1d33a4f5b371Bf1864AA125379Ba1B"})
        self.assertTrue(
            compare_dict(result['output'],
                         {"address": "0x208a9c9d8e1d33a4f5b371bf1864aa125379ba1b",
                          "name": None,
                          "symbol": None,
                          "score": None,
                          "items": [{"name": "Not an EOA", "impact": "!"}]}))

        result = self.run_model_with_output(
            'tls.score', {"address": "0x208A9C9D8E1d33a4f5b371Bf1864AA125379Ba1B"}, block_number=16583473)
        self.assertTrue(
            compare_dict(result['output'],
                         {"address": "0x208a9c9d8e1d33a4f5b371bf1864aa125379ba1b",
                          "name": None,
                          "symbol": None,
                          "score": None,
                          "items": [{"name": "EOA", "impact": "0"}, {"name": "No ABI from EtherScan", "impact": "!"}]}))

        # Comptroller 0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B
        result = self.run_model_with_output(
            'tls.score', {"address": "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"}, block_number=16583473)
        self.assertTrue(
            compare_dict(result['output'],
                         {"address": "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",
                          "name": None,
                          "symbol": None,
                          "score": None,
                          "items": [{"name": "EOA", "impact": "0"}, {"name": "Proxy contract", "impact": "0"}, {"name": "Found ABI from EtherScan", "impact": "+"}, {"name": "Not an ERC20 Token", "impact": "!"}]}))

        result = self.run_model_with_output(
            'tls.score', {"address": "0x0AdD679A421f63455372B57530e614B6CD77d2Fe"}, block_number=16583473)
        print(result)
        self.assertTrue(
            compare_dict(result['output'],
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
                        "name": "There is no liquidity (4.999625031232302e-13 <= 1e-8) in 1 pools for 0x0add679a421f63455372b57530e614b6cd77d2fe.",
                        "impact": "-"
                    },
                    {
                        "name": "No transfer during during last 24h (16576315 to 16583473) or (2023-02-07 10:29:59+00:00 to 2023-02-08 10:29:59+00:00)",
                        "impact": "!"
                    }
                ]
            }))
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
