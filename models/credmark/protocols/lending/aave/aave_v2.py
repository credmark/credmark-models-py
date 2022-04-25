from credmark.dto import (
    DTO,
    EmptyInput,
    IterableListGenericDTO,
)

from credmark.cmf.types import (
    Address,
    Contract,
    Token,
    Position,
    Portfolio
)

from credmark.cmf.model.errors import (
    ModelRunError,
    ModelDataError
)

from credmark.cmf.model import Model

from typing import (
    List,
    Optional,
)


class AaveDebtInfo(DTO):
    token: Token
    tokenName: str
    aToken: Token
    stableDebtToken: Token
    variableDebtToken: Token
    interestRateStrategyContract: Optional[Contract]
    supplyRate: float
    variableBorrowRate: float
    stableBorrowRate: float
    totalSupply_qty: float
    totalStableDebt_qty: float
    totalStableDebtPrinciple_qty: float
    totalInterest_qty: float
    totalVariableDebt_qty: float
    totalDebt_qty: float
    totalLiquidity_qty: float


class AaveDebtInfos(IterableListGenericDTO[AaveDebtInfo]):
    aaveDebtInfos: List[AaveDebtInfo]
    _iterator: str = 'aaveDebtInfos'


# For different markets
AAVE_LENDING_POOL_ADDRESS_PROVIDER_REGISTRY = '0x52D306e36E3B6B02c153d0266ff0f85d18BCD413'

# For main market
AAVE_LENDING_POOL_ADDRESS_PROVIDER = '0xb53c1a33016b2dc2ff3653530bff1848a515c8c5'

AAVE_LENDING_POOL_V2 = '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9'


@Model.describe(slug="aave-v2.get-lending-pool",
                version="1.0",
                display_name="Aave V2 - Get lending pool for main market",
                description="Aave V2 - Get lending pool for main market",
                input=EmptyInput,
                output=Contract)
class AaveV2GetLendingPool(Model):
    def run(self, input: EmptyInput) -> Contract:
        address_provider = Contract(address=Address(AAVE_LENDING_POOL_ADDRESS_PROVIDER).checksum)
        lending_pool_address = address_provider.functions.getLendingPool().call()
        lending_pool_contract = Contract(address=lending_pool_address)
        return lending_pool_contract


@Model.describe(slug="aave-v2.get-price-oracle",
                version="1.0",
                display_name="Aave V2 - Get price oracle for main market",
                description="Aave V2 - Get price oracle for main market",
                input=EmptyInput,
                output=Contract)
class AaveV2GetPriceOracle(Model):
    def run(self, input: EmptyInput) -> Contract:
        address_provider = Contract(address=Address(AAVE_LENDING_POOL_ADDRESS_PROVIDER).checksum)
        price_oracle_address = address_provider.functions.getPriceOracle().call()
        price_oracle_contract = Contract(address=price_oracle_address)
        return price_oracle_contract


@Model.describe(slug="aave-v2.overall-liabilities-portfolio",
                version="1.0",
                display_name="Aave V2 Lending Pool overall liabilities",
                description="Aave V2 liabilities for the main lending pool",
                output=Portfolio)
class AaveV2GetLiability(Model):

    def run(self, input) -> Portfolio:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract)

        aave_assets = aave_lending_pool.functions.getReservesList().call()

        positions = []
        for asset in aave_assets:
            # self.logger.info(f'getting info for {asset=}')
            pos = self.context.run_model(slug='aave-v2.token-liability',
                                         input=Token(address=asset),
                                         return_type=Position)
            positions.append(pos)

        return Portfolio(positions=positions)


@Model.describe(slug="aave-v2.token-liability",
                version="1.0",
                display_name="Aave V2 token liability",
                description="Aave V2 token liability at a given block number",
                input=Token,
                output=Position)
class AaveV2GetTokenLiability(Model):

    def run(self, input: Contract) -> Position:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract)

        reservesData = aave_lending_pool.functions.getReserveData(input.address).call()
        # self.logger.info(f'info {reservesData}, {reservesData[7]}')

        aToken = Token(address=reservesData[7])
        try:
            aToken.total_supply
        except ModelDataError:
            self.logger.error(f"total supply cannot be None for {aToken.address}")
            raise
        return Position(asset=aToken, amount=float(aToken.total_supply))


@ Model.describe(slug="aave-v2.lending-pool-assets",
                 version="1.0",
                 display_name="Aave V2 Lending Pool Assets",
                 description="Aave V2 assets for the main lending pool",
                 output=AaveDebtInfos)
