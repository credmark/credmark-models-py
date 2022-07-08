import numpy as np
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import Address, Contract, Price, Some, Token
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, EmptyInput

np.seterr(all='raise')

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
    cash: float
    totalBorrows: float
    totalReserves: float
    totalSupply: float
    exchangeRate: float
    invExchangeRate: float
    totalLiability: float
    borrowRate: float
    supplyRate: float
    borrowAPY: float
    supplyAPY: float
    utilizationRate: float
    reserveFactor: float
    isListed: bool
    collateralFactor: float
    isComped: bool
    block_number: int
    block_datetime: str
    ir_model: Contract


class CompoundV2PoolValue(DTO):
    tp: float
    tpSrc: str
    cTokenSymbol: str
    cTokenAddress: Address
    tp: float
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


def get_comptroller(model):
    compound_comptroller = {
        1: '0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b',
        42: '0x5eae89dc1c671724a672ff0630122ee834098657'
    }
    addr = compound_comptroller[model.context.chain_id]

    # pylint:disable=locally-disabled,protected-access
    comptroller = Contract(address=addr)
    assert comptroller.contract_name == 'Unitroller'
    assert comptroller.proxy_for is not None

    proxy_address = comptroller.instance.functions.comptrollerImplementation().call()

    contract_implementation = Contract(address=proxy_address)
    if proxy_address != comptroller.proxy_for.address:
        model.context.logger.debug(
            f'Comptroller\'s implmentation is corrected to {proxy_address} '
            f'from {comptroller.proxy_for.address}')
    comptroller._meta.is_transparent_proxy = True
    comptroller._meta.proxy_implementation = contract_implementation
    return comptroller


@ Model.describe(slug="compound-v2.get-comptroller",
                 version="1.2",
                 display_name="Compound V2 - comptroller",
                 description="Get comptroller contract",
                 category='protocol',
                 subcategory='compound',
                 input=EmptyInput,
                 output=Contract)
class CompoundV2Comptroller(Model):
    # pylint:disable=locally-disabled,protected-access
    def run(self, _: EmptyInput) -> Contract:
        comptroller = get_comptroller(self)
        if comptroller._meta.proxy_implementation is not None:
            cc = comptroller._meta.proxy_implementation
            _ = cc.abi
            return cc
        else:
            raise ModelRunError('proxy implementation is missing.')


@ Model.describe(slug="compound-v2.get-pools",
                 version="1.1",
                 display_name="Compound V2 - get cTokens/markets",
                 description="Query the comptroller for all cTokens/markets",
                 category='protocol',
                 subcategory='compound',
                 input=EmptyInput,
                 output=dict)
class CompoundV2GetAllPools(Model):
    def run(self, _: EmptyInput) -> dict:
        comptroller = get_comptroller(self)
        cTokens = comptroller.functions.getAllMarkets().call()

        # Check whether our list is complete
        # assert ( sorted([Address(x) for x in COMPOUND_CTOKEN.values()]) ==
        #          sorted([Address(x) for x in cTokens]) )
        return {'cTokens': cTokens}


@Model.describe(slug="compound-v2.all-pools-info",
                version="1.3",
                display_name="Compound V2 - get all pool info",
                description="Get all pools and query for their info (deposit, borrow, rates)",
                category='protocol',
                subcategory='compound',
                input=EmptyInput,
                output=Some[CompoundV2PoolInfo])
class CompoundV2AllPoolsInfo(Model):
    def run(self, input: EmptyInput) -> Some[CompoundV2PoolInfo]:
        pools = self.context.run_model(slug='compound-v2.get-pools')

        model_slug = 'compound-v2.pool-info'
        model_inputs = [Token(address=cTokenAddress) for cTokenAddress in pools['cTokens']]

        def _use_compose():
            all_pool_infos_results = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug,
                       'modelInputs': model_inputs},
                return_type=MapInputsOutput[dict, CompoundV2PoolInfo]
            )

            pool_infos = []
            for pool_n, pool_result in enumerate(all_pool_infos_results):
                if pool_result.output is not None:
                    pool_infos.append(pool_result.output)
                elif pool_result.error is not None:
                    self.logger.error(pool_result.error)
                    raise ModelRunError(f'Error with {model_slug}({model_inputs[pool_n]}). ' +
                                        pool_result.error.message)
                else:
                    raise ModelRunError('compose.map-inputs: output/error cannot be both None')
            return pool_infos

        pool_infos = _use_compose()

        ret = Some[CompoundV2PoolInfo](some=pool_infos)
        return ret


@ Model.describe(slug="compound-v2.all-pools-value",
                 version="0.1",
                 display_name="Compound V2 - get all pools value",
                 description="Compound V2 - convert pool's info to value",
                 category='protocol',
                 subcategory='compound',
                 input=EmptyInput,
                 output=Some[CompoundV2PoolValue])
