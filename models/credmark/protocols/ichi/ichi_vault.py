# pylint: disable= line-too-long, too-many-lines, no-name-in-module

import json
from datetime import datetime
from typing import Any, List, Optional

import numpy as np
import numpy_financial as npf
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import (
    ModelDataError,
    ModelEngineError,
    ModelRunError,
    create_instance_from_error_dict,
)
from credmark.cmf.model.models import LookupType, ModelResultInput, ModelResultOutput
from credmark.cmf.types import Address, Contract, Network, Records, Token
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, DTOField, EmptyInput
from pyxirr import xirr
from requests.exceptions import HTTPError

from models.credmark.protocols.dexes.uniswap.univ3_math import tick_to_price
from models.tmp_abi_lookup import ICHI_VAULT, ICHI_VAULT_DEPOSIT_GUARD, ICHI_VAULT_FACTORY, UNISWAP_V3_POOL_ABI

# ICHI Vault
# https://app.ichi.org/vault?token={}',


class EmptyInputWithNetwork(EmptyInput):
    class Config:
        schema_extra = {
            'examples': [{'_test_multi_chain': {'chain_id': 137, 'block_number': None}}],
            'test_multi_chain': True
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


# credmark-dev run ichi.vaults --api_url http://localhost:8700 -c 137

@Model.describe(slug='ichi.vaults',
                version='0.9',
                display_name='',
                description='ICHI vaults',
                category='protocol',
                input=EmptyInputWithNetwork,
                subcategory='ichi',
                output=dict)
class IchiVaults(Model):
    VAULT_FACTORY = '0x2d2c72C4dC71AA32D64e5142e336741131A73fc0'

    ICHI_POLYGON_VAULTS = [
        '0x9ff3C1390300918B40714fD464A39699dDd9Fe00',  # WMATIC-WETH, WMATIC
        '0x692437de2cAe5addd26CCF6650CaD722d914d974',  # LINK-WETH, LINK
        '0x70Aa3c8e256c859e52c0B8C263f763D9051B95e1',  # ICHI-GOVI, GOVI
        '0xf461063819fFBC6e22704aDe1861B0dF3BaC9585',  # WETH-BAL, BAL
        '0xf3De925524cE6bBa606107CFCB2A7A6259CD01EA',  # GHST-WETH, GHST
        '0x711901e4b9136119Fb047ABe8c43D49339f161c3',  # ICHI-USDC, USDC
        '0x3ac9b3db3350A515c702ba19a001d099d4a5F132',  # USDC-WETH, USDC
        '0xf7B1ab2545451b60345FA3aB8C5210d53c703c98',  # CRV-WETH', CRV
        '0xB05bE549a570e430e5ddE4A10a0d34cf09a7df21',  # USDC-WETH, WETH
        '0x74F9d8861D42Ac09759aDE7809A67cF053dc7bA5',  # SUSHI-WETH', SUSHI
        '0xE5bf5D33C617556B91558aAfb7BeadB68E9Cea81',  # ICHI-oneBTC, oneBTC
        '0x5a0834EBaFdF97DB54f45a43290b6B09D4226ec6',  # ICHI-WETH, ICHI
        '0x5394eb43700Ce8fBbF4CB83E8b52ea73b71426B6',  # ICHI-WBTC, ICHI
        '0xac6c0264511EeEC305Da9Afc2e1ABa08409F99f6',  # WMATIC-ICHI, ICHI
        '0xc9C785d61455A44E9281C60D19e97A5Fdd858510',  # ICHI-USDC, ICHI
        '0x8AC3D7cd56816Da9fB45e7640aA70A24884e02f7',  # WETH-DPI, DPI
        '0x4aEF5144131dB95c110af41c8Ec09f46295a7C4B',  # ICHI-WBTC, WBTC
        '0xFc089714519E84B7ce0a4023bfEE0D99F6d767dA',  # WBTC-WETH, WBTC
        '0x21e6910A769d10ef4236107493406a9788C758a3'   # TRADE-USDT', TRADE
    ]

    def run(self, _) -> dict:
        latest_run = self.context.models.get_result(
            self.slug, self.version,
            self.context.__dict__['original_input'],
            LookupType.BACKWARD_LAST_EXCLUDE)

        from_block = 0
        prev_result = {'vaults': {}}
        if latest_run is not None:
            from_block = int(latest_run['blockNumber'])
            prev_result = latest_run['result']
            if from_block == self.context.block_number:
                return prev_result

        vault_factory = Contract(self.VAULT_FACTORY).set_abi(ICHI_VAULT_FACTORY, set_loaded=True)

        try:
            vault_created = pd.DataFrame(vault_factory.fetch_events(
                vault_factory.events.ICHIVaultCreated,
                from_block=0,
                to_block=self.context.block_number))
        except HTTPError:
            deployed_info = self.context.run_model('token.deployment', {
                "address": self.VAULT_FACTORY, "ignore_proxy": True})
            self.logger.info('Use by_range=10_000')
            deployed_block_number = deployed_info['deployed_block_number']
            # 25_697_834 for vault_factory
            vault_created = pd.DataFrame(vault_factory.fetch_events(
                vault_factory.events.ICHIVaultCreated,
                from_block=max(from_block + 1, deployed_block_number),
                by_range=10_000))

        vault_info = prev_result | {'model_result_block': from_block}
        if vault_created.empty:
            return vault_info

        ichi_vaults = vault_created.ichiVault.to_list()
        for _n_vault, vault_addr in enumerate(ichi_vaults):
            vault = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
            token0 = Token(vault.functions.token0().call()
                           ).as_erc20(set_loaded=True)
            token1 = Token(vault.functions.token1().call()
                           ).as_erc20(set_loaded=True)

            vault_info['vaults'][vault_addr] = {  # type: ignore
                'vault': vault_addr,
                'owner': vault.functions.owner().call(),
                'pool': vault.functions.pool().call(),
                'token0_symbol': token0.symbol,
                'token1_symbol': token1.symbol,
                'allow_token0': vault.functions.allowToken0().call(),
                'allow_token1': vault.functions.allowToken1().call(),
                'total_supply_scaled': vault.total_supply_scaled,
            }

        return vault_info


class IchiVaultContract(Contract):
    class Config:
        schema_extra = {
            'examples': [{"address": "0x8ac3d7cd56816da9fb45e7640aa70a24884e02f7", "_test_multi_chain": {'chain_id': 137, 'block_number': None}}],
            'test_multi_chain': True
        }


@Model.describe(slug='ichi.vault-info',
                version='0.14',
                display_name='ICHI vault info',
                description='Get the value of vault token for an ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=IchiVaultContract,
                output=dict)
class IchiVaultInfo(Model):
    def run(self, input: IchiVaultContract) -> dict:
        latest_run = self.context.models.get_result(
            self.slug,
            self.version,
            self.context.__dict__['original_input'],
            LookupType.BACKWARD_LAST_EXCLUDE)
        if latest_run is not None:
            model_result_block = int(latest_run['blockNumber'])
            prev_result = latest_run['result']
        else:
            model_result_block = None
            prev_result = {}

        # model_result_block = None

        vault_addr = input.address
        vault_ichi = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
        vault_pool_addr = Address(vault_ichi.functions.pool().call())
        vault_pool = Contract(vault_pool_addr).set_abi(
            UNISWAP_V3_POOL_ABI, set_loaded=True)

        allow_token0 = vault_ichi.functions.allowToken0().call()
        allow_token1 = vault_ichi.functions.allowToken1().call()

        assert not (allow_token0 and allow_token1) and (
            allow_token0 or allow_token1)

        if model_result_block is None:
            token0_addr = Address(vault_ichi.functions.token0().call())
            token1_addr = Address(vault_ichi.functions.token1().call())
            token0 = Token(token0_addr).as_erc20(set_loaded=True)
            token1 = Token(token1_addr).as_erc20(set_loaded=True)
            self.logger.info(('token0', token0.address))
            token0_decimals = token0.decimals
            token1_decimals = token1.decimals
            token0_address_checksum = token0.address.checksum
            token1_address_checksum = token1.address.checksum
            token0_symbol = token0.symbol
            token1_symbol = token1.symbol
            scale_multiplier = 10 ** (token0_decimals - token1_decimals)
        else:
            token0_decimals = prev_result['token0_decimals']
            token1_decimals = prev_result['token1_decimals']
            token0_address_checksum = prev_result['token0']
            token1_address_checksum = prev_result['token1']
            token0_symbol = prev_result['token0_symbol']
            token1_symbol = prev_result['token1_symbol']
            scale_multiplier = prev_result['scale_multiplier']

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
            'vault_token_ratio': total_amount_in_token_n * amount_scaling / total_supply,
            'token0_amount_ratio': token0_amount / total_supply_scaled,
            'token1_amount_ratio': token1_amount / total_supply_scaled,
            'pool_price0': _tick_price0,
            'ratio_price0': _ratio_price0,
            'tvl': (
                (token0_amount * token0_chainlink_price +
                 token1_amount * token1_chainlink_price)
                if token0_chainlink_price is not None and token1_chainlink_price is not None
                else None),
            'token0_chainlink_price': token0_chainlink_price,
            'token1_chainlink_price': token1_chainlink_price,
            'model_result_block': model_result_block,
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
            'vault_token_ratio': total_amount_in_token / (token0.scaled(1) if allow_token0 else token1.scaled(1)) / total_supply,
            'pool_price0': _tick_price0,
            'ratio_price0': _ratio_price0,
            'token0_chainlink_price': token0_chainlink_price,
            'token1_chainlink_price': token1_chainlink_price,
            'vault_token_value_chainlink': (
                ((token0_amount * token0_chainlink_price + token1_amount *
                 token1_chainlink_price) / total_supply_scaled)
                if token0_chainlink_price is not None and token1_chainlink_price is not None
                else None),
        }


