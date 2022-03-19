from typing import List
import credmark.model
from credmark.dto import (
    DTO,
    DTOField,
)
from credmark.types import Contract


class ContractName(DTO):
    contractName: str = DTOField(..., description='The name of the Contract you want to load.')


class ContractList(DTO):
    contracts: List[Contract] = DTOField(..., description='The list of loaded contracts.')


@credmark.model.describe(slug='example.load-contract-by-name',
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
        contracts = self.context.contracts.load_description(contract_name=input.contractName)
        return ContractList(contracts=contracts)


@credmark.model.describe(slug='example.load-contract-by-address',
                         version='1.0',
                         display_name='Contract Loading',
                         description='Load the ABI of a Contract with its Name',
                         input=Contract,
                         output=Contract)
class LoadContractByAddress(credmark.model.Model):

    """
    This Example Loads a Contract by it's name and returns all the addresses in our database
    """

    def run(self, input: Contract) -> Contract:
        contract = self.context.contracts.load_address(address=input.address.checksum)

        self.logger.info(f'ABI functions: {contract.functions.__dict__.keys()}')
        return contract
