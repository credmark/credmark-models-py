import credmark.model
from credmark.types.data import Address

min_erc20_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'


@credmark.model.describe(slug='erc20-balanceOf',
                         version='1.0',
                         display_name='ERC20 balanceOf',
                         description='Get the balance of an ERC20 Token from a wallet address')
class BalanceOf(credmark.model.Model):

    def run(self, input) -> dict:
        wallet_address = '0xbdfa4f4492dd7b7cf211209c4791af8d52bf5c50'
        wallet_address = '0x109B3C39d675A2FF16354E116d080B94d238a7c9'

        cmk_address = '0x68cfb82eacb9f198d508b514d898a403c449533e'
        ether_address = '0xc0829421c1d260bd3cb3e0f06cfe2d52db2ce315'
        conves_fxs_address = '0xfeef77d3f69374f66429c91d732a244f074bdf74'
        usdc_address = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
        usdt_address = '0xdac17f958d2ee523a2206206994597c13d831ec7'
        dai_address = '0x6b175474e89094c44da98b954eedeac495271d0f'

        results = {}
        for token_address in [cmk_address, ether_address, conves_fxs_address, usdc_address, usdt_address, dai_address]:
            contract = self.context.web3.eth.contract(
                address=Address(token_address),
                abi=min_erc20_abi)

            balance = contract.functions.balanceOf(
                Address(wallet_address)).call()

            decimals = contract.functions.decimals().call()

            results[token_address] = {'balanceOf': balance / 10 ** decimals}

        return results
