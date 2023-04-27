
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.dto import DTO, DTOField


class BlockNumberInput(DTO):
    start_block: int
    unique: bool = DTOField(False, describe='filter for unique address')


@Model.describe(
    slug='contrib.neilz-new-addresses',
    display_name='New Addresses in the past interval',
    description="",
    version='1.0',
    developer='neilz.eth',
    input=BlockNumberInput,
    output=dict
)
class MyModel(Model):
    def run(self, input: BlockNumberInput) -> dict:
        if input.start_block > 0:
            if input.start_block > self.context.block_number:
                raise ModelRunError(
                    f'input\'s start_block {input.start_block} '
                    f'is larger than current block_number ({self.context.block_number})')

            actual_start_block = input.start_block
        else:
            actual_start_block = self.context.block_number + input.start_block

        with self.context.ledger.Transaction as q:
            df_ts = []
            offset = 0

            while True:
                df_tt = (q.select(
                    columns=[q.FROM_ADDRESS],
                    where=q.NONCE.eq(0).and_(
                        q.BLOCK_NUMBER.gt(actual_start_block)),
                    order_by=q.BLOCK_NUMBER,
                    offset=offset)
                    .to_dataframe())

                if df_tt.shape[0] > 0:
                    df_ts.append(df_tt)
                if df_tt.shape[0] < 5000:
                    break
                offset += 5000

        if len(df_ts) == 0:
            return {"accounts": [], "count": 0}

        if input.unique:
            addresses = pd.concat(
                df_ts)['from_address'].unique().tolist()  # type: ignore
        else:
            addresses = pd.concat(df_ts)['from_address'].to_list()
        return {"accounts": addresses, "count": len(addresses)}
