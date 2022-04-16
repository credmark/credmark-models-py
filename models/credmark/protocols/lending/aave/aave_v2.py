from models.tmp_abi_lookup import (
    AAVE_STABLEDEBT_ABI
)
from credmark.dto import (
    DTO,
    EmptyInput,
    IterableListGenericDTO,
)
from credmark.cmf.types.series import BlockSeries
from credmark.cmf.types import (
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
import pandas as pd
from web3.exceptions import (
    ABIFunctionNotFound
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


AAVE_LENDING_POOL_V2 = '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9'


def get_eip1967_implementation(context, logger, token_address):
    """
    eip-1967 compliant, https://eips.ethereum.org/EIPS/eip-1967
    """
    default_proxy_address = ''.join(['0'] * 40)

    token = Token(address=token_address)
    # Got 0xca823F78C2Dd38993284bb42Ba9b14152082F7BD unrecognized by etherscan
    # assert token.proxy_for is not None

    # Many aTokens are not recognized as proxy in Etherscan
    # Token(address='0xfe8f19b17ffef0fdbfe2671f248903055afaa8ca').is_transparent_proxy
    # https://etherscan.io/address/0xfe8f19b17ffef0fdbfe2671f248903055afaa8ca#code
    # token.contract_name == 'InitializableImmutableAdminUpgradeabilityProxy'
    proxy_address = context.web3.eth.get_storage_at(
        token.address,
        '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc').hex()
    if proxy_address[-40:] != default_proxy_address:
        proxy_address = '0x' + proxy_address[-40:]
        token_implemenation = Token(address=proxy_address)
        # TODO: Work around before we can load proxy in the past based on block number.
        if token._meta.is_transparent_proxy:
            if token.proxy_for is not None and proxy_address != token.proxy_for.address:
                logger.warning(
                    f'token\'s implmentation is corrected to '
                    f'{proxy_address} from {token.proxy_for.address} for {token.address}')
        else:
            logger.warning(
                f'token\'s implmentation is corrected to '
                f'{proxy_address} from no-proxy for {token.address}')

        token._meta.is_transparent_proxy = True
        token._meta.proxy_implementation = token_implemenation
    else:
        raise ModelDataError(f'Unable to retrieve proxy implementation for {token_address}')
    return token


@Model.describe(slug="aave.overall-liabilities-portfolio",
                version="1.0",
                display_name="Aave V2 Lending Pool overall liabilities",
                description="Aave V2 liabilities for the main lending pool",
                output=Portfolio)
class AaveV2GetLiability(Model):

    def run(self, input) -> Portfolio:
        aave_lending_pool = get_eip1967_implementation(self.context,
                                                       self.logger,
                                                       AAVE_LENDING_POOL_V2)
        aave_assets = aave_lending_pool.functions.getReservesList().call()

        positions = []
        for asset in aave_assets:
            # self.logger.info(f'getting info for {asset=}')
            pos = self.context.run_model(slug='aave.token-liability',
                                         input=Token(address=asset),
                                         return_type=Position)
            positions.append(pos)

        return Portfolio(positions=positions)


@Model.describe(slug="aave.token-liability",
                version="1.0",
                display_name="Aave V2 token liability",
                description="Aave V2 token liability at a given block number",
                input=Token,
                output=Position)
class AaveV2GetTokenLiability(Model):

    def run(self, input: Contract) -> Position:
        aave_lending_pool = get_eip1967_implementation(self.context,
                                                       self.logger,
                                                       AAVE_LENDING_POOL_V2)

        reservesData = aave_lending_pool.functions.getReserveData(input.address).call()
        # self.logger.info(f'info {reservesData}, {reservesData[7]}')

        aToken = get_eip1967_implementation(self.context, self.logger, reservesData[7])
        try:
            aToken.total_supply
        except ModelDataError:
            self.logger.error(f"total supply cannot be None for {aToken.address}")
            raise
        return Position(asset=aToken, amount=float(aToken.total_supply))


@ Model.describe(slug="aave.lending-pool-assets",
                 version="1.0",
                 display_name="Aave V2 Lending Pool Assets",
                 description="Aave V2 assets for the main lending pool",
                 output=AaveDebtInfos)
class AaveV2GetAssets(Model):
    def run(self, input: EmptyInput) -> IterableListGenericDTO[AaveDebtInfo]:
        aave_lending_pool = get_eip1967_implementation(self.context,
                                                       self.logger,
                                                       AAVE_LENDING_POOL_V2)
        aave_assets_address = aave_lending_pool.functions.getReservesList().call()

        aave_debts_infos = []
        for asset_address in aave_assets_address:
            info = self.context.run_model('aave.token-asset',
                                          input=Token(address=asset_address),
                                          return_type=AaveDebtInfo)
            aave_debts_infos.append(info)
        pd.DataFrame([x.dict() for x in aave_debts_infos]).to_excel(
            f'tmp/aave_debts_infos_{self.context.block_number}.xlsx')
        return AaveDebtInfos(aaveDebtInfos=aave_debts_infos)


@Model.describe(slug="aave.token-asset",
                version="1.0",
                display_name="Aave V2 token liquidity",
                description="Aave V2 token liquidity at a given block number",
                input=Token,
                output=AaveDebtInfo)
class AaveV2GetTokenAsset(Model):
    def run(self, input: Token) -> AaveDebtInfo:
        aave_lending_pool = get_eip1967_implementation(self.context,
                                                       self.logger,
                                                       AAVE_LENDING_POOL_V2)
        reservesData = aave_lending_pool.functions.getReserveData(input.address).call()

        # reservesData
        # | Name | Type | Description |
        # 0. configuration | uint256 | bitmark
        # 1. liquidityIndex | uint128 | liquidity index in ray (1e27) |
        # reservesData[1] / 1e27 ~= aToken.functions.totalSupply().call() / aToken.functions.scaledTotalSupply().call()
        # 2. variableBorrowIndex | uint128 | variable borrow index in ray |
        # reservesData[2] / 1e27 ~= variableDebtToken.functions.totalSupply().call() / variableDebtToken.functions.scaledTotalSupply().call()

        # 3. currentLiquidityRate | uint128 | current supply / liquidity / deposit rate in ray |
        # 4. currentVariableBorrowRate | uint128 | current variable borrow rate in ray |
        # 5. currentStableBorrowRate | uint128 | current stable borrow rate in ray |
        # 6. lastUpdateTimestamp | uint40 | timestamp of when reserve data was last updated |

        # 7. aTokenAddress | address | address of associated aToken (tokenised deposit) |
        # 8. stableDebtTokenAddress | address | address of associated stable debt token |
        # 9. variableDebtTokenAddress | address | address of associated variable debt token |
        # 10. interestRateStrategyAddress | address | address of interest rate strategy. See Risk docs for more info. |
        # 11. id | uint8 | the position in the list of active reserves |

        aToken = get_eip1967_implementation(self.context, self.logger, reservesData[7])
        stableDebtToken = get_eip1967_implementation(self.context, self.logger, reservesData[8])
        variableDebtToken = get_eip1967_implementation(self.context, self.logger, reservesData[9])
        interestRateStrategyContract = Contract(address=reservesData[10])

        currentLiquidityRate = reservesData[3] / 1e27
        currentVariableBorrowRate = reservesData[4] / 1e27
        currentStableBorrowRate = reservesData[5] / 1e27

        try:
            # [total principle, total stable debt for the reserve (principle+interest), average stable rate]
            totalStablePrincipleDebt, _totalStableDebt, _avgStableRate, _timestampLastUpdate = stableDebtToken.functions.getSupplyData().call()
        except ABIFunctionNotFound:
            if stableDebtToken.proxy_for._meta is not None:
                stableDebtToken.proxy_for._meta.abi = AAVE_STABLEDEBT_ABI
                totalStablePrincipleDebt, _totalStableDebt, _avgStableRate, _timestampLastUpdate = stableDebtToken.functions.getSupplyData().call()
            else:
                raise

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


@ Model.describe(slug="aave.token-asset-historical",
                 version="1.0",
                 display_name="Aave V2 token liquidity",
                 description="Aave V2 token liquidity at a given block number",
                 input=Token,
                 output=BlockSeries[AaveDebtInfo])
class AaveV2GetTokenAssetHistorical(Model):
    def run(self, input: Token) -> BlockSeries:
        return self.context.historical.run_model_historical(
            'aave.token-asset',
            model_input=input,
            window='5 days',
            interval='1 day',
            model_return_type=AaveDebtInfo)
