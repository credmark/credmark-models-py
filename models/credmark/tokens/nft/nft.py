# pylint: disable = line-too-long
# ruff noqa: F401

import json
import os
import warnings
from datetime import datetime

import ipfshttpclient
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Token

AZUKI_NFT = '0xED5AF388653567Af2F388E6224dC7C4b3241C544'

# credmark-dev run nft.about -i '{"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544"}' -j --api_url http://localhost:8700


@Model.describe(slug='nft.about',
                version='0.1',
                display_name='NFT about',
                description="nft",
                input=Contract,
                output=dict)
class NFTAbout(Model):
    def run(self, input: Contract) -> dict:
        name = input.functions.name().call()
        symbol = input.functions.symbol().call()
        total_supply = input.functions.totalSupply().call()
        return {'name': name, 'symbol': symbol, 'total_supply': total_supply}

# credmark-dev run nft.mint -i '{"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544"}' -j --api_url http://localhost:8700


@Model.describe(slug='nft.mint',
                version='0.2',
                display_name='NFT mint in ETH',
                description="nft",
                input=Contract,
                output=dict)
class NFTMint(Model):
    def run(self, input: Contract) -> dict:
        pg = 0
        dfs = []
        with input.ledger.events.Transfer as ts:
            while True:
                df = ts.select([ts.CONTRACT_ADDRESS, ts.EVT_FROM, ts.EVT_TO, ts.BLOCK_NUMBER, ts.TXN_HASH],
                               order_by=ts.BLOCK_NUMBER,
                               where=ts.EVT_FROM.eq(Address.null()),
                               limit=5000,
                               offset=pg * 5000).to_dataframe()

                if not df.empty:
                    dfs.append(df)
                pg += 1
                if df.shape[0] < 5000 or pg > 10:
                    break

        if len(dfs) == 0:
            return {'status': 'no mint'}

        df_all = pd.concat(dfs)
        # df_all.groupby('transaction_hash').count().sort_values('block_number', ascending=False).index[0]

        pg = 0
        dfs = []
        with self.context.ledger.Transaction as tx:
            while True:
                df = tx.select([tx.FROM_ADDRESS, tx.HASH, tx.BLOCK_NUMBER, tx.TRANSACTION_INDEX, tx.VALUE],
                               aggregates=[(tx.BLOCK_TIMESTAMP.extract_epoch().as_bigint(), 'block_timestamp')],
                               order_by=tx.HASH,
                               # where=tx.HASH.in_(df_all.transaction_hash.unique().tolist()),
                               where=tx.TO_ADDRESS.eq(Address(AZUKI_NFT)).and_(tx.VALUE.gt(0)),
                               limit=5000,
                               offset=pg * 5000).to_dataframe()
                if not df.empty:
                    dfs.append(df)
                pg += 1
                if df.shape[0] < 5000 or pg > 10:
                    break

        df_all_tx = pd.concat(dfs)

        # set(df_all.transaction_hash) - set(df_all_tx.hash)

        df_all = df_all.merge(df_all_tx,
                              left_on=['transaction_hash', 'block_number'],
                              right_on=['hash', 'block_number'])

        df_all['value'] = df_all['value'].astype(float) / 1e18
        df_all['block_timestamp'] = df_all['block_timestamp'].astype(int)
        # df_all['block_date'] = df_all['block_timestamp'].apply(datetime.fromtimestamp)

        df_all = (df_all
                  .sort_values(['block_number', 'transaction_index'])
                  .reset_index(drop=True)
                  .assign(block_timestamp_day=lambda df:
                          df.block_timestamp.max() - ((df.block_timestamp.max() - df.block_timestamp) // (6 * 3600) * 6 * 3600)))

        _total_eth = df_all.value.sum()
        _eth_price = self.context.models.price.quote(base='WETH', quote='USD')['price']

        price_series = self.context.run_model('price.dex-db-interval',
                                              {'address': Token('WETH').address,
                                               "start": df_all.block_timestamp_day.min() - 3600 * 6,
                                               "end": df_all.block_timestamp_day.max() + 3600 * 6,
                                               "interval": 3600})

        df_price_series = (pd.DataFrame(price_series['results'])
                           .loc[:, ['sampleTimestamp', 'price']]
                           .assign(sampleTimestamp=lambda df: df.sampleTimestamp.astype(int)))
        df_all = df_all.merge(df_price_series, left_on='block_timestamp_day', right_on='sampleTimestamp', how='left')
        df_all['cost'] = df_all.value * df_all.price

        df_all['cost_cumu'] = df_all['cost'].cumsum()
        df_all['qty_cumu'] = df_all['value'].cumsum()

        # df_all.plot('block_number', 'qty_cumu')
        # df_all.plot('block_number', 'cost_cumu')

        return {
            'total_cost': df_all.cost.sum(),
        }


class NFTGetInput(Contract):
    id: int

# credmark-dev run nft.get -i '{"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544", "id": 9638}'


@Model.describe(slug='nft.get',
                version='0.1',
                display_name='NFT Get',
                description="nft",
                input=NFTGetInput,
                output=dict)
class NFTGet(Model):
    def run(self, input: NFTGetInput) -> dict:
        owner = Address(input.functions.ownerOf(input.id).call()).checksum
        balance_of = input.functions.balanceOf(owner).call()
        ids = [input.functions.tokenOfOwnerByIndex(owner, i).call() for i in range(balance_of)]
        tokenURI = input.functions.tokenURI(input.id).call()
        _, startTimestamp = input.functions.getOwnershipData(input.id).call()

        key = os.environ.get('INFURA_IPFS_KEY')
        secret = os.environ.get('INFURA_IPFS_SECRET')

        if key is not None and secret is not None:
            warnings.filterwarnings('ignore', category=ipfshttpclient.exceptions.VersionMismatch)
            with ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https', auth=(key, secret)) as client:
                path = tokenURI.replace('ipfs://', '')
                nft_meta = json.loads(client.cat(path).decode())
                image_path = nft_meta['image'].replace('ipfs://', '')

                # image_data = client.cat(image_path)
                # nft_image = Image.open(BytesIO(image_data))
                # nft_image.show()
                # base64_encoded_image = base64.b64encode(image_data)
        else:
            image_path = None

        return {
            'owner': owner,
            'balance_of': balance_of,
            'ids': ids,
            'tokenURI': tokenURI,
            'image_path': image_path,
            'startTimestamp': startTimestamp,
            'startTime': datetime.fromtimestamp(startTimestamp).isoformat(),
            'duration': self.context.block_number.timestamp - startTimestamp,
            'duration_days': (self.context.block_number.timestamp - startTimestamp) / 86400
        }
