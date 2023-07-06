# pylint: disable= line-too-long, too-many-lines, no-name-in-module

import json
import math
from collections import defaultdict
from datetime import datetime
from typing import DefaultDict, List

import numpy as np
import numpy_financial as npf
import pandas as pd
from credmark.cmf.model import CachePolicy, ImmutableModel, ImmutableOutput, IncrementalModel, Model
from credmark.cmf.model.errors import (
    ModelDataError,
    ModelEngineError,
    ModelRunError,
    create_instance_from_error_dict,
)
from credmark.cmf.types import Address, BlockNumber, Contract, Network, Records, Token
from credmark.cmf.types.compose import MapInputsOutput
from credmark.cmf.types.series import BlockSeries, BlockSeriesRow
from credmark.dto import DTO, DTOField, EmptyInput
from pyxirr import InvalidPaymentsError, xirr
from requests.exceptions import HTTPError

from models.credmark.chain.contract import ContractEventsInput, ContractEventsOutput
from models.credmark.protocols.dexes.uniswap.univ3_math import tick_to_price
from models.tmp_abi_lookup import ICHI_VAULT, ICHI_VAULT_DEPOSIT_GUARD, ICHI_VAULT_FACTORY, UNISWAP_V3_POOL_ABI

# ICHI Vault
# https://app.ichi.org/vault?token={}',


class EmptyInputWithNetwork(EmptyInput):
    class Config:
        schema_extra = {
            'examples': [{'_test_multi': {'chain_id': 137, 'block_number': None}}],
            'test_multi': True
        }


@Model.describe(slug='ichi.vault-tokens',
                version='0.1',
                display_name='',
                description='The tokens used in ICHI vaults',
                category='protocol',
                input=EmptyInputWithNetwork,
                subcategory='ichi',
                output=dict)
class IchiVaultTokens(Model):
    ICHI_POLYGON_COINS = [
        '0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270',
        '0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39',
        '0x43Df9c0a1156c96cEa98737b511ac89D0e2A1F46',
        '0x9a71012B13CA4d3D0Cdc72A177DF3ef03b0E76A3',
        '0x385Eeac5cB85A38A9a07A70c73e0a3271CfB54A7',
        '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
        '0x172370d5Cd63279eFa6d502DAB29171933a610AF',
        '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
        '0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a',
        '0x1f194578e7510A350fb517a9ce63C40Fa1899427',
        '0x111111517e4929D3dcbdfa7CCe55d30d4B6BC4d6',
        '0x85955046DF4668e1DD369D2DE9f3AEB98DD2A369',
        '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',
        '0x692AC1e363ae34b6B489148152b12e2785a3d8d6',
    ]

    def run(self, _) -> dict:
        result = {}
        for token_addr in self.ICHI_POLYGON_COINS:
            tok = Token(token_addr).as_erc20(set_loaded=True)
            result[Address(token_addr).checksum] = (
                tok.symbol, tok.name, tok.decimals)
        return result


class IchiVault(DTO):
    vault: str
    owner: str
    pool: str
    token0_symbol: str
    token1_symbol: str
    allow_token0: bool
    allow_token1: bool
    total_supply_scaled: float


@IncrementalModel.describe(slug='ichi.vaults-block-series',
                           version='0.1',
                           display_name='ICHI vaults block series',
                           description='ICHI vaults block series',
                           category='protocol',
                           input=EmptyInputWithNetwork,
                           subcategory='ichi',
                           output=BlockSeries[List[IchiVault]])
class IchiVaultsBlock(IncrementalModel):
    ICHI_VAULT_FACTORY = '0x2d2c72C4dC71AA32D64e5142e336741131A73fc0'

    def run(self, _, from_block: BlockNumber) -> BlockSeries[List[IchiVault]]:
        vault_factory = Contract(self.ICHI_VAULT_FACTORY).set_abi(
            ICHI_VAULT_FACTORY, set_loaded=True)

        try:
            vault_created_events = list(vault_factory.fetch_events(
                vault_factory.events.ICHIVaultCreated,
                from_block=int(from_block)))
        except HTTPError:
            deployed_info = self.context.run_model('token.deployment', {
                "address": self.ICHI_VAULT_FACTORY, "ignore_proxy": True})
            self.logger.info('Use by_range=10_000')
            deployed_block_number = deployed_info['deployed_block_number']
            # 25_697_834 for vault_factory
            vault_created_events = list(vault_factory.fetch_events(
                vault_factory.events.ICHIVaultCreated,
                from_block=max(from_block, deployed_block_number),
                by_range=10_000))

        outputs_by_block: DefaultDict[int, List[IchiVault]] = defaultdict(list)
        for event in vault_created_events:
            vault_addr = event['ichiVault']
            block_number = int(event['blockNumber'])

            vault = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
            token0 = Token(vault.functions.token0().call()).as_erc20(set_loaded=True)
            token1 = Token(vault.functions.token1().call()).as_erc20(set_loaded=True)

            vault_info = IchiVault(
                vault=vault_addr,
                owner=vault.functions.owner().call(),
                pool=vault.functions.pool().call(),
                token0_symbol=token0.symbol,
                token1_symbol=token1.symbol,
                allow_token0=vault.functions.allowToken0().call(),
                allow_token1=vault.functions.allowToken1().call(),
                total_supply_scaled=vault.total_supply_scaled,
            )

            outputs_by_block[block_number].append(vault_info)

        series = []
        for block_number, vaults in outputs_by_block.items():
            block = BlockNumber(block_number)
            series.append(BlockSeriesRow(
                blockNumber=int(block_number),
                blockTimestamp=block.timestamp,
                sampleTimestamp=block.sample_timestamp,
                output=vaults
            ))

        return BlockSeries(series=series)


@Model.describe(slug='ichi.vaults',
                version='1.0',
                display_name='ICHI vaults',
                description='ICHI vaults',
                category='protocol',
                subcategory='ichi',
                input=EmptyInputWithNetwork,
                output=dict,
                cache=CachePolicy.SKIP)
class IchiVaults(Model):
    ICHI_VAULT_FACTORY = '0x2d2c72C4dC71AA32D64e5142e336741131A73fc0'

    def run(self, _) -> dict:
        vaults_series = self.context.run_model('ichi.vaults-block-series', {},
                                               return_type=BlockSeries[List[IchiVault]])
        vaults = {}
        for row in vaults_series:
            for vault in row.output:
                vaults[vault.vault] = vault
        return {'vaults': vaults}


