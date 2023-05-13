# pylint: disable = line-too-long

import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import Address, Contract


@Model.describe(slug='contrib.nft=tx',
                version='0.2',
                display_name='NFT mint in ETH',
                description="nft",
                input=Contract,
                output=dict)
class NFTTx(Model):
    """
    An experiment model for fetching NFT mint and related tx.
    Inconsistency in value between the runs
    """
    def get_mint(self, contract):
            pg = 0
            dfs = []
            with contract.ledger.events.Transfer as ts:
                while True:
                    df = ts.select([ts.CONTRACT_ADDRESS, ts.EVT_FROM, ts.EVT_TO, ts.BLOCK_NUMBER, ts.TXN_HASH],
                                order_by=ts.BLOCK_NUMBER,
                                where=ts.EVT_FROM.eq(Address.null()),
                                limit=5000,
                                offset=pg * 5000).to_dataframe()

                    if not df.empty:
                        dfs.append(df)
                    pg += 1
                    self.logger.info(f'get_mint {pg=} {df.shape[0]=}')
                    if df.shape[0] < 5000:
                        break

            if len(dfs) == 0:
                return None

            df_mint = pd.concat(dfs)
            # df_all.groupby('transaction_hash').count().sort_values('block_number', ascending=False).index[0]

            return df_mint

        def get_mint_tx(self, contract):
            pg = 0
            dfs = []
            with self.context.ledger.Transaction as tx:
                while True:
                    df = tx.select([tx.FROM_ADDRESS, tx.HASH, tx.BLOCK_NUMBER, tx.TRANSACTION_INDEX, tx.VALUE],
                                aggregates=[(tx.BLOCK_TIMESTAMP.extract_epoch().as_bigint(), 'block_timestamp')],
                                order_by=tx.HASH,
                                # where=tx.HASH.in_(df_all.transaction_hash.unique().tolist()),
                                where=tx.TO_ADDRESS.eq(contract.address).and_(tx.VALUE.gt(0)),
                                limit=5000,
                                offset=pg * 5000).to_dataframe()
                    self.logger.info(f'get_mint_tx {pg=} {df.shape[0]=}')
                    if not df.empty:
                        dfs.append(df)
                    pg += 1
                    if df.shape[0] < 5000:
                        break

            if len(dfs) == 0:
                return None

            df_tx = pd.concat(dfs)
            return df_tx

            # set(df_all.transaction_hash) - set(df_all_tx.hash)

        def get_mint_and_tx(self, contract):
            df_mint = self.get_mint(contract)
            if df_mint is None:
                return None

            df_tx = self.get_mint_tx(contract)
            if df_tx is None:
                raise ModelRunError('no tx')

            self.logger.info(f'{sum(df_tx.value.astype(int).to_list())} {df_tx.shape}')
            df_tx['value'] = df_tx['value'].astype(float) / 1e18

            self.logger.info(f'{sum(df_tx.value.to_list())} {df_tx.shape}')
            df_mint_merged = df_mint.merge(df_tx,
                                        left_on=['transaction_hash', 'block_number'],
                                        right_on=['hash', 'block_number'],
                                        how='inner')

            self.logger.info(f'{sum(df_mint_merged.value.to_list())} {df_mint_merged.shape}')
            return df_mint_merged

    def run(self, input: Contract) -> dict:
        df_mint = self.get_mint_and_tx(input)
        if df_mint is None:
            return {'status': 'no mint'}

        self.logger.info(f'{sum(df_mint.value.to_list())} {df_mint.shape}')

        return {
             'total_eth': df_mint.value.sum(),
        }