# credmark-dev run ichi.vault-first-deposit -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' --api_url http://localhost:8700 -c 137 -j
# credmark-dev run ichi.vault-first-deposit -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' -c 137 -j

class IchiVaultFirstDepositOutput(DTO):
    first_deposit_block_number: Optional[int] = DTOField(
        description='First deposit block number')
    first_deposit_block_timestamp: Optional[int] = DTOField(
        description='First deposit block timestamp')
    model_result_block: Optional[int] = DTOField(
        None, description='Result from previous block number')


@Model.describe(slug='ichi.vault-first-deposit',
                version='0.5',
                display_name='ICHI vault first deposit',
                description='Get the block_number of the first deposit of an ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=IchiVaultContract,
                output=IchiVaultFirstDepositOutput)
class IchiVaultFirstDeposit(Model):
    def run(self, input: IchiVaultContract) -> IchiVaultFirstDepositOutput:
        latest_run = self.context.models.get_result(
            self.slug,
            self.version,
            self.context.__dict__['original_input'],
            LookupType.BACKWARD_LAST_EXCLUDE)
        if latest_run is not None:
            return latest_run['result'] | {'model_result_block': latest_run['blockNumber']}

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

        first_deposit_block_number = (
            None if df_first_deposit.empty
            else int(df_first_deposit.sort_values('blockNumber').iloc[0]['blockNumber']))
        first_deposit_block_timestamp = (
            None
            if first_deposit_block_number is None
            else self.context.web3.eth.get_block(first_deposit_block_number).get('timestamp', None))

        return IchiVaultFirstDepositOutput(
            first_deposit_block_number=first_deposit_block_number,
            first_deposit_block_timestamp=first_deposit_block_timestamp,
            model_result_block=self.context.block_number)


