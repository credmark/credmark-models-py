import credmark.model
from credmark.model import EmptyInput
from credmark.types import Contract


@credmark.model.describe(
    slug='example.contract',
    version='1.0',
    display_name='Contract Usage Examples',
    description='This model gives examples of the functionality available on the Contract class',
    developer='Credmark',
    input=EmptyInput,
    output=dict)
class ExampleAddress(credmark.model.Model):
    def run(self, input) -> dict:

        """
            This model demonstrates the functionality of the Address class
        """
        # curve.fi gauge controller
        contract = Contract(address='0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB') 

        self.logger.info(
            "Contract is a subclass of Account, and is itialized with an address.")
        self.logger.info(
            f"Contract(address='0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB') : {contract.dict()}")
        return {"message": "see https://github.com/credmark/credmark-models-py/blob/main/models/examples/contract_examples.py for examples of Contract usage"}
