from typing import Union

from models.tmp_abi_lookup import CMK_ADDRESS, STAKED_CREDMARK_ADDRESS

from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract
from credmark.dto import DTO

# TODO: Need to get ABI's programmatically, I want to be able to do something like:
# self.context.contract(protocol:Union[str, None], product:Union[str,None],
#                       address:Union[str, None], abi:Union[str,None])


@Model.describe(slug='xcmk.total-supply',
                version='1.0',
                display_name='xCMK Total Supply',
                description='the Total supply of the xCMK contract',
                category='protocol',
                subcategory='xcmk')
class xCmkCmkStaked(Model):  # pylint: disable=invalid-name

    def run(self, input) -> dict:
        cmk_contract = Contract(address=Address(CMK_ADDRESS).checksum)
        result = cmk_contract.functions.balanceOf(STAKED_CREDMARK_ADDRESS).call()
        return {'result': result}


@Model.describe(slug='xcmk.cmk-staked',
                version='1.0',
                display_name='The amount of CMK that\'s been staked',
                description='The amount of cmk staked in the staking contract',
                category='protocol',
                subcategory='xcmk')
class xCmkTotalSupply(Model):  # pylint: disable=invalid-name

    def run(self, input) -> dict:

        staked_credmark = Contract(address=Address(STAKED_CREDMARK_ADDRESS).checksum)
        result = staked_credmark.functions.totalSupply().call()
        return {'result': result}


class xCmkDeploymentTimeOutput(DTO):  # pylint: disable=invalid-name
    timestamp: Union[int, None]


@Model.describe(slug='xcmk.deployment-time',
                version='1.1',
                display_name='xCMK deployment time',
                description='xCMK deployment time',
                developer='Credmark',
                category='protocol',
                subcategory='xcmk',
                output=xCmkDeploymentTimeOutput)
class xCmkDeploymentTime(Model):  # pylint: disable=invalid-name
    """
    xCmkDeploymentTime
    """

    def run(self, input) -> xCmkDeploymentTimeOutput:
        # get minimum block with to=staked_credmark
        with self.context.ledger.Transaction as txn:
            result = txn.select(
                columns=[txn.Columns.BLOCK_TIMESTAMP],
                where=f"{txn.Columns.TO_ADDRESS} = '{Address(STAKED_CREDMARK_ADDRESS)}'",
                order_by=f'{txn.Columns.BLOCK_TIMESTAMP} ASC',
                limit='1')

            rows = result.data
            timestamp = rows[0].get(txn.Columns.BLOCK_TIMESTAMP) if len(rows) else None
        return xCmkDeploymentTimeOutput(timestamp=timestamp)
