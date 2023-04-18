# pylint:disable=unsupported-membership-test, line-too-long, pointless-string-statement, protected-access

import pandas as pd

from typing import Optional

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError, ModelEngineError
from credmark.cmf.types import (Address, Account, Contract, Contracts,
                                NativeToken, Network, Portfolio, Position,
                                PriceWithQuote, Some, Token)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, EmptyInput
from models.credmark.tokens.token import get_eip1967_proxy, get_eip1967_proxy_err
from models.dtos.tvl import LendingPoolPortfolios
from models.tmp_abi_lookup import AAVE_STABLEDEBT_ABI, AAVE_LENDING_POOL_PROVIDER, AAVE_DATA_PROVIDER, AAVE_ATOKEN
from web3.exceptions import ABIFunctionNotFound  # , Web3ValidationError
from web3 import Web3


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


@Model.describe(slug="aave-v2.get-lending-pool-providers-from-registry",
                version="1.1",
                display_name="Aave V2 - Get lending pool providers",
                description="Aave V2 - Get lending pool providers",
                category='protocol',
                subcategory='aave-v2',
                input=EmptyInput,
                output=Contracts)
class AaveV2GetLendingPoolProviders(Model):
    """
    Returns the lending pool providers
    """
    LENDING_POOL_ADDRESS_PROVIDER_REGISTRY = {
        Network.Mainnet: '0x52D306e36E3B6B02c153d0266ff0f85d18BCD413',
        Network.Görli: '0x3465454D658019f8A0eABD3bC61d2d1Dd3a0735F',
        Network.Polygon: '0x3ac4e9aa29940770aeC38fe853a4bbabb2dA9C19',
        Network.Avalanche: '0x4235E22d9C3f28DCDA82b58276cb6370B01265C2',
        # DEPRECATED - Kovan
        # Network.Kovan: '0x1E40B561EC587036f9789aF83236f057D1ed2A90'
    }

    def run(self, _) -> Contracts:
        addr = Address(
            self.LENDING_POOL_ADDRESS_PROVIDER_REGISTRY[self.context.network])
        address_provider_registry = Contract(address=addr)
        address_providers = address_provider_registry.functions.getAddressesProvidersList().call()
        all_providers = []
        for addr in address_providers:
            cc = Contract(address=addr)
            _ = cc.abi
            all_providers.append(cc)
        return Contracts(contracts=all_providers)


@Model.describe(slug="aave-v2.get-incentive-controller",
                version="0.1",
                display_name="Aave V2 - Get incentive controller",
                description="Aave V2 - Get incentive controller",
                category='protocol',
                subcategory='aave-v2',
                input=EmptyInput,
                output=Contract)
class AaveV2GetIncentiveController(Model):
    """
    Returns the incentive controller
    """
    LENDING_POOL_INCENTIVE_CONTROLLER = {
        Network.Mainnet: '0xd784927Ff2f95ba542BfC824c8a8a98F3495f6b5',
        Network.Polygon: '0x357D51124f59836DeD84c8a1730D72B749d8BC23',
        Network.Avalanche: '0x01D83Fe6A10D2f2B7AF17034343746188272cAc9',
    }

    def run(self, _) -> Contract:
        addr = Address(
            self.LENDING_POOL_INCENTIVE_CONTROLLER[self.context.network])
        return Contract(address=addr)


@Model.describe(slug="aave-v2.get-lp-reward",
                version="0.1",
                display_name="Aave V2 - Get incentive controller",
                description="Aave V2 - Get incentive controller",
                category='protocol',
                subcategory='aave-v2',
                input=Account,
                output=dict)
