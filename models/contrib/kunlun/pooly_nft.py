# pylint: disable = line-too-long

import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.types import Contract, Records, Token
from credmark.dto import DTO, DTOField, EmptyInput


class PoolyNFT:
    POOLY_SUPPORT = '0x90B3832e2F2aDe2FE382a911805B6933C056D6ed'
    POOLY_LAWYER = '0x3545192b340F50d77403DC0A64cf2b32F03d00A9'
    POOLY_JUDGE = '0x5663e3E096f1743e77B8F71b5DE0CF9Dfd058523'

# Dune Analytics tutorial
# https://mirror.xyz/phillan.eth/17VAXsMPpwJg4OQNBHKTYAQTWfJMwFuXZQDAxPStf0o

# Query 1: Funds Raised in ETH
# https://dune.com/queries/882266


@Model.describe(slug='contrib.pooly-fund-raise',
                version='0.1',
                display_name='Pooly NFT fund raise',
                description="nft",
                input=EmptyInput,
                output=dict)
class PoolyNFTFundRaise(Model, PoolyNFT):
    """
    select SUM("value"/1e18) from ethereum.transactions
    where "to" = '\x90B3832e2F2aDe2FE382a911805B6933C056D6ed'
    or "to" = '\x3545192b340F50d77403DC0A64cf2b32F03d00A9'
    or "to" = '\x5663e3E096f1743e77B8F71b5DE0CF9Dfd058523'

    Run with:
    credmark-dev run contrib.pooly-fund-raise -j

    Reference:
    https://dune.com/queries/882266
    """

    @staticmethod
    def fetch_balance(nft):
        contract = Contract(nft)
        name = contract.functions.name().call()
        return nft, name

    def run(self, _: EmptyInput) -> dict:
        with self.context.ledger.Transaction as q:
            df_group_by = (
                q.select(
                    aggregates=[(q.VALUE.sum_(),
                                 'sum_value')],
                    where=q.TO_ADDRESS.in_([self.POOLY_JUDGE,
                                            self.POOLY_LAWYER,
                                            self.POOLY_SUPPORT]),
                    group_by=[q.TO_ADDRESS])
                .to_dataframe())

        all_nfts = [self.POOLY_JUDGE, self.POOLY_LAWYER, self.POOLY_SUPPORT]
        nft_list = [self.fetch_balance(nft) for nft in all_nfts]
        nft_dict = {name: nft for nft, name in nft_list}

        if df_group_by.empty:
            self.logger.info('No funds raised')
            return {'total_raised_qty': 0}

        df_group_by = df_group_by.assign(sum_value=lambda x: x.sum_value.apply(int) / 1e18)

        total_raised_qty_from_sum = df_group_by.sum_value.sum()
        self.logger.info(f'total raised: {total_raised_qty_from_sum}')
        per_nft = df_group_by.set_index('to_address').to_dict()['sum_value']
        return {'total_raised_qty': total_raised_qty_from_sum, **per_nft, **nft_dict}

# Query 2: Funds raised in USD


@Model.describe(slug='contrib.pooly-fund-raise-usd-and-count',
                version='0.1',
                display_name='Pooly NFT fund raise in USD',
                description="nft",
                input=EmptyInput,
                output=dict)
