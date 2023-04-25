# pylint: disable= line-too-long, unused-import
import math
import numpy_financial as npf
from typing import List, Optional
import numpy as np
import sys

import pandas as pd
from requests.exceptions import HTTPError

from credmark.cmf.model import Model
from credmark.dto import EmptyInput, DTOField, DTO
from credmark.dto.encoder import json_dumps
from credmark.cmf.model.errors import ModelDataError, ModelRunError, create_instance_from_error_dict
from credmark.cmf.types import (Address, Contract, BlockNumber, Contracts, Price,
                                Some, Token)

from credmark.cmf.types.compose import MapInputsOutput

from models.credmark.protocols.dexes.uniswap.univ3_math import (
    tick_to_price, in_range, out_of_range)
from models.utils.model_run import get_latest_run
from models.tmp_abi_lookup import ICHI_VAULT, ICHI_VAULT_FACTORY, UNISWAP_V3_POOL_ABI

# ICHI Vault
# https://app.ichi.org/vault?token={}',


@Model.describe(slug='ichi.vault-tokens',
                version='0.1',
                display_name='',
                description='The tokens used in ICHI vaults',
                category='protocol',
                subcategory='ichi',
                input=EmptyInput,
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

    def run(self, _: EmptyInput) -> dict:
        result = {}
        for token_addr in self.ICHI_POLYGON_COINS:
            tok = Token(token_addr).as_erc20(set_loaded=True)
            result[Address(token_addr).checksum] = (
                tok.symbol, tok.name, tok.decimals)
        return result


# credmark-dev run ichi.vaults --api_url http://localhost:8700 -c 137

@Model.describe(slug='ichi.vaults',
                version='0.3',
                display_name='',
                description='ICHI vaults',
                category='protocol',
                subcategory='ichi',
                input=EmptyInput,
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

    def run(self, _: EmptyInput) -> dict:
        latest_run = get_latest_run(self.context, self.slug, self.version)
        if latest_run is not None:
            from_block = int(latest_run['blockNumber'])
            prev_result = latest_run['result']
        else:
            from_block = 0
            prev_result = {}

        if from_block == self.context.block_number:
            return prev_result

        vault_factory = Contract(self.VAULT_FACTORY).set_abi(
            ICHI_VAULT_FACTORY, set_loaded=True)

        try:
            vault_created = pd.DataFrame(vault_factory.fetch_events(
                vault_factory.events.ICHIVaultCreated,
                from_block=max(from_block + 1, 0),
                to_block=self.context.block_number))
        except HTTPError:
            deployed_info = self.context.run_model('token.deployment', {
                "address": self.VAULT_FACTORY, "ignore_proxy": True})
            vault_created = pd.DataFrame(vault_factory.fetch_events(
                vault_factory.events.ICHIVaultCreated,
                from_block=max(
                    from_block + 1, deployed_info['deployed_block_number']),
                by_range=10_000))
            # 25_697_834 for vault_factory

        vault_info = prev_result | {}
        if vault_created.empty:
            return vault_info

        ichi_vaults = vault_created.ichiVault.to_list()
        for _n_vault, vault_addr in enumerate(ichi_vaults):
            vault = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
            token0 = Token(vault.functions.token0().call()
                           ).as_erc20(set_loaded=True)
            token1 = Token(vault.functions.token1().call()
                           ).as_erc20(set_loaded=True)

            vault_info[vault_addr] = {
                'owner': vault.functions.owner().call(),
                'pool': vault.functions.pool().call(),
                'token0_symbol': token0.symbol,
                'token1_symbol': token1.symbol,
                'allow_token0': vault.functions.allowToken0().call(),
                'allow_token1': vault.functions.allowToken1().call(),
                'total_supply_scaled': vault.total_supply_scaled,
            }

        return vault_info


@Model.describe(slug='ichi.vault-info',
                version='0.1',
                display_name='ICHI vault info',
                description='Get the value of vault token for an ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=Contract,
                output=dict)
class IchiVaultInfo(Model):
    def run(self, input: Contract) -> dict:
        vault_addr = input.address
        vault_ichi = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
        vault_pool_addr = Address(vault_ichi.functions.pool().call())
        vault_pool = Contract(vault_pool_addr).set_abi(
            UNISWAP_V3_POOL_ABI, set_loaded=True)

        token0_addr = Address(vault_ichi.functions.token0().call())
        token1_addr = Address(vault_ichi.functions.token1().call())
        token0 = Token(token0_addr).as_erc20(set_loaded=True)
        token1 = Token(token1_addr).as_erc20(set_loaded=True)

        allow_token0 = vault_ichi.functions.allowToken0().call()
        allow_token1 = vault_ichi.functions.allowToken1().call()

        assert not (allow_token0 and allow_token1) and (
            allow_token0 or allow_token1)

        scale_multiplier = 10 ** (token0.decimals - token1.decimals)

        current_tick = vault_ichi.functions.currentTick().call()
        sqrtPriceX96 = vault_pool.functions.slot0().call()[0]

        _tick_price0 = tick_to_price(current_tick) * scale_multiplier
        _ratio_price0 = sqrtPriceX96 * sqrtPriceX96 / \
            (2 ** 192) * scale_multiplier

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
            'token0_amount_ratio': token0_amount / total_supply_scaled,
            'token1_amount_ratio': token1_amount / total_supply_scaled,
            'pool_price0': _tick_price0,
            'ratio_price0': _ratio_price0,
        }


@Model.describe(slug='ichi.vault-info-full',
                version='0.1',
                display_name='ICHI vault info (full)',
                description='Get the vault info from ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=Contract,
                output=dict)
class IchiVaultInfoFull(Model):
    def run(self, input: Contract) -> dict:
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
        _ratio_price0 = sqrtPriceX96 * sqrtPriceX96 / \
            (2 ** 192) * scale_multiplier
        # print(f'{tick_price0, ratio_price0=}')

        try:
            token0_chainlink_price = self.context.run_model(
                'price.oracle-chainlink', {'base': token0.address.checksum})['price']
        except ModelRunError:
            token0_chainlink_price = math.nan

        try:
            token1_chainlink_price = self.context.run_model(
                'price.oracle-chainlink', {'base': token1.address.checksum})['price']
        except ModelRunError:
            token1_chainlink_price = math.nan

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
            'token0_price_chainlink': token0_chainlink_price,
            'token1_price_chainlink': token1_chainlink_price,
            'vault_token_value_chainlink': (token0_amount * token0_chainlink_price + token1_amount * token1_chainlink_price) / total_supply_scaled,
        }


