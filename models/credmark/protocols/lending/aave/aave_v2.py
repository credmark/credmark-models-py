from typing import List, Optional

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import Address, Contract, Contracts, Portfolio, Position, Token
from credmark.dto import DTO, EmptyInput, IterableListGenericDTO
from models.tmp_abi_lookup import AAVE_STABLEDEBT_ABI
from web3.exceptions import ABIFunctionNotFound


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


# PriceOracle
# getAssetPrice() Returns the price of the supported _asset in ETH wei units.
# getAssetsPrices() Returns the price of the supported _asset in ETH wei units.
# getSourceOfAsset()
# getFallbackOracle()

@Model.describe(slug="aave-v2.get-lending-pool-providers-from-registry",
                version="1.1",
                display_name="Aave V2 - Get lending pool providers",
                description="Aave V2 - Get lending pool providers",
                input=EmptyInput,
                output=Contracts)
class AaveV2GetLendingPoolProviders(Model):
    """
    Returns the lending pool providers
    """
    LENDING_POOL_ADDRESS_PROVIDER_REGISTRY = {
        1: '0x52D306e36E3B6B02c153d0266ff0f85d18BCD413',
        42: '0x1E40B561EC587036f9789aF83236f057D1ed2A90'
    }

    def run(self, _) -> Contracts:
        addr = Address(self.LENDING_POOL_ADDRESS_PROVIDER_REGISTRY[self.context.chain_id]).checksum
        address_provider_registry = Contract(address=addr)
        address_providers = address_provider_registry.functions.getAddressesProvidersList().call()
        return Contracts(contracts=address_providers)


@Model.describe(slug="aave-v2.get-lending-pool-provider",
                version="1.1",
                display_name="Aave V2 - Get lending pool providers",
                description="Aave V2 - Get lending pool providers",
                input=EmptyInput,
                output=Contract)
class AaveV2GetLendingPoolProvider(Model):
    """
    Returns the lending pool address provider
    """
    LENDING_POOL_ADDRESS_PROVIDER = {
        # For mainnet
        1: '0xb53c1a33016b2dc2ff3653530bff1848a515c8c5',
        # Kovan
        42: '0x88757f2f99175387ab4c6a4b3067c77a695b0349'
    }

    def run(self, _) -> Contract:
        return Contract(address=self.LENDING_POOL_ADDRESS_PROVIDER[self.context.chain_id])


@ Model.describe(slug="aave-v2.get-lending-pool",
                 version="1.1",
                 display_name="Aave V2 - Get lending pool for main market",
                 description="Aave V2 - Get lending pool for main market",
                 input=EmptyInput,
                 output=Contract)
class AaveV2GetLendingPool(Model):
    def run(self, input: EmptyInput) -> Contract:
        lending_pool_provider = self.context.run_model('aave-v2.get-lending-pool-provider',
                                                       input=EmptyInput(),
                                                       return_type=Contract)
        lending_pool_address = lending_pool_provider.functions.getLendingPool().call()
        lending_pool_contract = Contract(address=lending_pool_address)
        return lending_pool_contract


@Model.describe(slug="aave-v2.get-price-oracle",
                version="1.1",
                display_name="Aave V2 - Get price oracle for main market",
                description="Aave V2 - Get price oracle for main market",
                input=EmptyInput,
                output=Contract)
class AaveV2GetPriceOracle(Model):
    def run(self, input: EmptyInput) -> Contract:
        lending_pool_provider = self.context.run_model('aave-v2.get-lending-pool-provider',
                                                       input=EmptyInput(),
                                                       return_type=Contract)
        price_oracle_address = lending_pool_provider.functions.getPriceOracle().call()
        price_oracle_contract = Contract(address=price_oracle_address)
        return price_oracle_contract


def get_eip1967_implementation(context, logger, token_address):
    # pylint:disable=locally-disabled,protected-access
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
                logger.debug(
                    f'token\'s implmentation is corrected to '
                    f'{proxy_address} from {token.proxy_for.address} for {token.address}')
        else:
            logger.debug(
                f'token\'s implmentation is corrected to '
                f'{proxy_address} from no-proxy for {token.address}')

        token._meta.is_transparent_proxy = True
        token._meta.proxy_implementation = token_implemenation
    else:
        raise ModelDataError(f'Unable to retrieve proxy implementation for {token_address}')
    return token


