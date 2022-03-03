import sys
import credmark.model

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
        pool_address = input.address.checksum

        tokens = []
        underlying = []
        balances = []
        try:
            pool_contract = self.context.dask_client.get_contract(
                pool_address, SWAP_ABI)
            pool_contract.functions.coins(0).call()
        except Exception:
            pool_contract = self.context.dask_client.get_contract(
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


@credmark.model.describe(slug="curve-fi-all-pool-info-p",
                         version="1.0",
                         display_name="Curve Finance Pool Liqudity",
                         description="The amount of Liquidity for Each Token in a Curve Pool")
class CurveFinanceTotalTokenLiqudity(credmark.model.Model):
    def run(self, input) -> dict:
        pools = self.context.run_model("curve-fi-pools")['result']
        t1 = Task('pool-info', lambda x, pools: CurveFinancePoolInfo(x).run(pools),
                  ([self.context, pools], []))

        cc = CurveFinancePoolInfo(self.context)
        breakpoint()

        t1 = Task('pool-info', lambda p, cc=cc: (load_models(), cc.run(p))[1], ([pools], []))
        t1 = Task('pool-info', lambda p, cc=cc: (load_models(), cc.run(p))[1], ([pools], []))

        t1 = Task('pool-info', lambda x, pools: (load_models(),
                  models.credmark.protocols.curve.curve_finance_p.CurveFinancePoolInfo(x).run(pools))[1], ([self.context, pools], []))

        self.context.dask_client.get_client().submit(lambda x: sys.path, 1)
        self.context.dask_client.get_client().submit(lambda x: load_models(), 1).result()
        self.context.dask_client.get_client().submit(lambda x: test_models(), 1).result()
        breakpoint()
        pool_infos = self.context.run_pipe(Pipe(t1), ['pool-info'])
        breakpoint()
        return {"pools": pool_infos}


@ credmark.model.describe(slug="curve-fi-pools-p",
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
