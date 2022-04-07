from typing import (
    List,
    Tuple,
)

from datetime import (
    datetime,
    date,
    timezone,
    timedelta,
)

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError

from credmark.cmf.types import (
    Address,
    Token,
    Contract,
    Price,
    BlockNumber,
)

from credmark.dto import (
    DTO,
    EmptyInput,
    IterableListGenericDTO,
)

from models.tmp_abi_lookup import (
    COMPOUND_CTOKEN_CONTRACT_ABI,
)

COMPOUND_ASSETS = {
    "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
    "BAT": "0x0D8775F648430679A709E98d2b0Cb6250d2887EF",
    "COMP": "0xc00e94Cb662C3520282E6f5717214004A7f26888",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "FEI": '0x956F47F50A910163D8BF957Cf5846D573E7f87CA',
    "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "MKR": "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
    "REP": "0x1985365e9f78359a9B6AD760e32412f4a445E862",
    "SAI": "0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359",
    "SUSHI": "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2",
    "TUSD": "0x0000000000085d4780B73119b644AE5ecd22b376",
    "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDP": "0x8E870D67F660D95d5be530380D0eC0bd388289E1",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "WBTC2": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # same as WBTC
    "YFI": "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
    "ZRX": "0xE41d2489571d322189246DaFA5ebDe1F4699F498",

}

COMPOUND_CTOKEN = {
    'cAAVE': '0xe65cdb6479bac1e22340e4e755fae7e509ecd06c',
    'cBAT': '0x6c8c6b02e7b2be14d4fa6022dfd6d75921d90e4e',
    'cCOMP': '0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4',
    'cDAI': '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643',
    'cETH': '0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5',
    'cFEI': '0x7713dd9ca933848f6819f38b8352d9a15ea73f67',
    'cLINK': '0xface851a4921ce59e912d19329929ce6da6eb0c7',
    'cMKR': '0x95b4ef2869ebd94beb4eee400a99824bf5dc325b',
    'cREP': '0x158079ee67fce2f58472a96584a73c7ab9ac95c1',
    'cSAI': '0xf5dce57282a584d2746faf1593d3121fcac444dc',
    'cSUSHI': '0x4b0181102a0112a2ef11abee5563bb4a3176c9d7',
    'cTUSD': '0x12392f67bdf24fae0af363c24ac620a2f67dad86',
    'cUNI': '0x35a18000230da775cac24873d00ff85bccded550',
    'cUSDC': '0x39aa39c021dfbae8fac545936693ac917d5e7563',
    'cUSDP': '0x041171993284df560249b57358f931d9eb7b925d',
    'cUSDT': '0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9',
    'cWBTC': '0xc11b1268c1a384e55c48c2391d8d480264a3a7f4',
    'cWBTC2': '0xccf4429db6322d5c611ee964527d42e5d685dd6a',
    'cYFI': '0x80a2ae356fc9ef4305676f7a3e2ed04e12c33946',
    'cZRX': '0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407'
}

assert sorted(COMPOUND_ASSETS.keys()) == sorted(
    ['WETH' if t == 'cETH' else t[1:] for t, _ in COMPOUND_CTOKEN.items()])

COMPOUND_COMP = '0xc00e94cb662c3520282e6f5717214004a7f26888'

COMPOUND_COMPTROLLER = '0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b'
COMPOUND_GOVERNANCE = '0xc0da02939e1441f497fd74f78ce7decb17b66529'
COMPOUND_TIMELOCK = '0x6d903f6003cca6255d85cca4d3b5e5146dc33925'

# Pool(Contract)
# LendingPool(Pool)
# CompoundLendingPool(LendingPool)


class CompoundV2PoolInfo(DTO):
    tokenSymbol: str
    cTokenSymbol: str
    token: Token
    cToken: Token
    tokenDecimal: int
    cTokenDecimal: int
    tokenPrice: float
    tokenPriceSrc: str
    cash: float
    totalBorrows: float
    totalReserves: float
    totalSupply: float
    exchangeRate: float
    invExchangeRate: float
    totalLiability: float
    borrowRate: float
    supplyRate: float
    reserveFactor: float
    isListed: bool
    collateralFactor: float
    isComped: bool
    block_number: int
    block_datetime: str