class ContractEventsInput(Contract, ModelResultInput):
    event_name: str = DTOField(description='Event name')
    event_abi: Optional[Any] = DTOField(None, description='ABI of the event')

    class Config:
        schema_extra = {
            'examples': [{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974",
                          "event_name": "Deposit",
                          "event_abi": [{"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": True, "internalType": "address", "name": "to", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "shares", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Deposit", "type": "event"}],
                          '_test_multi_chain': {'chain_id': 137, 'block_number': 40100090}}],
            'test_multi_chain': True
        }


class ContractEventsOutput(ModelResultOutput):
    records: Records = DTOField(description='Vault cashflow records')


@Model.describe(slug='contract.events',
                version='0.8',
                display_name='Events from contract (non-mainnet)',
                description='Get the past events from a contract',
                category='contract',
                subcategory='event',
                input=ContractEventsInput,
                output=ContractEventsOutput)
class ContractEvents(Model):
    def run(self, input: ContractEventsInput) -> ContractEventsOutput:
        if self.context.chain_id == 1:
            raise ModelDataError('This model is not available on mainnet')

        start_block = 0
        prev_result = pd.DataFrame()

        if input.use_model_result:
            forward_first_run = self.context.models.get_result(
                self.slug,
                self.version,
                self.context.__dict__['original_input'],
                LookupType.FORWARD_FIRST)

            if forward_first_run is not None:
                _current_block = int(self.context.block_number)
                prev_result = (Records(**forward_first_run['result']['records']).to_dataframe())
                if not prev_result.empty:
                    prev_result = prev_result.query('blockNumber <= @_current_block')
                return ContractEventsOutput(
                    records=Records.from_dataframe(prev_result),
                    model_result_block=forward_first_run['blockNumber'],
                    model_result_direction=LookupType.FORWARD_FIRST.value)

            backward_last_run = self.context.models.get_result(
                self.slug,
                self.version,
                self.context.__dict__['original_input'],
                LookupType.BACKWARD_LAST_EXCLUDE)
            if backward_last_run is not None:
                start_block = int(backward_last_run['blockNumber'])
                prev_result = Records(**backward_last_run['result']['records']).to_dataframe()

        self.logger.info(f'[{self.slug}] Fetching {input.event_name} events from {input.address} '
                         f'from block {start_block} on {self.context.block_number}')

        if input.event_abi is not None:
            input_contract = Contract(input.address).set_abi(input.event_abi, set_loaded=True)
        else:
            input_contract = Contract(input.address)

        try:
            deployment = self.context.run_model(
                'token.deployment', {'address': input_contract.address, 'ignore_proxy': True})
        except ModelDataError as err:
            if err.data.message.endswith('is not an EOA account'):
                return ContractEventsOutput(
                    records=Records.from_dataframe(pd.DataFrame()),
                    model_result_block=start_block,
                    model_result_direction=LookupType.BACKWARD_LAST.value
                )
            raise
        deployed_block_number = deployment['deployed_block_number']

        try:
            df_events = (pd.DataFrame(input_contract.fetch_events(
                input_contract.events[input.event_name],
                from_block=max(deployed_block_number, start_block+1),
                to_block=int(self.context.block_number),
                contract_address=input_contract.address.checksum)))
        except HTTPError:
            df_events = (pd.DataFrame(input_contract.fetch_events(
                input_contract.events[input.event_name],
                from_block=max(deployed_block_number, start_block+1),
                to_block=int(self.context.block_number),
                contract_address=input_contract.address.checksum,
                by_range=10_000)))
            self.logger.info('Use by_range=10_000')

        self.logger.info(
            f'[{self.slug}] Finished fetching event {input.event_name} from {max(deployed_block_number, start_block+1)} '
            f'to {int(self.context.block_number)} on {datetime.now()}')

        if not df_events.empty:
            df_events = (df_events.drop('args', axis=1)
                         .assign(transactionHash=lambda r: r.transactionHash.apply(lambda x: x.hex()),
                                 blockHash=lambda r: r.blockHash.apply(lambda x: x.hex())))
            df_comb = (pd.concat([prev_result, df_events], ignore_index=True)
                       .sort_values(['blockNumber', 'transactionIndex', 'logIndex'])
                       .reset_index(drop=True))
        else:
            df_comb = prev_result

        return ContractEventsOutput(
            records=Records.from_dataframe(df_comb),
            model_result_block=start_block,
            model_result_direction=LookupType.BACKWARD_LAST.value
        )


class IchiVaultContractWithUseModelResult(IchiVaultContract, ModelResultInput):
    pass

# credmark-dev run ichi.vault-cashflow -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' -c 137 --api_url=http://localhost:8700 -j -b 42454582
# credmark-dev run ichi.vault-cashflow -i '{"address": "0x711901e4b9136119Fb047ABe8c43D49339f161c3"}' -c 137 --api_url=http://localhost:8700 -j -b 41675859


@Model.describe(slug='ichi.vault-cashflow',
                version='0.21',
                display_name='ICHI vault cashflow',
                description='Get the past deposit and withdraw events of an ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=IchiVaultContractWithUseModelResult,
                output=Records)
class IchiVaultCashflow(Model):
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
                                event_abi=deposit_forwarded_event_abi, use_model_result=False),
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

    def run(self, input: IchiVaultContractWithUseModelResult) -> Records:
        _prev_result_block = 0
        prev_result = pd.DataFrame()

        if input.use_model_result:
            forward_first_run = self.context.models.get_result(
                self.slug,
                self.version,
                self.context.__dict__['original_input'],
                LookupType.FORWARD_FIRST)

            if forward_first_run is not None:
                _current_block = int(self.context.block_number)
                prev_result = (Records(**forward_first_run['result']).to_dataframe())
                if not prev_result.empty:
                    prev_result = prev_result.query('block_number <= @_current_block')
                return Records.from_dataframe(prev_result)

            backward_last_run = self.context.models.get_result(
                self.slug,
                self.version,
                self.context.__dict__['original_input'],
                LookupType.BACKWARD_LAST_EXCLUDE)
            if backward_last_run is not None:
                _prev_result_block = int(backward_last_run['blockNumber']) + 1
                prev_result = Records(**backward_last_run['result']).to_dataframe()

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
                                event_abi=deposit_event_abi, use_model_result=True),
            return_type=ContractEventsOutput).records.to_dataframe()

        df_withdraw = self.context.run_model(
            'contract.events',
            ContractEventsInput(address=input.address, event_name='Withdraw',
                                event_abi=withdraw_event_abi, use_model_result=True),
            return_type=ContractEventsOutput).records.to_dataframe()

        if not df_deposit.empty:
            df_deposit = (df_deposit
                          .loc[:, ['blockNumber', 'transactionIndex', 'logIndex', 'event', 'shares', 'amount0', 'amount1', 'to']]
                          .assign(shares=lambda df: df.shares.apply(int) / (10 ** vault_ichi_decimals),
                                  amount0=lambda df: df.amount0.apply(int) / (10 ** token0_decimals),
                                  amount1=lambda df: df.amount1.apply(int) / (10 ** token1_decimals)))

        if not df_withdraw.empty:
            df_withdraw = (df_withdraw
                           .loc[:, ['blockNumber', 'transactionIndex', 'logIndex', 'event', 'shares', 'amount0', 'amount1', 'to']]
                           .assign(shares=lambda df: -(df.shares.apply(int) / (10 ** vault_ichi_decimals)),
                                   amount0=lambda df: -(df.amount0.apply(int) / (10 ** token0_decimals)),
                                   amount1=lambda df: -(df.amount1.apply(int) / (10 ** token1_decimals))))

        # fetch results
        df_comb = pd.concat([df_deposit, df_withdraw], ignore_index=True)

        self.logger.info(f'[{self.slug}] Deposit/Withdraw events: {len(df_comb)}={len(df_deposit)}+{len(df_withdraw)}')

        if df_comb.empty:
            return Records.from_dataframe(prev_result)

        self.logger.info(f'Using {_prev_result_block=}')
        df_comb = (df_comb
                   .query('blockNumber >= @_prev_result_block')
                   .sort_values(['blockNumber', 'transactionIndex', 'logIndex'])
                   .reset_index(drop=True))

        df_cash_flow = pd.DataFrame()
        if not df_comb.empty:
            cash_flow = []
            for n_row, row in df_comb.iterrows():
                past_block_number = row['blockNumber']
                token0_amount = row['amount0']
                token1_amount = row['amount1']

                with self.context.enter(past_block_number) as past_context:
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
                            .assign(timestamp_date=lambda df: df.timestamp_datetime.dt.date))

        df_cash_flow_comb = pd.concat([prev_result, df_cash_flow], ignore_index=True)

        return Records.from_dataframe(df_cash_flow_comb)