class IchiVaultContract(Contract):
    class Config:
        schema_extra = {
            'examples': [{"address": "0x8ac3d7cd56816da9fb45e7640aa70a24884e02f7", "_test_multi": {'chain_id': 137, 'block_number': None}}],
            'test_multi': True
        }


class IchiVaultTokensOutput(ImmutableOutput):
    token0_decimals: int
    token1_decimals: int
    token0_address_checksum: str
    token1_address_checksum: str
    token0_symbol: str
    token1_symbol: str


@ImmutableModel.describe(slug='ichi.vault-tokens-info',
                         version='0.1',
                         display_name='ICHI vault tokens',
                         description='Get the information of tokens for an ICHI vault',
                         category='protocol',
                         subcategory='ichi',
                         input=IchiVaultContract,
                         output=IchiVaultTokensOutput)
class IchiVaultTokensInfo(ImmutableModel):
    def run(self, input: IchiVaultContract):
        vault_addr = input.address
        vault_ichi = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)

        token0_addr = Address(vault_ichi.functions.token0().call())
        token1_addr = Address(vault_ichi.functions.token1().call())
        token0 = Token(token0_addr).as_erc20(set_loaded=True)
        token1 = Token(token1_addr).as_erc20(set_loaded=True)

        firstResultBlockNumber = self.context.run_model(
            'token.deployment', vault_ichi, return_type=ImmutableOutput).firstResultBlockNumber

        return IchiVaultTokensOutput(
            firstResultBlockNumber=firstResultBlockNumber,
            token0_decimals=token0.decimals,
            token1_decimals=token1.decimals,
            token0_address_checksum=token0.address.checksum,
            token1_address_checksum=token1.address.checksum,
            token0_symbol=token0.symbol,
            token1_symbol=token1.symbol,
        )


@Model.describe(slug='ichi.vault-info',
                version='0.15',
                display_name='ICHI vault info',
                description='Get the value of vault token for an ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=IchiVaultContract,
                output=dict)
class IchiVaultInfo(Model):
    def run(self, input: IchiVaultContract) -> dict:
        vault_addr = input.address
        vault_ichi = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
        vault_pool_addr = Address(vault_ichi.functions.pool().call())
        vault_pool = (Contract(vault_pool_addr)
                      .set_abi(UNISWAP_V3_POOL_ABI, set_loaded=True))

        allow_token0 = vault_ichi.functions.allowToken0().call()
        allow_token1 = vault_ichi.functions.allowToken1().call()

        assert not (allow_token0 and allow_token1) and (
            allow_token0 or allow_token1)

        tokens = self.context.run_model('ichi.vault-tokens-info',
                                        vault_ichi,
                                        return_type=IchiVaultTokensOutput)

        token0_decimals = tokens.token0_decimals
        token1_decimals = tokens.token1_decimals
        token0_address_checksum = tokens.token0_address_checksum
        token1_address_checksum = tokens.token1_address_checksum
        token0_symbol = tokens.token0_symbol
        token1_symbol = tokens.token1_symbol
        scale_multiplier = 10 ** (token0_decimals - token1_decimals)

        current_tick = vault_ichi.functions.currentTick().call()
        sqrtPriceX96 = vault_pool.functions.slot0().call()[0]

        _tick_price0 = tick_to_price(current_tick) * scale_multiplier
        _ratio_price0 = sqrtPriceX96 * sqrtPriceX96 / (2 ** 192) * scale_multiplier

        # value of ichi vault token at a block
        total_supply = vault_ichi.total_supply
        total_supply_scaled = vault_ichi.total_supply_scaled
        token0_amount, token1_amount = vault_ichi.functions.getTotalAmounts().call()
        token0_amount = token0_amount / (10 ** token0_decimals)
        token1_amount = token1_amount / (10 ** token1_decimals)

        if allow_token0:
            token1_in_token0_amount = token1_amount / _tick_price0
            total_amount_in_token_n = token0_amount + token1_in_token0_amount
        else:
            token0_in_token1_amount = token0_amount * _tick_price0
            total_amount_in_token_n = token1_amount + token0_in_token1_amount

        amount_scaling = 10 ** (token0_decimals if allow_token0 else token1_decimals)

        try:
            token0_chainlink_price = self.context.run_model(
                'price.oracle-chainlink', {'base': token0_address_checksum})['price']
        except ModelRunError:
            token0_chainlink_price = None

        try:
            token1_chainlink_price = self.context.run_model(
                'price.oracle-chainlink', {'base': token1_address_checksum})['price']
        except ModelRunError:
            token1_chainlink_price = None

        if token0_chainlink_price is None and token1_chainlink_price is not None:
            token0_chainlink_price = token1_chainlink_price * _tick_price0

        if token1_chainlink_price is None and token0_chainlink_price is not None:
            token1_chainlink_price = token0_chainlink_price / _tick_price0

        return {
            'token0': token0_address_checksum,
            'token1': token1_address_checksum,
            'token0_decimals': token0_decimals,
            'token1_decimals': token1_decimals,
            'scale_multiplier': scale_multiplier,
            'token0_symbol': token0_symbol,
            'token1_symbol': token1_symbol,
            'allowed_token': 0 if allow_token0 else 1,
            'token0_amount': token0_amount,
            'token1_amount': token1_amount,
            'total_amount_in_token': total_amount_in_token_n,
            'total_supply_scaled': total_supply_scaled,
            'vault_token_ratio': (0
                                  if math.isclose(total_supply, 0)
                                  else total_amount_in_token_n * amount_scaling / total_supply),
            'token0_amount_ratio': (0
                                    if math.isclose(total_supply_scaled, 0)
                                    else token0_amount / total_supply_scaled),
            'token1_amount_ratio': (0
                                    if math.isclose(total_supply_scaled, 0)
                                    else token1_amount / total_supply_scaled),
            'pool_price0': _tick_price0,
            'ratio_price0': _ratio_price0,
            'tvl': (
                (token0_amount * token0_chainlink_price + token1_amount * token1_chainlink_price)
                if token0_chainlink_price is not None and token1_chainlink_price is not None
                else None),
            'token0_chainlink_price': token0_chainlink_price,
            'token1_chainlink_price': token1_chainlink_price,
        }


@Model.describe(slug='ichi.vault-info-full',
                version='0.5',
                display_name='ICHI vault info (full)',
                description='Get the vault info from ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=IchiVaultContract,
                output=dict)
