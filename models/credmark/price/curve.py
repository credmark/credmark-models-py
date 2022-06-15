import numpy as np

from credmark.cmf.types import (
    Address,
    Token,
    Price,
    Contract,
)

from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from models.credmark.protocols.dexes.curve.curve_finance import CurveFiPoolInfo


PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='Not supported by Curve')


@Model.describe(slug="price.dex-curve-fi",
                version="1.0",
                display_name="Curve Finance Pool - Price for stablecoins and LP",
                description="For those tokens primarily traded in curve",
                input=Token,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class CurveFinancePrice(Model):
    """
    Price from Curve Pool.
    For there are three types
    - Stablecoins: list of tokens hard-coded to $1 now. TODO
    - Derived: From pool with other tokens with prices from oracle
    - LP token: From the minimal price of the token in the pool * virtual price

    Reference for LP token:
    - Chainlink: https://blog.chain.link/using-chainlink-oracles-to-securely-utilize-curve-lp-pools/
    """
    CRV_CTOKENS = {
        1: {
            'cyDAI': Address('0x8e595470ed749b85c6f7669de83eae304c2ec68f'),
            'cyUSDC': Address('0x76eb2fe28b36b3ee97f3adae0c69606eedb2a37c'),
            'cyUSDT': Address('0x48759f220ed983db51fa7a8c0d2aab8f3ce4166a'),
        }
    }

    CRV_DERIVED = {
        1: {
            Address('0xFEEf77d3f69374f66429C91d732A244f074bdf74'):
            {
                'name': 'cvxFXS',
                'pool_address': '0xd658A338613198204DCa1143Ac3F01A722b5d94A'
            },
        }
    }

    CRV_LP = {
        1: {
            Address('0x6c3f90f043a72fa612cbac8115ee7e52bde6e490'):
            {
                'name': '3Crv',
                'pool_address': '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
            }
        }
    }

    @staticmethod
    def supported_coins(chain_id):
        return (list(CurveFinancePrice.CRV_CTOKENS[chain_id].values()) +
                list(CurveFinancePrice.CRV_DERIVED[chain_id].keys()) +
                list(CurveFinancePrice.CRV_LP[chain_id].keys())
                )

    def run(self, input: Token) -> Price:
        if input.address in self.CRV_CTOKENS[self.context.chain_id].values():
            ctoken = Token(address=input.address)
            ctoken_decimals = ctoken.decimals
            underlying_addr = ctoken.functions.underlying().call()
            underlying_token = Token(address=Address(underlying_addr))
            underlying_token_decimals = underlying_token.decimals

            mantissa = 18 + underlying_token_decimals - ctoken_decimals
            exchange_rate_stored = ctoken.functions.exchangeRateStored().call()
            exchange_rate = exchange_rate_stored / 10**mantissa

            price_underlying = self.context.run_model('price.quote',
                                                      input=underlying_token,
                                                      return_type=Price)

            price_underlying.price *= exchange_rate
            if price_underlying.src is not None:
                price_underlying.src = price_underlying.src + '|cToken'
            return price_underlying

        derived_info = self.CRV_DERIVED[self.context.chain_id].get(input.address)
        if derived_info is not None:
            pool = Contract(address=derived_info['pool_address'])
            pool_info = self.context.run_model('curve-fi.pool-info',
                                               input=pool,
                                               return_type=CurveFiPoolInfo)
            n_token_input = np.where([tok == input for tok in pool_info.tokens])[0].tolist()
            if len(n_token_input) != 1:
                raise ModelRunError(
                    f'{self.slug} does not find {input=} in pool {pool.address=}')
            n_token_input = n_token_input[0]

            price_to_others = []
            for n_token_other, other_token in enumerate(pool_info.tokens):
                if n_token_other != n_token_input:
                    ratio_to_other = pool.functions.get_dy(n_token_input,
                                                           n_token_other,
                                                           10**input.decimals).call() / 1e18
                    price_other = self.context.run_model('price.quote',
                                                         input={'base': other_token},
                                                         return_type=Price).price
                    price_to_others.append(ratio_to_other * price_other)

            n_price_min = np.where(price_to_others)[0][0]
            return Price(price=np.min(price_to_others),
                         src=f'{self.slug}|{pool.address}|{pool_info.tokens_symbol[n_price_min]}')

        lp_token_info = self.CRV_LP[self.context.chain_id].get(input.address)
        if lp_token_info is not None:
            pool = Contract(address=lp_token_info['pool_address'])
            pool_info = self.context.run_model('curve-fi.pool-info',
                                               input=pool,
                                               return_type=CurveFiPoolInfo)
            if pool_info.lp_token_addr != input.address:
                raise ModelRunError(
                    f'{self.slug} does not find LP {input=} in pool {pool.address=}')

            price_tokens = []
            for tok in pool_info.tokens:
                price_tok = self.context.run_model('price.quote',
                                                   input=tok,
                                                   return_type=Price).price
                price_tokens.append(price_tok)

            virtual_price = pool.functions.get_virtual_price().call()
            lp_token_price = input.scaled(min(price_tokens) * virtual_price)
            n_min_token_symbol = np.where(np.isclose(min(price_tokens), price_tokens))[0][0]
            min_token_symbol = pool_info.tokens_symbol[n_min_token_symbol]

            return Price(price=lp_token_price,
                         src=(f'{self.slug}|{pool.address}|LP|'
                              f'{min_token_symbol}|min({",".join(pool_info.tokens_symbol)})'))

        raise ModelRunError(f'{self.slug} does not support {input=}')
