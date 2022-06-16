import numpy as np

from credmark.cmf.types import (
    Address,
    Price,
)

from credmark.cmf.model.errors import ModelRunError

CRV_DERIVED = {
    1: {
        Address('0xFEEf77d3f69374f66429C91d732A244f074bdf74'):
        {
            'name': 'cvxFXS',
            'pool_address': '0xd658A338613198204DCa1143Ac3F01A722b5d94A'
        },
    }
}


def curve_price_for_derived_token(model, input, pool, pool_tokens, pool_tokens_symbol):
    n_token_input = np.where([tok == input for tok in pool_tokens])[0].tolist()
    if len(n_token_input) != 1:
        raise ModelRunError(
            f'{model.slug} does not find {input=} in pool {pool.address=}')
    n_token_input = n_token_input[0]

    price_to_others = []
    for n_token_other, other_token in enumerate(pool_tokens):
        if n_token_other != n_token_input:
            ratio_to_other = pool.functions.get_dy(n_token_input,
                                                   n_token_other,
                                                   10**input.decimals).call() / 1e18
            price_other = model.context.run_model('chainlink.price-usd',
                                                  input=other_token,
                                                  return_type=Price).price
            price_to_others.append(ratio_to_other * price_other)

    n_price_min = np.where(price_to_others)[0][0]
    return Price(price=np.min(price_to_others),
                 src=f'{model.slug}|{pool.address}|{pool_tokens_symbol[n_price_min]}')