class IchiVaultInfoFull(Model):
    def run(self, input: IchiVaultContract) -> dict:
        vault_addr = input.address
        vault_ichi = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
        vault_pool_addr = Address(vault_ichi.functions.pool().call())
        vault_pool = Contract(vault_pool_addr).set_abi(
            UNISWAP_V3_POOL_ABI, set_loaded=True)

        _affiliate = Address(vault_ichi.functions.affiliate().call())
        ichi_vault_factory_addr = vault_ichi.functions.ichiVaultFactory().call()
        ichi_vault_factory = Contract(ichi_vault_factory_addr).set_abi(
            abi=ICHI_VAULT_FACTORY, set_loaded=True)
        _fee_recipient = Address(
            ichi_vault_factory.functions.feeRecipient().call())
        _baseFee = ichi_vault_factory.functions.baseFee().call()
        _baseFeeSplit = ichi_vault_factory.functions.baseFeeSplit().call()

        token0_addr = Address(vault_ichi.functions.token0().call())
        token1_addr = Address(vault_ichi.functions.token1().call())
        token0 = Token(token0_addr).as_erc20(set_loaded=True)
        token1 = Token(token1_addr).as_erc20(set_loaded=True)

        allow_token0 = vault_ichi.functions.allowToken0().call()
        allow_token1 = vault_ichi.functions.allowToken1().call()

        assert not (allow_token0 and allow_token1) and (
            allow_token0 or allow_token1)

        # (vault_addr, vault_pool, affiliate, fee_recipient, allow_token0, allow_token1, baseFee / 1e18, baseFeeSplit / 1e18)

        _base_position_liquidity, _base_token0, _base_token1 = vault_ichi.functions.getBasePosition().call()
        _limit_position_liquidity, _limit_token0, _limit_token1 = vault_ichi.functions.getLimitPosition().call()

        scale_multiplier = 10 ** (token0.decimals - token1.decimals)

        current_tick = vault_ichi.functions.currentTick().call()
        sqrtPriceX96 = vault_pool.functions.slot0().call()[0]

        _tick_price0 = tick_to_price(current_tick) * scale_multiplier
        _ratio_price0 = sqrtPriceX96 * sqrtPriceX96 / (2 ** 192) * scale_multiplier

        try:
            token0_chainlink_price = self.context.run_model(
                'price.oracle-chainlink', {'base': token0.address.checksum})['price']
        except ModelRunError:
            token0_chainlink_price = None

        try:
            token1_chainlink_price = self.context.run_model(
                'price.oracle-chainlink', {'base': token1.address.checksum})['price']
        except ModelRunError:
            token1_chainlink_price = None

        # value of ichi vault token at a block
        total_supply = vault_ichi.total_supply
        total_supply_scaled = vault_ichi.total_supply_scaled
        token0_amount, token1_amount = vault_ichi.functions.getTotalAmounts().call()
        token0_amount = token0.scaled(token0_amount)
        token1_amount = token1.scaled(token1_amount)

        if allow_token0:
            token1_in_token0_amount = token1_amount / _tick_price0
            total_amount_in_token = token0_amount + token1_in_token0_amount
        else:
            token0_in_token1_amount = token0_amount * _tick_price0
            total_amount_in_token = token1_amount + token0_in_token1_amount

        return {
            'token0': token0.address.checksum,
            'token1': token1.address.checksum,
            'token0_symbol': token0.symbol,
            'token1_symbol': token1.symbol,
            'allowed_token': 0 if allow_token0 else 1,
            'token0_amount': token0_amount,
            'token1_amount': token1_amount,
            'total_amount_in_token': total_amount_in_token,
            'total_supply_scaled': total_supply_scaled,
            'vault_token_ratio': (0 if math.isclose(total_supply, 0)
                                  else (total_amount_in_token / (token0.scaled(1) if allow_token0 else token1.scaled(1)) / total_supply)),
            'pool_price0': _tick_price0,
            'ratio_price0': _ratio_price0,
            'token0_chainlink_price': token0_chainlink_price,
            'token1_chainlink_price': token1_chainlink_price,
            'vault_token_value_chainlink': (
                0 if math.isclose(total_supply_scaled, 0)
                else (((token0_amount * token0_chainlink_price + token1_amount * token1_chainlink_price) / total_supply_scaled)
                      if token0_chainlink_price is not None and token1_chainlink_price is not None
                      else None)),
        }


# credmark-dev run ichi.vault-first-deposit -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' --api_url http://localhost:8700 -c 137 -j
# credmark-dev run ichi.vault-first-deposit -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' -c 137 -j

class IchiVaultFirstDepositOutput(ImmutableOutput):
    first_deposit_block_number: int = DTOField(description='First deposit block number')
    first_deposit_block_timestamp: int = DTOField(description='First deposit block timestamp')


@ImmutableModel.describe(slug='ichi.vault-first-deposit',
                         version='0.6',
                         display_name='ICHI vault first deposit',
                         description='Get the block_number of the first deposit of an ICHI vault',
                         category='protocol',
                         subcategory='ichi',
                         input=IchiVaultContract,
                         output=IchiVaultFirstDepositOutput)
class IchiVaultFirstDeposit(ImmutableModel):
    def run(self, input: IchiVaultContract) -> IchiVaultFirstDepositOutput:
        vault_addr = input.address
        vault_ichi = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
        try:
            df_first_deposit = pd.DataFrame(vault_ichi.fetch_events(
                vault_ichi.events.Deposit, from_block=0))
        except HTTPError:
            deployed_info = self.context.run_model('token.deployment', {
                "address": input.address, "ignore_proxy": True})
            deployed_block_number = deployed_info['deployed_block_number']
            try:
                df_first_deposit = pd.DataFrame(vault_ichi.fetch_events(
                    vault_ichi.events.Deposit, from_block=deployed_block_number, by_range=10_000))
            except ValueError:
                try:
                    df_first_deposit = pd.DataFrame(vault_ichi.fetch_events(
                        vault_ichi.events.Deposit, from_block=deployed_block_number, by_range=1_000))
                except ValueError:
                    try:
                        df_first_deposit = pd.DataFrame(vault_ichi.fetch_events(
                            vault_ichi.events.Transfer, from_block=deployed_block_number, by_range=10_000))
                    except ValueError:
                        try:
                            df_first_deposit = pd.DataFrame(vault_ichi.fetch_events(
                                vault_ichi.events.Transfer, from_block=deployed_block_number, by_range=1_000))
                        except ValueError as err:
                            raise ValueError(
                                f'Can not fetch events for {vault_ichi.address} from {deployed_info["deployed_block_number"]}') from err

        if df_first_deposit.empty:
            raise ModelDataError('No deposit has been made to the model')

        first_deposit_block_number = int(
            df_first_deposit.sort_values('blockNumber').iloc[0]['blockNumber'])
        first_deposit_block_timestamp = BlockNumber(first_deposit_block_number).timestamp

        return IchiVaultFirstDepositOutput(
            first_deposit_block_number=first_deposit_block_number,
            first_deposit_block_timestamp=first_deposit_block_timestamp,
            firstResultBlockNumber=first_deposit_block_number)


