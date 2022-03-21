# pylint: disable=locally-disabled, line-too-long

from typing import (
    Union
)

import credmark.model

from credmark.types import (
    Address,
    Contract,
)

from credmark.dto import (
    DTO,
)

# TODO: Need to get ABI's programmatically, I want to be able to do something like:
# self.context.contract(protocol:Union[str, None], product:Union[str,None], address:Union[str, None], abi:Union[str,None])

from models.tmp_abi_lookup import (
    CMK_ADDRESS,
    CMK_ABI,
    STAKED_CREDMARK_ADDRESS,
    STAKED_CREDMARK_ABI,
)


@credmark.model.describe(slug='xcmk.total-supply',
                         version='1.0',
                         display_name='xCMK Total Supply',
                         description='the Total supply of the xCMK contract'
                         )
class xCmkCmkStaked(credmark.model.Model):  # pylint: disable=invalid-name

    def run(self, input) -> dict:

        cmk_contract = Contract(address=Address(CMK_ADDRESS).checksum,
                                abi=CMK_ABI)
        result = cmk_contract.functions.balanceOf(STAKED_CREDMARK_ADDRESS).call()
        return {'result': result}


@credmark.model.describe(slug='xcmk.cmk-staked',
                         version='1.0',
                         display_name='The amount of CMK that\'s been staked',
                         description='The amount of cmk staked in the staking contract')
class xCmkTotalSupply(credmark.model.Model):  # pylint: disable=invalid-name

    def run(self, input) -> dict:

        staked_credmark = Contract(address=Address(STAKED_CREDMARK_ADDRESS).checksum,
                                   abi=STAKED_CREDMARK_ABI)
        result = staked_credmark.functions.totalSupply().call()
        return {'result': result}


class xCmkDeploymentTimeOutput(DTO):  # pylint: disable=invalid-name
    timestamp: Union[int, None]


@credmark.model.describe(slug='xcmk.deployment-time',
                         version='1.0',
                         display_name='xCMK deployment time',
                         description='xCMK deployment time',
                         developer='Credmark',
                         output=xCmkDeploymentTimeOutput)
class xCmkDeploymentTime(credmark.model.Model):  # pylint: disable=invalid-name
    """
    xCmkDeploymentTime
    """

    def run(self, input) -> xCmkDeploymentTimeOutput:
        txn_cols = self.context.ledger.Transaction.Columns

        # get minimum block with to=staked_credmark
        result = self.context.ledger.get_transactions(
            [txn_cols.BLOCK_TIMESTAMP],
            where=f"{txn_cols.TO_ADDRESS} = '{Address(STAKED_CREDMARK_ADDRESS)}'",
            order_by=f'{txn_cols.BLOCK_TIMESTAMP} ASC',
            limit='1')

        rows = result.data
        timestamp = rows[0].get(txn_cols.BLOCK_TIMESTAMP) if len(rows) else None
        return xCmkDeploymentTimeOutput(timestamp=timestamp)
