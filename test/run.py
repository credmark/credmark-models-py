import os
import sys
import argparse
import unittest
from unittest import TestCase
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level='INFO')


class CMKTest(TestCase):
    type: str = 'prod'
    local_flag: str = ''
    block_number: str = '-b 123143'

    def test_run(self):
        print(self.type)
        print(self.local_flag)

        input = '{"address": "0xCE017A1dcE5A15668C4299263019c017154ACE17"}'
        sys.argv = ['', 'run', 'account.portfolio', f'-i {input}', '-j']
        try:
            main()
        except SystemExit as err:
            self.assertTrue(err.code == 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--type', type=str, default='prod', required=False,
                        help='Test type: prod (local model + gw), test (local gw), gw (official gateway only)')

    args = vars(parser.parse_args())
    CMKTest.type = args['type']
    print(args)

    if args['type'] == 'test':
        sys.path.insert(0, os.path.join('..', 'credmark-model-framework-py'))
        CMKTest.local_flag = '-l -'
    elif args['type'] == 'prod':
        CMKTest.local_flag = ''
    elif args['type'] == 'gw':
        CMKTest.local_flag = '-l -'

    from credmark.cmf.credmark_dev import main

    sys.argv = sys.argv[:1]
    unittest.main()
