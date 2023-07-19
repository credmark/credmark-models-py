# pylint:disable=unsupported-membership-test, line-too-long, pointless-string-statement, protected-access

from typing import Optional, cast

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (
    Address,
    Contract,
    NativeToken,
    Portfolio,
    Position,
    PriceWithQuote,
    Some,
    Token,
)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO
from web3.exceptions import ABIFunctionNotFound  # , Web3ValidationError

from models.credmark.tokens.token import get_eip1967_proxy, get_eip1967_proxy_err
from models.dtos.tvl import LendingPoolPortfolios
from models.tmp_abi_lookup import (
    AAVE_ATOKEN,
    AAVE_STABLEDEBT_ABI,
)


class AaveDebtInfo(DTO):
    token: Token
    token_price: PriceWithQuote
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


class AaveV2Token(Token):
    class Config:
        schema_extra = {
            'description': "Tokens to be supplied and lend from Aave V2",
            'examples': [{"symbol": "AAVE"},
                         {"address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"},
                         {"symbol": "USDC"}]}


@Model.describe(slug="aave-v2.get-oracle-price",
                version="1.3",
                display_name="Aave V2 - Query price oracle for main market - in ETH",
                description="Price of Token / ETH",
                category='protocol',
                subcategory='aave-v2',
                input=AaveV2Token,
                output=PriceWithQuote)
class AaveV2GetOraclePrice(Model):
    def run(self, input: AaveV2Token) -> PriceWithQuote:
        oracle = Contract(
            **self.context.models(local=True).aave_v2.get_price_oracle())
        price = oracle.functions.getAssetPrice(input.address).call()
        source = oracle.functions.getSourceOfAsset(input.address).call()
        native_token = NativeToken()
        return PriceWithQuote.eth(price=native_token.scaled(price),
                                  src=f'{self.slug}|{source}')


@Model.describe(slug="aave-v2.overall-liabilities-portfolio",
                version="1.4",
                display_name="Aave V2 Lending Pool overall liabilities",
                description="Aave V2 liabilities for the main lending pool",
                category='protocol',
                subcategory='aave-v2',
                output=Portfolio)
class AaveV2GetLiability(Model):
    def run(self, input) -> Portfolio:
        aave_lending_pool = self.context.run_model(
            'aave-v2.get-lending-pool', {},
            return_type=Contract, local=True)

        aave_lending_pool = get_eip1967_proxy_err(self.context,
                                                  self.logger,
                                                  aave_lending_pool.address,
                                                  True)

        aave_assets = aave_lending_pool.functions.getReservesList().call()

        map_results = self.context.models.compose.map_inputs(
            modelSlug='aave-v2.token-liability',
            modelInputs=[Token(address=asset) for asset in aave_assets],
            return_type=MapInputsOutput[Token, Position])

        map_results = cast(MapInputsOutput[Token, Position], map_results)
        positions = [res.output for res in map_results.results
                     if res.error is None and res.output is not None]
        assert len(positions) == len(aave_assets)
        return Portfolio(positions=positions)


@Model.describe(slug="aave-v2.token-liability",
                version="1.2",
                display_name="Aave V2 token liability",
                description="Aave V2 token liability at a given block number",
                category='protocol',
                subcategory='aave-v2',
                input=AaveV2Token,
                output=Position)
class AaveV2GetTokenLiability(Model):

    def run(self, input: Contract) -> Position:
        aave_lending_pool = self.context.run_model(
            'aave-v2.get-lending-pool', {},
            return_type=Contract, local=True)
        aave_lending_pool = get_eip1967_proxy_err(
            self.context, self.logger, aave_lending_pool.address, True)

        reservesData = aave_lending_pool.functions.getReserveData(
            input.address).call()
        # self.logger.info(f'info {reservesData}, {reservesData[7]}')

        aToken = get_eip1967_proxy_err(
            self.context, self.logger, reservesData[7], True)
        try:
            _ = aToken.total_supply
        except ModelDataError:
            self.logger.error(
                f"total supply cannot be None for {aToken.address}")
            raise
        return Position(asset=aToken, amount=float(aToken.total_supply))


@Model.describe(slug="aave-v2.assets",
                version="0.3",
                display_name="Aave V2 Lending Pool Assets",
                description="Aave V2 assets for the main lending pool",
                category='protocol',
                subcategory='aave-v2',
                output=Some[Address])
