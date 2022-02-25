import credmark.model
from credmark.types.dto import DTO, DTOField
from credmark.types.data.address import Address


class ContractName(DTO):
    contractName: str = DTOField(..., description='The name of the Contract you want to load.')


@credmark.model.describe(slug='example-contract-name',
                         version='1.0',
                         display_name='Runner test model',
                         description='Test model runs another model specified with \'model\' in input.',
                         developer='Credmark',
                         input=ContractName)
class LoadContractByName(credmark.model.Model):

    """
    This Example Loads a Contract by it's name and returns all the addresses in our database
    """

    def run(self, input: ContractName):
        contracts = self.context.contracts.load(name=input.contractName)
        supplies = []
        for c in contracts:
            supplies.append(c.functions.totalSupply().call())
        return {'result': supplies}


@credmark.model.describe(slug='load-contract-address',
                         version='1.0',
                         display_name='Contract Loading',
                         description='Load the ABI of a Contract with its Name')
class LoadContractByAddress(credmark.model.Model):

    """
    This Example Loads a Contract by it's name and returns all the addresses in our database
    """

    def run(self, input) -> dict:

        contracts = self.context.contracts.load(
            address=Address("0x68CFb82Eacb9f198d508B514d898a403c449533E"))
        supplies = []
        for c in contracts:
            supplies.append(c.functions.totalSupply().call())
        return {'result': supplies}
