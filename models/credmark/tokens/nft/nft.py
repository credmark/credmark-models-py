# pylint: disable = line-too-long bare-except


import asyncio
import json
import os
import warnings
from datetime import datetime
from typing import Iterable
from urllib.parse import urljoin

import aiohttp
import ipfshttpclient
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelInputError
from credmark.cmf.types import Address, Contract, JoinType, Token
from credmark.dto import DTO, DTOField
from web3.exceptions import ABIFunctionNotFound, BadFunctionCallOutput, ContractLogicError

from models.tmp_abi_lookup import NFT_ABI

AZUKI_NFT = "0xED5AF388653567Af2F388E6224dC7C4b3241C544"
RTFKT_MNLTH_NFT = "0x86825dFCa7A6224cfBd2DA48e85DF2fc3Aa7C4B1"


# credmark-dev run nft.about -i '{"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544"}' -j --api_url http://localhost:8700


class NFTContract(Contract):
    class Config:
        schema_extra = {"examples": [{"address": AZUKI_NFT}]}


@Model.describe(
    slug="nft.about",
    version="0.2",
    display_name="NFT about",
    description="nft",
    input=NFTContract,
    output=dict,
)
class NFTAbout(Model):
    def run(self, input: NFTContract) -> dict:
        name = input.functions.name().call()
        symbol = input.functions.symbol().call()
        total_supply = input.functions.totalSupply().call()
        return {"name": name, "symbol": symbol, "total_supply": total_supply}


# credmark-dev run nft.mint -i '{"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544"}' -j --api_url http://localhost:8700 -b 17_000_000

# ERC-721: Plain Transfer
# - OpenSea
# - Blur: Blur Pool Token 0x0000000000A39bb272e79075ade125fd351887Ac

# Clonex: 0x49cF6f5d44E70224e2E23fDcdd2C053F30aDA28B
# Tx: 0x5d622c1e56ac5e7da7bb844ae7c7e4265d38ccd92f6b38efea3ab5ef050777b7

# ERC-1151: TransferSingle, find the ethereum amount in the Tx, or Find the Token Transfer of WETH with to as the sender in the same transaction.
# - Tx: 0xe6bd16b4ed7a5e2fa34adbd0ba38b6639e43142fd293614867ee9da01a2a653d
# -


