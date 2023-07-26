# pylint:disable=unused-import,line-too-long, invalid-name
# ruff: noqa: F401

import argparse
import inspect
import logging
import os
import sys
import unittest

# from test.no_test_avalanche import TestAvalanche
from cmf_test import CMFTest
from concurrencytest import ConcurrentTestSuite, fork_for_tests
from test_aave import TestAAVE
from test_aave_v3 import TestAAVEV3
from test_account import TestAccount
from test_arbitrum import TestArbitrumOne
from test_balancer import TestBalancer
from test_bsc import TestBSC
from test_chainlink import TestChainlink
from test_cmk import TestCMK
from test_compose import TestCompose
from test_compound import TestCompound, TestCompoundV3
from test_curve import TestCurve
from test_dashboard import TestDashboard
from test_example import TestExample
from test_fantom import TestFantom
from test_fiat import TestFiat
from test_finance import TestFinance
from test_ichi import TestICHI
from test_index_coop import TestIndexCoop
from test_ipor import TestIPOR
from test_models import TestModels
from test_nft import TestNFT
from test_optimism import TestOptimism
from test_pancake import TestPancakeSwap
from test_polygon import TestPolygon
from test_price import TestPrice
from test_quickswap import TestQuickSwap
from test_speed import TestSpeed
from test_sushiswap import TestSushiSwap
from test_tls import TestTLS, TestTLSAll, TestTLSBatch, init_tls_batch
from test_token import TestToken
from test_tvl import TestTVL
from test_uniswap import TestUniswap

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level='INFO')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('type', type=str, default='prod',
                        help=('Test type: \n'
                              '- prod(local model + gw)\n'
                              '- test(local gw)\n'
                              '- gw (official gateway only'))
    parser.add_argument('start_n', type=int, default=0,
                        help='case number to start')
    parser.add_argument('-b', '--block_number', type=int, default=14249450,
                        help='Block number to run')
    parser.add_argument('-s', '--serial', action='store_true', default=False,
                        help='Run tests in serial')
    parser.add_argument('-p', '--parallel_count', type=int, default=10,
                        help='Parallel count')
    parser.add_argument('--api_url', type=str, default='http://localhost:8700',
                        help='API to use')
    parser.add_argument('-t', '--tests', type=str, default='__all__',
                        help='test to run')
    parser.add_argument('-l', '--list', action='store_true', default=False,
                        help='List runnable tests')
    parser.add_argument('-g', '--page', type=int, default=1,
                        help='page to run tlsall')
    parser.add_argument('-ge', '--page-end', type=int, default=1,
                        help='page end to run tlsall')
    parser.add_argument('-gl', '--page-limit', type=int, default=5000,
                        help='page limit to run tlsall')

    args = vars(parser.parse_args())
    CMFTest.type = args['type']

    if CMFTest.type == 'test':
        sys.path.insert(0, os.path.join('..', 'credmark-model-framework-py'))
        CMFTest.post_flag = ['-l', '-', f'--api_url={args["api_url"]}']
        CMFTest.pre_flag = ['--model_path', 'x']
        parallel_count = args['parallel_count']
    elif CMFTest.type == 'test-local':
        sys.path.insert(0, os.path.join('..', 'credmark-model-framework-py'))
        CMFTest.post_flag = ['-l', '*', f'--api_url={args["api_url"]}']
        CMFTest.pre_flag = []
        parallel_count = args['parallel_count']
    elif CMFTest.type == 'prod':
        CMFTest.post_flag = []
        CMFTest.pre_flag = []
        parallel_count = args['parallel_count']
    elif CMFTest.type == 'prod-local':
        CMFTest.post_flag = ['-l', '*']
        CMFTest.pre_flag = []
        parallel_count = args['parallel_count']
    elif CMFTest.type == 'gw':
        CMFTest.post_flag = ['-l', '-']
        CMFTest.pre_flag = ['--model_path', 'x']
        CMFTest.skip_nonzero = True
        parallel_count = args['parallel_count']
    else:
        print(f'Unknown test type {args["type"]}')
        parallel_count = 1
        sys.exit()

    print(f'Run with flags of: {CMFTest.pre_flag} {CMFTest.post_flag} {args["tests"]}')

    CMFTest.block_number = args["block_number"]
    CMFTest.start_n = args["start_n"]

    # token_price_deps='price.quote,price.quote,uniswap-v2.get-weighted-price,uniswap-v3.get-weighted-price,sushiswap.get-weighted-price,uniswap-v3.get-pool-info'
    # var_deps=finance.var-engine,finance.var-reference,price.quote,finance.get-one,${token_price_deps}

    # test-model -t bsc,polygon,aave,account,balancer,chainlink,cmk,compose,compound,curve,dashboard,example,fiat,finance
    # test-model -t index,price,speed,sushiswap,token,tvl,uniswap

    all_tests_name = [o.__name__
                      for _n, o in locals().items()
                      if inspect.isclass(o) and
                      issubclass(o, CMFTest) and o != CMFTest
                      ]

    print(f'All Tests: {all_tests_name} but only run [TestTLSBatch, TestTLSAll] with '
          '[-t tlsbatch, -t tlsall -g n -ge m -gl x] individually')
    if args['list']:
        sys.exit(0)

    tests_split = args['tests'].split(",")

    all_tests_sel = [o for _n, o in locals().items()
                     if inspect.isclass(o) and
                     issubclass(o, CMFTest) and
                     (args['tests'] == '__all__' or sum(o.__name__.lower().endswith(t.lower())
                                                        for t in tests_split) == 1)]

    if len(tests_split) == 1:
        if tests_split[0] == 'tlsbatch':
            init_tls_batch()
        if tests_split[0] == 'tlsall':
            TestTLSAll().init_tls_all(
                page=args['page'], page_end=args['page_end'], page_limit=args['page_limit'])
    else:
        all_tests_sel = [o for o in all_tests_sel if o.__name__ !=
                         'TestTLSBatch' or o.__name__ != 'TestTLSAll']
        print(f'Run Tests: {all_tests_sel}')

    suites = unittest.TestSuite([unittest.TestLoader().loadTestsFromTestCase(
        testCaseClass=x) for x in all_tests_sel])

    if args['serial']:
        CMFTest.fail_first = True
        sys.argv = sys.argv[:1]
        if args['tests'] != '__all__':
            if len(all_tests_sel) == 0:
                sys.exit()

            for test_name in (x.__name__ for x in all_tests_sel):
                sys.argv.insert(len(sys.argv), test_name)
        unittest.main(failfast=True)
    else:
        runner = unittest.TextTestRunner()
        CMFTest.fail_first = False
        concurrent_suite = ConcurrentTestSuite(
            suites, fork_for_tests(parallel_count))
        runner.run(concurrent_suite)
