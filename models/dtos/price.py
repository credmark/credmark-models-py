from typing import List, Union, ClassVar, Dict
from credmark.cmf.types import Address, Token
from credmark.dto import DTO, DTOField, IterableListGenericDTO, PrivateAttr


def to_hex_address(code):
    return '0x{:040x}'.format(code)


class ChainlinkAddress(Address):
    """
    Extension to the existing Address to accept code
    """
    CODE_CONVERSION: ClassVar[Dict[str, str]] = {
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
        'ETH': '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
        'BTC': '0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB',
    }

    @classmethod
    def validate(cls, addr: str):
        return cls.__new__(cls, addr)

        if isinstance(addr, str):
            new_addr = cls.CODE_CONVERSION.get(addr.upper(), None)
            if new_addr is not None:
                return super().validate(new_addr)
        return super().validate(addr)

    def __new__(cls, addr: str):
        if isinstance(addr, str):
            new_addr = cls.CODE_CONVERSION.get(addr.upper(), None)
            if new_addr is not None:
                return super().__new__(cls, new_addr)
        return super().__new__(cls, addr)


class PriceInput(DTO):
    """
    In FX, the pair is quoted as base/quote for 1 base = x quote
    e.g. 1883.07 ETH / USD means 1883.07 USD for 1 ETH.

    *Base* token to get the value in the quote token
    *Quote* token to determine the value of the base token.

    If quote is not provided, default to the native token of the chain, i.e. ETH for Ethereum.

    Fiat is expressed in the currency code in ISO 4217.

    Base and quote can be either Token (symbol or address)
    or code (BTC, ETH, and all fiat, like USD, EUR, CNY, etc.)

    For fiat, with USD being the most active traded currency.
    It's direct quoting with (x USD/DOM) for x DOM = 1 USD, e.g. USD/JPY;
    and indirect quoting with (x DOM/USD) for x USD = 1 DOM, e.g. GBP/USD.

    For DeFi, we call it a direct quoting when the native token is the base.
    e.g. ETH / USD
    """
    base: ChainlinkAddress = DTOField(description='Base token address to get the value for')
    quote: Union[None, ChainlinkAddress] = \
        DTOField(None, description='Quote token address to count the value')


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
