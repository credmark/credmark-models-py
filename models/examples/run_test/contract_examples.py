
import credmark.model


@credmark.model.it(slug='load-contract-name',
                   version='1.0',
                   display_name='Contract Loading',
                   description='Load the ABI of a Contract with its Name')
class LoadContractByName(credmark.model.Model):

    """
    This Example Loads a Contract by it's name and returns all the addresses in our database
    """

    def run(self, input) -> dict:

        contracts = self.context.contract_helper.get_contracts(name="mutantmfers")
        supplies = []
        for c in contracts:
            supplies.append(c.functions.totalSupply().call())
        return supplies


@credmark.model.it(slug='load-contract-address',
                   version='1.0',
                   display_name='Contract Loading',
                   description='Load the ABI of a Contract with its Name')
class LoadContractByName(credmark.model.Model):

    """
    This Example Loads a Contract by it's name and returns all the addresses in our database
    """

    def run(self, input) -> dict:

        contracts = self.context.contract_helper.get_contracts(
            address="0x6d95d3ed3a6de47c384e667bf5f05c8e32a3e3a5")
        supplies = []
        for c in contracts:
            supplies.append(c.functions.totalSupply().call())
        return supplies
