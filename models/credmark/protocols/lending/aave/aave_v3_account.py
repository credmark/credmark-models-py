# pylint:disable=line-too-long, protected-access, invalid-name

from typing import NamedTuple, Union, cast

import numpy as np
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import (
    ModelRunError,
    create_instance_from_error_dict,
)
from credmark.cmf.types import (
    Account,
    MapBlocksOutput,
    PriceWithQuote,
    Token,
)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.cmf.types.series import BlockSeries
from credmark.dto import DTOField

from models.credmark.chain.contract import ContractEventsInput, ContractEventsOutput, fetch_events_with_range
from models.credmark.protocols.lending.aave.aave_v3_deployment import AaveV3


class AaveV3LPAccount(Account):
    class Config:
        schema_extra = {
            'description': "Account had supplied to Aave V3",
            'examples': [{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E",
                          '_test_multi': {'chain_id': 1, 'block_number': 17718495}}],
            'test_multi': True,
        }

# credmark-dev run aave-v3.account-summary -i '{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E"}' -j -b 17718495 -j
# credmark-dev run aave-v3.account-summary -i '{"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699"}' -j -b 45221317 -c 137


class AaveV3UserAccountData(NamedTuple):
    totalCollateralBase: int
    totalDebtBase: int
    availableBorrowsBase: int
    currentLiquidationThreshold: int
    ltv: int
    healthFactor: int


@Model.describe(slug="aave-v3.account-summary",
                version="1.0",
                display_name="Aave V3 user account summary",
                description="Aave V3 user total collateral, debt, available borrows in base currency, current liquidation threshold and ltv",
                category="protocol",
                subcategory="aave-v3",
                input=AaveV3LPAccount,
                output=dict)
class AaveV3GetAccountSummary(AaveV3):
    def run(self, input: AaveV3LPAccount) -> dict:
        reserves_data = self.get_ui_data_provider()

        base_info = reserves_data.base_info

        def scaled(x):
            return x / 10 ** base_info.networkBaseTokenPriceDecimals

        base_currency_price_in_usd = float(
            base_info.marketReferenceCurrencyPriceInUsd / base_info.marketReferenceCurrencyUnit)
        network_currency_price_in_usd = scaled(base_info.networkBaseTokenPriceInUsd)

        user_account_data = {'base_currency_price_in_usd': base_currency_price_in_usd,
                             'network_currency_price_in_usd': network_currency_price_in_usd}

        aave_lending_pool = self.get_lending_pool()

        account_data = AaveV3UserAccountData(
            *cast(tuple[int, int, int, int, int, int],
                  aave_lending_pool.functions.getUserAccountData(input.address.checksum).call()))

        user_account_data['totalCollateralBase'] = scaled(account_data.totalCollateralBase)
        user_account_data['totalDebtBase'] = scaled(account_data.totalDebtBase)
        user_account_data['availableBorrowsBase'] = scaled(account_data.availableBorrowsBase)
        user_account_data['currentLiquidationThreshold'] = account_data.currentLiquidationThreshold / 10000
        user_account_data['ltv'] = account_data.ltv / 10000
        user_account_data['healthFactor'] = account_data.healthFactor / 1e18

        return user_account_data


# credmark-dev run aave-v3.account-info -i '{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E"}' -b 17718495 -j
# credmark-dev run aave-v3.account-info -i '{"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699"}' -j -b 45221317 -c 137

@Model.describe(slug="aave-v3.account-info",
                version="1.0",
                display_name="Aave V3 user account info",
                description="Aave V3 user balance (principal and interest) and debt",
                category="protocol",
                subcategory="aave-v3",
                input=AaveV3LPAccount,
                output=dict)
class AaveV3GetAccountInfo(AaveV3):
    def run(self, input: AaveV3LPAccount) -> dict:
        protocolDataProvider = self.get_protocol_data_provider()

        reserve_tokens = cast(
            list[str], protocolDataProvider.functions.getAllReservesTokens().call())

        def _use_for():
            user_reserve_data = []
            for _token_name, token_address in reserve_tokens:
                token_info = self.context.run_model(
                    'aave-v3.account-info-reserve',
                    input={'address': input.address, 'reserve': token_address})
                if token_info != {}:
                    user_reserve_data.append(token_info)
            return user_reserve_data

        def _use_compose():
            user_reserve_data_run = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': 'aave-v3.account-info-reserve',
                       'modelInputs': [{'address': input.address, 'reserve': token_address} for _, token_address in reserve_tokens]},
                return_type=MapInputsOutput[AaveV3LPAccountInfo4Reserve, dict])

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