class AaveV2GetLPIncentive(Model):
    STAKED_AAVE = {
        Network.Mainnet: Address('0x4da27a545c0c5B758a6BA100e3a049001de870f5')
    }

    def run(self, input: Account) -> dict:
        """
        https://app.aave.com/governance/proposal/?proposalId=11
        2,200 stkAAVE per day will be allocated pro-rata across supported markets
        based on the dollar value of the borrowing activity in the underlying market
        """

        incentive_controller = self.context.run_model(
            'aave-v2.get-incentive-controller', input=EmptyInput(), local=True, return_type=Contract)

        # _accrued_rewards shall match with accrued amount from event log
        _accrued_rewards = incentive_controller.functions.getUserUnclaimedRewards(
            input.address).call()

        # data provider gets the reserve tokens and find asset for that reserve token
        _data_provider = self.context.run_model(
            'aave-v2.get-protocol-data-provider', input=EmptyInput(), local=True, return_type=Contract)
        # data_provider.functions.getReserveTokensAddresses().call()
        # incentive_controller.functions.getUserAssetData(input.address).call()

        if not incentive_controller.proxy_for:
            raise ModelDataError('Incentive Controller is a proxy contract')

        df_accrued = pd.DataFrame(
            incentive_controller.fetch_events(
                incentive_controller.proxy_for.events.RewardsAccrued,
                from_block=0,
                to_block=self.context.block_number,
                contract_address=incentive_controller.address, argument_filters={'user': input.address}))

        df_claimed = pd.DataFrame(
            incentive_controller.fetch_events(
                incentive_controller.proxy_for.events.RewardsClaimed,
                from_block=0,
                to_block=self.context.block_number,
                contract_address=incentive_controller.address, argument_filters={'claimer': input.address}))

        staked_aave = Token(self.STAKED_AAVE[self.context.network])

        return {
            'accrued_scaled': int(df_accrued.amount.sum()) / 10 ** staked_aave.decimals if not df_accrued.empty else 0,
            'claimed_scaled': int(df_claimed.amount.sum()) / 10 ** staked_aave.decimals if not df_claimed.empty else 0,
            'staked_aave_address': staked_aave.address.checksum
        }


@Model.describe(slug="aave-v2.get-staking-reward",
                version="0.2",
                display_name="Aave V2 - Get staking controller",
                description="Aave V2 - Get staking controller",
                category='protocol',
                subcategory='aave-v2',
                input=Account,
                output=dict)
class AaveV2GetStakingIncentive(Model):
    STAKED_AAVE = {
        Network.Mainnet: Address('0x4da27a545c0c5B758a6BA100e3a049001de870f5')
    }

    def run(self, input: Account) -> dict:
        staked_aave = Token(self.STAKED_AAVE[self.context.network])
        balance_of_scaled = staked_aave.balance_of_scaled(
            input.address.checksum)
        total_reward = staked_aave.scaled(
            staked_aave.functions.getTotalRewardsBalance(input.address.checksum).call())

        rewards_claimed_df = pd.DataFrame(staked_aave.fetch_events(
            staked_aave.events.RewardsClaimed,
            argument_filters={
                'from': input.address.checksum},
            from_block=0,
            contract_address=staked_aave.address.checksum))

        if rewards_claimed_df.empty:
            rewards_claimed = 0.0
        else:
            rewards_claimed = staked_aave.scaled(
                rewards_claimed_df.amount.sum())

        # this does not include unclaimed rewards
        _staker_reward_to_claim = staked_aave.functions.stakerRewardsToClaim(
            input.address.checksum).call()

        return {
            'staked_aave_address': staked_aave.address.checksum,
            'balance_scaled': balance_of_scaled,
            'reward_scaled': total_reward,
            'total_rewards_claimed': rewards_claimed}


@Model.describe(slug="aave-v2.get-lending-pool-provider",
                version="1.1",
                display_name="Aave V2 - Get lending pool providers",
                description="Aave V2 - Get lending pool providers",
                category='protocol',
                subcategory='aave-v2',
                input=EmptyInput,
                output=Contract)
class AaveV2GetAddressProvider(Model):
    """
    Returns the lending pool address provider
    """
    LENDING_POOL_ADDRESS_PROVIDER = {
        Network.Mainnet: '0xB53C1a33016B2DC2fF3653530bfF1848a515c8c5',
        Network.Görli: '0x5E52dEc931FFb32f609681B8438A51c675cc232d',
        Network.Polygon: '0xd05e3E715d945B59290df0ae8eF85c1BdB684744',
        Network.Avalanche: '0xb6A86025F0FE1862B372cb0ca18CE3EDe02A318f',
        # DEPRECATED - Kovan
        # Network.Kovan: '0x88757f2f99175387ab4c6a4b3067c77a695b0349'
    }

    def run(self, _) -> Contract:
        cc = Contract(address=self.LENDING_POOL_ADDRESS_PROVIDER[self.context.network]).set_abi(
            AAVE_LENDING_POOL_PROVIDER, set_loaded=True)
        _ = cc.abi
        return cc


