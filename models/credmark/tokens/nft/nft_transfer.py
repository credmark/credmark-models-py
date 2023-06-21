# pylint: disable=pointless-string-statement, line-too-long, unused-import

from typing import List, Tuple

import pandas as pd
from credmark.cmf.types import Address, Contract
from credmark.dto import DTO

from models.tmp_abi_lookup import BLUR_MARKET_PLACE_ABI

# 1. ERC-721
# 2. ERC-1151

# Blur
# OrdersMatched
# 0x0000000000A39bb272e79075ade125fd351887Ac Blur Pool token == WETH

"""
from models.tmp_abi_lookup import BLUR_MARKET_PLACE_ABI

cc = Contract('0x000000000000Ad05Ccc4F10045630fb830B95127').set_abi(BLUR_MARKET_PLACE_ABI, set_loaded=True)

df = pd.DataFrame(cc.fetch_events(cc.events.OrdersMatched, from_block=17511492,
                                  to_block=17511492, contract_address=cc.address))

df.loc[0].buy
"""

# OpenSea
# transfer (NFT) with OrderMatched (OpenSea, Project Wyvern Exchange)

"""
v1 sales

# OrdersMatched
# https://etherscan.io/address/0x7be8076f4ea4a4ad08075c2508e481d6c946d12b. The sales are recorded by an event called OrderMatch.
# https://etherscan.io/tx/0x7efdbef1c377126b5bb5381b8f46a5dd7cb4b992b5f2f48a5f47eec86297c281#eventlog

cc = Contract('0x7Be8076f4EA4A4AD08075C2508e481d6C946D12b')
df = pd.DataFrame(cc.fetch_events(cc.events.OrdersMatched, from_block=14029202, to_block=14029202, contract_address=cc.address))
df.loc[:, 'txHash'] = df.transactionHash.apply(lambda x: x.hex())
df.query('txHash == "0x7efdbef1c377126b5bb5381b8f46a5dd7cb4b992b5f2f48a5f47eec86297c281"').T

fee is 2.5% for OpenSea, 5% for secondary sales to the creator.

                                                                 26
args              (maker, taker, metadata, buyHash, sellHash, pr...
event                                                 OrdersMatched
logIndex                                                        350
transactionIndex                                                284
transactionHash   ...
address                  0x7Be8076f4EA4A4AD08075C2508e481d6C946D12b
blockHash         ...
blockNumber                                                14029202
maker                    0x8129D4010a676A660502a4770d8a97F8D1788e5f
taker                    0xeBEAa2cFDa253b0DF33A10eaf58a399d0d00a781
metadata          ...
buyHash           ...
sellHash          ...
price                                          10000000000000000000
txHash            0x7efdbef1c377126b5bb5381b8f46a5dd7cb4b992b5f2...

seaport (v2)
https://opensea.io/activity?search[chains][0]=ETHEREUM&search[eventTypes][0]=AUCTION_SUCCESSFUL

seaport = Contract('0x00000000000000ADc04C56Bf30aC9d3c0aAF14dC')
pd.DataFrame(seaport.fetch_events(seaport.events.OrderFulfilled, from_block=17512390, to_block=17512390))
pd.DataFrame(seaport.fetch_events(seaport.events.OrderFulfilled, from_block=17512390, to_block=17512390)).loc[0].address
pd.DataFrame(seaport.fetch_events(seaport.events.OrderFulfilled, from_block=17512390, to_block=17512390)).loc[0].offer
pd.DataFrame(seaport.fetch_events(seaport.events.OrderFulfilled, from_block=17512390, to_block=17512390)).loc[0].consideration
pd.DataFrame(seaport.fetch_events(seaport.events.OrderFulfilled, from_block=17512390, to_block=17512390)).loc[0].transactionHash

0x4d0bfdf25b4666b777fed889855c015d141d55de8e2977640e52e7ecbb0fc24b

enum ItemType {
  NATIVE,
  ERC20,
  ERC721,
  ERC1155,
  ERC721_WITH_CRITERIA,
  ERC1155_WITH_CRITERIA
}

enum Side {
  OFFER,
  CONSIDERATION
}

struct SpentItem {
  enum ItemType itemType;
  address token;
  uint256 identifier;
  uint256 amount;
}

[(2, '0x1A2A5Cdb346b8C5C83764C27266C5E52B35f93B6', 6890, 1)]

struct ReceivedItem {
  enum ItemType itemType;
  address token;
  uint256 identifier;
  uint256 amount;
  address payable recipient;
}

[(0,
  '0x0000000000000000000000000000000000000000',
  0,
  44750000000000000, // => previous owner
  '0x7c4b23fD000D6FeD7B3091c5b24c60922E733C51'),
 (0,
  '0x0000000000000000000000000000000000000000',
  0,
  1250000000000000, // => Creator Fee
  '0x0000a26b00c1F0DF003000390027140000fAa719'),
 (0,
  '0x0000000000000000000000000000000000000000',
  0,
  4000000000000000, // => Seaport Fee
  '0x8a3CAD5C23B5E7199592F7EB790245F9E07EDC6b')]


Example 2:

df = pd.DataFrame(seaport.fetch_events(seaport.events.OrderFulfilled, from_block=17502391, to_block=17502391)

df.loc[0].T

args                (offerer, zone, orderHash, recipient, offer, c...
event                                                  OrderFulfilled
logIndex                                                          105
transactionIndex                                                   70
transactionHash     ...
address                    0x00000000000000ADc04C56Bf30aC9d3c0aAF14dC
blockHash           ...
blockNumber                                                  17502391
*offerer*                  0xa21565e046873f939dcE98bd220C1C8e67a5AAB8
zone                       0x000000e7Ec00e7B300774b00001314B8610022b8
orderHash           ...
*recipient*                0x9034Fa7E735EfbCF5a3Bc81271BA72a3141Bb43b
offer               [(1, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc...
consideration       [(2, 0xc99c679C50033Bbc5321EB88752E89a93e9e83C...

df.transactionHash[0]
0xb519a46f3e702977c51a47258b6fdc0fd6edb78175b346934f1f527624796e49

df.offer[0]
[(1, '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 0, 1161100000000000000)]

df.consideration[0]
[(2,
  '0xc99c679C50033Bbc5321EB88752E89a93e9e83C5',
  1563,
  1,
  '0xa21565e046873f939dcE98bd220C1C8e67a5AAB8'),
 (1,
  '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
  0,
  29027500000000000, // => Fee
  '0x0000a26b00c1F0DF003000390027140000fAa719')]
"""

