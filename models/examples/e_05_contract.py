from credmark.cmf.model import Model, EmptyInput
from credmark.cmf.types import Contract
from models.dtos.example import ExampleModelOutput


@Model.describe(
    slug='example.contract',
    version='1.2',
    display_name='Example - Contract',
    description='This model gives examples of the functionality available on the Contract class',
    developer='Credmark',
    input=EmptyInput,
    output=ExampleModelOutput)
class ExampleContract(Model):
    def run(self, _) -> ExampleModelOutput:
        output = ExampleModelOutput(
            title="5. Example - Contract",
            description="This model gives examples of the functionality available on the "
            "Contract class",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_05_contract.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "reference/credmark.cmf.types.contract.Contract.html")

        output.log("Contract is a subclass of Account, and is initialized with an address.")
        output.log("To interact with one of CMK's vesting contracts:")
        contract = Contract(address="0xCbF507C87f19B58fB719B65697Fb7fA84D682aA9")
        output.log_io(input="Contract(address='0xCbF507C87f19B58fB719B65697Fb7fA84D682aA9')",
                      output=contract.dict())

        output.log("You can interact with contract functions")
        output.log_io(input="contract.functions.getTokenAddress().call()",
                      output=contract.functions.getTokenAddress().call())
        output.log_io(input="contract.functions.getTotalAllocation().call()",
                      output=contract.functions.getTotalAllocation().call())
        output.log_io(input="contract.functions.getTotalClaimedAllocation().call()",
                      output=contract.functions.getTotalClaimedAllocation().call())
        output.log("You can also pass parameters to contract functions")
        output.log_io(input="contract.functions.getClaimableAmount("
                      "0x2DA5e2C09d4DEc83C38Db2BBE2c1Aa111dDEe028').call()",
                      output=contract.functions.getClaimableAmount(
                          '0x2DA5e2C09d4DEc83C38Db2BBE2c1Aa111dDEe028').call())

        output.log("You can get events by creating filters. To get all vested accounts, "
                   "we can query \"VestingScheduleAdded\" events.")
        vesting_added_events = contract.events.VestingScheduleAdded.createFilter(
            fromBlock=0,
            toBlock=self.context.block_number
        ).get_all_entries()

        output.log_io(input="""
vesting_added_events = contract.events.VestingScheduleAdded.createFilter(
            fromBlock=0,
            toBlock=self.context.block_number
        ).get_all_entries()""", output=vesting_added_events)

        output.log("And to map the events to list of accounts")
        output.log_io(input="[event['args']['account'] for event in vesting_added_events]",
                      output=[event['args']['account'] for event in vesting_added_events])

        return output