# credmark-dev run ichi.vault-cashflow -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' -c 137 --api_url=http://localhost:8700 -j -b 42454582
# credmark-dev run ichi.vault-cashflow -i '{"address": "0x711901e4b9136119Fb047ABe8c43D49339f161c3"}' -c 137 --api_url=http://localhost:8700 -j -b 41675859


@IncrementalModel.describe(
    slug='ichi.vault-cashflow-block-series',
    version='0.23',
    display_name='ICHI vault cashflow',
    description='Get the past deposit and withdraw events of an ICHI vault',
    category='protocol',
    subcategory='ichi',
    input=IchiVaultContract,
    output=BlockSeries[Records])
class IchiVaultCashflowSeries(IncrementalModel):
    ICHI_VAULT_DEPOSIT_GUARD = {
        Network.Polygon.value: '0xA5cE107711789b350e04063D4EffBe6aB6eB05a4'
    }

    def fetch_deposit_forwarded(self, allow_token0):
        vault_deposit_guard = Contract(self.ICHI_VAULT_DEPOSIT_GUARD[self.context.chain_id])

        deposit_forwarded_event_abi = [x for x in json.loads(ICHI_VAULT_DEPOSIT_GUARD)
                                       if 'type' in x and x['type'] == 'event' and 'name' in x and x['name'] == 'DepositForwarded']

        df_deposit_forwarded = self.context.run_model(
            'contract.events',
            ContractEventsInput(address=vault_deposit_guard.address, event_name='DepositForwarded',
                                event_abi=deposit_forwarded_event_abi),
            return_type=ContractEventsOutput).records.to_dataframe()

        if not df_deposit_forwarded.empty:
            df_deposit_forwarded = (
                df_deposit_forwarded
                .query('vault == @input.address.checksum')
                .loc[:, ['blockNumber', 'transactionIndex', 'logIndex', 'event', 'shares', 'amount']])
            if allow_token0:
                df_deposit_forwarded.rename(columns={'amount': 'amount0'}, inplace=True)
                df_deposit_forwarded = df_deposit_forwarded.assign(amount1=0)
            else:
                df_deposit_forwarded.rename(columns={'amount': 'amount1'}, inplace=True)
                df_deposit_forwarded = df_deposit_forwarded.assign(amount0=0)

    def run(self, input: IchiVaultContract, from_block: BlockNumber) -> BlockSeries[Records]:
        vault_ichi = Contract(input.address).set_abi(ICHI_VAULT, set_loaded=True)
        vault_ichi_decimals = vault_ichi.functions.decimals().call()

        allow_token0 = vault_ichi.functions.allowToken0().call()
        token0_addr = Address(vault_ichi.functions.token0().call())
        token1_addr = Address(vault_ichi.functions.token1().call())
        token0 = Token(token0_addr).as_erc20(set_loaded=True)
        token1 = Token(token1_addr).as_erc20(set_loaded=True)
        token0_decimals = token0.decimals
        token1_decimals = token1.decimals
        scale_multiplier = 10 ** (token0_decimals - token1_decimals)
        self.logger.info(('token0', token0.address, 'token1', token1.address))

        ichi_vault_abi = json.loads(ICHI_VAULT)
        deposit_event_abi = [x for x in ichi_vault_abi
                             if 'type' in x and x['type'] == 'event' and 'name' in x and x['name'] == 'Deposit']
        withdraw_event_abi = [x for x in ichi_vault_abi
                              if 'type' in x and x['type'] == 'event' and 'name' in x and x['name'] == 'Withdraw']

        df_deposit = self.context.run_model(
            'contract.events',
            ContractEventsInput(address=input.address, event_name='Deposit',
                                event_abi=deposit_event_abi),
            return_type=ContractEventsOutput).records.to_dataframe()

        df_withdraw = self.context.run_model(
            'contract.events',
            ContractEventsInput(address=input.address, event_name='Withdraw',
                                event_abi=withdraw_event_abi),
            return_type=ContractEventsOutput).records.to_dataframe()

        if not df_deposit.empty:
            df_deposit = (df_deposit
                          .loc[:, ['blockNumber', 'transactionIndex', 'logIndex', 'event', 'shares', 'amount0', 'amount1', 'to']]
                          .assign(shares=lambda df: df.shares.apply(int) / (10 ** vault_ichi_decimals),
                                  amount0=lambda df: df.amount0.apply(
                                      int) / (10 ** token0_decimals),
                                  amount1=lambda df: df.amount1.apply(int) / (10 ** token1_decimals)))

        if not df_withdraw.empty:
            df_withdraw = (df_withdraw
                           .loc[:, ['blockNumber', 'transactionIndex', 'logIndex', 'event', 'shares', 'amount0', 'amount1', 'to']]
                           .assign(shares=lambda df: -(df.shares.apply(int) / (10 ** vault_ichi_decimals)),
                                   amount0=lambda df: -(df.amount0.apply(int) /
                                                        (10 ** token0_decimals)),
                                   amount1=lambda df: -(df.amount1.apply(int) / (10 ** token1_decimals))))

        _from_block_number = int(from_block)  # pylint: disable=unused-variable
        df_comb = pd.concat([df_deposit, df_withdraw], ignore_index=True)
        df_comb = (df_comb
                   .query('blockNumber >= @from_block_number')
                   .sort_values(['blockNumber', 'transactionIndex', 'logIndex'])
                   .reset_index(drop=True))

        self.logger.info(
            f'[{self.slug}] Deposit/Withdraw events: {len(df_comb)}={len(df_deposit)}+{len(df_withdraw)}')

        if df_comb.empty:
            return BlockSeries()

        df_cash_flow = pd.DataFrame()
        cash_flow = []
        for n_row, row in df_comb.iterrows():
            past_block_number = row['blockNumber']
            token0_amount = row['amount0']
            token1_amount = row['amount1']

            with self.context.fork(block_number=past_block_number) as past_context:
                past_block_timestamp = past_context.block_number.timestamp
                past_block_date = past_context.block_number.timestamp_datetime

                current_tick = vault_ichi.functions.currentTick().call()
                _tick_price0 = tick_to_price(current_tick) * scale_multiplier
                if allow_token0:
                    token1_in_token0_amount = token1_amount / _tick_price0
                    total_amount_in_token_n = token0_amount + token1_in_token0_amount
                else:
                    token0_in_token1_amount = token0_amount * _tick_price0
                    total_amount_in_token_n = token1_amount + token0_in_token1_amount

                self.logger.info((n_row, past_block_number, past_block_timestamp,
                                  current_tick, total_amount_in_token_n))
                cash_flow.append((past_block_number, past_block_timestamp, past_block_date, row['event'],
                                  allow_token0, current_tick, row['shares'],
                                  token0_amount, token1_amount, total_amount_in_token_n, row['to']))

        df_cash_flow = (pd.DataFrame(
            cash_flow, columns=['block_number', 'timestamp', 'timestamp_datetime', 'event', 'allow_token0',
                                'tick_price0', 'shares', 'amount0', 'amount1', 'total_amount_in_token_n', 'to'])
                        .assign(timestamp_date=lambda df: df.timestamp_datetime.dt.date)
                        .groupby('block_number'))

        series = []
        for block_number, group in df_cash_flow:
            block_number = BlockNumber(int(str(block_number)))
            series.append(BlockSeriesRow(
                blockNumber=int(block_number),
                blockTimestamp=block_number.timestamp,
                sampleTimestamp=block_number.sample_timestamp,
                output=Records.from_dataframe(group)
            ))
        return BlockSeries(series=series)


