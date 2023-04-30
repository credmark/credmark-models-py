# pylint: disable=line-too-long
from credmark.cmf.model import Model
from credmark.cmf.types import Contract
from credmark.dto import DTO, DTOField
from requests.exceptions import ReadTimeout
from urllib3.exceptions import ReadTimeoutError
from web3._utils.events import get_event_data
from web3._utils.filters import construct_event_filter_params

from .dtos import ExampleModelOutput


class ExampleContractInput(DTO):
    disable_function_ledger: bool = DTOField(
        False, description="Disable function ledger queries")


@Model.describe(slug='example.contract',
                version='1.4',
                display_name='Example - Contract',
                description='This model gives examples of the functionality available on the Contract class',
                developer='Credmark',
                category='example',
                tags=['contract'],
                input=ExampleContractInput,
                output=ExampleModelOutput)
class ExampleContract(Model):
    @staticmethod
    def test_ledger_function(contract, output):
        if not input.disable_function_ledger:
            with contract.ledger.functions.addVestingSchedule as q:
                output.log(
                    "You can query ledger data for contract function calls")
                output.log_io(
                    input="""
    with contract.ledger.functions.addVestingSchedule as q:
        q.select(columns=[
                    q.BLOCK_NUMBER,
                    q.FN_ACCOUNT,
                    q.FN_ALLOCATION
                ],
                order_by=q.BLOCK_NUMBER.asc(),
                limit=5)
    """,
                    output=q.select(
                        columns=[
                            q.BLOCK_NUMBER,
                            q.FN_ACCOUNT,
                            q.FN_ALLOCATION
                        ],
                        order_by=q.BLOCK_NUMBER,
                        limit=5))

    def run(self, input: ExampleContractInput) -> ExampleModelOutput:
        output = ExampleModelOutput(
            title="5. Example - Contract",
            description="This model gives examples of the functionality available on the "
            "Contract class",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_05_contract.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "reference/credmark.cmf.types.contract.Contract.html")

        output.log(
            "Contract is a subclass of Account, and is initialized with an address.")
        output.log("To interact with one of CMK's vesting contracts:")
        contract = Contract(
            address="0xCbF507C87f19B58fB719B65697Fb7fA84D682aA9")
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

        vesting_added_events = []
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
            vesting_added_events = self.context.web3.eth.get_logs(
                event_filter_params)
            vesting_added_events = [get_event_data(self.context.web3.codec, event_abi, s)
                                    for s in vesting_added_events]

            # Contract ledger queries
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
        except (ReadTimeoutError, ReadTimeout):
            output.log_error('There was timeout error when reading logs for '
                             f'{contract.address}')

        output.log("You can query ledger data for contract events")
        with contract.ledger.events.VestingScheduleAdded as q:
            output.log_io(
                input="""
Get help of the event-specific columns with ``q.colnames``

with contract.ledger.events.VestingScheduleAdded as q:
    q.select(columns=[
                q.BLOCK_NUMBER,
                q.FN_ACCOUNT,
                q.FN_ALLOCATION
            ],
            order_by=f'{q.BLOCK_NUMBER}',
            limit=5))
""",
                output=q.select(
                    columns=[
                        q.BLOCK_NUMBER,
                        q.EVT_ACCOUNT,
                        q.EVT_ALLOCATION
                    ],
                    order_by=q.BLOCK_NUMBER.asc(),
                    limit=5))

        # self.test_ledger_function(contract, output)

        return output