# credmark-dev run ichi.vault-first-deposit -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' --api_url http://localhost:8700 -c 137 -j
# credmark-dev run ichi.vault-first-deposit -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974"}' -c 137 -j

class IchiVaultFirstDepositOutput(DTO):
    first_deposit_block_number: Optional[int] = DTOField(
        description='First deposit block number')


@Model.describe(slug='ichi.vault-first-deposit',
                version='0.1',
                display_name='ICHI vault performance',
                description='Get the vault performance from ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=Contract,
                output=IchiVaultFirstDepositOutput)
class IchiVaultFirstDeposit(Model):
    def run(self, input: Contract) -> IchiVaultFirstDepositOutput:
        latest_run = get_latest_run(self.context, self.slug, self.version)
        if latest_run is not None:
            return latest_run['result']

        vault_addr = input.address
        vault_ichi = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
        try:
            first_deposit = vault_ichi.fetch_events(
                vault_ichi.events.Deposit, from_block=0)
        except HTTPError:
            deployed_info = self.context.run_model('token.deployment', {
                "address": input.address, "ignore_proxy": True})
            first_deposit = vault_ichi.fetch_events(
                vault_ichi.events.Deposit, from_block=deployed_info['deployed_block_number'], by_range=10_000)

        df_first_deposit = pd.DataFrame(first_deposit)

        return IchiVaultFirstDepositOutput(
            first_deposit_block_number=None
            if df_first_deposit.empty
            else df_first_deposit.sort_values('blockNumber').iloc[0]['blockNumber'])


class PerformanceInput(DTO):
    time_horizon: List[int] = DTOField(
        [], description='Time horizon in days')


class VaultPerformanceInput(Contract, PerformanceInput):
    pass

# credmark-dev run ichi.vault-performance -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "time_horizon":[7, 30,60]}' -c 137 --api_url=http://localhost:8700 -j


@Model.describe(slug='ichi.vault-performance',
                version='0.5',
                display_name='ICHI vault performance',
                description='Get the vault performance from ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=VaultPerformanceInput,
                output=dict)