@Model.describe(slug="aave-v2.overall-liabilities-portfolio",
                version="1.1",
                display_name="Aave V2 Lending Pool overall liabilities",
                description="Aave V2 liabilities for the main lending pool",
                output=Portfolio)
class AaveV2GetLiability(Model):

    def run(self, input) -> Portfolio:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract)
        aave_lending_pool = get_eip1967_implementation(self.context,
                                                       self.logger,
                                                       aave_lending_pool.address)

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
                version="1.1",
                display_name="Aave V2 token liability",
                description="Aave V2 token liability at a given block number",
                input=Token,
                output=Position)
class AaveV2GetTokenLiability(Model):

    def run(self, input: Contract) -> Position:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract)
        aave_lending_pool = get_eip1967_implementation(self.context,
                                                       self.logger,
                                                       aave_lending_pool.address)

        reservesData = aave_lending_pool.functions.getReserveData(input.address).call()
        # self.logger.info(f'info {reservesData}, {reservesData[7]}')

        aToken = get_eip1967_implementation(self.context, self.logger, reservesData[7])
        try:
            aToken.total_supply
        except ModelDataError:
            self.logger.error(f"total supply cannot be None for {aToken.address}")
            raise
        return Position(asset=aToken, amount=float(aToken.total_supply))


@ Model.describe(slug="aave-v2.lending-pool-assets",
                 version="1.1",
                 display_name="Aave V2 Lending Pool Assets",
                 description="Aave V2 assets for the main lending pool",
                 output=AaveDebtInfos)
class AaveV2GetAssets(Model):
    def run(self, input: EmptyInput) -> IterableListGenericDTO[AaveDebtInfo]:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract)
        aave_lending_pool = get_eip1967_implementation(self.context,
                                                       self.logger,
                                                       aave_lending_pool.address)

        aave_assets_address = aave_lending_pool.functions.getReservesList().call()

        aave_debts_infos = []
        for asset_address in aave_assets_address:
            info = self.context.run_model('aave-v2.token-asset',
                                          input=Token(address=asset_address),
                                          return_type=AaveDebtInfo)
            aave_debts_infos.append(info)

        return AaveDebtInfos(aaveDebtInfos=aave_debts_infos)


@Model.describe(slug="aave-v2.token-asset",
                version="1.1",
                display_name="Aave V2 token liquidity",
                description="Aave V2 token liquidity at a given block number",
                input=Token,
                output=AaveDebtInfo)
class AaveV2GetTokenAsset(Model):
    def run(self, input: Token) -> AaveDebtInfo:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract)
        aave_lending_pool = get_eip1967_implementation(self.context,
                                                       self.logger,
                                                       aave_lending_pool.address)

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

        aToken = get_eip1967_implementation(self.context, self.logger, reservesData[7])
        stableDebtToken = get_eip1967_implementation(self.context, self.logger, reservesData[8])
        variableDebtToken = get_eip1967_implementation(self.context, self.logger, reservesData[9])
        interestRateStrategyContract = Contract(address=reservesData[10])

        currentLiquidityRate = reservesData[3] / 1e27
        currentVariableBorrowRate = reservesData[4] / 1e27
        currentStableBorrowRate = reservesData[5] / 1e27

        try:
            # getSupplyData() returns
            # 0. total principle,
            # 1. total stable debt for the reserve (principle+interest),
            # 2. average stable rate
            # 3. last update timestamp
            _ = stableDebtToken.functions.getSupplyData().call()
        except ABIFunctionNotFound:
            # pylint:disable=locally-disabled,protected-access
            if stableDebtToken.proxy_for is not None:
                if stableDebtToken.proxy_for._meta is not None:
                    stableDebtToken.proxy_for._meta.abi = AAVE_STABLEDEBT_ABI
            else:
                raise

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
