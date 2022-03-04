import sys
import credmark.model
from datetime import datetime

from credmark.types import Address
from credmark.types.dto import DTO, DTOField
from credmark.model import Task, ModelTask, Pipe, get_worker, get_client

from models.tmp_abi_lookup import SWAP_ABI, SWAP_AB2, CURVE_REGISTRY_ADDRESS, CURVE_REGISTRY_ABI


class PoolAddress(DTO):
    address: Address = DTOField(..., description='Address of Pool')


@credmark.model.describe(slug="curve-fi-pool-info-p",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool",
                         input=PoolAddress)
class CurveFinancePoolInfo(credmark.model.Model):
    def run(self, input: PoolAddress) -> dict:
        pool_address = input.address

        tokens = []
        underlying = []
        balances = []
        try:
            pool_contract = self.context.dask_utils.get_contract(
                pool_address, SWAP_ABI)
            pool_contract.functions.coins(0).call()
        except Exception:
            pool_contract = self.context.dask_utils.get_contract(
                pool_address, SWAP_ABI)

        for i in range(0, 8):
            try:
                tok = pool_contract.functions.coins(i).call()
                bal = pool_contract.functions.balances(i).call()
                try:
                    und = pool_contract.functions.underlying_coins(i).call()
                    underlying.append(und)
                except Exception:
                    pass
                balances.append(bal)
                tokens.append(tok)
            except Exception:
                break

        virtual_price = pool_contract.functions.get_virtual_price().call()
        a = pool_contract.functions.A().call()

        return {
            "swap_contract_address": pool_address,
            "virtualPrice": virtual_price,
            "tokens": tokens,
            "balances": balances,
            "underlying": underlying,
            "A": a,
        }


def load_models():
    import models
    import models.credmark.protocols.curve.curve_finance_p
    import credmark.model
    return models.__name__, models.credmark.protocols.curve.curve_finance_p.__name__, credmark.model.__name__


def test_models():
    return models.__name__, models.credmark.protocols.curve.curve_finance_p.__name__

# python test\test.py run -b 14000000 -i '{}' --dask='tcp://localhost:8786' curve-fi-all-pool-info-p
# credmark-dev run curve-fi-all-pool-info -b 14234904 --api_url=http://localhost:8700/v1/models/run -i '{"address":"0x06364f10B501e868329afBc005b3492902d6C763"}'
# python test\test.py run curve-fi-all-pool-info-p -b 14234904 --api_url=http://localhost:8700/v1/models/run -i '{"address":"0x06364f10B501e868329afBc005b3492902d6C763"}' --dask='tcp://localhost:8786'


def do_multiple_address(model, pools):
    client = model.context.dask_utils.get_client()
    fs = client.map(model.run, [PoolAddress(address=Address(addr))
                    for addr in pools['result']])
    res = client.gather(fs)
    return res


@credmark.model.describe(slug="curve-fi-all-pool-info-p",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool")
class CurveFinanceTotalTokenLiqudity(credmark.model.Model):
    def run(self, input) -> dict:
        start_time = datetime.now()

        curve_pools = CurveFinancePools(self.context)
        curve_pool_info = CurveFinancePoolInfo(self.context)

        t0 = Task('pools', curve_pools.run, ([{}], []))
        t1 = Task('pool-info', do_multiple_address, ([curve_pool_info], [t0]))
        p = Pipe(t0, t1)
        result = self.context.run_pipe(p, ['pool-info'])

        print(datetime.now() - start_time)
        return {'result': result['pool-info']}


@credmark.model.describe(slug="curve-fi-pools-p",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool")
class CurveFinancePools(credmark.model.Model):

    def run(self, input) -> dict:
        registry = self.context.web3.eth.contract(
            address=Address(CURVE_REGISTRY_ADDRESS).checksum,
            abi=CURVE_REGISTRY_ABI)

        total_pools = registry.functions.pool_count().call()
        pool_addresses = []
        for i in range(0, total_pools):
            pool_addresses.append(registry.functions.pool_list(i).call())
        return {'result': pool_addresses}
