from typing import List
import credmark.model
from credmark.types.dto import DTO, DTOField
from credmark.types import AddressDTO, ContractDTO


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
        return ContractList(contracts=contracts)


@credmark.model.describe(slug='example-load-contract-by-address',
                         version='1.0',
                         display_name='Contract Loading',
                         description='Load the ABI of a Contract with its Name',
                         input=AddressDTO,
                         output=ContractDTO)
class LoadContractByAddress(credmark.model.Model):

    """
    This Example Loads a Contract by it's name and returns all the addresses in our database
    """

    def run(self, input: AddressDTO) -> ContractDTO:
        contract = self.context.contracts.load_address(address=input.address.checksum)
        return contract
