# pylint:disable=line-too-long, protected-access

from typing import NamedTuple, Union

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import (
    ModelDataError,
    ModelRunError,
    create_instance_from_error_dict,
)
from credmark.cmf.types import (
    Account,
    Address,
    Contract,
    MapBlocksOutput,
    NativeToken,
    Network,
    PriceWithQuote,
    Token,
)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.cmf.types.series import BlockSeries
from credmark.dto import DTOField

from models.credmark.chain.contract import ContractEventsInput, ContractEventsOutput
from models.credmark.tokens.token import get_eip1967_proxy_err
from models.tmp_abi_lookup import AAVE_DATA_PROVIDER


class AAVEUserReserveData(NamedTuple):
    currentATokenBalance: Union[int, float]
    currentStableDebt: Union[int, float]
    currentVariableDebt: Union[int, float]
    principalStableDebt: Union[int, float]
    scaledVariableDebt: Union[int, float]
    stableBorrowRate: Union[int, float]
    liquidityRate: Union[int, float]
    stableRateLastUpdated: Union[int, float]
    usageAsCollateralEnabled: bool

    def normalize(self):
        return self.__class__(
            currentATokenBalance=self.currentATokenBalance / 1e18,
            currentStableDebt=self.currentStableDebt / 1e18,
            currentVariableDebt=self.currentVariableDebt / 1e18,
            principalStableDebt=self.principalStableDebt / 1e18,
            scaledVariableDebt=self.scaledVariableDebt / 1e18,
            stableBorrowRate=self.stableBorrowRate / 1e27,
            liquidityRate=self.liquidityRate / 1e27,
            stableRateLastUpdated=self.stableRateLastUpdated,
            usageAsCollateralEnabled=self.usageAsCollateralEnabled,
        )


