# pylint: disable=pointless-string-statement

from datetime import datetime
from typing import Any, Optional

import pandas as pd
from credmark.cmf.model import CachePolicy, IncrementalModel, Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import BlockNumber, Contract, Records
from credmark.cmf.types.series import BlockSeries, BlockSeriesRow
from credmark.dto import DTO, DTOField
from requests.exceptions import HTTPError


class ContractEventsInput(Contract):
    event_name: str = DTOField(description='Event name')
    event_abi: Optional[Any] = DTOField(None, description='ABI of the event')

    class Config:
        schema_extra = {
            'examples': [{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974",
                          "event_name": "Deposit",
                          "event_abi": [{"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": True, "internalType": "address", "name": "to", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Deposit", "type": "event"}],  # pylint: disable=line-too-long
                          '_test_multi': {'chain_id': 137, 'block_number': 40100090}}],
            'test_multi': True
        }


@IncrementalModel.describe(slug='contract.events-block-series',
                           version='0.11',
                           display_name='Events from contract (non-mainnet)',
                           description='Get the past events from a contract in block series',
                           category='contract',
                           subcategory='event',
                           input=ContractEventsInput,
                           output=BlockSeries[Records])
class ContractEventsSeries(IncrementalModel):
    def run(self, input: ContractEventsInput, from_block: BlockNumber) -> BlockSeries[dict]:
        if self.context.chain_id == 1:
            raise ModelDataError('This model is not available on mainnet')

        if input.event_abi is not None:
            input_contract = Contract(input.address).set_abi(input.event_abi, set_loaded=True)
        else:
            input_contract = Contract(input.address)

        from_block_number = int(from_block)
        if from_block_number == 0:
            try:
                deployment = self.context.run_model(
                    'token.deployment', {'address': input_contract.address, 'ignore_proxy': True})
                from_block_number = max(from_block_number, deployment['deployed_block_number'])
            except ModelDataError as err:
                if err.data.message.endswith('is not an EOA account'):
                    return BlockSeries()
                raise

        try:
            df_events = pd.DataFrame(input_contract.fetch_events(
                input_contract.events[input.event_name],
                from_block=from_block_number,
                to_block=int(self.context.block_number),
                contract_address=input_contract.address.checksum))
        except HTTPError:
            df_events = pd.DataFrame(input_contract.fetch_events(
                input_contract.events[input.event_name],
                from_block=from_block_number,
                to_block=int(self.context.block_number),
                contract_address=input_contract.address.checksum,
                by_range=10_000))
            self.logger.info('Use by_range=10_000')

        self.logger.info(
            f'[{self.slug}] Finished fetching event {input.event_name} from {from_block_number} '
            f'to {int(self.context.block_number)} on {datetime.now()}')

        if df_events.empty:
            return BlockSeries(series=[])

        df_events = (df_events
                     .drop('args', axis=1)
                     .assign(transactionHash=lambda r: r.transactionHash.apply(lambda x: x.hex()),
                             blockHash=lambda r: r.blockHash.apply(lambda x: x.hex()))
                     .sort_values(['blockNumber', 'transactionIndex', 'logIndex'])
                     .groupby('blockNumber'))

        series = []
        for block_number, group in df_events:
            block_number = BlockNumber(int(str(block_number)))
            series.append(BlockSeriesRow(
                blockNumber=int(block_number),
                blockTimestamp=block_number.timestamp,
                sampleTimestamp=block_number.sample_timestamp,
                output=Records.from_dataframe(group)
            ))
        return BlockSeries(series=series)


class ContractEventsOutput(DTO):
    records: Records = DTOField(description='Contract events records')


@Model.describe(slug='contract.events',
                version='0.11',
                display_name='Events from contract (non-mainnet)',
                description='Get the past events from a contract',
                category='contract',
                subcategory='event',
                input=ContractEventsInput,
                output=ContractEventsOutput,
                cache=CachePolicy.SKIP)
class ContractEvents(Model):
    def run(self, input: ContractEventsInput) -> ContractEventsOutput:
        events_series = self.context.run_model('contract.events-block-series',
                                               input,
                                               return_type=BlockSeries[Records])
        if len(events_series.series) == 0:
            return ContractEventsOutput(records=Records.from_dataframe(pd.DataFrame()))

        df_comb = (pd.concat([r.output.to_dataframe() for r in events_series], ignore_index=True)
                   .sort_values(['blockNumber', 'transactionIndex', 'logIndex'])
                   .reset_index(drop=True))

        return ContractEventsOutput(
            records=Records.from_dataframe(df_comb),
        )