@Model.describe(
    slug="nft.mint",
    version="0.4",
    display_name="NFT mint in ETH",
    description="nft",
    input=NFTContract,
    output=dict,
)
class NFTMint(Model):
    def get_mint_and_tx_with_join(self, contract):
        pg = 0
        dfs = []
        with contract.ledger.events.Transfer.as_("ts") as ts:
            with self.context.ledger.Transaction.as_("tx") as tx:
                while True:
                    df = ts.select(
                        aggregates=[
                            (tx.VALUE, "value"),
                            (ts.EVT_FROM, "evt_from"),
                            (ts.EVT_TO, "evt_to"),
                            (ts.EVT_TOKENID, "evt_tokenid"),
                            (ts.BLOCK_NUMBER, "block_number"),
                            (tx.BLOCK_TIMESTAMP.extract_epoch().as_integer(), "block_timestamp"),
                            (tx.FROM_ADDRESS, "from_address"),
                            (tx.TO_ADDRESS, "to_address"),
                            (tx.TRANSACTION_INDEX, "transaction_index"),
                            (ts.TXN_HASH, "hash"),
                        ],
                        where=ts.EVT_FROM.eq(Address.null()).and_(
                            tx.TO_ADDRESS.eq(contract.address)
                        ),
                        joins=[(JoinType.LEFT_OUTER, tx, tx.HASH.eq(ts.TXN_HASH))],
                        # When use limit/offset, the order_by must be unique
                        order_by=tx.BLOCK_NUMBER.comma_(tx.TRANSACTION_INDEX).comma_(
                            ts.EVT_TOKENID
                        ),
                        limit=5000,
                        offset=pg * 5000,
                    ).to_dataframe()

                    self.logger.info(f"get_mint_and_tx_with_join {pg=} {df.shape[0]=}")
                    if not df.empty:
                        dfs.append(df)
                    pg += 1
                    if df.shape[0] < 5000:
                        break

        if len(dfs) == 0:
            return None

        df_tx = pd.concat(dfs)
        return df_tx

    def run(self, input: NFTContract) -> dict:
        df_mint = self.get_mint_and_tx_with_join(input)
        if df_mint is None:
            return {"status": "no mint"}

        minted_ids = df_mint.evt_tokenid.unique()
        minted_ids_count = minted_ids.shape[0]

        self.logger.info(
            f'{minted_ids_count=} {set(range(0, minted_ids_count)) - set(df_mint.evt_tokenid.astype("int"))}'
        )

        df_mint["value"] = df_mint["value"].astype("float64") / 1e18
        df_mint["block_timestamp"] = df_mint["block_timestamp"].astype(int)
        # df_all['block_date'] = df_all['block_timestamp'].apply(datetime.fromtimestamp)

        df_mint = (
            df_mint.sort_values(["block_number", "transaction_index"])
            .reset_index(drop=True)
            .assign(
                block_timestamp_day=lambda df: df.block_timestamp.max()
                - ((df.block_timestamp.max() - df.block_timestamp) // (6 * 3600) * 6 * 3600)
            )
        )

        total_eth = df_mint.value.sum()
        _eth_price = self.context.models.price.quote(base="WETH", quote="USD")["price"]

        price_series = self.context.run_model(
            "price.dex-db-interval",
            {
                "address": Token("WETH").address,
                "start": df_mint.block_timestamp_day.min() - 3600 * 6,
                "end": df_mint.block_timestamp_day.max() + 3600 * 6,
                "interval": 3600,
            },
        )

        df_price_series = (
            pd.DataFrame(price_series["results"])
            .loc[:, ["sampleTimestamp", "price"]]
            .assign(sampleTimestamp=lambda df: df.sampleTimestamp.astype(int))
        )
        df_all = df_mint.merge(
            df_price_series, left_on="block_timestamp_day", right_on="sampleTimestamp", how="left"
        )
        df_all["cost"] = df_all.value * df_all.price

        df_all["cost_cumu"] = df_all["cost"].cumsum()
        df_all["qty_cumu"] = df_all["value"].cumsum()

        # df_all.plot('block_number', 'qty_cumu')
        # df_all.plot('block_number', 'cost_cumu')

        return {
            "total_eth": total_eth,
            "total_cost": df_all.cost.sum(),
            "minted_ids_count": minted_ids_count,
        }


class NFTGetInput(NFTContract):
    id: int

    class Config:
        schema_extra = {"examples": [{"address": AZUKI_NFT, "id": 1123}]}


# credmark-dev run nft.get -i '{"address": "0xED5AF388653567Af2F388E6224dC7C4b3241C544", "id": 9638}'


@Model.describe(
    slug="nft.get",
    version="0.4",
    display_name="NFT Get",
    description="nft",
    input=NFTGetInput,
    output=dict,
)
class NFTGet(Model):
    # disable due to outdated ifps library to Python 3.11
    ENABLE_IPFS = False

    def run(self, input: NFTGetInput) -> dict:
        owner = Address(input.functions.ownerOf(input.id).call()).checksum
        balance_of = input.functions.balanceOf(owner).call()
        if "tokenOfOwnerByIndex" in input.functions:
            ids = [input.functions.tokenOfOwnerByIndex(owner, i).call() for i in range(balance_of)]
        else:
            ids = None
        if "getOwnershipData" in input.functions:
            _, startTimestamp = input.functions.getOwnershipData(input.id).call()
        else:
            startTimestamp = None

        tokenURI = input.functions.tokenURI(input.id).call()
        key = os.environ.get("INFURA_IPFS_KEY")
        secret = os.environ.get("INFURA_IPFS_SECRET")

        if self.ENABLE_IPFS and key is not None and secret is not None:
            warnings.filterwarnings("ignore", category=ipfshttpclient.exceptions.VersionMismatch)
            with ipfshttpclient.connect(
                "/dns/ipfs.infura.io/tcp/5001/https", auth=(key, secret)
            ) as client:
                path = tokenURI.replace("ipfs://", "")
                nft_meta = json.loads(client.cat(path).decode())
                image_path = nft_meta["image"].replace("ipfs://", "")

                # image_data = client.cat(image_path)
                # nft_image = Image.open(BytesIO(image_data))
                # nft_image.show()
                # base64_encoded_image = base64.b64encode(image_data)
        else:
            image_path = None

        # TODO: current owner's price
        # past transaction price

        return {
            "owner": owner,
            "balance_of": balance_of,
            "ids": ids,
            "tokenURI": tokenURI,
            "image_path": image_path,
            "startTimestamp": startTimestamp,
            "startTime": datetime.fromtimestamp(startTimestamp).isoformat()
            if startTimestamp is not None
            else None,
            "current_owner_duration": self.context.block_number.timestamp - startTimestamp
            if startTimestamp is not None
            else None,
            "current_owner_duration_days": (self.context.block_number.timestamp - startTimestamp)
            / 86400
            if startTimestamp is not None
            else None,
        }


class NFTHolderInput(NFTContract):
    limit: int = DTOField(1000, gt=0, description="Limit the number of holders that are returned")
    offset: int = DTOField(
        0, ge=0, description="Omit a specified number of holders from beginning of result set"
    )
    start_from_one: bool = DTOField(False)
    include_attributes: bool = DTOField(False)


class NFTHolder(DTO):
    token_id: int
    address: Address | None
    token_attributes: dict | None


class NFTHoldersOutput(DTO):
    holders: list[NFTHolder]
    total_supply: int | None


@Model.describe(
    slug="nft.holders",
    version="0.1",
    display_name="NFT holders",
    description="nft",
    input=NFTHolderInput,
    output=NFTHoldersOutput,
)
class GetNFTHolders(Model):
    async def get_nft_attributes(self, session: aiohttp.ClientSession, url: str) -> dict | None:
        if not url:
            return None

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                json = await response.json()
                response.close()
            return json
        except Exception as e:
            print(e)
            print("Request failed.")
            return None

    async def get_attributes_bulk_async(self, urls: Iterable[str]):
        max_workers = 100
        tcp_connection = aiohttp.TCPConnector(
            limit=max_workers, force_close=True, enable_cleanup_closed=True
        )
        async with aiohttp.ClientSession(
            connector=tcp_connection
        ) as session, asyncio.TaskGroup() as tg:
            responses = [tg.create_task(self.get_nft_attributes(session, url)) for url in urls]
        responses = await asyncio.gather(*responses)
        # await asyncio.sleep(0.250)
        await tcp_connection.close()
        return responses

    def get_attributes_bulk(self, urls: Iterable[str]):
        return asyncio.run(self.get_attributes_bulk_async(urls))

    def get_owners(self, input: NFTContract, token_ids: Iterable[int]):
        return self.context.web3_batch.call(
            [input.functions.ownerOf(token_id) for token_id in token_ids], unwrap=True
        )

    def get_attributes(self, input: NFTContract, token_ids: Iterable[int]):
        try:
            baseURI = input.functions.baseURI().call()
            uris = [urljoin(baseURI, str(token_id)) for token_id in token_ids]
        except (BadFunctionCallOutput, ABIFunctionNotFound, ContractLogicError) as err:
            uris = self.context.web3_batch.call(
                [input.functions.tokenURI(token_id) for token_id in token_ids],
                unwrap=True,
            )
        return self.get_attributes_bulk(uris)

    def run(self, input: NFTHolderInput) -> NFTHoldersOutput:
        input.set_abi(abi=NFT_ABI, set_loaded=True)
        try:
            total_supply = input.functions.totalSupply().call()
        except:  # noqa: E722
            total_supply = None

        _local_offset = 1 if input.start_from_one else 0
        first = _local_offset + input.offset
        last = first + input.limit - 1

        if total_supply and last > total_supply - (0 if input.start_from_one else 1):
            last = total_supply - (0 if input.start_from_one else 1)

        if first >= last:
            raise ModelInputError(f"Invalid limit/offset. Total supply is {total_supply}.")

        token_ids = range(first, last + 1)

        owners = self.get_owners(input, token_ids)

        if input.include_attributes:
            attributes = self.get_attributes(input, token_ids)

        holders = [
            NFTHolder(
                address=Address(owner) if owner else None,
                token_id=first + idx,
                token_attributes=attributes[idx] if input.include_attributes else None,
            )
            for (idx, owner) in enumerate(owners)
        ]

        return NFTHoldersOutput(
            holders=holders,
            total_supply=total_supply,
        )
