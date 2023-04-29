# pylint: disable= line-too-long

from typing import List, Optional

import numpy as np
import numpy_financial as npf
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.model.errors import (
    ModelEngineError,
    ModelRunError,
    create_instance_from_error_dict,
)
from credmark.cmf.types import Address, Contract, Token
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, DTOField, EmptyInput
from requests.exceptions import HTTPError

from models.credmark.protocols.dexes.uniswap.univ3_math import tick_to_price
from models.tmp_abi_lookup import ICHI_VAULT, ICHI_VAULT_FACTORY, UNISWAP_V3_POOL_ABI
from models.utils.model_run import get_latest_run


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
                version='0.6',
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
            prev_result = {'vaults': {}}

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
            self.logger.info('Use by_range=10_000')
            vault_created = pd.DataFrame(vault_factory.fetch_events(
                vault_factory.events.ICHIVaultCreated,
                from_block=max(
                    from_block + 1,
                    deployed_info['deployed_block_number']),
                by_range=10_000))
            # 25_697_834 for vault_factory

        vault_info = prev_result | {'prev_block': from_block}
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


@Model.describe(slug='ichi.vault-info',
                version='0.9',
                display_name='ICHI vault info',
                description='Get the value of vault token for an ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=Contract,
                output=dict)
class IchiVaultInfo(Model):
    def run(self, input: Contract) -> dict:
        latest_run = get_latest_run(self.context, self.slug, self.version)
        if latest_run is not None:
            prev_block = int(latest_run['blockNumber'])
            prev_result = latest_run['result']
            if prev_block == self.context.block_number:
                return prev_result
        else:
            prev_block = None
            prev_result = {}

        # prev_block = None

        vault_addr = input.address
        vault_ichi = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
        vault_pool_addr = Address(vault_ichi.functions.pool().call())
        vault_pool = Contract(vault_pool_addr).set_abi(
            UNISWAP_V3_POOL_ABI, set_loaded=True)

        allow_token0 = vault_ichi.functions.allowToken0().call()
        allow_token1 = vault_ichi.functions.allowToken1().call()

        assert not (allow_token0 and allow_token1) and (
            allow_token0 or allow_token1)

        if prev_block is None:
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
        else:
            token0_decimals = prev_result['token0_decimals']
            token1_decimals = prev_result['token1_decimals']
            token0_address_checksum = prev_result['token0']
            token1_address_checksum = prev_result['token1']
            token0_symbol = prev_result['token0_symbol']
            token1_symbol = prev_result['token1_symbol']

        scale_multiplier = 10 ** (token0_decimals - token1_decimals)

        current_tick = vault_ichi.functions.currentTick().call()
        sqrtPriceX96 = vault_pool.functions.slot0().call()[0]

        _tick_price0 = tick_to_price(current_tick) * scale_multiplier
        _ratio_price0 = sqrtPriceX96 * sqrtPriceX96 / \
            (2 ** 192) * scale_multiplier

        # value of ichi vault token at a block
        total_supply = vault_ichi.total_supply
        total_supply_scaled = vault_ichi.total_supply_scaled
        token0_amount, token1_amount = vault_ichi.functions.getTotalAmounts().call()
        token0_amount = token0_amount / (10 ** token0_decimals)
        token1_amount = token1_amount / (10 ** token1_decimals)

        if allow_token0:
            token1_in_token0_amount = token1_amount / _tick_price0
            total_amount_in_token = token0_amount + token1_in_token0_amount
        else:
            token0_in_token1_amount = token0_amount * _tick_price0
            total_amount_in_token = token1_amount + token0_in_token1_amount

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
            'token0_symbol': token0_symbol,
            'token1_symbol': token1_symbol,
            'allowed_token': 0 if allow_token0 else 1,
            'token0_amount': token0_amount,
            'token1_amount': token1_amount,
            'total_amount_in_token': total_amount_in_token,
            'total_supply_scaled': total_supply_scaled,
            'vault_token_ratio': total_amount_in_token * 10 ** (token0_decimals if allow_token0 else token1_decimals) / total_supply,
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
            'prev_block': prev_block,
        }