class AaveV3LPAccountInfo4Reserve(AaveV3LPAccount):
    reserve: Token = DTOField(description='Reserve token')

    class Config:
        schema_extra = {
            'examples': [{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E",
                          "reserve": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # USDT variable debt
                          '_test_multi': {'chain_id': 1, 'block_number': 17718495}},
                         {"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699",
                          "reserve": "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39",
                          '_test_multi': {'chain_id': 137, 'block_number': 45221317}},
                         ],
            'test_multi': True,
        }

# credmark-dev run aave-v3.account-info-reserve -i '{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E", "reserve": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"}' -b 17718495 -j
# credmark-dev run aave-v3.account-info-reserve -i '{"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699", "reserve": "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39"}' -b 45221317 -j -c 137


@Model.describe(slug="aave-v3.account-info-reserve",
                version="1.1",
                display_name="Aave V3 user account info for one reserve token",
                description="Aave V3 user balance (principal and interest) and debt",
                category="protocol",
                subcategory="aave-v3",
                input=AaveV3LPAccountInfo4Reserve,
                output=dict,
                )
class AaveV3GetAccountInfoAsset(AaveV3):
    def run(self, input: AaveV3LPAccountInfo4Reserve) -> dict:
        protocolDataProvider = self.get_protocol_data_provider()

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

        reserve_data = cast(tuple[int, int, int, int, int, int, int, int, bool],
                            (protocolDataProvider.functions
                             .getUserReserveData(token_address, user_address).call()))

        total_balance_and_debt = sum(reserve_data[:3])
        if total_balance_and_debt == 0:
            return {}

        aToken_addresses = cast(tuple[str, str, str],
                                (protocolDataProvider.functions.getReserveTokensAddresses(token_address).call()))

        aToken = self.get_atoken(aToken_addresses[0])

        # Fetch aToken transfer for an account
        def _use_fetch_events():
            _received = fetch_events_with_range(
                self.logger,
                aToken,
                aToken.events.Transfer,
                from_block=0,
                to_block=None,
                argument_filters={'to': user_address},
                contract_address=aToken.address.checksum)
            _sent = fetch_events_with_range(
                self.logger,
                aToken,
                aToken.events.Transfer,
                from_block=0,
                to_block=None,
                argument_filters={'from': user_address},
                contract_address=aToken.address.checksum)

            return _received, _sent

        def use_contract_events():
            if aToken.proxy_for and aToken.proxy_for.abi:
                transfer_abi = aToken.proxy_for.abi.events.Transfer.raw_abi
            elif aToken.abi:
                transfer_abi = aToken.abi.events.Transfer.raw_abi
            else:
                raise ModelRunError('No abi found for aToken')

            _received = self.context.run_model(
                'contract.events',
                ContractEventsInput(
                    address=aToken.address,
                    event_name='Transfer',
                    event_abi=transfer_abi,
                    argument_filters={'to': user_address},
                    from_block=0),
                return_type=ContractEventsOutput).records.to_dataframe()

            _sent = self.context.run_model(
                'contract.events',
                ContractEventsInput(
                    address=aToken.address,
                    event_name='Transfer',
                    event_abi=transfer_abi,
                    argument_filters={'from': user_address},
                    from_block=0),
                return_type=ContractEventsOutput).records.to_dataframe()
            return _received, _sent

        _received, _sent = use_contract_events()

        if _received.empty and _sent.empty:
            atoken_tx = 0.0
        elif _received.empty or _sent.empty:
            _combined = pd.DataFrame()
            if _received.empty:
                _combined = _sent.assign(value=lambda x: x.value*-1)
            elif _sent.empty:
                _combined = _received
            atoken_tx = aToken.scaled(_combined.value.sum())
        else:
            _combined = (pd.concat(
                [_received.loc[:, ['blockNumber', 'logIndex', 'from', 'to', 'value']],
                    (_sent.loc[:, ['blockNumber', 'logIndex', 'from',
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

        price_oracle_contract = self.get_price_oracle()

        base_currency_unit = cast(int, price_oracle_contract.functions.BASE_CURRENCY_UNIT().call())

        atoken_underlying = aToken.functions.UNDERLYING_ASSET_ADDRESS().call()

        asset_price = cast(int, price_oracle_contract.functions.getAssetPrice(
            atoken_underlying).call()) / base_currency_unit
        price_source = price_oracle_contract.functions.getSourceOfAsset(atoken_underlying).call()

        pq = PriceWithQuote.usd(
            price=asset_price, src=f'Aave V3 Oracle {price_oracle_contract.address} from {price_source}')
        token_info["PriceWithQuote"] = pq.dict()
        token_info["ATokenValue"] = token_info['currentATokenBalance'] * pq.price
        token_info["StableDebtValue"] = token_info['currentStableDebt'] * pq.price
        token_info["VariableDebtValue"] = token_info['currentVariableDebt'] * pq.price
        token_info["NetValue"] = token_info["ATokenValue"] - \
            token_info["StableDebtValue"] - token_info["VariableDebtValue"]
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


class AaveV3LPAccountHistorical(AaveV3LPAccount):
    window: str
    interval: str

    class Config:
        schema_extra = {
            'examples': [{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E",
                          "window": "10 days", "interval": "1 days"}]}

# credmark-dev run aave-v3.account-summary-historical -i '{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E", "window": "10 days", "interval": "1 days"}' -b 17718495 -j
# credmark-dev run aave-v3.account-summary-historical -i '{"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699", "window": "10 days", "interval": "1 days"}' -j -b 45221317 -c 137
# credmark-dev run aave-v3.account-summary -i '{"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699"}' -j -b 45221317 -c 137

# Empty
# credmark-dev run aave-v3.account-summary-historical -i '{"address": "0x8130ed5f79aA83d2dB5165EB35bc420B1A48898E", "window": "10 days", "interval": "1 days"}' -j -b 45221317 -c 137
# Non-empty
# credmark-dev run aave-v3.account-summary-historical -i '{"address": "0x9b556c24ed6a8b0de593355ba2f6e43830b53699", "window": "10 days", "interval": "1 days"}' -j -b 45221317 -c 137


@Model.describe(slug="aave-v3.account-summary-historical",
                version="1.1",
                display_name="Aave V3 user account summary historical",
                description=("Aave V3 user total collateral, debt, available borrows in base currency, current liquidation threshold and ltv.\n"
                             "Assume there are \"efficient liquidators\" to act upon each breach of health factor."),
                category="protocol",
                subcategory="aave-v3",
                input=AaveV3LPAccountHistorical,
                output=dict,
                )
class AaveV3GetAccountSummaryHistorical(AaveV3):
    def run(self, input: AaveV3LPAccountHistorical) -> dict:
        """
        # Test in console

        credmark-dev run console -b 45221317 -c 137 --api_url http://localhost:8700

        goto_block(45221317)

        result = context.run_model('aave-v3.account-summary-historical', {"address":"0x9b556c24ed6a8b0de593355ba2f6e43830b53699", "window": "90 days", "interval": "1 days"})
        df = (pd.DataFrame(
                data = [(r['blockNumber'],
                  r['result']['healthFactor'],
                  r['result']['totalDebtBase'],
                  r['result']['totalCollateralBase'],
                  r['result']['currentLiquidationThreshold']) for r in result['result']],
                columns = ['blockNumber', 'healthFactor', 'totalDebtBase', 'totalCollateralBase', 'currentLiquidationThreshold'])
                .query('totalDebtBase > 0'))

        df.plot('blockNumber', 'healthFactor')
        plt.show()

        df.plot('blockNumber', ['totalDebtBase', 'totalCollateralBase'])
        plt.show()
        """

        # 1. Fetch historical user account data
        result_historical = self.context.run_model(
            'historical.run-model',
            {'model_slug': 'aave-v3.account-summary',
             'window': input.window,
             'interval': input.interval,
             'model_input': input,
             'debug': False},
            return_type=BlockSeries[dict])

        result_historical_format = [
            {'blockNumber': p.blockNumber, 'result': p.output} for p in result_historical]

        historical_blocks = set(p.blockNumber for p in result_historical)

        first_block = result_historical[0].blockNumber
        last_block = result_historical[-1].blockNumber

        # 2. Fetch liquidationCall events for this user
        result_blocks_format = []
        if last_block > first_block:
            lending_pool = self.get_lending_pool()

            def _use_fetch_events():
                assert lending_pool.proxy_for
                df = pd.DataFrame(
                    lending_pool.fetch_events(
                        lending_pool.proxy_for.events.LiquidationCall,
                        argument_filters={'user': input.address.checksum},
                        from_block=first_block,
                        to_block=last_block,
                        contract_address=lending_pool.address,
                    ))  # type: ignore
                return df

            def use_contract_events():
                assert lending_pool.proxy_for
                assert lending_pool.proxy_for.abi

                liquidity_call_abi = lending_pool.proxy_for.abi.events.LiquidationCall.raw_abi

                df = self.context.run_model(
                    'contract.events',
                    ContractEventsInput(
                        address=lending_pool.address,
                        event_name='LiquidationCall',
                        event_abi=liquidity_call_abi,
                        argument_filters={'user': str(input.address.checksum)},
                        from_block=first_block),
                    block_number=last_block,
                    return_type=ContractEventsOutput).records.to_dataframe()
                return df

            df = use_contract_events()

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
                        {"modelSlug": "aave-v3.account-summary",
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