class AccountInfo4Reserve(Account):
    reserve: Token = DTOField(description='Reserve token')

    class Config:
        schema_extra = {
            'examples': [{"address": "0x4a49985b14bd0ce42c25efde5d8c379a48ab02f3",
                          "reserve": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"}]
        }


@Model.describe(slug="aave-v2.account-info-reserve",
                version="0.4",
                display_name="Aave V2 user account info for one reserve token",
                description="Aave V2 user balance (principal and interest) and debt",
                category="protocol",
                subcategory="aave-v2",
                input=AccountInfo4Reserve,
                output=dict,
                )
class AaveV2GetAccountInfoAsset(Model):
    def run(self, input: AccountInfo4Reserve) -> dict:
        protocolDataProvider = (self.context.run_model(
            "aave-v2.get-protocol-data-provider", {},
            return_type=Contract, local=True)
            .set_abi(AAVE_DATA_PROVIDER, set_loaded=True))

        keys_need_to_be_scaled = [
            "currentATokenBalance",
            "currentStableDebt",
            "currentVariableDebt",
            "principalStableDebt",
            "scaledVariableDebt",
        ]
        keys_need_not_to_scaled = ["stableBorrowRate",
                                   "liquidityRate",
                                   "stableRateLastUpdated",
                                   "usageAsCollateralEnabled", ]
        keys = keys_need_to_be_scaled + keys_need_not_to_scaled

        ray = 10**27
        seconds_per_year = 31536000

        reserve_token = input.reserve
        token_address = input.reserve.address.checksum
        user_address = input.address.checksum

        reserve_data = (protocolDataProvider.functions
                        .getUserReserveData(token_address, user_address).call())
        total_balance_and_debt = sum(reserve_data[:3])
        if total_balance_and_debt == 0:
            return {}

        aToken_addresses = (protocolDataProvider.functions
                            .getReserveTokensAddresses(token_address).call())

        aToken = get_eip1967_proxy_err(self.context,
                                       self.logger,
                                       aToken_addresses[0],
                                       True)

        aToken = Token(aToken_addresses[0]).as_erc20(set_loaded=True)

        # Fetch aToken transfer for an account
        _minted = pd.DataFrame(aToken.fetch_events(
            aToken.events.Transfer,
            argument_filters={
                'to': user_address},
            from_block=0,
            contract_address=aToken.address.checksum))

        _burnt = pd.DataFrame(aToken.fetch_events(
            aToken.events.Transfer,
            argument_filters={
                'from': user_address},
            from_block=0,
            contract_address=aToken.address.checksum))

        if _minted.empty and _burnt.empty:
            atoken_tx = 0.0
        elif _minted.empty or _burnt.empty:
            _combined = pd.DataFrame()
            if _minted.empty:
                _combined = _burnt.assign(value=lambda x: x.value*-1)
            elif _burnt.empty:
                _combined = _minted
            atoken_tx = aToken.scaled(_combined.value.sum())
        else:
            _combined = (pd.concat(
                [_minted.loc[:, ['blockNumber', 'logIndex', 'from', 'to', 'value']],
                    (_burnt.loc[:, ['blockNumber', 'logIndex', 'from',
                                    'to', 'value']].assign(value=lambda x: x.value*-1))
                 ])
                .sort_values(['blockNumber', 'logIndex'])
                .reset_index(drop=True))
            atoken_tx = aToken.scaled(_combined.value.sum())

        token_info = {}
        token_info['tokenSymbol'] = reserve_token.symbol
        token_info['tokenAddress'] = reserve_token.address

        for key, value in zip(keys, reserve_data):
            if key in keys_need_to_be_scaled:
                token_info[key] = aToken.scaled(value)
            else:
                token_info[key] = value

        pdb = self.context.models.price.dex(
            base=token_address)
        pq = PriceWithQuote.usd(price=pdb["price"], src=pdb["src"])
        token_info["PriceWithQuote"] = pq.dict()
        token_info['ATokenReward'] = token_info['currentATokenBalance'] - atoken_tx

        # get variableBorrowRate from getReserveData
        token_reserve_data = (protocolDataProvider.functions
                              .getReserveData(token_address).call())
        token_info['variableBorrowRate'] = token_reserve_data[4]

        for key in ["variableBorrowRate", "stableBorrowRate", "liquidityRate"]:
            token_info[key] = token_info[key]/ray

        # Calculate APY for deposit and borrow
        deposit_APR = token_info['liquidityRate']
        variable_borrow_APR = token_info['variableBorrowRate']
        stable_borrow_APR = token_info['stableBorrowRate']

        deposit_APY = ((1 + (deposit_APR / seconds_per_year))
                       ** seconds_per_year) - 1
        variable_borrow_APY = (
            (1 + (variable_borrow_APR / seconds_per_year)) ** seconds_per_year) - 1
        stable_borrow_APY = (
            (1 + (stable_borrow_APR / seconds_per_year)) ** seconds_per_year) - 1

        token_info['depositAPY'] = deposit_APY
        token_info['variableBorrowAPY'] = variable_borrow_APY
        token_info['stableBorrowAPY'] = stable_borrow_APY

        return token_info


class AaveLPAccount(Account):
    class Config:
        schema_extra = {
            'description': "Account had supplied to Aave V2",
            'examples': [{"address": "0x5a7ED8CB7360db852E8AB5B10D10Abd806dB510D"}]}


@Model.describe(slug="aave-v2.get-lp-reward",
                version="0.2",
                display_name="Aave V2 - Get incentive controller",
                description="Aave V2 - Get incentive controller",
                category='protocol',
                subcategory='aave-v2',
                input=AaveLPAccount,
                output=dict)
class AaveV2GetLPIncentive(Model):
    STAKED_AAVE = {
        Network.Mainnet: Address('0x4da27a545c0c5B758a6BA100e3a049001de870f5')
    }

    def run(self, input: AaveLPAccount) -> dict:
        """
        https://app.aave.com/governance/proposal/?proposalId=11
        2,200 stkAAVE per day will be allocated pro-rata across supported markets
        based on the dollar value of the borrowing activity in the underlying market
        """

        incentive_controller = self.context.run_model(
            'aave-v2.get-incentive-controller', {}, local=True, return_type=Contract)

        # _accrued_rewards shall match with accrued amount from event log
        _accrued_rewards = incentive_controller.functions.getUserUnclaimedRewards(
            input.address).call()

        # data provider gets the reserve tokens and find asset for that reserve token
        _data_provider = (self.context.run_model(
            'aave-v2.get-protocol-data-provider', {}, local=True, return_type=Contract)
            .set_abi(AAVE_DATA_PROVIDER, set_loaded=True))
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
            'accrued_scaled': (df_accrued.amount / 10 ** staked_aave.decimals).sum() if not df_accrued.empty else 0,
            'claimed_scaled': (df_claimed.amount / 10 ** staked_aave.decimals).sum() if not df_claimed.empty else 0,
            'staked_aave_address': staked_aave.address.checksum
        }


@Model.describe(slug="aave-v2.get-staking-reward",
                version="0.2",
                display_name="Aave V2 - Get staking controller",
                description="Aave V2 - Get staking controller",
                category='protocol',
                subcategory='aave-v2',
                input=AaveLPAccount,
                output=dict)
class AaveV2GetStakingIncentive(Model):
    STAKED_AAVE = {
        Network.Mainnet: Address('0x4da27a545c0c5B758a6BA100e3a049001de870f5')
    }

    def run(self, input: AaveLPAccount) -> dict:
        if self.context.network != Network.Mainnet:
            return {}

        staked_aave = Token(self.STAKED_AAVE[self.context.network])
        balance_of_scaled = staked_aave.balance_of_scaled(
            input.address.checksum)
        total_reward = staked_aave.scaled(
            staked_aave.functions.getTotalRewardsBalance(input.address.checksum).call())

        def _use_contract_events():
            assert staked_aave.proxy_for and staked_aave.proxy_for.abi

            rewards_claimed_event_abi = [x for x in staked_aave.proxy_for.abi
                                         if 'type' in x and x['type'] == 'event' and
                                         'name' in x and x['name'] == 'RewardsClaimed']

            df_rewards_claimed_all = self.context.run_model(
                'contract.events',
                ContractEventsInput(address=staked_aave.address,
                                    event_name='RewardsClaimed',
                                    event_abi=rewards_claimed_event_abi),
                return_type=ContractEventsOutput).records.to_dataframe()

            _input_address_checksum = input.address.checksum
            df_rewards_claimed = df_rewards_claimed_all.query('`from` == @_input_address_checksum')
            return df_rewards_claimed

        def _use_fetch_events():
            df_rewards_claimed = pd.DataFrame(staked_aave.fetch_events(
                staked_aave.events.RewardsClaimed,
                argument_filters={
                    'from': input.address.checksum},
                from_block=0,
                contract_address=staked_aave.address.checksum))
            return df_rewards_claimed

        df_rewards_claimed = _use_contract_events()

        if df_rewards_claimed.empty:
            rewards_claimed = 0.0
        else:
            rewards_claimed = staked_aave.scaled(sum(df_rewards_claimed.amount.to_list()))

        # this does not include unclaimed rewards
        _staker_reward_to_claim = staked_aave.functions.stakerRewardsToClaim(
            input.address.checksum).call()

        return {
            'staked_aave_address': staked_aave.address.checksum,
            'balance_scaled': balance_of_scaled,
            'reward_scaled': total_reward,
            'total_rewards_claimed': rewards_claimed}


@Model.describe(slug="aave-v2.account-info",
                version="0.4",
                display_name="Aave V2 user account info",
                description="Aave V2 user balance (principal and interest) and debt",
                category="protocol",
                subcategory="aave-v2",
                input=AaveLPAccount,
                output=dict)
class AaveV2GetAccountInfo(Model):
    def run(self, input: AaveLPAccount) -> dict:
        protocolDataProvider = (self.context.run_model(
            "aave-v2.get-protocol-data-provider", {}, return_type=Contract, local=True)
            .set_abi(AAVE_DATA_PROVIDER, set_loaded=True))
        reserve_tokens = protocolDataProvider.functions.getAllReservesTokens().call()

        def _use_for():
            user_reserve_data = []
            for _token_name, token_address in reserve_tokens:
                token_info = self.context.run_model(
                    'aave-v2.account-info-reserve',
                    input={'address': input.address, 'reserve': token_address})
                if token_info != {}:
                    user_reserve_data.append(token_info)
            return user_reserve_data

        def _use_compose():
            user_reserve_data_run = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': 'aave-v2.account-info-reserve',
                       'modelInputs': [{'address': input.address, 'reserve': token_address} for _, token_address in reserve_tokens]},
                return_type=MapInputsOutput[AccountInfo4Reserve, dict])

            user_reserve_data = []
            for p in user_reserve_data_run:
                if p.output is not None:
                    if p.output != {}:
                        user_reserve_data.append(p.output)
                elif p.error is not None:
                    self.logger.error(p.error)
                    raise create_instance_from_error_dict(p.error.dict())
                else:
                    raise ModelRunError(
                        'compose.map-inputs: output/error cannot be both None')

            return user_reserve_data

        def _get_net_apy(user_reserve_data):
            balance_list = []
            for reserve_token in user_reserve_data:
                if reserve_token['currentATokenBalance'] != 0:
                    amount = reserve_token['PriceWithQuote']['price'] * \
                        reserve_token['currentATokenBalance']
                    balance_list.append({'amount': amount,
                                         'APY': reserve_token['depositAPY']})
                if reserve_token['currentStableDebt'] != 0:
                    amount = reserve_token['PriceWithQuote']['price'] * \
                        reserve_token['currentStableDebt']
                    balance_list.append({'amount': -1 * amount,
                                         'APY': reserve_token['stableBorrowAPY']})
                if reserve_token['currentVariableDebt'] != 0:
                    amount = reserve_token['PriceWithQuote']['price'] * \
                        reserve_token['currentVariableDebt']
                    balance_list.append({'amount': -1 * amount,
                                         'APY': reserve_token['variableBorrowAPY']})

            net_worth = 0
            for balance in balance_list:
                net_worth += balance['amount']

            # (deposit amount/net_worth)*APY - (debt amount/net_worth)*APY
            net_apy = 0
            for balance in balance_list:
                net_apy += (balance['amount']/net_worth) * balance['APY']

            return net_apy

        # user_reserve_data = _use_compose()
        user_reserve_data = _use_for()
        net_apy = _get_net_apy(user_reserve_data)
        return {'accountAAVEInfo': user_reserve_data, 'netAPY': net_apy}