@Model.describe(slug='ichi.vault-cashflow',
                version='0.23',
                display_name='ICHI vault cashflow',
                description='Get the past deposit and withdraw events of an ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=IchiVaultContract,
                output=Records,
                cache=CachePolicy.SKIP)
class IchiVaultCashflow(Model):
    def run(self, input: IchiVaultContract) -> Records:
        cashflow_series = self.context.run_model('ichi.vault-cashflow-block-series',
                                                 input,
                                                 return_type=BlockSeries[Records])
        df_comb = (pd.concat([r.output.to_dataframe() for r in cashflow_series], ignore_index=True)
                   .sort_values(['block_number'])
                   .reset_index(drop=True))

        return Records.from_dataframe(df_comb)


class IchiPerformanceInput(DTO):
    days_horizon: List[int] = DTOField(
        [], description='Time horizon in days')
    base: int = DTOField(1000, description='Base amount to calculate value')

    class Config:
        schema_extra = {
            'examples': [{"days_horizon": [7],
                          "base": 1000,
                          "_test_multi": {'chain_id': 137, 'block_number': None}}],
            'test_multi': True
        }


class IchiVaultPerformanceInput(IchiVaultContract, IchiPerformanceInput):
    class Config:
        schema_extra = {
            'examples': [{"address": "0x8ac3d7cd56816da9fb45e7640aa70a24884e02f7",
                          "days_horizon": [7],
                          "base": 1000,
                          "_test_multi": {'chain_id': 137, 'block_number': None}}],
            'test_multi': True
        }

# credmark-dev run ichi.vault-performance -i '{"address": "0x711901e4b9136119fb047abe8c43d49339f161c3", "days_horizon":[7, 30, 60]}' -c 137 --api_url=http://localhost:8700 -j -b 42488937
# credmark-dev run ichi.vault-performance -i '{"address": "0x711901e4b9136119fb047abe8c43d49339f161c3", "days_horizon":[]}' -c 137 --api_url=http://localhost:8700 -j -b 42488937

# credmark-dev run ichi.vault-performance -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "days_horizon":[7, 30, 60]}' -c 137 --api_url=http://localhost:8700 -j -b 42488937
# credmark-dev run ichi.vault-performance -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "days_horizon":[]}' -c 137 --api_url=http://localhost:8700 -j -b 42488937
# credmark-dev run ichi.vault-performance -i '{"address": "0xf461063819ffbc6e22704ade1861b0df3bac9585", "days_horizon":[]}' -c 137 --api_url=http://localhost:8700 -j -b 42538803
# credmark-dev run ichi.vault-performance -i '{"address": "0xb05be549a570e430e5dde4a10a0d34cf09a7df21", "days_horizon":[]}' -c 137 --api_url=http://localhost:8700 -j -b 42538803

# BAL
# credmark-dev run ichi.vault-performance -i '{"address": "0xf461063819ffbc6e22704ade1861b0df3bac9585", "days_horizon":[]}' -c 137 --api_url=http://localhost:8700 -j -b 42538803


@Model.describe(slug='ichi.vault-performance',
                version='0.39',
                display_name='ICHI vault performance',
                description='Get the vault performance from ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=IchiVaultPerformanceInput,
                output=dict)
