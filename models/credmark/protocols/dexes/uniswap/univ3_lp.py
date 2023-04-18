# pylint: disable=locally-disabled, unused-import, invalid-name, line-too-long

from typing import List

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import (Address, Contract, Token)
from credmark.cmf.types.compose import MapInputsOutput
from credmark.dto import DTO, DTOField
from models.credmark.protocols.dexes.uniswap.univ3_math import (
    tick_to_price, in_range, out_of_range)
from models.credmark.protocols.dexes.uniswap.constant import (
    V3_POS_NFT, V3_FACTORY_ADDRESS, V3_TICK, V3_POS)
from models.credmark.protocols.dexes.uniswap.types import PositionWithFee
from models.tmp_abi_lookup import UNISWAP_V3_POOL_ABI, UNISWAP_V3_NFT_MANAGER_ABI, UNISWAP_V3_FACTORY_ABI
from web3.exceptions import BadFunctionCallOutput
from web3.exceptions import ContractLogicError


class V3LPInput(DTO):
    lp: Address = DTOField(description='Account')


class V3LPPosition(DTO):
    lp: Address = DTOField(description='Account')
    id: int
    pool: Address
    tokens: List[PositionWithFee]
    in_range: str


class V3LPOutput(DTO):
    lp: Address
    positions: List[V3LPPosition]


def V3NFTManager(_network_id):
    nft_manager = Contract(V3_POS_NFT[_network_id]).set_abi(
        UNISWAP_V3_NFT_MANAGER_ABI, set_loaded=True)
    return nft_manager


@Model.describe(slug='uniswap-v3.lp',
                version='0.2',
                display_name='Uniswap v3 LP Position and Fee for account',
                description='Returns position and Fee for account',
                category='protocol',
                subcategory='uniswap-v3',
                input=V3LPInput,
                output=V3LPOutput)
class UniswapV2LP(Model):
    def run(self, input: V3LPInput) -> V3LPOutput:
        nft_manager = V3NFTManager(self.context.network)

        lp = input.lp
        nft_total = int(nft_manager.functions.balanceOf(lp.checksum).call())
        nft_ids = []
        for nft_n in range(nft_total):
            try:
                nft_ids.append(nft_manager.functions.tokenOfOwnerByIndex(
                    lp.checksum, nft_n).call())
            except BadFunctionCallOutput:
                continue

        def _use_for():
            lp_poses = []
            for nft_id in nft_ids:
                lp_pos = self.context.run_model(
                    'uniswap-v3.id',
                    {'id': nft_id},
                    return_type=V3LPPosition)
                lp_poses.append(lp_pos)
            return lp_poses

        def _use_compose():
            slug = 'uniswap-v3.id'
            model_inputs = {"modelSlug": slug,
                            "modelInputs": [{'id': nft_id}
                                            for nft_id in nft_ids]}

            all_results = self.context.run_model(
                slug='compose.map-inputs',
                input=model_inputs,
                return_type=MapInputsOutput[dict, V3LPPosition])

            lp_poses = [
                obj.output for obj in all_results.results if obj.output is not None]
            return lp_poses

        if len(nft_ids) > 4:
            return V3LPOutput(lp=lp, positions=_use_compose())
        elif len(nft_ids) > 0:
            return V3LPOutput(lp=lp, positions=_use_for())
        else:
            return V3LPOutput(lp=lp, positions=[])


class V3IDInput(DTO):
    id: int = DTOField(gt=0, description='V3 NFT ID')


@Model.describe(slug='uniswap-v3.id',
                version='0.3',
                display_name='Uniswap v3 LP Position and Fee for NFT ID',
                description='Returns position and Fee for NFT ID',
                category='protocol',
                subcategory='uniswap-v3',
                input=V3IDInput,
                output=V3LPPosition)