@Model.describe(slug="aave-v2.account-summary",
                version="0.3",
                display_name="Aave V2 user account summary",
                description="Aave V2 user total collateral, debt, available borrows in ETH, current liquidation threshold and ltv",
                category="protocol",
                subcategory="aave-v2",
                input=AaveLPAccount,
                output=dict,
                )
class AaveV2GetAccountSummary(Model):
    def run(self, input: AaveLPAccount) -> dict:
        aave_lending_pool = self.context.run_model(
            'aave-v2.get-lending-pool', {}, return_type=Contract, local=True)

        user_account_data = {}
        account_data = aave_lending_pool.functions.getUserAccountData(
            input.address).call()

        keys_need_to_be_scaled = ['totalCollateralETH',
                                  'totalDebtETH',
                                  'availableBorrowsETH']
        keys_need_to_be_decimal = ['currentLiquidationThreshold',
                                   'ltv']

        keys = keys_need_to_be_scaled + keys_need_to_be_decimal + ['healthFactor']
        keys_need_to_be_scaled.append('healthFactor')

        native_token = NativeToken()
        for key, value in zip(keys, account_data):
            if key in keys_need_to_be_scaled:
                user_account_data[key] = native_token.scaled(value)
            elif key in keys_need_to_be_decimal:
                user_account_data[key] = value/10000
            else:
                user_account_data[key] = value

        return user_account_data


