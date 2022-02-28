from typing import List
import credmark.model
from credmark.types import DTO, DTOField
from credmark.types.data import Address, ContractDTO


class ContractName(DTO):
    contractName: str = DTOField(..., description='The name of the Contract you want to load.')


class ContractList(DTO):
    contracts: List[ContractDTO] = DTOField(..., description='The list of loaded contracts.')


@credmark.model.describe(slug='example-load-contract-by-name',
                         version='1.0',
                         display_name='(Example) Load Contract by Name',
                         description='Load a Contract By Name and Return it',
                         developer='Credmark',
                         input=ContractName,
                         output=ContractList)
class LoadContractByName(credmark.model.Model):

    """
    This Example Loads a Contract by it's name and returns all the addresses in our database
    """

    def run(self, input: ContractName):
        contracts = self.context.contracts.load_description(name=input.contractName)
        return ContractList(contracts=[c.info for c in contracts])


@credmark.model.describe(slug='example-load-contract-by-address',
                         version='1.0',
                         display_name='Contract Loading',
                         description='Load the ABI of a Contract with its Name',
                         input=Address,
                         output=ContractDTO)
class LoadContractByAddress(credmark.model.Model):

    """
    This Example Loads a Contract by it's name and returns all the addresses in our database
    """

    def run(self, input: Address) -> dict:
        contract = self.context.contracts.load_address(address=input.address)
        return contract.info
