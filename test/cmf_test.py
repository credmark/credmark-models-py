# pylint:disable=locally-disabled,line-too-long, dangerous-default-value

import contextlib
import io
import json
import logging
import sys
from datetime import datetime, timedelta
from importlib import import_module
from types import ModuleType
from typing import List, Optional
from unittest import TestCase


@contextlib.contextmanager
def capture_output():
    output = {}
    try:
        # Redirect
        sys.stdout = io.TextIOWrapper(io.BytesIO(), sys.stdout.encoding)
        sys.stderr = io.TextIOWrapper(io.BytesIO(), sys.stderr.encoding)
        yield output
    finally:
        # Read
        sys.stdout.seek(0)
        sys.stderr.seek(0)
        output['stdout'] = sys.stdout.read()
        output['stderr'] = sys.stderr.read()
        sys.stdout.close()
        sys.stderr.close()

        # Restore
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


class CMFTest(TestCase):
    def __init__(self, methodName='runTest', request_timeout: int = 6400):
        mod_model_api = import_module('credmark.cmf.engine.model_api')
        mod_model_api.RUN_REQUEST_TIMEOUT = request_timeout  # type: ignore
        super().__init__(methodName)

    type: str = 'prod'
    pre_flag: List[str] = []
    post_flag: List[str] = []
    api_url: List[str] = []

    block_number: int = 0
    test_n: int = 0
    start_n: int = 0
    test_main: ModuleType = import_module('credmark.cmf.credmark_dev')
    fail_first: bool = True
    skip_nonzero: bool = False

    def title(self, title):
        logging.info(f'\n{title}\n')

    def run_model_with_output(self,
                              model_slug,
                              model_input=None,
                              exit_code: Optional[int] = 0,
                              block_number: Optional[int] = None,
                              chain_id: int = 1,
                              latest_block=False):
        model_input = {} if model_input is None else model_input

        if self.type == 'test':
            cmd = 'python test/test.py'
        else:
            cmd = 'credmark-dev'

        sys.argv = ([cmd] +
                    self.pre_flag +
                    ['run', model_slug, '-j'] +
                    ['-i', json.dumps(model_input)] +
                    self.post_flag +
                    ([] if latest_block else ['-b', f'{self.block_number if block_number is None else block_number}']) +
                    ['-c', str(chain_id)])

        cmd_line = ' '.join(sys.argv)

        # no self.pre_flag
        cmd_line_local = ' '.join(
            [cmd] +
            ['run', model_slug, '-j'] +
            ['-i', f"'{json.dumps(model_input)}'"] +
            self.post_flag +
            ([] if latest_block else [f'-b {self.block_number if block_number is None else block_number}']) +
            ['-c', str(chain_id)])

        if self.start_n > CMFTest.test_n:
            logging.info(f'Skip ({CMFTest.test_n})')
            CMFTest.test_n += 1
            return {}

        logging.info(
            f'Running case ({self.__class__.__name__}.{self._testMethodName}.{CMFTest.test_n}): expected {exit_code=} {cmd_line}')

        if self.skip_nonzero and exit_code != 0:
            return {}

        succeed = False
        start = None
        duration = timedelta(seconds=0)
        err_code = None
        with capture_output() as output:
            try:
                start = datetime.now()
                self.test_main.main()
            except SystemExit as err:
                logging.info(f'{err=}, {err.code=}, Expected {exit_code=}')
                err_code = err.code

        print(output['stdout'], file=sys.stdout)
        print(output['stderr'], file=sys.stdout)

        self.assertTrue(err_code == exit_code)
        succeed = True

        if start is not None:
            duration = datetime.now() - start
        logging.info(
            (f'{"Finished" if succeed else "Failed"}\n'
             f'I ran: {cmd_line}\n'
             f'U run: {cmd_line_local}\n'
             f'case ({self.__class__.__name__}.{self._testMethodName}.{CMFTest.test_n}) {duration.total_seconds():.2f} sec\n'
             ))

        CMFTest.test_n += 1
        stdout_result: dict = json.loads(output['stdout'])

        if self.fail_first and not succeed:
            sys.exit()

        return stdout_result

    def run_model(self,
                  model_slug,
                  model_input=None,
                  exit_code: Optional[int] = 0,
                  block_number: Optional[int] = None,
                  chain_id: int = 1,
                  latest_block=False):
        model_input = {} if model_input is None else model_input
        if self.type == 'test':
            cmd = 'python test/test.py'
        else:
            cmd = 'credmark-dev'
        sys.argv = ([cmd] +
                    self.pre_flag +
                    ['run', model_slug, '-j'] +
                    ['-i', json.dumps(model_input)] +
                    self.post_flag +
                    ([] if latest_block else ['-b', f'{self.block_number if block_number is None else block_number}']) +
                    ['-c', str(chain_id)])

        cmd_line = ' '.join(sys.argv)

        # no self.pre_flag
        cmd_line_local = ' '.join(
            [cmd] +
            ['run', model_slug, '-j'] +
            ['-i', f"'{json.dumps(model_input)}'"] +
            self.post_flag +
            ([] if latest_block else [f'-b {self.block_number if block_number is None else block_number}']) +
            ['-c', str(chain_id)])

        if self.start_n > CMFTest.test_n:
            logging.info(f'Skip ({CMFTest.test_n})')
            CMFTest.test_n += 1
            return {}

        logging.info(
            f'Running case ({self.__class__.__name__}.{self._testMethodName}.{CMFTest.test_n}): expected {exit_code=} {cmd_line}')

        if self.skip_nonzero and exit_code != 0:
            return {}

        succeed = False
        start = None
        duration = timedelta(seconds=0)
        err_code = None
        try:
            start = datetime.now()
            self.test_main.main()
        except SystemExit as err:
            logging.info(f'{err=}, {err.code=}, Expected {exit_code=}')
            err_code = err.code
            self.assertTrue(err_code == exit_code)
            succeed = True
        finally:
            if start is not None:
                duration = datetime.now() - start
            logging.info(
                (f'{"Finished" if succeed else "Failed"}\n'
                 f'I ran: {cmd_line}\n'
                 f'U run: {cmd_line_local}\n'
                 f'case ({self.__class__.__name__}.{self._testMethodName}.{CMFTest.test_n}) {duration.total_seconds():.2f} sec\n'
                 ))

        CMFTest.test_n += 1

        if self.fail_first and not succeed:
            sys.exit()