@Model.describe(slug="aave-v2.get-protocol-data-provider",
                version="1.1",
                display_name="Aave V2 - Get protocol data provider",
                description="Query data provider from address provider",
                category='protocol',
                subcategory='aave-v2',
                input=EmptyInput,
                output=Contract)
class AaveV2GetProtocolDataProvider(Model):
    def run(self, _) -> Contract:
        lending_pool_provider = self.context.run_model('aave-v2.get-lending-pool-provider',
                                                       input=EmptyInput(),
                                                       return_type=Contract,
                                                       local=True,
                                                       )

        try:
            _ = lending_pool_provider.abi
        except ModelEngineError:
            lending_pool_provider.set_abi(
                AAVE_LENDING_POOL_PROVIDER, set_loaded=True)

        try:
            data_provider_address = lending_pool_provider.functions.getAddress(
                "0x01").call()
        except Exception:  # Web3ValidationError:
            data_provider_address = lending_pool_provider.functions.getAddress(Web3.to_bytes(  # type: ignore  # pylint: disable=no-member
                0x0100000000000000000000000000000000000000000000000000000000000000)).call()
        data_provider = Contract(data_provider_address).set_abi(
            AAVE_DATA_PROVIDER, set_loaded=True)
        return data_provider


@Model.describe(slug="aave-v2.get-lending-pool",
                version="1.1",
                display_name="Aave V2 - Get lending pool for main market",
                description="Aave V2 - Get lending pool for main market",
                category='protocol',
                subcategory='aave-v2',
                input=EmptyInput,
                output=Contract)
class AaveV2GetLendingPool(Model):
    def run(self, _) -> Contract:
        lending_pool_provider = self.context.run_model('aave-v2.get-lending-pool-provider',
                                                       input=EmptyInput(),
                                                       return_type=Contract,
                                                       local=True)
        lending_pool_address = lending_pool_provider.functions.getLendingPool().call()
        return Contract(address=lending_pool_address)


@Model.describe(slug="aave-v2.get-price-oracle",
                version="1.1",
                display_name="Aave V2 - Get price oracle for main market",
                description="Aave V2 - Get price oracle for main market",
                category='protocol',
                subcategory='aave-v2',
                input=EmptyInput,
                output=Contract)
class AaveV2GetPriceOracle(Model):
    def run(self, _) -> Contract:
        lending_pool_provider = self.context.run_model('aave-v2.get-lending-pool-provider',
                                                       input=EmptyInput(),
                                                       return_type=Contract,
                                                       local=True)
        price_oracle_address = lending_pool_provider.functions.getPriceOracle().call()
        price_oracle_contract = Contract(address=price_oracle_address)
        _ = price_oracle_contract.abi
        return price_oracle_contract


"""
# PriceOracle
# getAssetPrice() Returns the price of the supported _asset in ETH wei units.
# getAssetsPrices() Returns the price of the supported _asset in ETH wei units.
# getSourceOfAsset()
# getFallbackOracle()
"""


@Model.describe(slug="aave-v2.get-oracle-price",
                version="1.3",
                display_name="Aave V2 - Query price oracle for main market - in ETH",
                description="Price of Token / ETH",
                category='protocol',
                subcategory='aave-v2',
                input=Token,
                output=PriceWithQuote)
class AaveV2GetOraclePrice(Model):
    def run(self, input: Token) -> PriceWithQuote:
        oracle = Contract(
            **self.context.models(local=True).aave_v2.get_price_oracle())
        price = oracle.functions.getAssetPrice(input.address).call()
        source = oracle.functions.getSourceOfAsset(input.address).call()
        native_token = NativeToken()
        return PriceWithQuote.eth(price=native_token.scaled(price),
                                  src=f'{self.slug}|{source}')


@Model.describe(slug="aave-v2.overall-liabilities-portfolio",
                version="1.3",
                display_name="Aave V2 Lending Pool overall liabilities",
                description="Aave V2 liabilities for the main lending pool",
                category='protocol',
                subcategory='aave-v2',
                output=Portfolio)
class AaveV2GetLiability(Model):

    def run(self, input) -> Portfolio:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract,
                                                   local=True)

        aave_lending_pool = get_eip1967_proxy_err(self.context,
                                                  self.logger,
                                                  aave_lending_pool.address,
                                                  True)

        aave_assets = aave_lending_pool.functions.getReservesList().call()

        map_results = self.context.models.compose.map_inputs(
            modelSlug='aave-v2.token-liability',
            modelInputs=[Token(address=asset) for asset in aave_assets],
            return_type=MapInputsOutput[Token, Position])

        # type: ignore
        positions = [
            res.output for res in map_results.results if res.error is None]
        assert len(positions) == len(aave_assets)
        return Portfolio(positions=positions)