class IchiVaultPerformance(Model):
    """
    Output columns
    - vault: vault address
    - tvl: value of tokens in the vault, price comes from chainlink. Some tokens (e.g. GOVI, oneBTC, on the bottom) has no chainlink price
    - token0_symbol, token1_symbol: no need to explain
    - allowed_token: the single token to be deposited, can be displayed as `Deposit token`
    - days_since_first_deposit: vault starts to operate from first deposit, can be displayed as `Vault live days`
    - irr: internal return rate (annualized) for the deposit token since vault went live, can be displayed as "IRR"
    - value_hold: current value of hold $1000 worth of deposit token from the start time of the vault
    - value_vault: current value of deposit $1000 worth of deposit token from the start time of the vault
    - value_uniswap: current value of deposit $1000's token to Uniswap from the start time of the vault
    """

    @staticmethod
    # pylint: disable=too-many-arguments
    def vault_current(context, vault_ichi, scale_multiplier, token0_decimals, token1_decimals, allow_token0, event_name, make_negative):
        """
        get vault status of context
        """
        current_tick = vault_ichi.functions.currentTick().call()
        _tick_price0 = tick_to_price(current_tick) * scale_multiplier
        token0_amount, token1_amount = vault_ichi.functions.getTotalAmounts().call()
        token0_amount = token0_amount / (10 ** token0_decimals)
        token1_amount = token1_amount / (10 ** token1_decimals)

        if allow_token0:
            token1_in_token0_amount = token1_amount / _tick_price0
            total_amount_in_token_n = token0_amount + token1_in_token0_amount
        else:
            token0_in_token1_amount = token0_amount * _tick_price0
            total_amount_in_token_n = token1_amount + token0_in_token1_amount

        if make_negative:
            token0_amount, token1_amount, total_amount_in_token_n = - \
                token0_amount, -token1_amount, -total_amount_in_token_n

        return (context.block_number, context.block_number.timestamp, context.block_number.timestamp_datetime, event_name,
                allow_token0, current_tick, 0,
                token0_amount, token1_amount, total_amount_in_token_n,
                event_name, context.block_number.timestamp_datetime.date().isoformat())

    def irr_return(self, vault_info_past, vault_info_current, days, past_block_date, current_block_date):
        """
        IRR of the vault, derived from the exchange ratio between vault token to deposit/withdraw tokens
        """
        past_value, current_value = vault_info_past['vault_token_ratio'], vault_info_current['vault_token_ratio']

        if math.isclose(current_value, 0):
            return None

        irr = npf.irr([-past_value, current_value])

        _cagr_from_irr = np.power(irr + 1, 365 / days) - 1
        _cagr_annualized = np.power(current_value / past_value, 365 / days) - 1

        irr2 = xirr([past_block_date, current_block_date], [-past_value, current_value])

        irr_return = current_value / past_value - 1

        self.logger.info(('irr_return', days, irr_return, irr,
                         irr2, _cagr_from_irr, _cagr_annualized))

        return irr_return

    def irr_cashflow(self, vault_ichi, df_cashflow, start_block, end_block, vault_info):
        scale_multiplier = vault_info['scale_multiplier']
        token0_decimals = vault_info['token0_decimals']
        token1_decimals = vault_info['token1_decimals']
        allow_token0 = vault_info['allowed_token'] == 0

        def cash_flow(col_value, col_event):
            return lambda x, col_value=col_value, col_event=col_event: \
                x[col_value].abs() * (-1 * (x[col_event] == 'Deposit')) + \
                x[col_value].abs() * (1 * (x[col_event] == 'Withdraw'))

        non_zero_to = df_cashflow.groupby('to', as_index=False)['shares'].sum().query('shares != 0')
        zero_to = df_cashflow.groupby('to', as_index=False)['shares'].sum().query('shares == 0')

        df_cashflow_trim = (
            df_cashflow
            .query('block_number >= @start_block and block_number <= @end_block')
            .assign(total_amount_in_token_n=cash_flow('total_amount_in_token_n', 'event'),
                    amount0=cash_flow('amount0', 'event'),
                    amount1=cash_flow('amount1', 'event')))

        # In pandas make a column negative when another column's value is equal to "Deposit"

        self.logger.info(
            f'Trimmed df_cashflow from {df_cashflow.shape[0]} to {df_cashflow_trim.shape[0]}')
        if df_cashflow_trim.block_number.isin([start_block]).any():
            with self.context.fork(block_number=start_block - 1) as cc:
                df_row_start_block = pd.DataFrame(
                    [self.vault_current(cc, vault_ichi, scale_multiplier, token0_decimals,
                                        token1_decimals, allow_token0, 'Start', make_negative=True)],
                    columns=df_cashflow_trim.columns)
        else:
            with self.context.fork(block_number=start_block) as cc:
                df_row_start_block = pd.DataFrame(
                    [self.vault_current(cc, vault_ichi, scale_multiplier, token0_decimals,
                                        token1_decimals, allow_token0, 'Start', make_negative=True)],
                    columns=df_cashflow_trim.columns)

        with self.context.fork(block_number=end_block) as cc:
            df_row_end_block = pd.DataFrame(
                [self.vault_current(cc, vault_ichi, scale_multiplier, token0_decimals,
                                    token1_decimals, allow_token0, 'Final', make_negative=False)],
                columns=df_cashflow_trim.columns)

        df_cashflow_comb = pd.concat([
            df_row_start_block,
            df_cashflow_trim,
            df_row_end_block])

        df_cashflow_comb_non_zero = pd.concat([
            df_row_start_block,
            df_cashflow_trim.merge(non_zero_to.loc[:, ['to']], on='to', how='inner'),
            df_row_end_block])

        self.logger.info(
            f'Original:{df_cashflow_comb.shape[0]}, Non zero:{df_cashflow_comb_non_zero.shape[0]}. '
            f'non_zero_to:{non_zero_to.shape[0]} zero_to:{zero_to.shape[0]}')

        try:
            irr = xirr(df_cashflow_comb.timestamp_date.to_list(),
                       (df_cashflow_comb.total_amount_in_token_n).to_list())
        except InvalidPaymentsError:
            irr = None

        try:
            irr_non_zero = xirr(df_cashflow_comb_non_zero.timestamp_date.to_list(),
                                df_cashflow_comb_non_zero.total_amount_in_token_n.to_list())
        except InvalidPaymentsError:
            irr_non_zero = None

        return irr, irr_non_zero

    def qty_hold_and_vault(self, vault_info_past, vault_info_current, base=1000):
        """
        Quantity of hold and vault
        """

        try:
            qty_hold = base
            if vault_info_past['vault_token_ratio'] == 0:
                qty_vault = base
            else:
                qty_vault = qty_hold / vault_info_past['vault_token_ratio'] * \
                    vault_info_current['vault_token_ratio']
        except TypeError:
            return None, None

        self.logger.info(('qty_hold_and_vault', qty_hold, qty_vault))
        return qty_hold, qty_vault

    def value_hold_and_vault(self, vault_info_past, vault_info_current, base=1000):
        """
        Value of hold and vault
        """

        try:
            if vault_info_current['allowed_token'] == 0:
                value_hold = base / vault_info_past['token0_chainlink_price'] * \
                    vault_info_current['token0_chainlink_price']
                value_vault = value_hold / vault_info_past['vault_token_ratio'] * \
                    vault_info_current['vault_token_ratio']
            else:
                value_hold = base / vault_info_past['token1_chainlink_price'] * \
                    vault_info_current['token1_chainlink_price']
                value_vault = value_hold / vault_info_past['vault_token_ratio'] * \
                    vault_info_current['vault_token_ratio']
        except TypeError:
            return None, None

        self.logger.info(('value_hold_and_vault', value_hold, value_vault))
        return value_hold, value_vault

    def qty_hold_5050(self, vault_info_past, vault_info_current, base=1000):
        """
        Quantity of HOLD 50/50 position
        """

        if vault_info_current['allowed_token'] == 0:
            p1, p2 = base / 2, base / 2 * vault_info_past['ratio_price0']
            current_qty = p1 + p2 / vault_info_current['ratio_price0']
        else:
            p1, p2 = base / 2 / vault_info_past['ratio_price0'], base / 2
            current_qty = p1 * vault_info_current['ratio_price0'] + p2

        self.logger.info(('qty_hold_5050', current_qty))
        return current_qty

    def irr_return_hold_5050(self, vault_info_past, vault_info_current, days):
        """
        IRR of HOLD 50/50 position
        """

        p1, p2 = 0.5, 0.5

        past_value = p1 + p2
        if vault_info_current['allowed_token'] == 0:
            current_value = p1 + p2 * \
                vault_info_past['ratio_price0'] / vault_info_current['ratio_price0']
        else:
            current_value = p1 / vault_info_past['ratio_price0'] * \
                vault_info_current['ratio_price0'] + p2

        irr = npf.irr([-past_value, current_value])
        _cagr_from_irr = np.power(irr + 1, 365 / days) - 1
        _cagr_annualized = np.power(current_value / past_value, 365 / days) - 1
        self.logger.info(('irr_hold_5050', days, _cagr_from_irr,
                         _cagr_annualized, past_value, current_value,
                         vault_info_past['ratio_price0'], vault_info_current['ratio_price0']))
        return _cagr_from_irr

    def irr_return_uniswap(self, vault_info_past, vault_info_current, days):
        """
        IRR of Uniswap 50/50 position
        """

        if vault_info_current['allowed_token'] == 0:
            token0_amount, token1_amount = 0.5, 0.5 * vault_info_past['ratio_price0']
            liquidity = token0_amount * token1_amount
            token0_amount_new = np.sqrt(
                liquidity / vault_info_current['ratio_price0'])
            past_value = 1
            current_value = token0_amount_new * 2
        else:
            token0_amount, token1_amount = 0.5 / vault_info_past['ratio_price0'], 0.5
            liquidity = token0_amount * token1_amount
            token1_amount_new = np.sqrt(
                liquidity * vault_info_current['ratio_price0'])
            past_value = 1
            current_value = token1_amount_new * 2

        irr = npf.irr([-past_value, current_value])
        _cagr_from_irr = np.power(irr + 1, 365 / days) - 1
        _cagr_annualized = np.power(current_value / past_value, 365 / days) - 1
        self.logger.info(('irr_uniswap', days, _cagr_from_irr,
                         _cagr_annualized, past_value, current_value,
                         vault_info_past['ratio_price0'], vault_info_current['ratio_price0']))
        return _cagr_from_irr

    def calc_uniswap_value(self, vault_info_past, vault_info_current, base=1000):
        """
        Value of Uniswap 50/50 position
        """

        try:
            if vault_info_current['allowed_token'] == 0:
                token0_amount = base / 2 / vault_info_past['token0_chainlink_price']
                token1_amount = token0_amount * vault_info_past['ratio_price0']
                liquidity = token0_amount * token1_amount
                token0_amount_new = np.sqrt(
                    liquidity / vault_info_current['ratio_price0'])
                _past_value = 1_000
                current_value = token0_amount_new * 2 * vault_info_current['token0_chainlink_price']
            else:
                token1_amount = base / 2 / vault_info_past['token1_chainlink_price']
                token0_amount = token1_amount / vault_info_past['ratio_price0']

                liquidity = token0_amount * token1_amount
                token1_amount_new = np.sqrt(
                    liquidity * vault_info_current['ratio_price0'])
                _past_value = 1_000
                current_value = token1_amount_new * 2 * vault_info_current['token1_chainlink_price']
        except TypeError:
            return None

        self.logger.info(('calc_uniswap_value', current_value))
        return current_value

    def calc_uniswap_lp(self, vault_info_past, vault_info_current, base=1000):
        """
        Value of Uniswap position with the nee of additional other token, keep the other token of the same amount
        """

        allowed_token = vault_info_current['allowed_token']
        try:
            if allowed_token == 0:
                token0_amount = base / vault_info_past['token0_chainlink_price']
                token1_amount = token0_amount * vault_info_past['ratio_price0']
                liquidity = token0_amount * token1_amount
                token0_amount_new = np.sqrt(liquidity / vault_info_current['ratio_price0'])
                token1_amount_new = np.sqrt(liquidity * vault_info_current['ratio_price0'])
                current_token_value = token0_amount_new * \
                    vault_info_current['token0_chainlink_price']
                make_up_token_value = (token1_amount_new - token1_amount) * \
                    vault_info_current['token1_chainlink_price']
                current_value = current_token_value + make_up_token_value
            else:
                token1_amount = base / vault_info_past['token1_chainlink_price']
                token0_amount = token1_amount / vault_info_past['ratio_price0']
                liquidity = token0_amount * token1_amount

                token0_amount_new = np.sqrt(liquidity / vault_info_current['ratio_price0'])
                token1_amount_new = np.sqrt(liquidity * vault_info_current['ratio_price0'])
                current_token_value = token1_amount_new * \
                    vault_info_current['token1_chainlink_price']
                make_up_token_value = (token0_amount_new - token0_amount) * \
                    vault_info_current['token0_chainlink_price']
                current_value = current_token_value + make_up_token_value
        except TypeError:
            return None

        self.logger.info(('calc_uniswap_lp', allowed_token,
                         f't0: {token0_amount} => {token0_amount_new}', f't1: {token1_amount} => {token1_amount_new}'))
        self.logger.info(('t0_price', vault_info_past['token0_chainlink_price'],
                         vault_info_current['token0_chainlink_price']))
        self.logger.info(('t1_price', vault_info_past['token1_chainlink_price'],
                         vault_info_current['token1_chainlink_price']))
        self.logger.info((f'{current_token_value} + {make_up_token_value} = {current_value}'))

        return current_value

    def run(self, input: IchiVaultPerformanceInput) -> dict:
        vault_addr = input.address
        vault_ichi = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
        # _vault_pool_addr = Address(vault_ichi.functions.pool().call())

        deployment = self.context.run_model(
            'token.deployment', {'address': vault_addr, 'ignore_proxy': True})

        deployed_block_number = deployment['deployed_block_number']
        deployed_block_timestamp = deployment['deployed_block_timestamp']
        days_since_deployment = (
            self.context.block_number.timestamp - deployed_block_timestamp) / (60 * 60 * 24)

        vault_info_current = self.context.run_model(
            'ichi.vault-info', {"address": vault_addr}, block_number=self.context.block_number)

        try:
            first_deposit = self.context.run_model(
                'ichi.vault-first-deposit', {'address': vault_addr}, return_type=IchiVaultFirstDepositOutput)
            first_deposit_block_number = first_deposit.first_deposit_block_number
            first_deposit_block_timestamp = first_deposit.first_deposit_block_timestamp
            days_from_first_deposit = (
                self.context.block_number.timestamp - first_deposit_block_timestamp) / (60 * 60 * 24)
        except ModelDataError:
            first_deposit_block_number = None
            first_deposit_block_timestamp = None
            days_from_first_deposit = None

        self.logger.info(('days_from_first_deposit:', days_from_first_deposit))

        allowed_token = (
            vault_info_current['token0_symbol']
            if vault_info_current['allowed_token'] == 0
            else vault_info_current['token1_symbol'])

        result = {
            'vault': vault_addr,
            'token0': vault_info_current['token0'],
            'token1': vault_info_current['token1'],
            'tvl': vault_info_current['tvl'],
            'token0_symbol': vault_info_current['token0_symbol'],
            'token1_symbol': vault_info_current['token1_symbol'],
            'token0_amount': vault_info_current['token0_amount'],
            'token1_amount': vault_info_current['token1_amount'],
            'allowed_token': allowed_token,
            'allowed_token_n': vault_info_current['allowed_token'],
            'deployment_block_number': deployed_block_number,
            'deployment_block_timestamp': deployed_block_timestamp,
            'first_deposit_block_number': first_deposit_block_number,
            'first_deposit_block_timestamp': first_deposit_block_timestamp,
            'days_since_first_deposit': days_from_first_deposit,
            'days_since_deployment': days_since_deployment,
        }

        if first_deposit_block_number is None or first_deposit_block_timestamp is None:
            return result

        first_deposit_date = datetime.fromtimestamp(first_deposit_block_timestamp).date()
        current_block_date = self.context.block_number.timestamp_datetime.date()

        # Fill in result
        self.logger.info(('vault', vault_addr, first_deposit_block_number))

        df_cashflow = self.context.run_model(
            'ichi.vault-cashflow',
            {"address": input.address, 'use_model_result': True},
            return_type=Records).to_dataframe()

        vault_info_first_deposit = self.context.run_model(
            'ichi.vault-info', {"address": vault_addr}, block_number=first_deposit_block_number)

        result['vault_token_ratio_current'] = vault_info_current['vault_token_ratio']
        result['vault_token_ratio_start'] = vault_info_first_deposit['vault_token_ratio']

        result['return_rate'] = self.irr_return(vault_info_first_deposit,
                                                vault_info_current,
                                                days_from_first_deposit,
                                                first_deposit_date,
                                                current_block_date)
        if not df_cashflow.empty:
            result['irr_cashflow'], result['irr_cashflow_non_zero'] = self.irr_cashflow(vault_ichi,
                                                                                        df_cashflow,
                                                                                        start_block=first_deposit_block_number,
                                                                                        end_block=self.context.block_number,
                                                                                        vault_info=vault_info_current)
        else:
            result['irr_cashflow'], result['irr_cashflow_non_zero'] = None, None

        result['qty_hold'], result['qty_vault'] = self.qty_hold_and_vault(
            vault_info_first_deposit, vault_info_current, input.base)

        # result['irr_hold_5050'] = self.irr_return_hold_5050(vault_info_first_deposit, vault_info_current, days_from_first_deposit)
        # result['qty_hold_5050'] = self.qty_hold_5050(vault_info_first_deposit, vault_info_current, input.base)
        # result['irr_uniswap'] = self.irr_return_uniswap(vault_info_first_deposit, vault_info_current, days_from_first_deposit)

        # result['value_hold'], result['value_vault'] = self.value_hold_and_vault(vault_info_first_deposit, vault_info_current, input.base)
        # result['value_uniswap'] = self.calc_uniswap_value(vault_info_first_deposit, vault_info_current, input.base)
        # result['value_uniswap_lp'] = self.calc_uniswap_lp(vault_info_first_deposit, vault_info_current, input.base)

        for days in input.days_horizon:
            past_block_result = self.context.run_model(
                'chain.get-block', {'timestamp': self.context.block_number.timestamp - 60 * 60 * 24 * days})

            past_block = past_block_result['block_number']
            past_block_timestamp = past_block_result['block_timestamp']
            past_block_date = datetime.fromtimestamp(past_block_timestamp).date()

            if past_block > first_deposit_block_number:
                vault_info_past = self.context.run_model(
                    'ichi.vault-info', {"address": vault_addr}, block_number=past_block)
            else:
                result[f'return_rate_{days}'] = None
                result[f'irr_cashflow_{days}'] = None
                result[f'vault_token_ratio_{days}'] = None
                continue

            result[f'vault_token_ratio_{days}'] = vault_info_past['vault_token_ratio']
            result[f'return_rate_{days}'] = self.irr_return(
                vault_info_past, vault_info_current, days, past_block_date, current_block_date)
            result[f'irr_cashflow_{days}'], result[f'irr_cashflow_non_zero_{days}'] = \
                self.irr_cashflow(vault_ichi,
                                  df_cashflow,
                                  start_block=past_block,
                                  end_block=self.context.block_number,
                                  vault_info=vault_info_current)

            _, result[f'qty_vault_{days}'] = self.qty_hold_and_vault(
                vault_info_past, vault_info_current, input.base)

        return result

