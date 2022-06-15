from web3.exceptions import (
    BadFunctionCallOutput,
    ABIFunctionNotFound
)

from credmark.cmf.model.errors import (
    ModelDataError,
    ModelRunError
)

from credmark.cmf.model import Model
from credmark.cmf.types import (
    Address,
    ContractLedger,
    Contract,
    Contracts,
    Portfolio,
    Position,
    Price,
    Token,
    Tokens,
)

from models.dtos.price import PoolPriceInfo, PoolPriceInfos
from models.dtos.tvl import TVLInfo
from models.dtos.volume import (
    TradingVolume,
    TokenTradingVolume,
    VolumeInput,
    TradingVolumes,
)

from models.tmp_abi_lookup import (
    WETH9_ADDRESS,
    DAI_ADDRESS,
    USDC_ADDRESS,
    USDT_ADDRESS,
    UNISWAP_V2_POOL_ABI,
    UNISWAP_V3_POOL_ABI,
)

import pandas as pd


class UniswapV2PoolMeta:
    @staticmethod
    def get_uniswap_pools(model_input, factory_addr):
        factory = Contract(address=factory_addr)
        tokens = [Token(symbol='USDC'),
                  Token(symbol='USDT'),
                  Token(symbol='WETH'),
                  Token(symbol='DAI')]

        t2 = [Token(address=Address(USDC_ADDRESS)),
              Token(address=Address(USDT_ADDRESS)),
              Token(address=Address(WETH9_ADDRESS)),
              Token(address=Address(DAI_ADDRESS))]

        for a, b in zip(tokens, t2):
            assert a.address == b.address

        contracts = []
        try:
            for token in tokens:
                pair_address = factory.functions.getPair(model_input.address, token.address).call()
                if not pair_address == Address.null():
                    contracts.append(Contract(address=pair_address))
            return Contracts(contracts=contracts)
        except BadFunctionCallOutput:
            # Or use this condition: if self.context.block_number < 10000835 # Uniswap V2
            # Or use this condition: if self.context.block_number < 10794229 # SushiSwap
            return Contracts(contracts=[])


@Model.describe(slug='uniswap-v2.get-pools',
                version='1.1',
                display_name='Uniswap v2 Token Pools',
                description='The Uniswap v2 pools that support a token contract',
                input=Token,
                output=Contracts)
class UniswapV2GetPoolsForToken(Model, UniswapV2PoolMeta):
    # For mainnet, Ropsten, Rinkeby, Görli, and Kovan
    UNISWAP_V2_FACTORY_ADDRESS = {
        k: '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f' for k in [1, 3, 4, 5, 42]}

    def run(self, input: Token) -> Contracts:
        addr = self.UNISWAP_V2_FACTORY_ADDRESS[self.context.chain_id]
        return self.get_uniswap_pools(input, Address(addr).checksum)


class UniswapPoolPriceInfoMeta:
    @staticmethod
    def get_pool_price_infos(model, input, pools_address, pricer_slug) -> PoolPriceInfos:
        """
        Method to be shared between Uniswap V2 and SushiSwap
        """
        pools = []
        for p in pools_address:
            pool = Contract(address=p.address)
            try:
                pool.abi
            except ModelDataError:
                pool = Contract(address=p.address, abi=UNISWAP_V2_POOL_ABI)
            pools.append(pool)

        prices_with_info = []
        weth_price = None
        for pool in pools:
            reserves = pool.functions.getReserves().call()
            if reserves == [0, 0, 0]:
                continue

            token0 = Token(address=Address(pool.functions.token0().call()).checksum)
            token1 = Token(address=Address(pool.functions.token1().call()).checksum)
            scaled_reserve0 = token0.scaled(reserves[0])
            scaled_reserve1 = token1.scaled(reserves[1])

            if input.address == token0.address:
                inverse = False
                price = scaled_reserve1 / scaled_reserve0
                input_reserve = scaled_reserve0
            else:
                inverse = True
                price = scaled_reserve0 / scaled_reserve1
                input_reserve = scaled_reserve1

            weth_multiplier = 1
            if input.address != WETH9_ADDRESS:
                if WETH9_ADDRESS in (token1.address, token0.address):
                    if weth_price is None:
                        weth_price = model.context.run_model(pricer_slug,
                                                             {"address": WETH9_ADDRESS},
                                                             return_type=Price)
                        if weth_price.price is None:
                            raise ModelRunError('Can not retriev price for WETH')

                    weth_multiplier = weth_price.price

            price *= weth_multiplier

            pool_price_info = PoolPriceInfo(src=model.slug,
                                            price=price,
                                            liquidity=input_reserve,
                                            weth_multiplier=weth_multiplier,
                                            inverse=inverse,
                                            token0_address=token0.address,
                                            token1_address=token1.address,
                                            token0_symbol=token0.symbol,
                                            token1_symbol=token1.symbol,
                                            token0_decimals=token0.decimals,
                                            token1_decimals=token1.decimals,
                                            pool_address=pool.address)
            prices_with_info.append(pool_price_info)

        return PoolPriceInfos(pool_price_infos=prices_with_info)