class AaveV2GetAssets(Model):
    def run(self, _) -> Some[Address]:
        aave_lending_pool = self.context.run_model(
            'aave-v2.get-lending-pool', {},
            return_type=Contract, local=True)
        aave_lending_pool = get_eip1967_proxy_err(self.context,
                                                  self.logger,
                                                  aave_lending_pool.address,
                                                  True)

        aave_assets_address = aave_lending_pool.functions.getReservesList().call()
        return Some[Address](some=aave_assets_address)


@Model.describe(slug="aave-v2.lending-pool-assets",
                version="1.7",
                display_name="Aave V2 Lending Pool Assets Detail",
                description="Aave V2 assets for the main lending pool",
                category='protocol',
                subcategory='aave-v2',
                output=Some[AaveDebtInfo])
class AaveV2GetAssetsDetail(Model):
    def run(self, _) -> Some[AaveDebtInfo]:
        aave_assets_address = self.context.run_model(
            'aave-v2.assets', {}, return_type=Some[Address]).some

        model_slug = 'aave-v2.token-asset'
        model_inputs = [Token(address=addr)
                        for addr in aave_assets_address]

        def _use_compose():
            all_pool_infos_results = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': model_slug,
                       'modelInputs': model_inputs},
                return_type=MapInputsOutput[dict, AaveDebtInfo]
            )

            aave_debts_infos = []
            for pool_n, pool_result in enumerate(all_pool_infos_results):
                if pool_result.output is not None:
                    aave_debts_infos.append(pool_result.output)
                elif pool_result.error is not None:
                    self.logger.error(pool_result.error)
                    if pool_result.error.message.startswith('aToken') and pool_result.error.message.endswith('was not initialized'):
                        continue
                    raise ModelRunError(
                        (f'Error with models({self.context.block_number}).' +
                            f'{model_slug.replace("-","_")}(input={model_inputs[pool_n]}). ' +
                            pool_result.error.message))
                else:
                    raise ModelRunError(
                        'compose.map-inputs: output/error cannot be both None')

            return aave_debts_infos

        def _use_for():
            aave_debts_infos = []
            for asset_n, asset in enumerate(model_inputs):
                try:
                    debt_info = self.context.run_model(
                        model_slug, asset,
                        return_type=AaveDebtInfo)
                except ModelDataError as err:
                    if err.data.message.startswith('aToken') and err.data.message.endswith('was not initialized'):  # pylint:disable=no-member
                        continue
                    raise
                aave_debts_infos.append(debt_info)
                self.logger.info(
                    f'[{self.slug}] asset '
                    f'({asset_n+1}/{len(model_inputs)}): {asset}')
            return aave_debts_infos

        # return Some[AaveDebtInfo](some=_use_compose())
        return Some[AaveDebtInfo](some=_use_for())


@Model.describe(slug="aave-v2.lending-pool-assets-portfolio",
                version="0.2",
                display_name="Aave V2 Lending Pool overall liabilities",
                description="Aave V2 liabilities for the main lending pool",
                category='protocol',
                subcategory='aave-v2',
                output=LendingPoolPortfolios)
class AaveV2GetLiabilityInPortfolios(Model):
    def run(self, _) -> LendingPoolPortfolios:
        debt_pools = self.context.run_model(
            'aave-v2.lending-pool-assets', {}, return_type=Some[AaveDebtInfo])

        n_debts = len(debt_pools.some)
        positions_net = []
        positions_supply = []
        positions_debt = []
        prices = {}
        supply_value = 0
        debt_value = 0
        net_value = 0
        for n_debt, dbt in enumerate(debt_pools):
            self.logger.debug(f'{n_debt+1}/{n_debts} {dbt.aToken.address=} '
                              f'{dbt.totalLiquidity_qty=} '
                              f'from {dbt.totalSupply_qty=}-{dbt.totalDebt_qty=}')

            positions_net.append(
                Position(amount=dbt.totalLiquidity_qty, asset=dbt.token))
            positions_supply.append(
                Position(amount=dbt.totalSupply_qty, asset=dbt.token))
            positions_debt.append(
                Position(amount=dbt.totalDebt_qty, asset=dbt.token))
            prices[dbt.token.address] = dbt.token_price
            supply_value += dbt.totalSupply_qty * dbt.token_price.price
            debt_value += dbt.totalDebt_qty * dbt.token_price.price
            net_value += dbt.totalLiquidity_qty * dbt.token_price.price

        return LendingPoolPortfolios(
            supply=Portfolio(positions=positions_supply),
            debt=Portfolio(positions=positions_debt),
            net=Portfolio(positions=positions_net),
            prices=prices,
            supply_value=supply_value,
            debt_value=debt_value,
            net_value=net_value,
            tvl=net_value)