class CompoundV2PoolValue(DTO):
    cTokenSymbol: str
    cTokenAddress: Address
    tokenPrice: float
    qty_cash: float
    qty_borrow: float
    qty_liability: float
    qty_reserve: float
    qty_net: float
    cash: float
    borrow: float
    liability: float
    reserve: float
    net: float
    block_number: int
    block_datetime: str


class CompoundV2PoolInfos(IterableListGenericDTO[CompoundV2PoolInfo]):
    infos: List[CompoundV2PoolInfo]
    _iterator: str = 'infos'


class CompoundV2PoolValues(IterableListGenericDTO[CompoundV2PoolValue]):
    values: List[CompoundV2PoolValue]
    _iterator: str = 'values'

# TODO: work-around before proxy can be queried with past block number


@Model.describe(slug="compound-v2.get-comptroller",
                version="1.0",
                display_name="Compound V2 - comptroller",
                description="Compound V2 - comptroller",
                input=EmptyInput,
                output=Contract)
class CompoundV2Comptroller(Model):
    def run(self, input: EmptyInput) -> Contract:
        comptroller = Contract(address=COMPOUND_COMPTROLLER)
        proxy_address = comptroller.instance.functions.comptrollerImplementation().call()
        return Contract(address=proxy_address)


@Model.describe(slug="compound-v2.get-pools",
                version="1.0",
                display_name="Compound V2 - get cTokens/markets",
                description="Compound V2 - get all cTokens/Markets",
                input=EmptyInput,
                output=dict)
class CompoundV2GetAllPools(Model):
    def run(self, input: EmptyInput) -> dict:
        # TODO: before we can load proxy on a past date
        comptroller = Contract(address=COMPOUND_COMPTROLLER)
        cTokens = comptroller.functions.getAllMarkets().call()
        breakpoint()

        # Check whether our list is complete
        # assert ( sorted([Address(x) for x in COMPOUND_CTOKEN.values()]) ==
        #          sorted([Address(x) for x in cTokens]) )
        return {'cTokens': cTokens}


@Model.describe(slug="compound-v2.all-pools-info",
                version="1.0",
                display_name="Compound V2 - get cTokens/markets",
                description="Compound V2 - get all cTokens/Markets",
                input=EmptyInput,
                output=CompoundV2PoolInfos)
class CompoundV2AllPoolsInfo(Model):
    def run(self, input: EmptyInput) -> CompoundV2PoolInfos:
        pool_infos = []
        pools = self.context.run_model(slug='compound-v2.get-pools')
        breakpoint()
        for cTokenAddress in pools['cTokens']:
            pool_info = self.context.run_model(
                slug='compound-v2.get-pool-info',
                input=Token(address=cTokenAddress))
            pool_infos.append(pool_info)
        ret = CompoundV2PoolInfos(infos=pool_infos)
        return ret


@Model.describe(slug="compound-v2.all-pools-values",
                version="1.0",
                display_name="Compound V2 - get cTokens/markets",
                description="Compound V2 - get all cTokens/Markets",
                input=CompoundV2PoolInfos,
                output=CompoundV2PoolValues)
class CompoundV2AllPoolsValue(Model):
    def run(self, input: CompoundV2PoolInfos) -> CompoundV2PoolValues:
        self.logger.info(f'Data as of {self.context.block_number=}')
        pool_infos = input

        pool_values = []
        for pool_info in pool_infos:
            pool_value = self.context.run_model(slug='compound-v2.pool-value',
                                                input=pool_info,
                                                return_type=CompoundV2PoolValue)
            pool_values.append(pool_value)

        ret = CompoundV2PoolValues(values=pool_values)
        return ret


@ Model.describe(slug="compound-v2.get-pool-info",
                 version="1.0",
                 display_name="Compound V2 - pool/market information",
                 description="Compound V2 - pool/market information",
                 input=Token,
                 output=CompoundV2PoolInfo)