class IchiVaultPerformance(Model):
    def calc_irr(self, vault_info_past, vault_info_current, days):
        irr = npf.irr([-vault_info_past['vault_token_ratio'],
                       vault_info_current['vault_token_ratio']])

        _cagr_from_irr = np.power(irr + 1, 365 / days) - 1
        _cagr_annualized = np.power(vault_info_current['vault_token_ratio'] /
                                    vault_info_past['vault_token_ratio'], 365 / days) - 1

        self.logger.info((days, _cagr_from_irr, _cagr_annualized))
        return _cagr_from_irr

    def run(self, input: VaultPerformanceInput) -> dict:
        vault_addr = input.address
        # _vault_pool_addr = Address(vault_ichi.functions.pool().call())

        deployment = self.context.run_model(
            'token.deployment', {'address': vault_addr, 'ignore_proxy': True})

        deployed_block_number = deployment['deployed_block_number']
        deployed_block_timestamp = deployment['deployed_block_timestamp']

        vault_info_current = self.context.run_model(
            'ichi.vault-info', {"address": vault_addr}, block_number=self.context.block_number)
        first_deposit = self.context.run_model(
            'ichi.vault-first-deposit', {'address': vault_addr}, return_type=IchiVaultFirstDepositOutput)
        first_deposit_block_number = first_deposit.first_deposit_block_number

        result = {
            'vault': vault_addr,
            'token0': vault_info_current['token0'],
            'token1': vault_info_current['token1'],
            'token0_symbol': vault_info_current['token0_symbol'],
            'token1_symbol': vault_info_current['token1_symbol'],
            'deployed_block_number': deployed_block_number,
            'deployed_block_timestamp': deployed_block_timestamp,
            'first_deposit_block_number': first_deposit_block_number,
            'days_since_first_deposit': None,
            'irr_since_first_deposit': None,
            'performance': {},
            'vault_token_ratio': {},
        }

        if first_deposit_block_number is None:
            result['performance'] = {day: None for day in input.time_horizon}
            return result

        vault_info_fist_deposit = self.context.run_model(
            'ichi.vault-info', {"address": vault_addr}, block_number=first_deposit_block_number)

        first_deposit_block_timestamp = BlockNumber(
            first_deposit_block_number).timestamp
        days_from_first_deposit = (
            self.context.block_number.timestamp - first_deposit_block_timestamp) / (60 * 60 * 24)
        result['days_since_first_deposit'] = days_from_first_deposit
        result['irr_since_first_deposit'] = self.calc_irr(
            vault_info_fist_deposit, vault_info_current, days_from_first_deposit)
        result['vault_token_ratio'][0] = vault_info_current['vault_token_ratio']
        result['vault_token_ratio'][days_from_first_deposit] = vault_info_fist_deposit['vault_token_ratio']

        # if we hold: 50:50
        # if we uniswap v3

        for days in input.time_horizon:
            block_past_day = self.context.run_model(
                'chain.get-block', {'timestamp': self.context.block_number.timestamp - 60 * 60 * 24 * days})

            block_past = block_past_day['block_number']
            if block_past > first_deposit_block_number:
                vault_info_past = self.context.run_model(
                    'ichi.vault-info', {"address": vault_addr}, block_number=block_past)
            else:
                result['performance'][days] = None
                result['vault_token_ratio'][days] = None
                continue

            # print(days, vault_info_past['vault_token_ratio'],
            #      vault_info_current['vault_token_ratio'])

            result['vault_token_ratio'][days] = vault_info_past['vault_token_ratio']

            result['performance'][days] = self.calc_irr(
                vault_info_past, vault_info_current, days)

        return result


# credmark-dev run ichi.vaults-performance -i '{"time_horizon":[7, 30, 60, 90]}' -c 137 --api_url=http://localhost:8700 -j

@Model.describe(slug='ichi.vaults-performance',
                version='0.1',
                display_name='ICHI vaults performance on a chain',
                description='Get the vault performance from ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=PerformanceInput,
                output=dict)
class IchiVaultsPerformance(Model):
    def run(self, input: PerformanceInput) -> dict:
        vaults_all = self.context.run_model('ichi.vaults')

        def _use_for():
            result = {}
            # Change to a compose model to run
            for vault_addr in vaults_all.keys():
                result[vault_addr] = self.context.run_model(
                    'ichi.vault-performance', {"address": vault_addr, "time_horizon": input.time_horizon})
                print((vault_addr, result[vault_addr]), file=sys.stderr)
            return result

        def _use_compose():
            model_inputs = [{"address": vault_addr, "time_horizon": input.time_horizon}
                            for vault_addr in vaults_all.keys()]
            all_vault_infos_results = self.context.run_model(
                slug='compose.map-inputs',
                input={'modelSlug': 'ichi.vault-performance',
                       'modelInputs': model_inputs},
                return_type=MapInputsOutput[VaultPerformanceInput, dict])

            all_vault_infos = {}
            for model_input, vault_result in zip(model_inputs, all_vault_infos_results):
                if vault_result.output is not None:
                    all_vault_infos[model_input['address']] = vault_result
                elif vault_result.error is not None:
                    self.logger.error(vault_result.error)
                    raise create_instance_from_error_dict(
                        vault_result.error.dict())
                else:
                    raise ModelRunError(
                        'compose.map-inputs: output/error cannot be both None')
            return all_vault_infos

        results = _use_compose()
        return results