# credmark-dev run ichi.vaults-performance -i '{"days_horizon":[7, 30, 60, 90]}' -c 137 --api_url=http://localhost:8700 -j


@Model.describe(slug='ichi.vaults-performance',
                version='0.33',
                display_name='ICHI vaults performance on a chain',
                description='Get the vault performance from ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=IchiPerformanceInput,
                output=dict)
class IchiVaultsPerformance(Model):
    def run(self, input: IchiPerformanceInput) -> dict:
        vaults_all = self.context.run_model('ichi.vaults', {})['vaults']

        model_inputs = [{"address": vault_addr, "days_horizon": input.days_horizon, "base": input.base}
                        for vault_addr in vaults_all.keys()]

        def _use_for(_model_inputs):
            result = []
            # Change to a compose model to run
            for model_input in _model_inputs:
                self.logger.info((model_input['address'], "to run"))
                result.append(self.context.run_model(
                    'ichi.vault-performance', model_input))
                self.logger.info((model_input['address'], result))
            return result

        def _use_compose(_model_inputs):
            all_vault_infos_results = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': 'ichi.vault-performance',
                       'modelInputs': _model_inputs},
                return_type=MapInputsOutput[IchiVaultPerformanceInput, dict])

            all_vault_infos = []
            for vault_result in all_vault_infos_results:
                if vault_result.output is not None:
                    all_vault_infos.append(vault_result.output)
                elif vault_result.error is not None:
                    self.logger.error(vault_result.error)
                    raise create_instance_from_error_dict(
                        vault_result.error.dict())
                else:
                    raise ModelRunError(
                        'compose.map-inputs: output/error cannot be both None')
            return all_vault_infos

        try:
            results = _use_compose(model_inputs)
        except (ModelRunError, ModelEngineError) as err:
            if '429 Client Error: Too Many Requests for url' in err.data.message:
                results = _use_for(model_inputs)
            else:
                raise err

        if len(model_inputs) != len(results):
            results = _use_for(model_inputs)

        return {'data': results}