class CompoundV2AllPoolsValue(Model):
    def run(self, _: EmptyInput) -> Some[CompoundV2PoolValue]:
        pools = self.context.run_model(slug='compound-v2.get-pools')
        model_slug = 'compound-v2.pool-value'
        model_inputs = [Token(address=cTokenAddress) for cTokenAddress in pools['cTokens']]

        def _use_compose():
            all_pool_infos = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug,
                       'modelInputs': model_inputs},
                return_type=MapInputsOutput[dict, CompoundV2PoolValue]
            )

            pool_infos = []
            for pool_n, pool_result in enumerate(all_pool_infos):
                if pool_result.output is not None:
                    pool_infos.append(pool_result.output)
                elif pool_result.error is not None:
                    self.logger.error(pool_result.error)
                    raise ModelRunError(f'Error with {model_slug}({model_inputs[pool_n]}). ' +
                                        pool_result.error.message)
                else:
                    raise ModelRunError('compose.map-inputs: output/error cannot be both None')
            return pool_infos

        def _use_for():
            pool_values = []
            for pool_token in model_inputs:
                pool_value = self.context.run_model(
                    slug='compound-v2.pool-value',
                    input=pool_token,
                    return_type=CompoundV2PoolValue)
                pool_values.append(pool_value)
            return pool_values

        pool_infos = _use_compose()

        ret = Some[CompoundV2PoolValue](some=pool_infos)
        return ret


