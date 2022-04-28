from credmark.cmf.model import Model, EmptyInput
from credmark.cmf.types import Contract
from credmark.cmf.model.errors import ModelRunError

from models.dtos.example import ExampleModelOutput

from web3._utils.filters import construct_event_filter_params
from web3._utils.events import get_event_data

import socket
from urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ReadTimeout


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
        try:
            vesting_added_events = contract.events.VestingScheduleAdded.createFilter(
                fromBlock=0,
                toBlock=self.context.block_number
            ).get_all_entries()

            output.log_io(input="""
    vesting_added_events = contract.events.VestingScheduleAdded.createFilter(
                fromBlock=0,
                toBlock=self.context.block_number
            ).get_all_entries()""", output=vesting_added_events)
        except (ValueError, socket.timeout, ReadTimeoutError, ReadTimeout):
            # Some Eth node does not support the newer eth_newFilter method
            try:
                # pylint:disable=locally-disabled,protected-access
                event_abi = contract.instance.events.VestingScheduleAdded._get_event_abi()

                __data_filter_set, event_filter_params = construct_event_filter_params(
                    abi_codec=self.context.web3.codec,
                    event_abi=event_abi,
                    address=contract.address.checksum,
                    fromBlock=0,
                    toBlock=self.context.block_number
                )
                vesting_added_events = self.context.web3.eth.get_logs(event_filter_params)
                vesting_added_events = [get_event_data(self.context.web3.codec, event_abi, s)
                                        for s in vesting_added_events]
            except (ReadTimeoutError, ReadTimeout):
                raise ModelRunError(
                    f'There was timeout error when reading logs for {contract.address}')

            output.log_io(input="""
event_abi = contract.instance.events.VestingScheduleAdded._get_event_abi() # pylint:disable=locally-disabled,protected-access

__data_filter_set, event_filter_params = construct_event_filter_params(
    abi_codec=self.context.web3.codec,
    event_abi=event_abi,
    address=contract.address.checksum,
    fromBlock=0,
    toBlock=self.context.block_number
)
vesting_added_events = self.context.web3.eth.get_logs(event_filter_params)
vesting_added_events = [get_event_data(self.context.web3.codec, event_abi, s)
                        for s in vesting_added_events]
""", output=vesting_added_events)

        output.log("And to map the events to list of accounts")
        output.log_io(input="[event['args']['account'] for event in vesting_added_events]",
                      output=[event['args']['account'] for event in vesting_added_events])

        return output
