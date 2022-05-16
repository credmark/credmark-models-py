from credmark.cmf.model.errors import (
    ModelRunError,
)

import numpy as np


def calc_var(ppl, lvl):
    if lvl < 0 or lvl > 1:
        raise ModelRunError(f'Invalid confidence level {lvl=}')

    len_ppl_d = ppl.shape[0]
    if len_ppl_d <= 1:
        raise ModelRunError(f'PPL is too short to calculate VaR {ppl=}')

    ppl_d = ppl.copy()
    ppl_d.sort()
    if lvl == 0:
        return ppl_d[0]
    if lvl == 1:
        return ppl_d[-1]

    pos_f = lvl * (len_ppl_d - 1)
    if np.isclose(pos_f, 0):
        return ppl_d[0]
    if np.isclose(pos_f, len_ppl_d - 1):
        return ppl_d[-1]
    lower = int(np.floor(pos_f))
    upper = lower+1
    res = ppl_d[lower] * (upper - pos_f) + ppl_d[upper] * (pos_f - lower)
    return res


def calc_es(ppl, lvl):
    if lvl < 0 or lvl > 1:
        raise ModelRunError(f'Invalid confidence level {lvl=}')

    len_ppl_d = ppl.shape[0]
    if len_ppl_d <= 1:
        raise ModelRunError(f'PPL is too short to calculate VaR {ppl=}')

    ppl_d = ppl.copy()
    ppl_d.sort()
    if lvl == 0:
        return ppl_d[0]
    if lvl == 1:
        return ppl_d.mean()

    pos_f = lvl * (len_ppl_d - 1)
    if np.isclose(pos_f, 0):
        return ppl_d[0]
    if np.isclose(pos_f, len_ppl_d - 1):
        return ppl_d[-1]
    lower = int(np.floor(pos_f))
    upper = lower + 1
    es = (ppl_d[:(lower+1)].sum() + ppl_d[upper] * (pos_f - lower)) / (pos_f + 1)
    return es