class CompoundV2GetPoolInfo(Model):
    """
    # Pool info

    1. getCash: Cash is the amount of underlying balance owned by this cToken contract.
    2. totalBorrows: the amount of underlying currently loaned out by the market,
                     with interest
    3. totalReserves: Reserves of set-aside cash
    4. totalSupply: the number of tokens currently in circulation in this cToken market

    5. exchangeRate: The exchange rate between a cToken and the underlying asset
       exchangeRate = (getCash() + totalBorrows() - totalReserves()) / totalSupply()
                    => cToken.scaled / pow(10, 2)
       Liabitliy = totalSupply * exchangeRate, or
                 = totalSupply / invExchangeRate

    6. reserveFactor: defines the portion of borrower interest that is
                       converted into reserves.
    7./8. borrowRatePerBlock()/supplyRatePerBlock()

    (Skip 9 and 10 because they need a user account)
    9. balanceOfUnderlying(): balance of cToken * exchangeRate.
    10. borrowBalance(): balance of liability including interest

    # TODO
    11. accuralBlockNumber
    12. exchangeRateStored
    13. initialExchangeRateMantissa
    14. interestRateModel
        - WhitePaperInterestRateModel
        - getBorrowRate/multiplier/baseRate/blocksPerYear
    """

    def run(self, input: Token) -> CompoundV2PoolInfo:
        # TODO: before we can load proxy on a past date
        # comptroller = Contract(address=COMPOUND_COMPTROLLER)
        comptroller = self.context.run_model(slug='compound-v2.get-comptroller',
                                             input=EmptyInput(),
                                             return_type=Contract)

        cToken = Token(address=input.address)

        # print(f'{cToken._meta.is_transparent_proxy}')
        # print(f'{cToken.is_transparent_proxy}')
        # breakpoint()

        (isListed, collateralFactorMantissa, isComped) = \
            comptroller.functions.markets(cToken.address).call()
        collateralFactorMantissa /= pow(10, 18)

        # From cToken to Token
        if input.symbol == 'cETH':
            token = Token(address=COMPOUND_ASSETS['WETH'])
        elif (input.address == '0xf5dce57282a584d2746faf1593d3121fcac444dc' and
              input.symbol == 'cDAI'):
            # When input = cSAI, it has been renamed to cDAI in the contract.
            # We will still call up SAI
            token = Token(address=COMPOUND_ASSETS['SAI'])
        else:
            token = Token(address=cToken.functions.underlying().call())

        self.logger.info(f'{cToken.address, cToken.symbol}')

        # Check for cToken to be matched with a Token
        assert cToken.functions.isCToken().call()
        if cToken.proxy_for is not None:
            assert cToken.functions.implementation().call() == cToken.proxy_for.address
        assert cToken.functions.admin().call() == Address(COMPOUND_TIMELOCK)
        assert cToken.functions.comptroller().call() == Address(COMPOUND_COMPTROLLER)
        assert cToken.functions.symbol().call()
        if cToken.name != 'Compound Ether':
            assert cToken.functions.underlying().call() == token.address

        # Get/calcualte info

        # TODO: some ABI loading problem
        # irModel = Contract(address=cToken.functions.interestRateModel().call())
        # assert irModel.functions.isInterestRateModel().call()

        getCash = token.scaled(cToken.functions.getCash().call())
        totalBorrows = token.scaled(cToken.functions.totalBorrows().call())
        totalReserves = token.scaled(cToken.functions.totalReserves().call())
        totalSupply = cToken.scaled(cToken.functions.totalSupply().call())

        exchangeRate = token.scaled(cToken.functions.exchangeRateCurrent().call())
        invExchangeRate = 1 / exchangeRate * pow(10, 10)
        totalLiability = totalSupply / invExchangeRate

        reserveFactor = cToken.functions.reserveFactorMantissa().call() / pow(10, 18)
        borrowRate = cToken.functions.borrowRatePerBlock().call() / pow(10, 18)
        supplyRate = cToken.functions.supplyRatePerBlock().call() / pow(10, 18)

        tokenprice = self.context.run_model(slug='token.price-ext', input=token, return_type=Price)

        if tokenprice.price is None or tokenprice.src is None:
            raise ModelRunError(f'Can not get price for token {token.symbol=}/{token.address=}')

        pool_info = CompoundV2PoolInfo(
            tokenSymbol=input.symbol,
            cTokenSymbol=cToken.symbol,
            tokenDecimal=token.decimals,
            cTokenDecimal=cToken.decimals,
            token=token,
            tokenPrice=tokenprice.price,
            tokenPriceSrc=tokenprice.src,
            cToken=cToken,
            cash=getCash,
            totalReserves=totalReserves,
            totalBorrows=totalBorrows,
            totalSupply=totalSupply,
            totalLiability=totalLiability,
            exchangeRate=exchangeRate,
            invExchangeRate=invExchangeRate,
            borrowRate=borrowRate,
            supplyRate=supplyRate,
            reserveFactor=reserveFactor,
            isListed=isListed,
            collateralFactor=collateralFactorMantissa,
            isComped=isComped,
            block_number=int(self.context.block_number),
            block_datetime=self.context.block_number.timestamp_datetime.replace(tzinfo=None).isoformat(),
        )

        return pool_info


