# pylint:disable=unused-import, line-too-long

import numpy as np
import pandas as pd

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import (Account, Address, Contract, Contracts,
                                MapBlocksOutput, NativeToken, Network, Portfolio, Position,
                                PriceWithQuote, Some, Token)
from credmark.cmf.types.series import BlockSeries
from credmark.dto import EmptyInput
from models.credmark.tokens.token import get_eip1967_proxy_err


@Model.describe(
    slug="aave-v2.account-info",
    version="0.1",
    display_name="Aave V2 user account info",
    description="Aave V2 user balance (principal and interest) and debt",
    category="protocol",
    subcategory="aave-v2",
    input=Account,
    output=dict,
)
class AaveV2GetAccountInfo(Model):
    def run(self, input: Account) -> dict:
        protocolDataProvider = self.context.run_model(
            "aave-v2.get-protocol-data-provider",
            input=EmptyInput(),
            return_type=Contract,
            local=True,
        )
        reserve_tokens = protocolDataProvider.functions.getAllReservesTokens().call()

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
        user_reserve_data = {}
        for token_name, token_address in reserve_tokens:
            reserve_data = (protocolDataProvider.functions
                            .getUserReserveData(token_address, input.address.checksum).call())
            total_balance_and_debt = sum(reserve_data[:3])
            if total_balance_and_debt > 0:
                aToken_addresses = (protocolDataProvider.functions
                                    .getReserveTokensAddresses(token_address).call())

                aToken = get_eip1967_proxy_err(self.context,
                                               self.logger,
                                               aToken_addresses[0],
                                               True)

                # Fetch aToken transfer for an account
                _minted = pd.DataFrame(aToken.fetch_events(
                    aToken.events.Transfer,
                    argument_filters={
                        'to': input.address.checksum},
                    from_block=0,
                    contract_address=aToken.address.checksum))

                _burnt = pd.DataFrame(aToken.fetch_events(
                    aToken.events.Transfer,
                    argument_filters={
                        'from': input.address.checksum},
                    from_block=0,
                    contract_address=aToken.address.checksum))

                _combined = (pd.concat(
                    [_minted.loc[:, ['blockNumber', 'logIndex', 'from', 'to', 'value']],
                     (_burnt.loc[:, ['blockNumber', 'logIndex', 'from', 'to', 'value']].assign(value=lambda x: x.value*-1))
                     ])
                    .sort_values(['blockNumber', 'logIndex'])
                    .reset_index(drop=True))

                atoken_tx = aToken.scaled(_combined.value.sum())

                token_info = {}
                for key, value in zip(keys, reserve_data):
                    if key in keys_need_to_be_scaled:
                        token_info[key] = aToken.scaled(value)
                    else:
                        token_info[key] = value

                pdb = self.context.models.price.dex_db_prefer(
                    address=token_address)
                pq = PriceWithQuote.usd(price=pdb["price"], src=pdb["src"])
                token_info["PriceWithQuote"] = pq.dict()
                token_info['ATokenReward'] = token_info['currentATokenBalance'] - atoken_tx

                # get variableBorrowRate from getReserveData
                token_reserve_data = (protocolDataProvider.functions
                                      .getReserveData(token_address).call())
                token_info['variableBorrowRate'] = token_reserve_data[4]

                # Calculate APY for deposit and borrow
                deposit_APR = token_info['liquidityRate']/ray
                variable_borrow_APR = token_info['variableBorrowRate']/ray
                stable_borrow_APR = token_info['stableBorrowRate']/ray

                deposit_APY = ((1 + (deposit_APR / seconds_per_year)) ** seconds_per_year) - 1
                variable_borrow_APY = ((1 + (variable_borrow_APR / seconds_per_year)) ** seconds_per_year) - 1
                stable_borrow_APY = ((1 + (stable_borrow_APR / seconds_per_year)) ** seconds_per_year) - 1

                token_info['depositAPY'] = deposit_APY
                token_info['variableBorrowAPY'] = variable_borrow_APY
                token_info['stableBorrowAPY'] = stable_borrow_APY

                user_reserve_data[token_name] = token_info

        return user_reserve_data


@Model.describe(
    slug="aave-v2.account-summary",
    version="0.1",
    display_name="Aave V2 user account summary",
    description="Aave V2 user total collateral, debt, available borrows in ETH, current liquidation threshold and ltv",
    category="protocol",
    subcategory="aave-v2",
    input=Account,
    output=dict,
)
class AaveV2GetAccountSummary(Model):
    def run(self, input: Account) -> dict:
        aave_lending_pool = self.context.run_model('aave-v2.get-lending-pool',
                                                   input=EmptyInput(),
                                                   return_type=Contract,
                                                   local=True)

        user_account_data = {}
        account_data = aave_lending_pool.functions.getUserAccountData(input.address).call()

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


@Model.describe(
    slug="aave-v2.account-summary-historical",
    version="0.1",
    display_name="Aave V2 user account summary historical",
    description=("Aave V2 user total collateral, debt, available borrows in ETH, current liquidation threshold and ltv.\n"
                 "Assume there are \"efficient liquiditors\" to act upon each breach of health factor."),
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
        result_historical = self.context.run_model('historical.run-model',
                                                   dict(
                                                       model_slug='aave-v2.account-summary',
                                                       window=input.window,
                                                       interval=input.interval,
                                                       model_input=input),
                                                   return_type=BlockSeries[dict])

        result_historical_format = [dict(blockNumber=p.blockNumber, result=p.output) for p in result_historical]

        historical_blocks = set(p.blockNumber for p in result_historical)

        first_block = result_historical[0].blockNumber
        last_block = result_historical[-1].blockNumber

        # 2. Fetch liquidationCall events for this user
        result_blocks_format = []
        if last_block > first_block:
            lending_pool = Contract(**self.context.run_model('aave-v2.get-lending-pool', local=True))

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
                # To keep:             2  7
                # Shift difference:   *13113    (* to be replace with 3)
                # To keep             1 5  10   (to be subtracted by 1)

                blocks_to_run = df.blockNumber.unique()
                blocks_to_run_diff = blocks_to_run[1:] - blocks_to_run[:-1]

                blocks_to_run_last = np.insert(blocks_to_run_diff, blocks_to_run_diff.size, 3)
                blocks_to_run_simple_last = set(blocks_to_run[np.where(blocks_to_run_last > 2)].tolist())

                blocks_to_run_prev = np.insert(blocks_to_run_diff, 0, 3)
                blocks_to_run_simple_prev = set((blocks_to_run[np.where(blocks_to_run_prev > 2)] - 1).tolist())

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

                    result_blocks_format = [dict(blockNumber=p.blockNumber, result=p.output) for p in result_blocks]

        result_comb = sorted(result_historical_format + result_blocks_format,
                             key=lambda x: x['blockNumber'])  # type: ignore

        # The combined result is sorted by the block number
        # result_blocks = [p.blockNumber for p in result_comb])
        # assert sorted(result_blocks) == result_blocks
        return {'result': result_comb}