# Rarible
# SuperRare
# CryptoPunks
# Foundation

# Other swap
# NFT Trader 1:1
# https://www.nfttrader.io/faq
# https://etherscan.io/tx/0x755ab65d8180e12d79ff01b59b1ee1be858368086d0d28f5f5754a4099bb46c2


class BlurOrder(DTO):
    """
    enum Side { Buy, Sell }

    enum SignatureVersion { Single, Bulk }

    enum AssetType { ERC721, ERC1155 }

    struct Fee {
        uint16 rate; // divide by 10000 to get the rate, e.g. 50 for 0.005 = 0.5%
        address payable recipient;
    }

    struct Order {
        address trader; // order creator
        Side side; // direction of the order
        address matchingPolicy; // matching policy
        address collection; // ERC-721/1155 collection address
        uint256 tokenId; // tokenId
        uint256 amount;
        address paymentToken;
        uint256 price;
        uint256 listingTime;
        /* Order expiration timestamp - 0 for oracle cancellations. */
        uint256 expirationTime; // 0 for oracle cancellations
        Fee[] fees;
        uint256 salt;
        bytes extraParams; // if length > 0, and the first element is 1, it means oracle authorization
    }

    Example:
    https://etherscan.io/tx/0x6fb0a18b8e0ed8482a755c54f1e5c56654e15ebf901e588a3f40b3bbc181459c#eventlog

    Blur does not charge fee. All fee is royalty.

    # sell has tokenId
    ('0x4841Cb03Effcf02872596534e064F33ae99836E9',
    1,
    '0x0000000000b92D5d043FaF7CECf7E2EE6aaeD232',
    '0x49cF6f5d44E70224e2E23fDcdd2C053F30aDA28B',
    9228,
    1,
    '0x0000000000A39bb272e79075ade125fd351887Ac',
    2210000000000000000,
    1687047794,
    1687153382,
    [(50, '0xe65B6865DBCe299Ae6a20efcc7543362540741d8')],
    208289638015378432325367443839670845103,
    b'\x01')

    # buy
    ('0x63e0605491Bda6E4C1C37Cf818a45b836fAf46Ee',
    0,
    '0x0000000000b92D5d043FaF7CECf7E2EE6aaeD232',
    '0x49cF6f5d44E70224e2E23fDcdd2C053F30aDA28B',
    0,
    1,
    '0x0000000000A39bb272e79075ade125fd351887Ac',
    2210000000000000000,
    1687047793,
    1718583792,
    [],
    106987591149605657771124799103505215837,
    b'\x01')
    """

    trader: Address
    side: int  # 1 for sell, 0 for buy
    matchingPolicy: Address
    collection: Address
    tokenId: int
    amount: int
    paymentToken: Address
    price: int
    listingTime: int
    expirationTime: int
    fees: List[Tuple[int, Address]]
    salt: int
    extraParams: bytes

    @classmethod
    def from_tuple(cls, args):
        return cls(
            trader=args[0],
            side=args[1],
            matchingPolicy=args[2],
            collection=args[3],
            tokenId=args[4],
            amount=args[5],
            paymentToken=args[6],
            price=args[7],
            listingTime=args[8],
            expirationTime=args[9],
            fees=args[10],
            salt=args[11],
            extraParams=args[12],
        )
