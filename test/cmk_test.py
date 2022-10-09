# pylint:disable=locally-disabled,line-too-long

import json
import logging
import sys
from datetime import datetime, timedelta
from importlib import import_module
from types import ModuleType
from typing import List, Optional
from unittest import TestCase


class CMKTest(TestCase):
    def __init__(self, methodName='runTest'):
        mod_model_api = import_module('credmark.cmf.engine.model_api')
        mod_model_api.RUN_REQUEST_TIMEOUT = 6400  # type: ignore
        super().__init__(methodName)

    type: str = 'prod'
    pre_flag: List[str] = []
    post_flag: List[str] = []
    api_url: List[str] = []

    block_number: int = 0
    test_n: int = 0
    start_n: int = 0
    test_main: ModuleType
    fail_first: bool = True
    skip_nonzero: bool = False

    def title(self, title):
        logging.info(f'\n{title}\n')

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

        cmd_line = ' '.join(
            [cmd] +
            self.pre_flag +
            ['run', model_slug, '-j'] +
            ['-i', f"'{json.dumps(model_input)}'"] +
            self.post_flag +
            [f'-b {self.block_number if block_number is None else block_number}'])

        cmd_line_local = ' '.join(
            [cmd] +
            ['run', model_slug, '-j'] +
            ['-i', f"'{json.dumps(model_input)}'"] +
            self.post_flag +
            [f'-b {self.block_number if block_number is None else block_number}'])

        if self.start_n > CMKTest.test_n:
            logging.info(f'Skip ({CMKTest.test_n})')
            CMKTest.test_n += 1
            return

        logging.info(
            f'Running case ({self.__class__.__name__}.{self._testMethodName}.{CMKTest.test_n}): expected {exit_code=} {cmd_line}')

        if self.skip_nonzero and exit_code != 0:
            return

        succeed = False
        start = None
        duration = timedelta(seconds=0)
        try:
            start = datetime.now()
            self.test_main.main()
        except SystemExit as err:
            logging.info(f'{err=}, {err.code=}, Expected {exit_code=}')
            self.assertTrue(err.code == exit_code)
            succeed = True
        finally:
            if start is not None:
                duration = datetime.now() - start
            logging.info(
                (f'{"Finished" if succeed else "Failed"} '
                 f'case ({self.__class__.__name__}.{self._testMethodName}.{CMKTest.test_n}) {duration.total_seconds():.2f}s\n'
                 f'I ran: {cmd_line}\n'
                 f'U run: {cmd_line_local}'))
            if self.fail_first and not succeed:
                sys.exit()

        CMKTest.test_n += 1
