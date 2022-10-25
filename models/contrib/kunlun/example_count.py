from credmark.cmf.model import Model
from credmark.dto import DTO, DTOField
from credmark.cmf.model.errors import ModelRunError


class ApeCountInput(DTO):
    block_number_count: int = DTOField(1, gt=0, description='Number of blocks to look back')


@Model.describe(slug='contrib.ape-count',
                version='1.0',
                display_name='Count how many transactions in the one block',
                description="Use ledger and some counts",
                input=ApeCountInput,
                output=dict)
class ContribModel(Model):
    def run(self, input: ApeCountInput) -> dict:
        if input.block_number_count > self.context.block_number:
            raise ModelRunError(f'input block number {input.block_number_count} is larger than '
                                f'the current block numer ${self.context.block_number}')

        with self.context.ledger.Transaction as q:
            count = q.select(
                    aggregates=[(q.HASH.count_distinct_(), 'count_tx')],
                    where=q.BLOCK_NUMBER.gt(self.context.block_number - input.block_number_count))

        with self.context.ledger.Transaction as q:
            df_txs = (q.select(
                columns=[q.HASH,
                         q.FROM_ADDRESS,
                         q.TO_ADDRESS,
                         q.GAS,
                         q.GAS_PRICE],
                where=q.BLOCK_NUMBER.gt(self.context.block_number - input.block_number_count),
                order_by=q.TRANSACTION_INDEX)
                .to_dataframe()
                .drop_duplicates())

        with self.context.ledger.Receipt as q:
            df_rts = (q.select(
                columns=[q.TRANSACTION_HASH,
                         q.CUMULATIVE_GAS_USED,
                         q.EFFECTIVE_GAS_PRICE,
                         q.GAS_USED],
                where=q.BLOCK_NUMBER.eq(self.context.block_number - input.block_number_count),
                order_by=q.TRANSACTION_INDEX)
                .to_dataframe()
                .drop_duplicates())

        # Max gas
        max_gas = int(df_rts.gas_used.max())

        # Total gas cost
        total_gas_cost = (df_rts.gas_used * df_rts.effective_gas_price).sum() / 1e18

        # Unique address in both from and to
        count_address = len(set(df_txs.from_address) | set(df_txs.to_address))

        return {'block_number_count': input.block_number_count,
                'count_txs': count.data[0]['count_tx'],
                'max_gas': max_gas,
                'total_gas_cost': total_gas_cost,
                'count_address': count_address}
