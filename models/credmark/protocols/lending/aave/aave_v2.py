from typing import (
    List,
    Optional,
)

from credmark.cmf.model import Model

from credmark.cmf.model.errors import (
    ModelRunError,
    ModelDataError
)

from credmark.cmf.types import (
    Contract,
    Token,
    Position,
    Portfolio,
)

from credmark.cmf.types.series import BlockSeries

from credmark.dto import (
    DTO,
    EmptyInput,
    IterableListGenericDTO,
)


class AaveDebtInfo(DTO):
    token: Token
    aToken: Token
    stableDebtToken: Token
    variableDebtToken: Token
    interestRateStrategyContract: Optional[Contract]
    aTokenSupply: float
    totalStableDebt: float
    totalVariableDebt: float
    totalDebt: float
    net: float


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

    if token.contract_name == 'InitializableImmutableAdminUpgradeabilityProxy':
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

        aToken = get_eip1967_implementation(self.context, self.logger, reservesData[7])
        stableDebtToken = get_eip1967_implementation(self.context, self.logger, reservesData[8])
        variableDebtToken = get_eip1967_implementation(self.context, self.logger, reservesData[9])
        interestRateStrategyContract = Contract(address=reservesData[10])

        self.logger.info(f'{aToken.address=}')

        aTokenSupply = aToken.scaled(aToken.total_supply)
        totalStableDebt = stableDebtToken.scaled(stableDebtToken.total_supply)
        totalVariableDebt = variableDebtToken.scaled(variableDebtToken.total_supply)
        if totalStableDebt is not None and totalVariableDebt is not None:
            totalDebt = totalStableDebt + totalVariableDebt
            net = aTokenSupply - totalDebt

            return AaveDebtInfo(
                token=input,
                aToken=aToken,
                stableDebtToken=stableDebtToken,
                variableDebtToken=variableDebtToken,
                interestRateStrategyContract=interestRateStrategyContract,
                aTokenSupply=aTokenSupply,
                totalStableDebt=totalStableDebt,
                totalVariableDebt=totalVariableDebt,
                totalDebt=totalDebt,
                net=net)
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