class IchiPerformanceInput(DTO):
    days_horizon: List[int] = DTOField(
        [], description='Time horizon in days')
    base: int = DTOField(1000, description='Base amount to calculate value')

    class Config:
        schema_extra = {
            'examples': [{"days_horizon": [7],
                          "base": 1000,
                          "_test_multi_chain": {'chain_id': 137, 'block_number': None}}],
            'test_multi_chain': True
        }


class IchiVaultPerformanceInput(IchiVaultContract, IchiPerformanceInput):
    class Config:
        schema_extra = {
            'examples': [{"address": "0x8ac3d7cd56816da9fb45e7640aa70a24884e02f7",
                          "days_horizon": [7],
                          "base": 1000,
                          "_test_multi_chain": {'chain_id': 137, 'block_number': None}}],
            'test_multi_chain': True
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
                version='0.38',
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
            token0_amount, token1_amount, total_amount_in_token_n = -token0_amount, -token1_amount, -total_amount_in_token_n

        return ((context.block_number, context.block_number.timestamp, context.block_number.timestamp_datetime, event_name,
                 allow_token0, current_tick, 0,
                 token0_amount, token1_amount, total_amount_in_token_n,
                 event_name, context.block_number.timestamp_datetime.date()))

    def irr_return(self, vault_info_past, vault_info_current, days, past_block_date, current_block_date):
        """
        IRR of the vault, derived from the exchange ratio between vault token to deposit/withdraw tokens
        """
        past_value, current_value = vault_info_past['vault_token_ratio'], vault_info_current['vault_token_ratio']

        irr = npf.irr([-past_value, current_value])

        _cagr_from_irr = np.power(irr + 1, 365 / days) - 1
        _cagr_annualized = np.power(current_value / past_value, 365 / days) - 1

        irr2 = xirr([past_block_date, current_block_date], [-past_value, current_value])

        irr_return = current_value / past_value - 1

        self.logger.info(('irr_return', days, irr_return, irr, irr2, _cagr_from_irr, _cagr_annualized))

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

        self.logger.info(f'Trimmed df_cashflow from {df_cashflow.shape[0]} to {df_cashflow_trim.shape[0]}')
        if df_cashflow_trim.block_number.isin([start_block]).any():
            with self.context.enter(start_block - 1) as cc:
                df_row_start_block = pd.DataFrame(
                    [self.vault_current(cc, vault_ichi, scale_multiplier, token0_decimals,
                                        token1_decimals, allow_token0, 'Start', make_negative=True)],
                    columns=df_cashflow_trim.columns)
        else:
            with self.context.enter(start_block) as cc:
                df_row_start_block = pd.DataFrame(
                    [self.vault_current(cc, vault_ichi, scale_multiplier, token0_decimals,
                                        token1_decimals, allow_token0, 'Start', make_negative=True)],
                    columns=df_cashflow_trim.columns)

        with self.context.enter(end_block) as cc:
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

        irr = xirr(df_cashflow_comb.timestamp_date.to_list(),
                   (df_cashflow_comb.total_amount_in_token_n).to_list())

        irr_non_zero = xirr(df_cashflow_comb_non_zero.timestamp_date.to_list(),
                            df_cashflow_comb_non_zero.total_amount_in_token_n.to_list())
        return irr, irr_non_zero

    def qty_hold_and_vault(self, vault_info_past, vault_info_current, base=1000):
        """
        Quantity of hold and vault
        """

        try:
            if vault_info_current['allowed_token'] == 0:
                qty_hold = base
                qty_vault = qty_hold / vault_info_past['vault_token_ratio'] * \
                    vault_info_current['vault_token_ratio']
            else:
                qty_hold = base
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
            current_value = p1 + p2 * vault_info_past['ratio_price0'] / vault_info_current['ratio_price0']
        else:
            current_value = p1 / vault_info_past['ratio_price0'] * vault_info_current['ratio_price0'] + p2

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
                current_token_value = token0_amount_new * vault_info_current['token0_chainlink_price']
                make_up_token_value = (token1_amount_new - token1_amount) * vault_info_current['token1_chainlink_price']
                current_value = current_token_value + make_up_token_value
            else:
                token1_amount = base / vault_info_past['token1_chainlink_price']
                token0_amount = token1_amount / vault_info_past['ratio_price0']
                liquidity = token0_amount * token1_amount

                token0_amount_new = np.sqrt(liquidity / vault_info_current['ratio_price0'])
                token1_amount_new = np.sqrt(liquidity * vault_info_current['ratio_price0'])
                current_token_value = token1_amount_new * vault_info_current['token1_chainlink_price']
                make_up_token_value = (token0_amount_new - token0_amount) * vault_info_current['token0_chainlink_price']
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

        deployment = self.context.run_model('token.deployment', {'address': vault_addr, 'ignore_proxy': True})

        deployed_block_number = deployment['deployed_block_number']
        deployed_block_timestamp = deployment['deployed_block_timestamp']
        days_since_deployment = (
            self.context.block_number.timestamp - deployed_block_timestamp) / (60 * 60 * 24)

        vault_info_current = self.context.run_model(
            'ichi.vault-info', {"address": vault_addr}, block_number=self.context.block_number)
        first_deposit = self.context.run_model(
            'ichi.vault-first-deposit', {'address': vault_addr}, return_type=IchiVaultFirstDepositOutput)
        first_deposit_block_number = first_deposit.first_deposit_block_number
        first_deposit_block_timestamp = first_deposit.first_deposit_block_timestamp

        if first_deposit_block_timestamp is not None:
            days_from_first_deposit = (
                self.context.block_number.timestamp - first_deposit_block_timestamp) / (60 * 60 * 24)
        else:
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

        result['return_rate'] = self.irr_return(vault_info_first_deposit, vault_info_current,
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
                version='0.32',
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

        def _use_for():
            result = []
            # Change to a compose model to run
            for model_input in model_inputs:
                result.append(self.context.run_model(
                    'ichi.vault-performance', model_input))
                self.logger.info((model_input['address'], result))
            return result

        def _use_compose():
            all_vault_infos_results = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': 'ichi.vault-performance',
                       'modelInputs': model_inputs},
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
            results = _use_compose()
        except ModelEngineError as err:
            if err.data.message.startswith('429 Client Error: Too Many Requests for url'):
                results = _use_for()
            else:
                raise err

        return {'data': results}