@Model.describe(slug='ichi.vault-info-full',
                version='0.4',
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
    prev_block: Optional[int] = DTOField(
        None, description='Result from previous block number')


@Model.describe(slug='ichi.vault-first-deposit',
                version='0.3',
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
            return latest_run['result'] | {'prev_block': latest_run['blockNumber']}

        vault_addr = input.address
        vault_ichi = Token(vault_addr).set_abi(abi=ICHI_VAULT, set_loaded=True)
        try:
            df_first_deposit = pd.DataFrame(vault_ichi.fetch_events(
                vault_ichi.events.Deposit, from_block=0))
        except HTTPError:
            deployed_info = self.context.run_model('token.deployment', {
                "address": input.address, "ignore_proxy": True})
            try:
                df_first_deposit = pd.DataFrame(vault_ichi.fetch_events(
                    vault_ichi.events.Deposit, from_block=deployed_info['deployed_block_number'], by_range=10_000))
            except ValueError:
                try:
                    df_first_deposit = pd.DataFrame(vault_ichi.fetch_events(
                        vault_ichi.events.Deposit, from_block=deployed_info['deployed_block_number'], by_range=1_000))
                except ValueError:
                    try:
                        df_first_deposit = pd.DataFrame(vault_ichi.fetch_events(
                            vault_ichi.events.Transfer, from_block=deployed_info['deployed_block_number'], by_range=10_000))
                    except ValueError:
                        try:
                            df_first_deposit = pd.DataFrame(vault_ichi.fetch_events(
                                vault_ichi.events.Transfer, from_block=deployed_info['deployed_block_number'], by_range=1_000))
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
            prev_block=None)


class PerformanceInput(DTO):
    days_horizon: List[int] = DTOField(
        [], description='Time horizon in days')
    base: int = DTOField(1000, description='Base amount to calculate value')


class VaultPerformanceInput(Contract, PerformanceInput):
    pass
# credmark-dev run ichi.vault-performance -i '{"address": "0x692437de2cAe5addd26CCF6650CaD722d914d974", "days_horizon":[7, 30, 60]}' -c 137 --api_url=http://localhost:8700 -j


@Model.describe(slug='ichi.vault-performance',
                version='0.21',
                display_name='ICHI vault performance',
                description='Get the vault performance from ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=VaultPerformanceInput,
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

    def calc_irr(self, vault_info_past, vault_info_current, days):
        past_value, current_value = \
            vault_info_past['vault_token_ratio'], vault_info_current['vault_token_ratio']

        irr = npf.irr([-past_value, current_value])

        _cagr_from_irr = np.power(irr + 1, 365 / days) - 1
        _cagr_annualized = np.power(current_value / past_value, 365 / days) - 1

        self.logger.info(('irr', days, _cagr_from_irr, _cagr_annualized))
        return _cagr_from_irr

    def calc_irr_hold_5050(self, vault_info_past, vault_info_current, days):
        p1, p2 = 0.5, 0.5

        past_value = p1 + p2
        if vault_info_current['allowed_token'] == 0:
            current_value = p1 + p2 * \
                vault_info_past['ratio_price0'] / \
                vault_info_current['ratio_price0']
        else:
            current_value = p1 / \
                vault_info_past['ratio_price0'] * \
                vault_info_current['ratio_price0'] + p2

        irr = npf.irr([-past_value, current_value])
        _cagr_from_irr = np.power(irr + 1, 365 / days) - 1
        _cagr_annualized = np.power(current_value / past_value, 365 / days) - 1
        self.logger.info(('irr_hold_5050', days, _cagr_from_irr,
                         _cagr_annualized, past_value, current_value,
                         vault_info_past['ratio_price0'], vault_info_current['ratio_price0']))
        return _cagr_from_irr

    def calc_irr_uniswap(self, vault_info_past, vault_info_current, days):
        if vault_info_current['allowed_token'] == 0:
            token0_amount, token1_amount = 0.5, \
                0.5 * vault_info_past['ratio_price0']
            liquidity = token0_amount * token1_amount
            token0_amount_new = np.sqrt(
                liquidity / vault_info_current['ratio_price0'])
            past_value = 1
            current_value = token0_amount_new * 2
        else:
            token0_amount, token1_amount = \
                0.5 / vault_info_past['ratio_price0'], 0.5
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
        try:
            if vault_info_current['allowed_token'] == 0:
                token0_amount = base / 2 / \
                    vault_info_past['token0_chainlink_price']
                token1_amount = token0_amount * vault_info_past['ratio_price0']
                liquidity = token0_amount * token1_amount
                token0_amount_new = np.sqrt(
                    liquidity / vault_info_current['ratio_price0'])
                _past_value = 1_000
                current_value = token0_amount_new * 2 * \
                    vault_info_current['token0_chainlink_price']
            else:
                token1_amount = base / 2 / \
                    vault_info_past['token1_chainlink_price']
                token0_amount = token1_amount / vault_info_past['ratio_price0']

                liquidity = token0_amount * token1_amount
                token1_amount_new = np.sqrt(
                    liquidity * vault_info_current['ratio_price0'])
                _past_value = 1_000
                current_value = token1_amount_new * 2 * \
                    vault_info_current['token1_chainlink_price']
        except TypeError:
            return None

        self.logger.info(('calc_uniswap_value', current_value))
        return current_value

    def calc_value(self, vault_info_past, vault_info_current, base=1000):
        try:
            if vault_info_current['allowed_token'] == 0:
                value_hold = base / \
                    vault_info_past['token0_chainlink_price'] * \
                    vault_info_current['token0_chainlink_price']
                value_vault = value_hold / \
                    vault_info_past['vault_token_ratio'] * \
                    vault_info_current['vault_token_ratio']
            else:
                value_hold = base / \
                    vault_info_past['token1_chainlink_price'] * \
                    vault_info_current['token1_chainlink_price']
                value_vault = value_hold / \
                    vault_info_past['vault_token_ratio'] * \
                    vault_info_current['vault_token_ratio']
        except TypeError:
            return None, None

        self.logger.info(('calc_value', value_hold, value_vault))
        return value_hold, value_vault

    def run(self, input: VaultPerformanceInput) -> dict:
        vault_addr = input.address
        # _vault_pool_addr = Address(vault_ichi.functions.pool().call())

        deployment = self.context.run_model(
            'token.deployment', {'address': vault_addr, 'ignore_proxy': True})

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
            'irr': None,
            'irr_hold_5050': None,
            'irr_uniswap': None,
            'days_horizon': {},
            'vault_token_ratio': {},
        }

        if first_deposit_block_number is None:
            result['days_horizon'] = {day: None for day in input.days_horizon}
            return result

        self.logger.info(('vault', vault_addr, first_deposit_block_number))
        vault_info_first_deposit = self.context.run_model(
            'ichi.vault-info', {"address": vault_addr}, block_number=first_deposit_block_number)
        result['irr'] = self.calc_irr(
            vault_info_first_deposit, vault_info_current, days_from_first_deposit)
        result['irr_hold_5050'] = self.calc_irr_hold_5050(
            vault_info_first_deposit, vault_info_current, days_from_first_deposit)
        result['irr_uniswap'] = self.calc_irr_uniswap(
            vault_info_first_deposit, vault_info_current, days_from_first_deposit)

        value_uniswap = self.calc_uniswap_value(
            vault_info_first_deposit, vault_info_current, input.base)

        value_hold, value_vault = self.calc_value(
            vault_info_first_deposit, vault_info_current, input.base)

        result['value_hold'] = value_hold
        result['value_vault'] = value_vault
        result['value_uniswap'] = value_uniswap

        result['vault_token_ratio']['current'] = vault_info_current['vault_token_ratio']
        result['vault_token_ratio']['start'] = vault_info_first_deposit['vault_token_ratio']

        for days in input.days_horizon:
            block_past_day = self.context.run_model(
                'chain.get-block', {'timestamp': self.context.block_number.timestamp - 60 * 60 * 24 * days})

            block_past = block_past_day['block_number']
            if block_past > first_deposit_block_number:
                vault_info_past = self.context.run_model(
                    'ichi.vault-info', {"address": vault_addr}, block_number=block_past)
            else:
                result['days_horizon'][days] = None
                result['vault_token_ratio'][days] = None
                continue

            # print(days, vault_info_past['vault_token_ratio'],
            #      vault_info_current['vault_token_ratio'])

            result['vault_token_ratio'][days] = vault_info_past['vault_token_ratio']

            result['days_horizon'][days] = self.calc_irr(
                vault_info_past, vault_info_current, days)

        return result

# credmark-dev run ichi.vaults-performance -i '{"days_horizon":[7, 30, 60, 90]}' -c 137 --api_url=http://localhost:8700 -j


@Model.describe(slug='ichi.vaults-performance',
                version='0.15',
                display_name='ICHI vaults performance on a chain',
                description='Get the vault performance from ICHI vault',
                category='protocol',
                subcategory='ichi',
                input=PerformanceInput,
                output=dict)
class IchiVaultsPerformance(Model):
    def run(self, input: PerformanceInput) -> dict:
        vaults_all = self.context.run_model('ichi.vaults')['vaults']

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
                return_type=MapInputsOutput[VaultPerformanceInput, dict])

            all_vault_infos = []
            for _model_input, vault_result in zip(model_inputs, all_vault_infos_results):
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