class AaveV2GetAssets(Model):
    def run(self, input: EmptyInput) -> IterableListGenericDTO[AaveDebtInfo]:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract)

        aave_assets_address = aave_lending_pool.functions.getReservesList().call()

        aave_debts_infos = []
        for asset_address in aave_assets_address:
            info = self.context.run_model('aave-v2.token-asset',
                                          input=Token(address=asset_address),
                                          return_type=AaveDebtInfo)
            aave_debts_infos.append(info)

        return AaveDebtInfos(aaveDebtInfos=aave_debts_infos)


@Model.describe(slug="aave-v2.token-asset",
                version="1.0",
                display_name="Aave V2 token liquidity",
                description="Aave V2 token liquidity at a given block number",
                input=Token,
                output=AaveDebtInfo)
class AaveV2GetTokenAsset(Model):
    def run(self, input: Token) -> AaveDebtInfo:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract)

        reservesData = aave_lending_pool.functions.getReserveData(input.address).call()

        # reservesData
        # | Name | Type | Description |
        # 0. configuration | uint256 | bitmark
        # 1. liquidityIndex | uint128 | liquidity index in ray (1e27) |
        # / 1e27 ~= aToken.functions.totalSupply().call() /
        #           aToken.functions.scaledTotalSupply().call()
        # 2. variableBorrowIndex | uint128 | variable borrow index in ray |
        # / 1e27 ~= variableDebtToken.functions.totalSupply().call() /
        #           variableDebtToken.functions.scaledTotalSupply().call()

        # 3. currentLiquidityRate | uint128 | current supply / liquidity / deposit rate in ray |
        # 4. currentVariableBorrowRate | uint128 | current variable borrow rate in ray |
        # 5. currentStableBorrowRate | uint128 | current stable borrow rate in ray |
        # 6. lastUpdateTimestamp | uint40 | timestamp of when reserve data was last updated |

        # 7. aTokenAddress | address | address of associated aToken (tokenised deposit) |
        # 8. stableDebtTokenAddress | address | address of associated stable debt token |
        # 9. variableDebtTokenAddress | address | address of associated variable debt token |
        # 10. interestRateStrategyAddress | address | address of interest rate strategy
        # 11. id | uint8 | the position in the list of active reserves |

        aToken = Token(address=reservesData[7])
        stableDebtToken = Token(address=reservesData[8])
        variableDebtToken = Token(address=reservesData[9])
        interestRateStrategyContract = Contract(address=reservesData[10])

        currentLiquidityRate = reservesData[3] / 1e27
        currentVariableBorrowRate = reservesData[4] / 1e27
        currentStableBorrowRate = reservesData[5] / 1e27

        supplyData = stableDebtToken.functions.getSupplyData().call()
        (totalStablePrincipleDebt,
         _totalStableDebt,
         _avgStableRate,
         _timestampLastUpdate) = supplyData
        totalStablePrincipleDebt = stableDebtToken.scaled(totalStablePrincipleDebt)

        totalSupply = aToken.scaled(aToken.total_supply)
        totalStableDebt = stableDebtToken.scaled(stableDebtToken.total_supply)
        totalVariableDebt = variableDebtToken.scaled(variableDebtToken.total_supply)
        totalInterest = totalStableDebt - totalStablePrincipleDebt
        if totalStableDebt is not None and totalVariableDebt is not None:
            totalDebt = totalStableDebt + totalVariableDebt
            totalLiquidity = totalSupply - totalDebt

            return AaveDebtInfo(
                token=input,
                tokenName=input.name,
                aToken=aToken,
                stableDebtToken=stableDebtToken,
                variableDebtToken=variableDebtToken,
                interestRateStrategyContract=interestRateStrategyContract,
                supplyRate=currentLiquidityRate,
                variableBorrowRate=currentVariableBorrowRate,
                stableBorrowRate=currentStableBorrowRate,
                totalSupply_qty=totalSupply,
                totalStableDebt_qty=totalStableDebt,
                totalStableDebtPrinciple_qty=totalStablePrincipleDebt,
                totalVariableDebt_qty=totalVariableDebt,
                totalDebt_qty=totalDebt,
                totalInterest_qty=totalInterest,
                totalLiquidity_qty=totalLiquidity)
        else:
            raise ModelRunError(f'Unable to obtain {totalStableDebt=} and {totalVariableDebt=} '
                                f'for {aToken.address=}')
