from credmark.cmf.model import Model, EmptyInput
from credmark.cmf.types import Contract
from models.dtos.example import ExampleModelOutput

from models.tmp_abi_lookup import CMK_ADDRESS


@Model.describe(
    slug='example.contract',
    version='1.1',
    display_name='Example - Contract',
    description='This model gives examples of the functionality available on the Contract class',
    developer='Credmark',
    input=EmptyInput,
    output=ExampleModelOutput)
class ExampleContract(Model):
    def run(self, _) -> ExampleModelOutput:
        output = ExampleModelOutput(
            title="5. Example - Contract",
            description="This model gives examples of the functionality available on the Contract class",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_05_contract.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/reference/credmark.cmf.types.contract.Contract.html")

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
