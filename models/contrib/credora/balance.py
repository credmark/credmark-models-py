from typing import cast

from credmark.cmf.model import CachePolicy, Model
from credmark.cmf.model.errors import ModelDataError, ModelEngineError
from credmark.cmf.types import Account, Network, NetworkDict
from credmark.cmf.types.compose import MapInputsOutput


class CredoraBalancesInput(Account):
    zapper_api_key: str | None


@Model.describe(
    slug='contrib.credora-balances',
    version='1.0',
    display_name='Balances for credora',
    category='account',
    input=CredoraBalancesInput,
    output=dict,
    cache=CachePolicy.SKIP)
class CredoraBalances(Model):
    @property
    def apps(self) -> list[str]:
        return NetworkDict(list, {
            Network.Mainnet: ["lido", "vesper", "uniswap-v3", "synthetix", "sushiswap", "curve",
                              "aave-v2", "aave-safety-module", "compound", "angle",
                              "sushiswap-bentobox", "rari", "keeper", "goldfinch", "fixed-forex",
                              "convex-frax", "convex", "abracadabra", "impermax", "dfx", "rook",
                              "one-inch", "olympus", "morpho", "tokemak", "lyra-avalon", "gro",
                              "pendle", "frax-lend", "stake-dao", "ribbon-v2", "llamapay",
                              "balancer-v1", "rari-fuse", "illuvium", "blur", "unsheth",
                              "stargate", "aura", "uniswap-v2", "truefi", "saddle", "iron-bank",
                              "polygon-staking", "notional-finance", "across", "balancer-v2",
                              "powerpool", "yearn", "universe", "harvest", "homora-v2"],
            Network.ArbitrumOne: ["arbitrum-airdrop", "gmx", "aave-v3", "solid-lizard", "mycelium",
                                  "lyra-avalon", "radiant-capital", "radiant-v2", "camelot",
                                  "chronos", "curve", "dopex", "uniswap-v3", "balancer-v2"],
            Network.Avalanche: ["multichain", "aave-v3", "trader-joe", "gmx", "benqi",
                                "aave-v2", "nereus-finance", "platypus-finance", "vector-finance",
                                "trader-joe-v2", "trader-joe-banker", "stargate", "iron-bank",
                                "curve"],
            Network.BSC: ["radiant-v2", "belt", "venus", "openleverage"],
            Network.Fantom: ["geist", "hector-network", "curve", "reaper"],
            Network.Optimism: ["aave-v3", "synthetix", "velodrome", "synapse", "gamma-strategies",
                               "hidden-hand", "reaper", "aelin"],
            Network.Polygon: ["meshswap", "aave-v2", "stargate", "sushiswap",
                              "dfyn", "klima", "aave-v3", "uniswap-v3", "metavault-trade"]
        })[self.context.network]

    def run(self, input: CredoraBalancesInput) -> dict:
        model_slug = 'contrib.credora-balance'
        model_inputs = [{'address': input.address, 'zapper_api_key': input.zapper_api_key,
                         'app_id': app} for app in self.apps]

        apps_results = self.context.run_model(
            slug='compose.map-inputs',
            input={'modelSlug': model_slug,
                   'modelInputs': model_inputs},
            return_type=MapInputsOutput[CredoraBalanceInput, dict])

        result = {}
        for app_result in apps_results:
            app_input = cast(CredoraBalanceInput, app_result.input)
            app = app_input.app_id
            if app_result.error is not None:
                result[app] = None
            else:
                result[app] = app_result.output

        return result


class CredoraBalanceInput(Account):
    app_id: str
    zapper_api_key: str | None


@Model.describe(
    slug='contrib.credora-balance',
    version='1.0',
    display_name='App balance for credora',
    category='account',
    input=CredoraBalanceInput,
    output=dict,
    cache=CachePolicy.SKIP)
class CredoraBalance(Model):
    @property
    def zapper_network(self):
        zapper_networks = NetworkDict(str, {
            Network.Mainnet: 'ethereum',
            Network.Polygon: 'polygon',
            Network.Optimism: 'optimism',
            Network.BSC: 'binance-smart-chain',
            Network.Fantom: 'fantom',
            Network.Avalanche: 'avalanche',
            Network.ArbitrumOne: 'arbitrum'
        })

        zapper_network = zapper_networks[self.context.network]
        if not zapper_network:
            raise ModelDataError('Unsupported network')
        return zapper_network

    def run(self, input: CredoraBalanceInput) -> dict:
        app = input.app_id
        result = {}

        try:
            if app == 'tokens':
                model_input = {'address': input.address,
                               'include_curve_positions': False, 'with_price': False}
                result = self.context.run_model('account.portfolio', model_input)
                positions = result['positions']
                return {'src': 'credmark', 'positions': positions}
            if app == 'curve':
                model_input = {'address': input.address}
                result = self.context.run_model('curve.lp', model_input)
                positions = result['positions']
                return {'src': 'credmark', 'positions': positions}
            if app == 'uniswap-v3':
                model_input = {'lp': input.address}
                result = self.context.run_model('uniswap-v3.lp', model_input)
                positions = result['positions']
                return {'src': 'credmark', 'positions': positions}
        except (ModelDataError, ModelEngineError):
            pass

        model_input = {'apiKey': input.zapper_api_key, 'networks': [self.zapper_network],
                       'addresses': [input.address], 'appId': input.app_id}
        result = self.context.run_model('zapper.app-balances', model_input)
        products = result['balances'][input.address.lower()]['products']
        positions = []
        for product in products:
            positions.extend(product['assets'])

        return {'src': 'zapper', 'positions': positions}
