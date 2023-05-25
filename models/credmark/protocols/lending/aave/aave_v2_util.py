# pylint:disable=unsupported-membership-test, line-too-long, pointless-string-statement, protected-access

import pandas as pd
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import Contract

from models.credmark.tokens.token import get_eip1967_proxy_err
from models.tmp_abi_lookup import AAVE_LENDING_POOL, AAVE_LENDING_POOL_PROXY


def get_aave_lender(context, start_block, end_block, query_filter=''):
    """
    reserve in [@weth.address.checksum]
    reserve in [@weth.address.checksum, @usdc.address.checksum]
    """
    lending_pool_contract = get_lending_pool(context)
    if lending_pool_contract.proxy_for is not None:
        df_aave_deposit = pd.DataFrame(lending_pool_contract.fetch_events(
            lending_pool_contract.proxy_for.events.Deposit,
            from_block=start_block, to_block=end_block,
            contract_address=lending_pool_contract.address))

        if query_filter != '':
            return df_aave_deposit.query(query_filter).user.unique()

        return df_aave_deposit

    raise ModelDataError('Lending pool contract shall be a proxy contract')


def get_lending_pool(context):
    lending_pool = context.run_model('aave-v2.get-lending-pool')
    lending_pool_address = lending_pool['address']

    aave_lending_pool_proxy = get_eip1967_proxy_err(context,
                                                    context.logger,
                                                    lending_pool_address,
                                                    True)

    lending_pool_contract = Contract(address=lending_pool_address)
    lending_pool_contract.set_abi(AAVE_LENDING_POOL_PROXY, set_loaded=True)
    lending_pool_contract._meta.proxy_implementation = Contract(
        aave_lending_pool_proxy.address)
    lending_pool_contract._meta.proxy_implementation.set_abi(
        AAVE_LENDING_POOL, set_loaded=True)  # pylint: disable=protected-access

    return lending_pool_contract
