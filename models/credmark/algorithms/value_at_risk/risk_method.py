from credmark.cmf.model.errors import (
    ModelRunError,
)

import numpy as np
import logging


def calc_var(ppl, lvl):
    if lvl < 0 or lvl > 1:
        raise ModelRunError(f'Invalid confidence level {lvl=}')

    ppl_d = ppl.copy()
    len_ppl_d = ppl_d.shape[0]
    if len_ppl_d <= 1:
        raise ModelRunError(f'PPL is too short to calculate VaR {ppl_d=}')
    res = np.percentile(ppl_d, lvl*100, method='interpolated_inverted_cdf')
    return res


def calc_es(ppl, lvl):
    """
    Get the VaR from calc_var.

    ppl = 0 1 2 3 4
    var =    ^ midpoint of 1 and 2
    es  = (0 + 1 + 1.5 * 0.5) / 2.5
    """
    ppl_sorted = ppl.copy()
    ppl_sorted.sort()
    var = calc_var(ppl, lvl)
    multiplier = 1/(len(ppl_sorted)*lvl)
    weight_var = len(ppl_sorted)*lvl - ppl_sorted[ppl_sorted >= var][0]
    sum_of_less_than_var = ppl_sorted[ppl_sorted < var].sum()
    es = multiplier * (var * weight_var + sum_of_less_than_var)
    return es


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_ppl = np.arange(260)
    assert np.isclose(calc_var(test_ppl, 0.01), 1 * 0.4 + 2 * 0.6)
    logging.info(f'VaR for [0...260] at 0.01 confidence level is {calc_var(np.arange(260), 0.01)}')

    assert np.isclose(calc_var(test_ppl, 0.01), calc_var(test_ppl[::-1], 0.01))
    assert np.isclose(calc_es(test_ppl, 0.01), (0 + 1 + 1.6 * 0.6) / 2.6)
    logging.info(f'ES for [0...260] at 0.01 confidence level is {calc_es(test_ppl, 0.01)}')
