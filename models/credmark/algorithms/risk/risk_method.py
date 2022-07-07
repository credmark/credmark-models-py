import logging
from typing import List

import numpy as np
from credmark.cmf.model.errors import ModelRunError
from credmark.dto import DTO

np.seterr(all='raise')


class VaROutput(DTO):
    var: float
    ppls: List[float]
    weights: List[float]
    sorted_index: List[int]
    unsorted_index: List[int]

    @classmethod
    def default(cls):
        return cls(var=0.0, ppls=[], weights=[], sorted_index=[], unsorted_index=[])


class ESOutput(DTO):
    es: float
    ppls: List[float]
    weights: List[float]
    multiplier: float
    sorted_index: List[int]
    unsorted_index: List[int]
    var_result: VaROutput


def calc_var(ppl, lvl) -> VaROutput:
    if lvl < 0 or lvl > 1:
        raise ModelRunError(f'Invalid confidence level {lvl=}')

    ppl_sorted = ppl.copy()
    ppl_sorted.sort()
    len_ppl_d = ppl_sorted.shape[0]
    if len_ppl_d <= 1:
        raise ModelRunError(f'PPL is too short to calculate VaR {ppl_sorted=}')
    var = np.percentile(ppl_sorted, lvl*100, method='interpolated_inverted_cdf')
    where_var = ppl_sorted[np.isclose(ppl_sorted, var)]
    index_var = np.where(ppl_sorted >= var)[0][0]
    if where_var.shape[0] == 0:
        weight_var = [index_var+1-len_ppl_d*lvl, len_ppl_d*lvl - index_var]
        sorted_index = [index_var-1, index_var]
        unsorted_index = np.where(np.isin(ppl, ppl_sorted[sorted_index]))[0].tolist()
        return VaROutput(var=float(var),
                         ppls=ppl_sorted[sorted_index].tolist(),
                         weights=weight_var,
                         sorted_index=sorted_index,
                         unsorted_index=unsorted_index)
    else:
        weight_var = [len_ppl_d*lvl - index_var]
        sorted_index = [index_var]
        unsorted_index = np.where(np.isin(ppl, ppl_sorted[sorted_index]))[0].tolist()
        return VaROutput(var=float(var),
                         ppls=ppl_sorted[sorted_index].tolist(),
                         weights=weight_var,
                         sorted_index=sorted_index,
                         unsorted_index=unsorted_index)


def calc_es(ppl, lvl) -> ESOutput:
    """
    Get the VaR from calc_var.

    ppl = 0 1 2 3 4
    var =    ^ midpoint of 1 and 2
    es  = (0 + 1 + 1.5 * 0.5) / 2.5
    """
    ppl_dup = ppl.copy()
    var_result = calc_var(ppl_dup, lvl)
    var = var_result.var
    var_weight = var_result.weights
    multiplier = len(ppl_dup)*lvl
    sum_of_less_than_var = ppl_dup[ppl_dup < var].sum()
    sum_of_tails = var * var_weight[-1] + sum_of_less_than_var
    unsorted_index = np.where(ppl < var)[0].tolist()
    sorted_index = np.arange(var_result.sorted_index[-1]).tolist()
    es = 1/multiplier * sum_of_tails
    return ESOutput(es=es,
                    ppls=ppl_dup[ppl_dup < var].tolist() + [var],
                    weights=[1.0] * var_result.sorted_index[-1] + [var_result.weights[-1]],
                    multiplier=multiplier,
                    sorted_index=sorted_index,
                    unsorted_index=unsorted_index,
                    var_result=var_result)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_ppl = np.arange(260)
    assert np.isclose(calc_var(test_ppl, 0.01).var, calc_var(test_ppl[::-1], 0.01).var)

    assert np.isclose(calc_var(test_ppl, 0.01).var, 1 * 0.4 + 2 * 0.6)
    logging.info(f'VaR for [0...260] at 0.01 confidence level is {calc_var(np.arange(260), 0.01)}')

    assert np.isclose(calc_es(test_ppl, 0.01).es, (0 + 1 + 1.6 * 0.6) / 2.6)
    logging.info(f'ES for [0...260] at 0.01 confidence level is {calc_es(test_ppl, 0.01)}')

    test_ppl_100 = np.arange(100)
    assert np.isclose(calc_es(test_ppl_100, 0.01).es, (0) / 1)
    logging.info(f'ES for [0...100] at 0.01 confidence level is {calc_es(test_ppl_100, 0.01)}')

    assert np.isclose(calc_es(test_ppl_100, 0.03).es, (0 + 1 + 2) / 3)
    logging.info(f'ES for [0...100] at 0.03 confidence level is {calc_es(test_ppl_100, 0.03)}')

    assert np.isclose(calc_es(test_ppl_100, 0.035).es, (0 + 1 + 2 + 2.5 * 0.5) / 3.5)
    logging.info(f'ES for [0...100] at 0.035 confidence level is {calc_es(test_ppl_100, 0.035)}')

    assert np.isclose(calc_es(test_ppl_100, 0.037).es, (0 + 1 + 2 + 2.7 * 0.7) / 3.7)
    logging.info(f'ES for [0...100] at 0.0375 confidence level is {calc_es(test_ppl_100, 0.037)}')

    assert np.isclose(calc_es(test_ppl_100, 0.043).es, (0 + 1 + 2 + 3 + 3.3 * 0.3) / 4.3)
    logging.info(f'ES for [0...100] at 0.043 confidence level is {calc_es(test_ppl_100, 0.043)}')

    assert np.isclose(calc_es(test_ppl_100, 0.05).es, (0 + 1 + 2 + 3 + 4) / 5)
    logging.info(f'ES for [0...100] at 0.05 confidence level is {calc_es(test_ppl_100, 0.05)}')