@Model.describe(slug="aave-v2.token-asset",
                version="1.5",
                display_name="Aave V2 token liquidity",
                description="Aave V2 token liquidity at a given block number",
                category='protocol',
                subcategory='aave-v2',
                input=AaveV2Token,
                output=AaveDebtInfo)
class AaveV2GetTokenAsset(Model):
    def _get_token_price(self, token: Token):
        try:
            pdb = self.context.models.price.dex_db(address=token.address)
            return PriceWithQuote.usd(price=pdb['price'], src=pdb['protocol'])
        except ModelDataError as err:
            if "No price for" in err.data.message:
                return self.context.models.price.quote(base=token, return_type=PriceWithQuote)
            raise

    def run(self, input: AaveV2Token):
        aave_lending_pool = self.context.run_model(
            'aave-v2.get-lending-pool', {}, return_type=Contract)

        aave_lending_pool = get_eip1967_proxy_err(self.context,
                                                  self.logger,
                                                  aave_lending_pool.address,
                                                  True)

        reservesData = aave_lending_pool.functions.getReserveData(
            input.address).call()

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

        # 7. aTokenAddress | address | address of associated aToken (tokenized deposit) |
        # 8. stableDebtTokenAddress | address | address of associated stable debt token |
        # 9. variableDebtTokenAddress | address | address of associated variable debt token |
        # 10. interestRateStrategyAddress | address | address of interest rate strategy
        # 11. id | uint8 | the position in the list of active reserves |

        aToken = get_eip1967_proxy(
            self.context, self.logger, reservesData[7], True)
        if aToken is None:
            raise ModelDataError(
                f'aToken({reservesData[7]}) was not initialized')

        aToken.set_abi(AAVE_ATOKEN, set_loaded=True)
        if aToken.proxy_for is not None and aToken.proxy_for._meta.proxy_implementation is not None:
            aToken.proxy_for._meta.proxy_implementation.set_abi(
                AAVE_ATOKEN, set_loaded=True)

        stableDebtToken = get_eip1967_proxy_err(
            self.context, self.logger, reservesData[8], True)
        variableDebtToken = get_eip1967_proxy_err(
            self.context, self.logger, reservesData[9], True)
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
                stableDebtToken.proxy_for.set_abi(AAVE_STABLEDEBT_ABI)
            else:
                raise

        supplyData = stableDebtToken.functions.getSupplyData().call()
        (totalStablePrincipleDebt,
         _totalStableDebt,
         _avgStableRate,
         _timestampLastUpdate) = supplyData
        totalStablePrincipleDebt = stableDebtToken.scaled(
            totalStablePrincipleDebt)

        totalSupply = aToken.scaled(aToken.total_supply)
        totalStableDebt = stableDebtToken.scaled(stableDebtToken.total_supply)
        totalVariableDebt = variableDebtToken.scaled(
            variableDebtToken.total_supply)
        totalInterest = totalStableDebt - totalStablePrincipleDebt

        if totalStableDebt is not None and totalVariableDebt is not None:
            totalDebt = totalStableDebt + totalVariableDebt
            totalLiquidity = totalSupply - totalDebt

            return AaveDebtInfo(
                token=input,
                token_price=self._get_token_price(input),  # type: ignore
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


@Model.describe(slug="aave-v2.reserve-config",
                version="0.3",
                display_name="Aave V2 reserve configuration data",
                description="Aave V2 metadata of the inputted reserve token",
                category="protocol",
                subcategory="aave-v2",
                input=AaveV2Token,
                output=dict,
                )
class AaveV2GetReserveConfigurationData(Model):
    def run(self, input: AaveV2Token) -> dict:
        protocolDataProvider = self.context.run_model(
            "aave-v2.get-protocol-data-provider", {},
            return_type=Contract, local=True)

        config_data = protocolDataProvider.functions.getReserveConfigurationData(
            input.address).call()

        keys_need_to_be_decimal = ['ltv',
                                   'liquidationThreshold',
                                   'liquidationBonus',
                                   'reserveFactor']

        keys = ['decimals',
                'ltv',
                'liquidationThreshold',
                'liquidationBonus',
                'reserveFactor',
                'usageAsCollateralEnabled',
                'borrowingEnabled',
                'stableBorrowRateEnabled',
                'isActive',
                'isFrozen']

        reserve_config_data = {}
        for key, value in zip(keys, config_data):
            if key in keys_need_to_be_decimal:
                reserve_config_data[key] = value/10000
            else:
                reserve_config_data[key] = value

        return reserve_config_data
