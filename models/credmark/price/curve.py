import numpy as np
from credmark.cmf.model import Model, ModelDataErrorDesc
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (
    Address,
    Contract,
    Maybe,
    Network,
    Price,
    PriceWithQuote,
    Token,
)

from models.credmark.protocols.dexes.curve.curve_finance import CurveFiPoolInfoToken

np.seterr(all='raise')

PRICE_DATA_ERROR_DESC = ModelDataErrorDesc(
    code=ModelDataError.Codes.NO_DATA,
    code_desc='Not supported by Curve')


class CurveToken(Token):
    class Config:
        schema_extra = {
            'examples': [{'address': '0xFEEf77d3f69374f66429C91d732A244f074bdf74'}]  # cvxFXS
        }


@Model.describe(slug="price.dex-curve-fi-maybe",
                version="1.7",
                display_name="Curve Finance Pool - Price for stablecoins and LP",
                description=("For those tokens primarily traded in curve - "
                             "return None if cannot price"),
                category='protocol',
                subcategory='curve',
                tags=['price'],
                input=CurveToken,
                output=Maybe[Price])
class CurveFinanceMaybePrice(Model):
    def run(self, input: CurveToken) -> Maybe[Price]:
        if input.address in CurveFinancePrice.supported_coins(self.context.network):
            try:
                price = self.context.run_model('price.dex-curve-fi',
                                               input=input,
                                               return_type=Price)
                return Maybe[Price](just=price)
            except ModelRunError:
                pass

        return Maybe.none()


@Model.describe(slug="price.dex-curve-fi",
                version="1.7",
                display_name="Curve Finance Pool - Price for stablecoins and LP",
                description="For those tokens primarily traded in curve",
                category='protocol',
                subcategory='curve',
                tags=['price'],
                input=CurveToken,
                output=Price,
                errors=PRICE_DATA_ERROR_DESC)