@Model.describe(slug='uniswap-v2.get-pool-price-info',
                version='1.1',
                display_name='Uniswap v2 Token Pools Price ',
                description='Gather price and liquidity information from pools',
                input=Token,
                output=PoolPriceInfos)
class UniswapV2GetAveragePrice(Model, UniswapPoolPriceInfoMeta):
    def run(self, input: Token) -> PoolPriceInfos:
        pools_address = self.context.run_model('uniswap-v2.get-pools',
                                               input,
                                               return_type=Contracts)

        return self.get_pool_price_infos(self,
                                         input,
                                         pools_address,
                                         pricer_slug='uniswap-v2.get-weighted-price')


@Model.describe(slug="uniswap-v2.get-pool-info",
                version="1.2",
                display_name="Uniswap/Sushiswap get details for a pool",
                description="Returns the token details of the pool",
                input=Contract,
                output=dict)
class UniswapGetPoolInfo(Model):
    def run(self, input: Contract) -> dict:
        contract = input
        try:
            contract.abi
        except ModelDataError:
            contract = Contract(address=input.address, abi=UNISWAP_V2_POOL_ABI)

        token0 = Token(address=contract.functions.token0().call())
        token1 = Token(address=contract.functions.token1().call())
        # getReserves = contract.functions.getReserves().call()

        token0_balance = token0.scaled(token0.functions.balanceOf(input.address).call())
        token1_balance = token1.scaled(token1.functions.balanceOf(input.address).call())
        # token0_reserve = token0.scaled(getReserves[0])
        # token1_reserve = token1.scaled(getReserves[1])

        prices = []
        for tok in [token0, token1]:
            tok_price = self.context.run_model('chainlink.price-usd',
                                               input=tok,
                                               return_type=Price)
            prices.append(tok_price)

        output = {'pool_address': input.address,
                  'tokens': Tokens(tokens=[token0, token1]),
                  'tokens_name': [token0.name, token1.name],
                  'tokens_symbol': [token0.symbol, token1.symbol],
                  'tokens_decimals': [token0.decimals, token1.decimals],
                  'tokens_balance': [token0_balance, token1_balance],
                  'tokens_price': prices
                  }

        return output


@Model.describe(slug='uniswap-v2.pool-tvl',
                version='1.2',
                display_name='Uniswap/Sushiswap Token Pool TVL',
                description='Gather price and liquidity information from pools',
                input=Contract,
                output=TVLInfo)
class UniswapV2PoolTVL(Model):
    def run(self, input: Contract) -> TVLInfo:
        pool_info = self.context.run_model('uniswap-v2.get-pool-info', input=input)
        positions = []
        prices = []
        tvl = 0.0

        prices = []
        for token_info, tok_price, bal in zip(pool_info['tokens']['tokens'],
                                              pool_info['tokens_price'],
                                              pool_info['tokens_balance']):
            prices.append(Price(**tok_price))
            tvl += bal * tok_price['price']
            positions.append(Position(asset=Token(**token_info), amount=bal))

        try:
            pool_name = input.functions.name().call()
        except (ABIFunctionNotFound, ModelDataError):
            pool_name = 'Uniswap V3'

        tvl_info = TVLInfo(
            address=input.address,
            name=pool_name,
            portfolio=Portfolio(positions=positions),
            tokens_symbol=pool_info['tokens_symbol'],
            prices=prices,
            tvl=tvl
        )

        return tvl_info


@Model.describe(slug='dex.pool-volume',
                version='1.5',
                display_name='Uniswap/Sushiswap/Curve Pool Swap Volumes',
                description='The volume of each token swapped in a pool in a window',
                input=VolumeInput,
                output=TradingVolumes)
