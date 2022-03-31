# pylint:disable=locally-disabled,line-too-long

import credmark.model
from credmark.model import ModelRunError

import os
import json
import numpy as np


TEST_CASE_REFERENCE = {
    'AAVE+WETH (39 days)': {
        'skip': True,
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}, {"amount":  1, "asset": {"symbol": "AAVE"}}]}, "window": "39 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
    'AAVE+WETH (90 days)': {
        'skip': True,
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}, {"amount":  1, "asset": {"symbol": "AAVE"}}]}, "window": "90 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
    'WETH (90 days)': {
        'skip': True,
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}]}, "window": "90 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
    'WETH (39 days)': {
        'skip': True,
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}]}, "window": "39 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
    'AAVE (39 days)': {
        'skip': True,
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "AAVE"}}]}, "window": "39 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
    'AAVE (90 days)': {
        'skip': True,
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "AAVE"}}]}, "window": "90 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
}


TEST_CASE_ENGINE = {
    'AAVE+WETH (39 days)': {
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}, {"amount":  1, "asset": {"symbol": "AAVE"}}]}, "window": "39 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
    'AAVE+WETH (90 days)': {
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}, {"amount":  1, "asset": {"symbol": "AAVE"}}]}, "window": "90 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
    'WETH (90 days)': {
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}]}, "window": "90 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
    'WETH (39 days)': {
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "WETH"}}]}, "window": "39 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
    'AAVE (39 days)': {
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "AAVE"}}]}, "window": "39 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
    'AAVE (90 days)': {
        'input': {"portfolio": {"positions": [{"amount":  1, "asset": {"symbol": "AAVE"}}]}, "window": "90 days", "intervals": [
            "1 day", "2 day", "5 day", "10 day", "12 days"], "as_ofs": ["2022-02-17", "2022-02-05"], "as_of_is_range": True, "confidences": [0, 0.01, 0.05, 1.0], "dev_mode": True},
    },
}

TEST_CASE = {
    'finance.var-reference': TEST_CASE_REFERENCE,
    'finance.var-engine': TEST_CASE_ENGINE,
}


@ credmark.model.describe(slug='finance.var-regtest',
                          version='1.0',
                          display_name='Value at Risk - Regression Test',
                          description='Value at Risk - Regression Test',
                          input=dict,
                          output=dict)
class ValueAtRiskRegressionTest(credmark.model.Model):
    def compare_dict(self, key_path, dict_a, dict_b, ratio_a_over_b=1):
        for k_a, v in dict_a.items():
            if k_a in dict_b:
                k_b = k_a
            else:
                k_b = str(k_a)
                assert k_b in dict_b
            new_key_path = key_path + [k_b]
            try:
                if isinstance(v, dict):
                    assert self.compare_dict(new_key_path, v, dict_b[k_b])
                elif isinstance(v, str):
                    assert v == dict_b[k_b]
                elif isinstance(v, float):
                    assert np.isclose(v, ratio_a_over_b * dict_b[k_b])
                else:
                    raise ModelRunError('')
            except:  # AssertionError as _err:
                print(f'Unequal value {dict_a[k_a]} != {dict_b[k_b]} at {new_key_path}')
                raise
        return True

    def run(self, input: dict) -> dict:
        dev_mode = input.get('dev_mode', False)

        dev_mode = True

        passed = []

        for model_slug, cases in TEST_CASE.items():
            for case_name, case_detail in cases.items():
                if 'skip' in case_detail and case_detail['skip']:
                    continue
                test_case = f'{model_slug}.{case_name}'
                self.logger.info(f'Testing {case_name} with {model_slug}')
                res = self.context.run_model(model_slug, input=case_detail['input'] | {'dev_mode': dev_mode})

                if dev_mode:
                    os.rename(os.path.join('tmp', 'df_res.csv'),
                              os.path.join('tmp', f'df_res_{test_case}.csv'))
                    if model_slug == 'finance.var-reference':
                        os.rename(os.path.join('tmp', 'df_hist.csv'),
                                  os.path.join('tmp', f'df_hist_{test_case}.csv'))
                    with open(os.path.join('tmp', f'{model_slug}.{case_name}.json'), 'w') as f:
                        f.write(res.__str__())

                regtest_file = os.path.join('tmp', f'regtest_{test_case}.json')
                if os.path.isfile(regtest_file):
                    with open(regtest_file, 'r') as f:
                        regtest_result = json.load(f)
                        try:
                            assert self.compare_dict([], res, regtest_result)
                            passed.append(test_case)
                        except AssertionError:
                            raise ModelRunError(f'Failed test case {case_name} with {model_slug}')
                else:
                    raise ModelRunError(f'Missing regtest result file {regtest_file}')

        return {'passed': passed}