@ Model.describe(slug="compound-v2.pool-value",
                 version="1.0",
                 display_name="Compound V2 - value of a market",
                 description="Compound V2 - value of a market",
                 input=CompoundV2PoolInfo,
                 output=CompoundV2PoolValue)
class CompoundV2GetPoolValue(Model):
    def run(self, input: CompoundV2PoolInfo) -> CompoundV2PoolValue:
        # Liquidity = cash (reserve is part of it)
        # Asset = cash + totalBorrow
        # Liability = from totalSupply
        # Net = Asset - Liability

        return CompoundV2PoolValue(
            cTokenSymbol=input.cTokenSymbol,
            cTokenAddress=input.token.address,
            tokenPrice=input.tokenPrice,
            qty_cash=input.cash,
            qty_borrow=input.totalBorrows,
            qty_liability=input.totalLiability,
            qty_reserve=input.totalReserves,
            qty_net=(input.cash + input.totalBorrows - input.totalLiability),
            cash=input.tokenPrice * input.cash,
            borrow=input.tokenPrice * input.totalBorrows,
            liability=input.tokenPrice * input.totalLiability,
            reserve=input.tokenPrice * input.totalReserves,
            net=input.tokenPrice * (input.cash + input.totalBorrows - input.totalLiability),
            block_number=input.block_number,
            block_datetime=input.block_datetime,
        )


class CompoundV2PoolsValueHistoricalInput(DTO):
    date_range: Tuple[date, date]
    token: Token


@Model.describe(slug="compound-v2.pool-value-historical",
                version="1.0",
                display_name="Compound pools value history",
                description="Compound pools value history",
                input=CompoundV2PoolsValueHistoricalInput,
                output=CompoundV2PoolValues)
class CompoundV2PoolsValueHistorical(Model):
    def run(self, input: CompoundV2PoolsValueHistoricalInput) -> CompoundV2PoolValues:
        d_start, d_end = input.date_range
        if d_start > d_end:
            d_start, d_end = d_end, d_start

        dt_start = datetime.combine(d_start, datetime.max.time(), tzinfo=timezone.utc)
        dt_end = datetime.combine(d_end, datetime.max.time(), tzinfo=timezone.utc)

        interval = (dt_end - dt_start).days + 1
        window = f'{interval} days'
        interval = '1 day'

        # TODO: add two days to the end as work-around to current start-end-window
        ts_as_of_end_dt = self.context.block_number.from_timestamp(
            ((dt_end + timedelta(days=2)).timestamp())).timestamp

        pool_infos = self.context.historical.run_model_historical(
            model_slug='compound-v2.get-pool-info',
            model_input=input.token,
            model_return_type=CompoundV2PoolInfo,
            window=window,
            interval=interval,
            end_timestamp=ts_as_of_end_dt)

        pool_values = []

        for pl in pool_infos:
            pl_output = pl.output
            self.logger.info(f'{pl_output.block_number=}:'
                             f'{BlockNumber(pl_output.block_number).timestamp_datetime}')
            pool_value = self.context.run_model(
                slug='compound-v2.pool-value',
                input=pl_output,
                return_type=CompoundV2PoolValue)
            pool_values.append(pool_value)

        return CompoundV2PoolValues(values=pool_values)