class AccountAAVEHistorical(Account):
    window: str
    interval: str

    class Config:
        schema_extra = {
            'examples': [{"address": "0x57E04786E231Af3343562C062E0d058F25daCE9E",
                          "window": "10 days", "interval": "1 days"}]}


@Model.describe(slug="aave-v2.account-summary-historical",
                version="0.2",
                display_name="Aave V2 user account summary historical",
                description=("Aave V2 user total collateral, debt, available borrows in ETH, current liquidation threshold and ltv.\n"
                             "Assume there are \"efficient liquidators\" to act upon each breach of health factor."),
                category="protocol",
                subcategory="aave-v2",
                input=AccountAAVEHistorical,
                output=dict,
                )
class AaveV2GetAccountSummaryHistorical(Model):
    def run(self, input: AccountAAVEHistorical) -> dict:
        """
        # Test in console

        goto_block(16127000)

        result = context.run_model('aave-v2.account-summary-historical', {"address":"0x57E04786E231Af3343562C062E0d058F25daCE9E", "window": "90 days", "interval": "1 days"})
        df = (pd.DataFrame(
                data = [(r['blockNumber'],
                  r['result']['healthFactor'],
                  r['result']['totalDebtETH'],
                  r['result']['totalCollateralETH'],
                  r['result']['currentLiquidationThreshold']) for r in result['result']],
                columns = ['blockNumber', 'healthFactor', 'totalDebtETH', 'totalCollateralETH', 'currentLiquidationThreshold'])
                .query('totalDebtETH > 0'))

        df.plot('blockNumber', 'healthFactor')
        df.plot('blockNumber', ['totalDebtETH', 'totalCollateralETH'])
        plt.show()

        """

        # 1. Fetch historical user account data
        result_historical = self.context.run_model(
            'historical.run-model',
            {'model_slug': 'aave-v2.account-summary',
             'window': input.window,
             'interval': input.interval,
             'model_input': input},
            return_type=BlockSeries[dict])

        result_historical_format = [
            {'blockNumber': p.blockNumber, 'result': p.output} for p in result_historical]

        historical_blocks = set(p.blockNumber for p in result_historical)

        first_block = result_historical[0].blockNumber
        last_block = result_historical[-1].blockNumber

        # 2. Fetch liquidationCall events for this user
        result_blocks_format = []
        if last_block > first_block:
            lending_pool = Contract(
                **self.context.run_model('aave-v2.get-lending-pool', {}))

            if lending_pool.proxy_for is None:
                raise ModelDataError('lending pool shall be a proxy contract')

            df = pd.DataFrame(
                lending_pool.fetch_events(
                    lending_pool.proxy_for.events.LiquidationCall,
                    argument_filters={'user': input.address.checksum},
                    from_block=first_block, to_block=last_block,
                    contract_address=lending_pool.address,
                ))  # type: ignore

            if not df.empty:
                # Skip continuous blocks
                # Keep those blocks with > 2 differences to the next one and before the liquidation

                # Use * to label block with liquidation call event. - for without.
                # Block number: 12345678
                # Label:        ---***--
                # To be kept:   --+--+--

                # Event block series: 12567(10)
                # Difference:         13113(*)  (* to be replace with 3)
                # To keep:             2  7     (in blocks_to_run_simple_last)
                # Shift difference:   *13113    (* to be replace with 3)
                # To keep             1 5  10   (in blocks_to_run_simple_prev, to be subtracted by 1)

                blocks_to_run = df.blockNumber.unique()
                blocks_to_run_diff = blocks_to_run[1:] - blocks_to_run[:-1]

                blocks_to_run_last = np.insert(
                    blocks_to_run_diff, blocks_to_run_diff.size, 3)
                blocks_to_run_simple_last = set(
                    blocks_to_run[np.where(blocks_to_run_last > 2)].tolist())

                blocks_to_run_prev = np.insert(blocks_to_run_diff, 0, 3)
                blocks_to_run_simple_prev = set(
                    (blocks_to_run[np.where(blocks_to_run_prev > 2)] - 1).tolist())

                blocks_to_run_simple = blocks_to_run_simple_last | blocks_to_run_simple_prev

                # get block not in historical
                blocks_to_run_simple = blocks_to_run_simple - historical_blocks

                if len(blocks_to_run_simple) > 0:
                    result_blocks = self.context.run_model(
                        'compose.map-blocks',
                        {"modelSlug": "aave-v2.account-summary",
                         "modelInput": {'address': input.address},
                         "blockNumbers": blocks_to_run_simple},
                        return_type=MapBlocksOutput[dict])

                    result_blocks_format = [
                        {'blockNumber': p.blockNumber, 'result': p.output}
                        for p in result_blocks]

        result_comb = sorted(result_historical_format + result_blocks_format,
                             key=lambda x: x['blockNumber'])  # type: ignore

        # The combined result is sorted by the block number
        # result_blocks = [p.blockNumber for p in result_comb])
        # assert sorted(result_blocks) == result_blocks
        return {'result': result_comb}
