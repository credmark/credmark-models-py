from typing import List, Union, ClassVar, Dict
from credmark.cmf.types import Address, Token
from credmark.dto import DTO, DTOField, IterableListGenericDTO, PrivateAttr
from credmark.cmf.model.errors import ModelDataError


def to_hex_address(code):
    return Address('0x{:040x}'.format(code))


class StrToToken(Token):
    TRIPLET_CONVERSION: ClassVar[Dict[str, Address]] = {
        # 0x0000000000000000000000000000000000000348
        'USD': to_hex_address(840),
        # 0x000000000000000000000000000000000000033a
        'GBP': to_hex_address(826),
        # 0x00000000000000000000000000000000000003d2
        'EUR': to_hex_address(978),
        'JPY': to_hex_address(392),
        'CNY': to_hex_address(156),
        'AUD': to_hex_address(36),
        'KRW': to_hex_address(410),
        'BRL': to_hex_address(986),
        'CAD': to_hex_address(124),
        'CHF': to_hex_address(756),
        'IDR': to_hex_address(360),
        'INR': to_hex_address(356),
        'NGN': to_hex_address(566),
        'NZD': to_hex_address(554),
        'PHP': to_hex_address(608),
        'SGD': to_hex_address(702),
        'TRY': to_hex_address(949),
        'ZAR': to_hex_address(710),
        'ETH': Address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'),
        'BTC': Address('0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB'),
    }

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, val):
        if isinstance(val, str):
            tok = Token(address=cls.TRIPLET_CONVERSION.get(val, None))
            if tok is None:
                raise ModelDataError(f'Unsupported currency code {val}')
            return tok
        else:
            return Token.validate(val)


class PriceInput(DTO):
    """
    In FX, the pair is quoted as (x FOR/DOM) for x DOM = 1 FOR.
    FOR is the base currency to get the value for.
    DOM is the quote currency to determine the value of the base currency, i.e. FOR.
    e.g. 1883.07 ETH / USD means 1883.07 USD for 1 ETH.

    If DOM is not provided, default to the native token of each chain.

    Fiat is expressed in the currency code in ISO 4217.
    """
    base: StrToToken = DTOField(description='Base token to get the value for')
    quote: Union[None, StrToToken] = DTOField(None, description='Quote token to count the value')


class PoolPriceInfo(DTO):
    """
    @src: source
    @price: price derived from pool of stablecoin and WETH9
    @liquidity: Available liquidity in the pool for the token
    @weth_multiplier: WETH price used if one token is WETH9
    @inverse: True if token is the second token in the pool
    @token0_address: token0's address
    @token1_address: token1's address
    @token0_symbol: token0's symbol
    @token1_symbol: token1's symbol
    @token0_decimals: token0's decimals
    @token1_decimals: token1's decimals
    @pool_address: pool's address
    """
    src: str
    price: float
    liquidity: float
    weth_multiplier: float
    inverse: bool
    token0_address: Address
    token1_address: Address
    token0_symbol: str
    token1_symbol: str
    token0_decimals: int
    token1_decimals: int
    pool_address: Address


class PoolPriceInfos(IterableListGenericDTO[PoolPriceInfo]):
    pool_price_infos: List[PoolPriceInfo] = []
    _iterator: str = PrivateAttr('pool_price_infos')


class PoolPriceAggregatorInput(PoolPriceInfos):
    token: Token
    weight_power: float = DTOField(1.0, ge=1.0)
    price_src: str
