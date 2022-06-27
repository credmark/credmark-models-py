# pylint:disable=locally-disabled,line-too-long

import json
import sys
from typing import Optional, List
from types import ModuleType
from unittest import TestCase


class CMKTest(TestCase):
    type: str = 'prod'
    pre_flag: List[str] = []
    post_flag: List[str] = []
    api_url: List[str] = []

    block_number: int = 0
    test_n: int = 0
    start_n: int = 0
    test_module: ModuleType

    def title(self, title):
        print(f'\n{title}\n')

    def run_model(self, model_slug, model_input, exit_code: Optional[int] = 0, block_number: Optional[int] = None):
        if self.type == 'test':
            cmd = 'python test/test.py'
        else:
            cmd = 'credmark-dev'
        sys.argv = ([cmd] +
                    self.pre_flag +
                    ['run', model_slug, '-j'] +
                    ['-i', json.dumps(model_input)] +
                    self.post_flag +
                    [f'-b {self.block_number if block_number is None else block_number}'])

        if self.start_n > CMKTest.test_n:
            print(f'Skip ({CMKTest.test_n})')
            CMKTest.test_n += 1
            return

        cmd_line = ' '.join(sys.argv)
        print(f'Running case ({CMKTest.test_n}): expected {exit_code=} {cmd_line}')

        succeed = False
        try:
            self.test_module.main()
        except SystemExit as err:
            print(f'{err=}, {err.code=}, Expected {exit_code=}')
            self.assertTrue(err.code == exit_code)
            succeed = True
        finally:
            print(f'{"Finished" if succeed else "Failed"} case ({CMKTest.test_n}): {cmd_line}')
            if not succeed:
                sys.exit()

        CMKTest.test_n += 1