@Model.describe(slug="aave-v2.token-liability",
                version="1.1",
                display_name="Aave V2 token liability",
                description="Aave V2 token liability at a given block number",
                category='protocol',
                subcategory='aave-v2',
                input=Token,
                output=Position)
class AaveV2GetTokenLiability(Model):

    def run(self, input: Contract) -> Position:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract,
                                                   local=True)
        aave_lending_pool = get_eip1967_proxy_err(self.context,
                                                  self.logger,
                                                  aave_lending_pool.address,
                                                  True)

        reservesData = aave_lending_pool.functions.getReserveData(
            input.address).call()
        # self.logger.info(f'info {reservesData}, {reservesData[7]}')

        aToken = get_eip1967_proxy_err(
            self.context, self.logger, reservesData[7], True)
        try:
            aToken.total_supply
        except ModelDataError:
            self.logger.error(
                f"total supply cannot be None for {aToken.address}")
            raise
        return Position(asset=aToken, amount=float(aToken.total_supply))


@Model.describe(slug="aave-v2.assets",
                version="0.2",
                display_name="Aave V2 Lending Pool Assets",
                description="Aave V2 assets for the main lending pool",
                category='protocol',
                subcategory='aave-v2',
                output=Some[Address])
class AaveV2GetAssets(Model):
    def run(self, __input: EmptyInput) -> Some[Address]:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract,
                                                   local=True)
        aave_lending_pool = get_eip1967_proxy_err(self.context,
                                                  self.logger,
                                                  aave_lending_pool.address,
                                                  True)

        aave_assets_address = aave_lending_pool.functions.getReservesList().call()
        return Some[Address](some=aave_assets_address)


@Model.describe(slug="aave-v2.lending-pool-assets",
                version="1.6",
                display_name="Aave V2 Lending Pool Assets Detail",
                description="Aave V2 assets for the main lending pool",
                category='protocol',
                subcategory='aave-v2',
                output=Some[AaveDebtInfo])
class AaveV2GetAssetsDetail(Model):
    def run(self, __input: EmptyInput) -> Some[AaveDebtInfo]:
        aave_assets_address = self.context.run_model(
            'aave-v2.assets', input=EmptyInput(), return_type=Some[Address]).some

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
                    if pool_result.error.message.startswith('aToken') and \
                       pool_result.error.message.endswith('was not initialized'):
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

        return Some[AaveDebtInfo](some=_use_compose())
        # return Some[AaveDebtInfo](some=_use_for())


@Model.describe(slug="aave-v2.lending-pool-assets-portfolio",
                version="0.1",
                display_name="Aave V2 Lending Pool overall liabilities",
                description="Aave V2 liabilities for the main lending pool",
                category='protocol',
                subcategory='aave-v2',
                output=LendingPoolPortfolios)
class AaveV2GetLiabilityInPortfolios(Model):
    def run(self, __input: EmptyInput) -> LendingPoolPortfolios:
        debt_pools = self.context.run_model('aave-v2.lending-pool-assets',
                                            input=EmptyInput(),
                                            return_type=Some[AaveDebtInfo])

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
                version="1.4",
                display_name="Aave V2 token liquidity",
                description="Aave V2 token liquidity at a given block number",
                category='protocol',
                subcategory='aave-v2',
                input=Token,
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

    def run(self, input: Token):
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract,
                                                   local=True)

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
            aToken._meta.proxy_implementation.set_abi(
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


@Model.describe(
    slug="aave-v2.reserve-config",
    version="0.1",
    display_name="Aave V2 reserve configuration data",
    description="Aave V2 metadata of the inputted reserve token",
    category="protocol",
    subcategory="aave-v2",
    input=Token,
    output=dict,
)
class AaveV2GetReserveConfigurationData(Model):
    def run(self, input: Token) -> dict:
        protocolDataProvider = self.context.run_model(
            "aave-v2.get-protocol-data-provider",
            input=EmptyInput(),
            return_type=Contract,
            local=True,
        )
        config_data = protocolDataProvider.functions\
            .getReserveConfigurationData(input.address).call()

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
