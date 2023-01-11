# pylint:disable=unused-import

from typing import Optional

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelDataError, ModelRunError
from credmark.cmf.types import (Account, Address, Contract, Contracts,
                                NativeToken, Network, Portfolio, Position,
                                PriceWithQuote, Some, Token)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, EmptyInput
from models.credmark.tokens.token import get_eip1967_proxy_err
from models.dtos.tvl import LendingPoolPortfolios
from models.tmp_abi_lookup import AAVE_STABLEDEBT_ABI
from web3.exceptions import ABIFunctionNotFound


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
                user_reserve_data[token_name] = token_info
        return user_reserve_data


# Fetch aToken transfer for an account

# minted = pd.DataFrame(aToken.fetch_events(
#           aToken.events.Transfer,
#           argument_filters={
#          'to': 'account_address_in_checksum'},
#           from_block=0))

# burnt = pd.DataFrame(aToken.fetch_events(
#           aToken.events.Transfer,
#           argument_filters={
#          'from': 'account_address_in_checksum'},
#           from_block=0))