class UniswapV2LPId(Model):
    # pylint:disable=line-too-long
    def run(self, input: V3IDInput) -> V3LPPosition:
        nft_manager = V3NFTManager(self.context.network)

        nft_id = input.id

        try:
            position = V3_POS(*nft_manager.functions.positions(nft_id).call())
            lp_addr = nft_manager.functions.ownerOf(nft_id).call()
        except ContractLogicError as err:
            if 'execution reverted: Invalid token ID' in err.args[0]:
                raise ModelRunError(
                    f'Invalid token ID: {nft_id} for non-existed or burnt') from err
            raise

        token0_addr = Address(position.token0)
        token1_addr = Address(position.token1)
        token0 = Token(token0_addr).as_erc20(set_loaded=True)
        token1 = Token(token1_addr).as_erc20(set_loaded=True)

        addr = V3_FACTORY_ADDRESS[self.context.network]
        uniswap_factory = Contract(address=addr).set_abi(
            UNISWAP_V3_FACTORY_ABI, set_loaded=True)

        if token0_addr.to_int() < token1_addr.to_int():
            pool_addr = uniswap_factory.functions.getPool(
                token0_addr.checksum, token1_addr.checksum, position.fee).call()
        else:
            pool_addr = uniswap_factory.functions.getPool(
                token1_addr.checksum, token0_addr.checksum, position.fee).call()

        pool = Contract(pool_addr).set_abi(
            abi=UNISWAP_V3_POOL_ABI, set_loaded=True)

        slot0 = pool.functions.slot0().call()
        sqrtPriceX96 = slot0[0]
        current_tick = slot0[1]
        scale_multiplier = 10 ** (token0.decimals - token1.decimals)
        _ratio_price0 = sqrtPriceX96 * sqrtPriceX96 / \
            (2 ** 192) * scale_multiplier
        _price_lower = 1 / \
            (tick_to_price(position.tickLower)) / scale_multiplier
        _price_upper = 1 / \
            (tick_to_price(position.tickUpper)) / scale_multiplier

        sa = tick_to_price(position.tickLower / 2)
        sb = tick_to_price(position.tickUpper / 2)
        sp = tick_to_price(current_tick / 2)

        if position.tickUpper >= current_tick >= position.tickLower:
            a0, a1 = in_range(position.liquidity, sb, sa, sp)
            a0 = token0.scaled(a0)
            a1 = token1.scaled(a1)
            in_range_str = 'in range'
        elif current_tick < position.tickLower:
            a0, a1 = out_of_range(position.liquidity, sb, sa)
            a0 = token0.scaled(a0)
            a1 = 0.0
            in_range_str = 'out of range'
        elif current_tick > position.tickUpper:
            a0, a1 = out_of_range(position.liquidity, sb, sa)
            a0 = 0.0
            a1 = token1.scaled(a1)
            in_range_str = 'out of range'
        else:
            raise ModelRunError(
                '{position.tickUpper=} ?= {current_tick=} ?= {position.tickLower=}')

        ticks_lower = V3_TICK(*pool.functions.ticks(position.tickLower).call())
        ticks_upper = V3_TICK(*pool.functions.ticks(position.tickUpper).call())

        feeGrowthGlobal0X128 = pool.functions.feeGrowthGlobal0X128().call()
        feeGrowthOutside0X128_lower = ticks_lower.feeGrowthOutside0X128
        feeGrowthOutside0X128_upper = ticks_upper.feeGrowthOutside0X128
        feeGrowthInside0LastX128 = position.feeGrowthInside0LastX128

        feeGrowthGlobal1X128 = pool.functions.feeGrowthGlobal1X128().call()
        feeGrowthOutside1X128_lower = ticks_lower.feeGrowthOutside1X128
        feeGrowthOutside1X128_upper = ticks_upper.feeGrowthOutside1X128
        feeGrowthInside1LastX128 = position.feeGrowthInside1LastX128

        if position.tickUpper >= current_tick >= position.tickLower:
            # In whitepaper, uncollected fees = liquidity( feeGrowthGlobal - feeGrowthOutsideLowerTick - feeGrowthOutsideUpperTick - feeGrowthInside)
            # https://ethereum.stackexchange.com/questions/101955/trying-to-make-sense-of-uniswap-v3-fees-feegrowthinside0lastx128-feegrowthglob
            fee_token0 = (feeGrowthGlobal0X128 - feeGrowthOutside0X128_lower -
                          feeGrowthOutside0X128_upper - feeGrowthInside0LastX128)
            fee_token1 = (feeGrowthGlobal1X128 - feeGrowthOutside1X128_lower -
                          feeGrowthOutside1X128_upper - feeGrowthInside1LastX128)
        elif current_tick < position.tickLower:
            fee_token0 = feeGrowthOutside0X128_lower - \
                feeGrowthOutside0X128_upper - feeGrowthInside0LastX128
            fee_token1 = feeGrowthOutside1X128_lower - \
                feeGrowthOutside1X128_upper - feeGrowthInside1LastX128
        elif current_tick > position.tickUpper:
            fee_token0 = feeGrowthOutside0X128_upper - \
                feeGrowthOutside0X128_lower - feeGrowthInside0LastX128
            fee_token1 = feeGrowthOutside1X128_upper - \
                feeGrowthOutside1X128_lower - feeGrowthInside1LastX128
        else:
            raise ModelRunError(
                '{position.tickUpper=} ?= {current_tick=} ?= {position.tickLower=}')

        fee_token0 *= 1/(2**128) * position.liquidity
        fee_token1 *= 1/(2**128) * position.liquidity

        fee_token0 = token0.scaled(fee_token0)
        fee_token1 = token1.scaled(fee_token1)

        return V3LPPosition(lp=lp_addr, id=nft_id, pool=pool_addr,
                            tokens=[PositionWithFee(amount=a0, fee=fee_token0, asset=token0),
                                    PositionWithFee(amount=a1, fee=fee_token1, asset=token1)],
                            in_range=in_range_str)
