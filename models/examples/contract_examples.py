from credmark.cmf.model import Model, EmptyInput
from credmark.cmf.types import Contract
from models.examples.example_dtos import ExampleModelOutput

from models.tmp_abi_lookup import CMK_ABI, CMK_ADDRESS


@Model.describe(
    slug='example.contract',
    version='1.0',
    display_name='Contract Usage Examples',
    description='This model gives examples of the functionality available on the Contract class',
    developer='Credmark',
    input=EmptyInput,
    output=dict)
class ExampleAddress(Model):
    def run(self, _) -> ExampleModelOutput:
        output = ExampleModelOutput(
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/contract_examples.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/reference/credmark.cmf.types.contract.Contract.html")

        output.log("This model demonstrates the functionality of the Contract class")

        output.log("Contract is a subclass of Account, and is initialized with an address.")
        contract = Contract(address=CMK_ADDRESS)
        output.log_io(input=f"Contract(address='{CMK_ADDRESS}')", output=contract.dict())

        output.log("You can interact with contract functions")
        output.log_io(input="contract.functions.name().call()",
                      output=contract.functions.name().call())
        output.log_io(input="contract.functions.symbol().call()",
                      output=contract.functions.symbol().call())
        output.log_io(input="contract.functions.decimals().call()",
                      output=contract.functions.decimals().call())
        output.log("You can also pass parameters to contract functions")
        output.log_io(input="contract.functions.balanceOf('0xCbF507C87f19B58fB719B65697Fb7fA84D682aA9').call()",
                      output=contract.functions.balanceOf('0xCbF507C87f19B58fB719B65697Fb7fA84D682aA9').call())

        return output
