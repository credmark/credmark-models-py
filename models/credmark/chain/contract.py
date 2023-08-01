# pylint: disable=pointless-string-statement, line-too-long

from datetime import datetime
from typing import Any, Optional

import pandas as pd
from credmark.cmf.model import CachePolicy, IncrementalModel, Model
from credmark.cmf.model.errors import ModelDataError
from credmark.cmf.types import BlockNumber, Contract, Records
from credmark.cmf.types.series import BlockSeries, BlockSeriesRow
from credmark.dto import DTO, DTOField
from requests.exceptions import HTTPError


class ContractEventsBlockSeriesInput(Contract):
    event_name: str = DTOField(description='Event name')
    event_abi: Optional[Any] = DTOField(None, description='ABI of the event')
    argument_filters: Optional[dict] = DTOField(None, description='Event filters')

    class Config:
        schema_extra = {
            'examples': [{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974",
                          "event_name": "Deposit",
                          "event_abi": [{"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": True, "internalType": "address", "name": "to", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Deposit", "type": "event"}],  # pylint: disable=line-too-long
                          '_test_multi': {'chain_id': 137, 'block_number': 40100090}}],
            'test_multi': True
        }


class ContractEventsInput(ContractEventsBlockSeriesInput):
    from_block: int | None = DTOField(
        None, gte=0, description='Block number to start fetching events from')


def fetch_events_with_range(logger,
                            contract: Contract,
                            contract_event,
                            from_block: int,
                            to_block: Optional[int],
                            contract_address=None,
                            argument_filters=None
                            ):
    try:
        df_events = pd.DataFrame(contract.fetch_events(
            contract_event,
            from_block=from_block,
            to_block=to_block,
            contract_address=contract_address,
            argument_filters=argument_filters))
    except HTTPError:
        try:
            df_events = pd.DataFrame(contract.fetch_events(
                contract_event,
                from_block=from_block,
                to_block=to_block,
                contract_address=contract_address,
                argument_filters=argument_filters,
                by_range=10_000))
            if logger:
                logger.info('Use by_range=10_000')
        except ValueError:
            try:
                df_events = pd.DataFrame(contract.fetch_events(
                    contract_event,
                    from_block=from_block,
                    to_block=to_block,
                    contract_address=contract_address,
                    argument_filters=argument_filters,
                    by_range=5_000))
                if logger:
                    logger.info('Use by_range=5_000')
            except ValueError:
                try:
                    df_events = pd.DataFrame(contract.fetch_events(
                        contract_event,
                        from_block=from_block,
                        to_block=to_block,
                        contract_address=contract_address,
                        argument_filters=argument_filters,
                        by_range=2_000))
                    if logger:
                        logger.info('Use by_range=2_000')
                except ValueError:
                    try:
                        df_events = pd.DataFrame(contract.fetch_events(
                            contract_event,
                            from_block=from_block,
                            to_block=to_block,
                            contract_address=contract_address,
                            argument_filters=argument_filters,
                            by_range=1_000))
                        if logger:
                            logger.info('Use by_range=1_000')
                    except ValueError:
                        try:
                            df_events = pd.DataFrame(contract.fetch_events(
                                contract_event,
                                from_block=from_block,
                                to_block=to_block,
                                contract_address=contract_address,
                                argument_filters=argument_filters,
                                by_range=100))
                            if logger:
                                logger.info('Use by_range=100')
                        except ValueError as _err:
                            raise ValueError(
                                f'Can not fetch events for {contract.address} between [{from_block}-{to_block}]') from _err
    return df_events


@IncrementalModel.describe(slug='contract.events-block-series',
                           version='0.13',
                           display_name='Events from contract (non-mainnet)',
                           description='Get the past events from a contract in block series',
                           category='contract',
                           subcategory='event',
                           input=ContractEventsBlockSeriesInput,
                           output=BlockSeries[Records])
class ContractEventsSeries(IncrementalModel):
    def run(self, input: ContractEventsInput, from_block: BlockNumber) -> BlockSeries[dict]:
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

        df_events = fetch_events_with_range(self.logger,
                                            input_contract,
                                            input_contract.events[input.event_name],
                                            from_block_number,
                                            int(self.context.block_number),
                                            input_contract.address.checksum,
                                            input.argument_filters)
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
                version='0.13',
                display_name='Events from contract (non-mainnet)',
                description='Get the past events from a contract',
                category='contract',
                subcategory='event',
                input=ContractEventsInput,
                output=ContractEventsOutput,
                cache=CachePolicy.SKIP)
class ContractEvents(Model):
    def run(self, input: ContractEventsInput) -> ContractEventsOutput:
        events_series = self.context.run_model(
            'contract.events-block-series',
            input=ContractEventsBlockSeriesInput(
                address=input.address,
                event_name=input.event_name,
                event_abi=input.event_abi,
                argument_filters=input.argument_filters),
            return_type=BlockSeries[Records])
        if len(events_series.series) == 0:
            return ContractEventsOutput(records=Records.from_dataframe(pd.DataFrame()))

        df = (pd.concat([r.output.to_dataframe() for r in events_series], ignore_index=True)
              .sort_values(['blockNumber', 'transactionIndex', 'logIndex'])
              .reset_index(drop=True))

        if input.from_block is not None and input.from_block >= 0:
            df = df[df['blockNumber'] >= input.from_block]

        return ContractEventsOutput(
            records=Records.from_dataframe(df),
        )