class UniswapV2PoolSwapVolume(Model):
    def run(self, input: VolumeInput) -> TradingVolumes:
        # pylint:disable=locally-disabled,protected-access,line-too-long
        pool = Contract(address=input.address)

        try:
            pool.abi
        except ModelDataError:
            if input.pool_info_model == 'uniswap-v2.pool-tvl':
                pool.set_abi(UNISWAP_V3_POOL_ABI)
            else:
                raise

        if pool.abi is None:
            raise ModelRunError('Input contract\'s ABI is empty')

        pool_info = self.context.run_model(input.pool_info_model, input=input)
        tokens_n = len(pool_info['portfolio']['positions'])

        tokens = [Token(**token_info['asset'])
                  for token_info in pool_info['portfolio']['positions']]

        # initialize empty TradingVolume
        pool_volume_history = TradingVolumes(
            tradingVolumes=[
                TradingVolume(
                    tokenVolumes=[TokenTradingVolume.default(token=tok) for tok in tokens])
                for _ in range(input.count)])

        if input.pool_info_model == 'uniswap-v2.pool-tvl':
            event_swap_args = sorted(
                [c.lower() for c in pool.abi.events.Swap.args if c.lower().startswith('amount')])  # type: ignore
            df_all_swaps = (pool.ledger.events.Swap(
                columns=[],
                aggregates=(
                    [self.context.ledger.Aggregate(
                        f'sum((sign({ContractLedger.Events.InputCol(field)})+1) / 2 * {ContractLedger.Events.InputCol(field)})',
                        f'sum_pos_{ContractLedger.Events.InputCol(field)}')
                     for field in event_swap_args] +
                    [self.context.ledger.Aggregate(
                        f'sum((sign({ContractLedger.Events.InputCol(field)})-1) / 2 * {ContractLedger.Events.InputCol(field)})',
                        f'sum_neg_{ContractLedger.Events.InputCol(field)}')
                     for field in event_swap_args] +
                    [self.context.ledger.Aggregate(
                        f'floor(({self.context.block_number} - {ContractLedger.Events.Columns.EVT_BLOCK_NUMBER}) / {input.interval}, 0)',
                        'interval_n')] +
                    [self.context.ledger.Aggregate(
                        f'{func}({ContractLedger.Events.Columns.EVT_BLOCK_NUMBER})', f'{func}_block_number')
                     for func in ['min', 'max', 'count']]),
                where=(f'{ContractLedger.Events.Columns.EVT_BLOCK_NUMBER} > {self.context.block_number - input.interval * input.count} AND '
                       f'{ContractLedger.Events.Columns.EVT_BLOCK_NUMBER} <= {self.context.block_number}'),
                group_by=f'floor(({self.context.block_number} - {ContractLedger.Events.Columns.EVT_BLOCK_NUMBER}) / {input.interval}, 0)')
                .to_dataframe())

            if len(df_all_swaps) == 0:
                return pool_volume_history

            df_all_swaps.loc[:, 'start_block_number'] = (
                int(self.context.block_number) - (df_all_swaps.interval_n + 1) * input.interval)
            df_all_swaps.loc[:, 'end_block_number'] = (
                int(self.context.block_number) - (df_all_swaps.interval_n) * input.interval)

            if event_swap_args == sorted(['amount0in', 'amount1in', 'amount0out', 'amount1out']):
                df_all_swaps = (df_all_swaps.drop(columns=(
                    [f'sum_neg_inp_amount{n}in' for n in range(tokens_n)] +
                    [f'sum_neg_inp_amount{n}out' for n in range(tokens_n)]))
                    .rename(columns=(
                        {f'sum_pos_inp_amount{n}in': f'inp_amount{n}_in' for n in range(tokens_n)} |
                        {f'sum_pos_inp_amount{n}out': f'inp_amount{n}_out' for n in range(tokens_n)}))
                    .sort_values('min_block_number')
                    .reset_index(drop=True))
            else:
                df_all_swaps = (df_all_swaps.rename(columns=(
                    {f'sum_pos_inp_amount{n}': f'inp_amount{n}_in' for n in range(tokens_n)} |
                    {f'sum_neg_inp_amount{n}': f'inp_amount{n}_out' for n in range(tokens_n)}))
                    .sort_values('min_block_number')
                    .reset_index(drop=True))

            for n in range(tokens_n):
                for col in [f'inp_amount{n}_in', f'inp_amount{n}_out']:
                    df_all_swaps.loc[:, col] = df_all_swaps.loc[:, col].astype(float)  # type: ignore

        elif input.pool_info_model == 'curve-fi.pool-tvl':
            event_tokenexchange_args = [s.upper() for s in pool.abi.events.TokenExchange.args]
            assert sorted(event_tokenexchange_args) == sorted(
                ['BUYER', 'SOLD_ID', 'TOKENS_SOLD', 'BOUGHT_ID', 'TOKENS_BOUGHT'])

            df_all_swaps = (pool.ledger.events.TokenExchange(
                columns=[ContractLedger.Events.InputCol("SOLD_ID"), ContractLedger.Events.InputCol("BOUGHT_ID")],
                aggregates=(
                    [self.context.ledger.Aggregate(
                        f'sum({ContractLedger.Events.InputCol(field)})',
                        f'{ContractLedger.Events.InputCol(field)}')
                        for field in ['TOKENS_SOLD', 'TOKENS_BOUGHT']] +
                    [self.context.ledger.Aggregate(
                        f'floor(({self.context.block_number} - {ContractLedger.Events.Columns.EVT_BLOCK_NUMBER}) / {input.interval}, 0)',
                        'interval_n')] +
                    [self.context.ledger.Aggregate(
                        f'{func}({ContractLedger.Events.Columns.EVT_BLOCK_NUMBER})', f'{func}_block_number')
                        for func in ['min', 'max', 'count']]),
                where=(f'{ContractLedger.Events.Columns.EVT_BLOCK_NUMBER} > {self.context.block_number - input.interval * input.count} AND '
                       f'{ContractLedger.Events.Columns.EVT_BLOCK_NUMBER} <= {self.context.block_number}'),
                group_by=(f'floor(({self.context.block_number} - {ContractLedger.Events.Columns.EVT_BLOCK_NUMBER}) / {input.interval}, 0)' +
                          f',{ContractLedger.Events.InputCol("SOLD_ID")},{ContractLedger.Events.InputCol("BOUGHT_ID")}'))
                .to_dataframe())

            if len(df_all_swaps) == 0:
                return pool_volume_history

            for col in ['inp_tokens_bought', 'inp_tokens_sold']:
                df_all_swaps.loc[:, col] = df_all_swaps.loc[:, col].astype(float)  # type: ignore

            for n in range(tokens_n):
                # In: Sold to the pool
                # Out: Bought from the pool
                df_all_swaps.loc[:, f'inp_amount{n}_in'] = df_all_swaps.loc[:, 'inp_tokens_sold']       # type: ignore
                df_all_swaps.loc[:, f'inp_amount{n}_out'] = df_all_swaps.loc[:, 'inp_tokens_bought']    # type: ignore
                df_all_swaps.loc[df_all_swaps.inp_sold_id != n, f'inp_amount{n}_in'] = 0                # type: ignore
                df_all_swaps.loc[df_all_swaps.inp_bought_id != n, f'inp_amount{n}_out'] = 0             # type: ignore

            df_all_swaps = (df_all_swaps
                            .groupby(['interval_n'], as_index=False)
                            .agg({'min_block_number': ['min'],
                                  'max_block_number': ['max'],
                                  'count_block_number': ['sum']} |
                                 {f'inp_amount{n}_in': ['sum'] for n in range(tokens_n)} |
                                 {f'inp_amount{n}_out': ['sum'] for n in range(tokens_n)})
                            .sort_values('interval_n')
                            .reset_index(drop=True))

            df_all_swaps.columns = pd.Index([a for a, _ in df_all_swaps.columns])
            df_all_swaps.loc[:, 'start_block_number'] = (
                int(self.context.block_number) - (df_all_swaps.interval_n + 1) * input.interval)
            df_all_swaps.loc[:, 'end_block_number'] = (
                int(self.context.block_number) - (df_all_swaps.interval_n) * input.interval)
        else:
            raise ModelRunError(f'Unknown pool info model {input.pool_info_model=}')

        # TODO: get price for each block when composer model is ready
        # all_blocks = df_all_swaps.loc[:, ['evt_block_number']]  # type: ignore
        # for n in range(tokens_n):
        #     for n_row, row in all_blocks[::-1].iterrows():
        #         all_blocks.loc[n_row, f'token{n}_price'] = self.context.run_model(
        #             'chainlink.price-usd',
        #             input=tokens[n], block_number=row.evt_block_number, return_type=Price).price

        # df_all_swaps = df_all_swaps.merge(all_blocks, on=['evt_block_number'], how='left')

        # Use current block's price, instead.
        for cc in range(input.count):
            block_number = df_all_swaps.loc[cc, 'max_block_number']
            pool_info_past = self.context.run_model(input.pool_info_model, input=input, block_number=block_number)
            for n in range(tokens_n):
                token_out = df_all_swaps.loc[cc, f'inp_amount{n}_out']
                token_in = df_all_swaps.loc[cc, f'inp_amount{n}_in']
                token_price = pool_info_past['prices'][n]['price']  # type: ignore

                if tokens[n].address != '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee':
                    def scale_func(bal, n_tok):  # type: ignore
                        return tokens[n_tok].scaled(bal)
                else:
                    def scale_func(bal, _):
                        return float(self.context.web3.fromWei(bal, 'ether'))

                pool_volume_history.tradingVolumes[cc].tokenVolumes[n].sellAmount = scale_func(token_out, n)
                pool_volume_history.tradingVolumes[cc].tokenVolumes[n].buyAmount = scale_func(token_in, n)

                pool_volume_history.tradingVolumes[cc].tokenVolumes[n].sellValue = scale_func(
                    token_out * token_price, n)
                pool_volume_history.tradingVolumes[cc].tokenVolumes[n].buyValue = scale_func(token_in * token_price, n)

            return pool_volume_history
