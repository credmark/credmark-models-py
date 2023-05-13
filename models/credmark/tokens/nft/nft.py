# pylint: disable = line-too-long

import json
import os
import warnings
from datetime import datetime

import ipfshttpclient
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, JoinType, Token

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

# credmark-dev run nft.mint -i '{"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544"}' -j --api_url http://localhost:8700 -b 17_000_000


@Model.describe(slug='nft.mint',
                version='0.3',
                display_name='NFT mint in ETH',
                description="nft",
                input=Contract,
                output=dict)
class NFTMint(Model):
    def get_mint_and_tx_with_join(self, contract):
        pg = 0
        dfs = []
        with contract.ledger.events.Transfer.as_('ts') as ts:
            with self.context.ledger.Transaction.as_('tx') as tx:
                while True:
                    df = ts.select(
                        aggregates=[(tx.VALUE, 'value'),
                                    (ts.EVT_FROM, 'evt_from'),
                                    (ts.EVT_TO, 'evt_to'),
                                    (ts.EVT_TOKENID, 'evt_tokenid'),
                                    (ts.BLOCK_NUMBER, 'block_number'),
                                    (tx.BLOCK_TIMESTAMP.extract_epoch().as_integer(), 'block_timestamp'),
                                    (tx.FROM_ADDRESS, 'from_address'),
                                    (tx.TO_ADDRESS, 'to_address'),
                                    (tx.TRANSACTION_INDEX, 'transaction_index'),
                                    (ts.TXN_HASH, 'hash')],
                        where=ts.EVT_FROM.eq(Address.null()).and_(tx.TO_ADDRESS.eq(contract.address)),
                        joins=[(JoinType.LEFT_OUTER, tx, tx.HASH.eq(ts.TXN_HASH))],
                        # When use limit/offset, the order_by must be unique
                        order_by=tx.BLOCK_NUMBER.comma_(tx.TRANSACTION_INDEX).comma_(ts.EVT_TOKENID),
                        limit=5000,
                        offset=pg * 5000).to_dataframe()

                    self.logger.info(f'get_mint_and_tx_with_join {pg=} {df.shape[0]=}')
                    if not df.empty:
                        dfs.append(df)
                    pg += 1
                    if df.shape[0] < 5000:
                        break

        if len(dfs) == 0:
            return None

        df_tx = pd.concat(dfs)
        return df_tx

    def run(self, input: Contract) -> dict:
        df_mint = self.get_mint_and_tx_with_join(input)
        if df_mint is None:
            return {'status': 'no mint'}

        minted_ids = df_mint.evt_tokenid.unique()
        minted_ids_count = minted_ids.shape[0]

        self.logger.info(
            f'{minted_ids_count=} {set(range(0, minted_ids_count)) - set(df_mint.evt_tokenid.astype("int"))}')

        df_mint['value'] = df_mint['value'].astype("float64") / 1e18
        df_mint['block_timestamp'] = df_mint['block_timestamp'].astype(int)
        # df_all['block_date'] = df_all['block_timestamp'].apply(datetime.fromtimestamp)

        df_mint = (df_mint
                   .sort_values(['block_number', 'transaction_index'])
                   .reset_index(drop=True)
                   .assign(block_timestamp_day=lambda df:
                           df.block_timestamp.max() - ((df.block_timestamp.max() - df.block_timestamp) // (6 * 3600) * 6 * 3600)))

        total_eth = df_mint.value.sum()
        _eth_price = self.context.models.price.quote(base='WETH', quote='USD')['price']

        price_series = self.context.run_model('price.dex-db-interval',
                                              {'address': Token('WETH').address,
                                               "start": df_mint.block_timestamp_day.min() - 3600 * 6,
                                               "end": df_mint.block_timestamp_day.max() + 3600 * 6,
                                               "interval": 3600})

        df_price_series = (pd.DataFrame(price_series['results'])
                           .loc[:, ['sampleTimestamp', 'price']]
                           .assign(sampleTimestamp=lambda df: df.sampleTimestamp.astype(int)))
        df_all = df_mint.merge(df_price_series, left_on='block_timestamp_day', right_on='sampleTimestamp', how='left')
        df_all['cost'] = df_all.value * df_all.price

        df_all['cost_cumu'] = df_all['cost'].cumsum()
        df_all['qty_cumu'] = df_all['value'].cumsum()

        # df_all.plot('block_number', 'qty_cumu')
        # df_all.plot('block_number', 'cost_cumu')

        return {
            'total_eth': total_eth,
            'total_cost': df_all.cost.sum(),
            'minted_ids_count': minted_ids_count,
        }


class NFTGetInput(Contract):
    id: int

# credmark-dev run nft.get -i '{"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544", "id": 9638}'


@Model.describe(slug='nft.get',
                version='0.3',
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

        # TODO: current owner's price
        # past transaction price

        return {
            'owner': owner,
            'balance_of': balance_of,
            'ids': ids,
            'tokenURI': tokenURI,
            'image_path': image_path,
            'startTimestamp': startTimestamp,
            'startTime': datetime.fromtimestamp(startTimestamp).isoformat(),
            'current_owner_duration': self.context.block_number.timestamp - startTimestamp,
            'current_onwer_duration_days': (self.context.block_number.timestamp - startTimestamp) / 86400
        }