class PoolyNFTFundRaiseUSD(Model, PoolyNFT):
    """
    Run with
    credmark-dev run contrib.pooly-fund-raise-usd-and-count -j

    Reference
    https://dune.com/queries/883725 # contribution value as of current price
    https://dune.com/queries/884492 # contribution value as of price at the point of transfer
    https://dune.com/queries/887079 # count unique
    """

    def run(self, _: EmptyInput) -> dict:
        pg = 0
        dfs = []
        with self.context.ledger.Transaction as q:
            while True:
                df = (
                    q.select(
                        [q.BLOCK_NUMBER,
                         q.TRANSACTION_INDEX,
                         q.FROM_ADDRESS,
                         q.TO_ADDRESS,
                         q.VALUE],
                        aggregates=[(q.BLOCK_TIMESTAMP.extract_epoch().as_bigint(),
                                     'block_timestamp')],
                        where=q.TO_ADDRESS.in_([self.POOLY_JUDGE,
                                                self.POOLY_LAWYER,
                                                self.POOLY_SUPPORT]),
                        offset=pg * 5000,
                        bigint_cols=['block_timestamp'])
                    .to_dataframe())
                if not df.empty:
                    dfs.append(df)
                pg += 1
                if df.shape[0] < 5000:
                    break

        if len(dfs) == 0:
            return {'total_raise_value': 0, 'total_raise_value_latest': 0, 'total_raised_qty': 0}

        df_all = (
            pd
            .concat(dfs)
            .assign(block_timestamp_day=lambda df:
                    df.block_timestamp.max() - ((df.block_timestamp.max() - df.block_timestamp) // (24 * 3600) * 24 * 3600)))

        eth_price = self.context.models.price.quote(base='WETH', quote='USD')['price']

        self.logger.info(f'Fetched {df_all.shape[0]} rows of transactions to Pooly NFT')

        total_raised_qty = df_all.value.apply(int).sum() / 1e18
        total_raised_value_latest = total_raised_qty * eth_price

        price_series = self.context.run_model('price.dex-db-interval',
                                              {'address': Token('WETH').address,
                                               "start": df_all.block_timestamp_day.min() - 86400,
                                               "end": df_all.block_timestamp_day.max() + 86400,
                                               "interval": 86400})

        df_price_series = (pd.DataFrame(price_series['results'])
                           .loc[:, ['sampleTimestamp', 'price']]
                           .assign(sampleTimestamp=lambda df: df.sampleTimestamp.astype(int)))
        df_all = df_all.merge(df_price_series, left_on='block_timestamp_day', right_on='sampleTimestamp', how='left')
        total_raised_value = (df_all.value / 1e18 * df_all.price).sum()

        return {'total_supporters': df_all.from_address.nunique(),
                'total_raise_value': total_raised_value,
                'total_raise_value_latest': total_raised_value_latest,
                'total_raised_qty': total_raised_qty, }


class LeaderInput(DTO):
    top_n: int = DTOField(10, description='Top N leaders to return')


@Model.describe(slug='contrib.pooly-fund-raise-leaderboard',
                version='0.1',
                display_name='Pooly NFT fund raise - leaders',
                description="nft",
                input=LeaderInput,
                output=Records)
class PoolyNFTFundRaiseLeaders(Model, PoolyNFT):
    """
    Run with
    credmark-dev run contrib.pooly-fund-raise-leader -j

    Reference
    https://dune.com/queries/887141
    """

    @staticmethod
    def fetch_mint(nft):
        contract = Contract(nft)
        pg = 0
        dfs = []
        with contract.ledger.events.NFTMinted as q:
            while True:
                df = q.select([q.EVT_TO, q.EVT_NUMBEROFTOKENS, q.EVT_AMOUNT],
                              order_by=q.BLOCK_NUMBER,
                              limit=5000,
                              offset=pg*5000).to_dataframe()
                dfs.append(df)
                pg += 1
                if df.shape[0] < 5000:
                    break

        return pd.concat(dfs)

    def run(self, input: LeaderInput) -> Records:
        all_nfts = [self.POOLY_JUDGE, self.POOLY_LAWYER, self.POOLY_SUPPORT]
        all_mints = pd.concat([self.fetch_mint(nft) for nft in all_nfts]).assign(
            evt_amount=lambda x: x.evt_amount.apply(int))

        if all_mints.empty:
            return Records.empty()

        all_mints_summary = (
            all_mints
            .assign(evt_amount=lambda x: x.evt_amount.apply(int) / 1e18)
            .groupby('evt_to').agg({'evt_numberOfTokens': 'sum', 'evt_amount': 'sum'})
            .sort_values(['evt_amount', 'evt_numberOfTokens'], ascending=False)
            .reset_index(drop=False)
            .loc[:input.top_n, :])

        return Records.from_dataframe(all_mints_summary)

# Query 5: Max Supply and Remaining Supply of Each of the NFT sets


@Model.describe(slug='contrib.pooly-total-supply',
                version='0.1',
                display_name='Pooly NFT total supply and minted',
                description="nft",
                input=EmptyInput,
                output=Records)
class PoolyNFTSupply(Model, PoolyNFT):
    """
    Run with:
    credmark-dev run contrib.pooly-total-supply -j -b 15_000_000
    credmark-dev run contrib.pooly-total-supply -j

    Reference
    https://dune.com/queries/887355
    """

    @staticmethod
    def fetch_supply_and_minted(nft):
        contract = Contract(nft)
        supply = contract.functions.totalSupply().call()
        max_nft = contract.functions.maxNFT().call()
        name = contract.functions.name().call()
        return supply, max_nft, name

    def run(self, _: EmptyInput) -> Records:
        rows = []
        for nft in [self.POOLY_JUDGE, self.POOLY_LAWYER, self.POOLY_SUPPORT]:
            supply, max_nft, name = self.fetch_supply_and_minted(nft)
            self.logger.info(f'{name} supply: {supply}, max_nft: {max_nft}')
            rows.append({'nft': nft, 'name': name, 'supply': supply, 'max_nft': max_nft})

        return Records.from_dataframe(pd.DataFrame(rows))


# Query 6: Time series Chart of ETH Raised Over Time


@Model.describe(slug='contrib.pooly-fund-raise-timeseries',
                version='0.1',
                display_name='Pooly NFT fund raise in series',
                description="nft",
                input=EmptyInput,
                output=Records)
class PoolyNFTFundRaiseSeries(Model, PoolyNFT):
    """
    Run with:
    credmark-dev run contrib.pooly-fund-raise-series -j

    Reference:
    https://dune.com/queries/887727
    """

    def run(self, _: EmptyInput) -> Records:
        pg = 0
        dfs = []
        with self.context.ledger.Transaction as q:
            while True:
                df = (
                    q.select(
                        aggregates=[(q.BLOCK_TIMESTAMP.extract_epoch(), 'block_time'),
                                    ("sum(value/1e18) over (order by date_trunc('minute', block_timestamp) asc)",
                                    'cumu_value_eth')],
                        where=q.TO_ADDRESS.in_([self.POOLY_JUDGE,
                                                self.POOLY_LAWYER,
                                                self.POOLY_SUPPORT]),
                        order_by=q.BLOCK_TIMESTAMP.asc(),
                        limit=5000, offset=pg * 5000)
                    .to_dataframe())
                if not df.empty:
                    dfs.append(df)
                pg += 1
                if df.shape[0] < 5000:
                    break

        if len(dfs) == 0:
            return Records.empty()

        df_all = pd.concat(dfs).reset_index(drop=True)

        df_all = df_all.assign(block_time=lambda x: x.block_time.apply(lambda x: int(float(x))),
                               cumu_value_eth=lambda x: x.cumu_value_eth.apply(float))

        return Records.from_dataframe(df_all)