@Model.describe(slug="compound-v2.pool-info",
                version="1.4",
                display_name="Compound V2 - pool/market information",
                description="Compound V2 - pool/market information",
                category='protocol',
                subcategory='compound',
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
    COMPOUND_GOVERNANCE = {
        1: '0xc0da02939e1441f497fd74f78ce7decb17b66529',
        42: '0x100044c436dfb66ff106157970bc89f243411ffd',
    }
    COMPOUND_TIMELOCK = {
        1: '0x6d903f6003cca6255d85cca4d3b5e5146dc33925',
        42: '0xe3e07f4f3e2f5a5286a99b9b8deed08b8e07550b'
    }

    COMPOUND_ASSETS = {
        1: {
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
        },
        42: {
            # TODO: to be filled
        }
    }

    COMPOUND_CTOKEN = {
        1: {
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
            'cZRX': '0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407',
        },
        42: {
            'cBAT': '0x4a77faee9650b09849ff459ea1476eab01606c7a',
            'cDAI': '0xf0d0eb522cfa50b716b3b1604c4f0fa6f04376ad',
            'cETH': '0x41b5844f4680a8c38fbb695b7f9cfd1f64474a72',
            'cREP': '0xa4ec170599a1cf87240a35b9b1b8ff823f448b57',
            'cSAI': '0xb3f7fb482492f4220833de6d6bfcc81157214bec',
            'cUSDC': '0x4a92e71227d294f041bd82dd8f78591b75140d63',
            'cUSDT': '0x3f0a0ea2f86bae6362cf9799b523ba06647da018',
            'cWBTC': '0xa1faa15655b0e7b6b6470ed3d096390e6ad93abb',
            'cZRX': '0xaf45ae737514c8427d373d50cd979a242ec59e5a',
        }
    }

    # APY calculation
    ETH_MANTISSA = 1e18
    BLOCKS_PER_DAY = 6570  # 13.15 seconds per block
    DAYS_PER_YEAR = 365

    def test_fixture(self, chain_id):
        compoud_assets = sorted(self.COMPOUND_ASSETS[chain_id].keys())
        compoud_ctokens = sorted(['WETH' if t == 'cETH' else t[1:]
                                  for t, _ in self.COMPOUND_CTOKEN[chain_id].items()])
        assert compoud_assets == compoud_ctokens

    def run(self, input: Token) -> CompoundV2PoolInfo:
        comptroller = get_comptroller(self)

        cToken = Token(address=input.address)

        # self.logger.info(f'{cToken._meta.is_transparent_proxy}')
        # self.logger.info(f'{cToken.is_transparent_proxy}')

        market_info = comptroller.functions.markets(cToken.address).call()
        (isListed, collateralFactorMantissa, isComped) = market_info
        collateralFactorMantissa /= pow(10, 18)

        # From cToken to Token
        if input.symbol == 'cETH':
            token = Token(address=self.COMPOUND_ASSETS[self.context.chain_id]['WETH'])
        elif (input.address == self.COMPOUND_CTOKEN[self.context.chain_id]['cSAI'] and
              input.symbol == 'cDAI'):
            # When input = cSAI, it has been renamed to cDAI in the contract.
            # We will still call up SAI
            token = Token(address=self.COMPOUND_ASSETS[self.context.chain_id]['SAI'])
        else:
            token = Token(address=cToken.functions.underlying().call())

        self.logger.info(f'{cToken.address, cToken.symbol}')

        # Check for cToken to be matched with a Token
        assert cToken.functions.isCToken().call()
        # TODO: disable this test as we did not have loading ABI by block_number
        # if cToken.proxy_for is not None:
        #    try:
        #        assert cToken.functions.implementation().call() == cToken.proxy_for.address
        #    except AssertionError:
        #        self.logger.error(f'{cToken.functions.implementation().call()}, '
        #                          f'{cToken.proxy_for.address=}')
        assert cToken.functions.admin().call() == \
            Address(self.COMPOUND_TIMELOCK[self.context.chain_id])
        assert cToken.functions.comptroller().call() == Address(comptroller.address)
        assert cToken.functions.symbol().call()
        if cToken.name != 'Compound Ether':
            assert cToken.functions.underlying().call() == token.address

        # Get/calcualte info

        irModel = Contract(address=cToken.functions.interestRateModel().call())
        _ = irModel.functions.isInterestRateModel().call()
        # self.logger.info(f'{irModel.address=}, {irModel.functions.isInterestRateModel().call()=}')

        getCash = token.scaled(cToken.functions.getCash().call())
        totalBorrows = token.scaled(cToken.functions.totalBorrows().call())
        totalReserves = token.scaled(cToken.functions.totalReserves().call())
        totalSupply = cToken.scaled(cToken.functions.totalSupply().call())

        exchangeRate = token.scaled(cToken.functions.exchangeRateCurrent().call())
        invExchangeRate = 1 / exchangeRate * pow(10, 10)
        totalLiability = totalSupply / invExchangeRate

        reserveFactor = cToken.functions.reserveFactorMantissa().call() / self.ETH_MANTISSA
        borrowRate = cToken.functions.borrowRatePerBlock().call() / self.ETH_MANTISSA
        supplyRate = cToken.functions.supplyRatePerBlock().call() / self.ETH_MANTISSA

        if np.isclose(getCash + totalBorrows - totalReserves, 0):
            utilizationRate = 0
        else:
            utilizationRate = totalBorrows / (getCash + totalBorrows - totalReserves)
        supplyAPY = ((supplyRate * self.BLOCKS_PER_DAY + 1) ** self.DAYS_PER_YEAR - 1)
        borrowAPY = ((borrowRate * self.BLOCKS_PER_DAY + 1) ** self.DAYS_PER_YEAR - 1)
        # By definition, this is how supplyRate is derived.
        # supplyRate ~= borrowRate * utilizationRate * (1 - reserveFactor)

        block_dt = self.context.block_number.timestamp_datetime.replace(tzinfo=None).isoformat()
        pool_info = CompoundV2PoolInfo(
            tokenSymbol=input.symbol,
            cTokenSymbol=cToken.symbol,
            tokenDecimal=token.decimals,
            cTokenDecimal=cToken.decimals,
            token=token,
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
            supplyAPY=supplyAPY,
            borrowAPY=borrowAPY,
            utilizationRate=utilizationRate,
            reserveFactor=reserveFactor,
            isListed=isListed,
            collateralFactor=collateralFactorMantissa,
            isComped=isComped,
            block_number=int(self.context.block_number),
            block_datetime=block_dt,
            ir_model=irModel,
        )

        return pool_info


@ Model.describe(slug="compound-v2.pool-value",
                 version="1.2",
                 display_name="Compound V2 - value of a market",
                 description="Compound V2 - value of a market",
                 category='protocol',
                 subcategory='compound',
                 input=Token,
                 output=CompoundV2PoolValue)
class CompoundV2GetPoolValue(Model):
    def run(self, input: Token) -> CompoundV2PoolValue:
        pool_info = self.context.run_model(slug='compound-v2.pool-info',
                                           input=input,
                                           return_type=CompoundV2PoolInfo)
        tp = self.context.run_model(slug='price.quote',
                                    input={'base': pool_info.token},
                                    return_type=Price)

        if tp.price is None or tp.src is None:
            raise ModelRunError(f'Can not get price for token {input.symbol=}/{input.address=}')

        # Liquidity = cash (reserve is part of it)
        # Asset = cash + totalBorrow
        # Liability = from totalSupply
        # Net = Asset - Liability

        return CompoundV2PoolValue(
            tp=tp.price,
            tpSrc=tp.src,
            cTokenSymbol=pool_info.cTokenSymbol,
            cTokenAddress=pool_info.token.address,
            qty_cash=pool_info.cash,
            qty_borrow=pool_info.totalBorrows,
            qty_liability=pool_info.totalLiability,
            qty_reserve=pool_info.totalReserves,
            qty_net=(pool_info.cash + pool_info.totalBorrows - pool_info.totalLiability),
            cash=tp.price * pool_info.cash,
            borrow=tp.price * pool_info.totalBorrows,
            liability=tp.price * pool_info.totalLiability,
            reserve=tp.price * pool_info.totalReserves,
            net=tp.price * (pool_info.cash + pool_info.totalBorrows - pool_info.totalLiability),
            block_number=pool_info.block_number,
            block_datetime=pool_info.block_datetime,
        )