class CurveFinancePrice(Model):
    """
    Price from Curve Pool.
    For there are three types
    - Stablecoins: list of tokens hard-coded to $1 now. # TODO
    - Derived: From pool with other tokens with prices from oracle
    - LP token: From the minimal price of the token in the pool * virtual price

    Reference for LP token:
    - Chainlink: https://blog.chain.link/using-chainlink-oracles-to-securely-utilize-curve-lp-pools/
    """
    CRV_CTOKENS = {
        Network.Mainnet: {
            'cyDAI': Address('0x8e595470ed749b85c6f7669de83eae304c2ec68f'),
            'cyUSDC': Address('0x76eb2fe28b36b3ee97f3adae0c69606eedb2a37c'),
            'cyUSDT': Address('0x48759f220ed983db51fa7a8c0d2aab8f3ce4166a'),
        }
    }

    CRV_DERIVED = {
        Network.Mainnet: {
            Address('0xFEEf77d3f69374f66429C91d732A244f074bdf74'):
            {
                'name': 'cvxFXS',
                'pool_address': '0xd658A338613198204DCa1143Ac3F01A722b5d94A'
            },
            Address('0xADF15Ec41689fc5b6DcA0db7c53c9bFE7981E655'):
            {
                'name': 'tFXS',
                'pool_address': '0x961226B64AD373275130234145b96D100Dc0b655'
            },
            Address('0xeb4c2781e4eba804ce9a9803c67d0893436bb27d'):
            {
                'name': 'renBTC',
                'pool_address': '0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714'
            },
            Address('0xfe18be6b3bd88a2d2a7f928d00292e7a9963cfc6'):
            {
                'name': 'sBTC',
                'pool_address': '0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714'
            }
        }
    }

    CRV_LP = {
        Network.Mainnet: {
            # Curve.fi DAI/USDC/USDT (3Crv)
            Address('0x6c3f90f043a72fa612cbac8115ee7e52bde6e490'),
            # Curve.fi renBTC/wBTC/sBTC (crvRenWSB...)
            Address('0x075b1bb99792c9e1041ba13afef80c91a1e70fb3'),
            # Curve.fi USD-BTC-ETH (crv3crypto)
            Address('0xc4ad29ba4b3c580e6d59105fff484999997675ff'),
        }
    }

    @staticmethod
    def supported_coins(network):
        return set(
            list(CurveFinancePrice.CRV_CTOKENS[network].values()) +
            list(CurveFinancePrice.CRV_DERIVED[network].keys()) +
            list(CurveFinancePrice.CRV_LP[network]))

    def run(self, input: CurveToken) -> Price:
        if input.address in self.CRV_CTOKENS[self.context.network].values():
            ctoken = Token(address=input.address)
            ctoken_decimals = ctoken.decimals
            underlying_addr = ctoken.functions.underlying().call()
            underlying_token = Token(address=Address(underlying_addr))
            underlying_token_decimals = underlying_token.decimals

            mantissa = 18 + underlying_token_decimals - ctoken_decimals
            exchange_rate_stored = ctoken.functions.exchangeRateStored().call()
            exchange_rate = exchange_rate_stored / 10**mantissa

            if underlying_token.address in self.supported_coins(self.context.network):
                raise ModelRunError(
                    f'{underlying_token=} is self-referenced in {self.slug}')

            price_underlying = self.context.run_model(
                'price.quote', input={'base': underlying_token},
                return_type=PriceWithQuote)

            price_underlying.price *= exchange_rate
            if price_underlying.src is not None:
                price_underlying.src = price_underlying.src + f'|cToken*{exchange_rate:.3f}'
            return price_underlying

        derived_info = self.CRV_DERIVED[self.context.network].get(
            input.address)
        if derived_info is not None:
            pool = Contract(address=derived_info['pool_address'])
            pool_info = self.context.run_model('curve-fi.pool-info-tokens',
                                               input=pool,
                                               return_type=CurveFiPoolInfoToken)

            n_token_input = np.where([tok == input for tok in pool_info.tokens])[
                0].tolist()
            if len(n_token_input) != 1:
                raise ModelRunError(
                    f'{self.slug} does not find {input=} in pool {pool.address=}')
            n_token_input = n_token_input[0]

            price_to_others = []
            ratio_to_others = []
            price_others = []
            for n_token_other, other_token in enumerate(pool_info.tokens):
                if (n_token_other != n_token_input and
                        other_token.address not in self.supported_coins(self.context.network)):
                    ratio_to_other = other_token.scaled(
                        pool.functions.get_dy(n_token_input,  # token to send
                                              n_token_other,  # token to receive
                                              10**input.decimals  # amount of the token to send
                                              ).call())
                    price_other = self.context.run_model('price.quote',
                                                         input={
                                                             'base': other_token},
                                                         return_type=PriceWithQuote).price
                    price_to_others.append(ratio_to_other * price_other)
                    ratio_to_others.append(ratio_to_other)
                    price_others.append(price_other)

            n_price_min = np.where(
                price_to_others == np.min(price_to_others))[0][0]
            return Price(
                price=np.min(price_to_others),
                src=(f'{self.slug}|{pool.address}|'
                     f'{pool_info.tokens_symbol[n_price_min]}|{ratio_to_others[n_price_min]}|'
                     f'{pool_info.tokens[n_price_min].symbol}|{price_others[n_price_min]}'))

        if input.address in self.CRV_LP[self.context.network]:
            if input.abi is not None and 'minter' in input.abi.functions:
                pool_addr = input.functions.minter().call()
            else:
                registry = Contract(
                    **self.context.models.curve_fi.get_registry())
                pool_addr = registry.functions.get_pool_from_lp_token(
                    input.address.checksum).call()
            pool = Contract(address=Address(pool_addr))
            pool_info = self.context.run_model('curve-fi.pool-info-tokens',
                                               input=pool,
                                               return_type=CurveFiPoolInfoToken)

            if input.address != pool_info.lp_token_addr:
                raise ModelRunError(
                    f'{self.slug} does not find LP {input=} in pool {pool.address=}')

            price_tokens = []
            for tok in pool_info.tokens:
                if tok.address not in self.supported_coins(self.context.chain_id):
                    price_tok = self.context.run_model('price.quote',
                                                       input={'base': tok},
                                                       return_type=PriceWithQuote).price
                    price_tokens.append(price_tok)

            virtual_price = pool.functions.get_virtual_price().call()
            lp_token_price = input.scaled(min(price_tokens) * virtual_price)
            n_min_token_symbol = np.where(np.isclose(
                min(price_tokens), price_tokens))[0][0]
            min_token_symbol = pool_info.tokens_symbol[n_min_token_symbol]

            return Price(price=lp_token_price,
                         src=(f'{self.slug}|{pool.address}|LP|'
                              f'{min_token_symbol}|min({",".join(pool_info.tokens_symbol)})'))

        raise ModelRunError(f'{self.slug} does not support {input=}')
