from datetime import datetime, timedelta, timezone, date
from typing import Tuple
from models.tmp_abi_lookup import ABRACADABRA_CAULDRON_ABI
from credmark.cmf.model import Model
from credmark.cmf.types import (
    Address,
    Contract,
    Token,
)
from credmark.dto import (
    DTO,
    EmptyInput,
)


# Get token balance of an address on ethereum chain
def ethereum_token_balance_of_address(contract_address, account_address):
    '''
            Get token balance of an address method
            Args::
                contract_address: Ethereum Address of the token contract
                account_address: Ethereum Address of account whose token balance is to be fetched
                _apiKey: Etherscan API Key
            Returns::
                _name: Name of token
                _balance: Token Balance of Account
    '''

    contract_address = Address(contract_address).checksum

    _contract = Token(address=contract_address)

    _name = _contract.functions.name().call()
    _balance = _contract.functions.balanceOf(account_address).call()
    _decimals = _contract.functions.decimals().call()
    _symbol = _contract.functions.symbol().call()

    _balance = float(_balance)/pow(10, _decimals)

    return (_name, _symbol, _balance)



## Vaults' addresses on ethereum chain
BENTOBOX_ADDRESS_ETH = Address("0xF5BCE5077908a1b7370B9ae04AdC565EBd643966").checksum
DEGENBOX_ADDRESS_ETH = Address("0xd96f48665a1410C0cd669A88898ecA36B9Fc2cce").checksum



# Contract address of various markets of abracadabra

## Ethereum Active Markets
ethereum_active_markets = {
    "yvDAI": "0x7ce7d9ed62b9a6c5ace1c6ec9aeb115fa3064757",
    "ALCX": "0x7b7473a76D6ae86CE19f7352A1E89F6C9dc39020",
    "yvCVXETH": "0xf179fe36a36B32a4644587B8cdee7A23af98ed37",
    "FTM": "0x05500e2Ee779329698DF35760bEdcAAC046e7C27",
    "wsOHM": "0x003d5A75d284824Af736df51933be522DE9Eed0f",
    "xSUSHI": "0x98a84EfF6e008c5ed0289655CcdCa899bcb6B99F",
    "yvcrvIB": "0xEBfDe87310dc22404d918058FAa4D56DC4E93f0A",
    "yvstETH": "0x0BCa8ebcB26502b013493Bf8fE53aA2B1ED401C1",
    "yvWETH v2": "0x920D9BD936Da4eAFb5E25c6bDC9f6CB528953F9f",
    "cvxtricrypto2": "0x4EAeD76C3A388f4a841E9c765560BBe7B3E4B3A0",
    "SHIB": "0x252dCf1B621Cc53bc22C256255d2bE5C8c32EaE4",
    "cvxrenCrv": "0x35a0Dd182E4bCa59d5931eae13D0A2332fA30321",
    "ALGD": "0xc1879bf24917ebE531FbAA20b0D05Da027B592ce",
    "FTT": "0x9617b633EF905860D919b88E1d9d9a6191795341",
    "SPELL": "0xCfc571f3203756319c231d3Bc643Cee807E74636",
    "sSPELL": "0x3410297D89dCDAf4072B805EFc1ef701Bb3dd9BF",
    "cvx3pool(non deprecated)": "0x257101F20cB7243E2c7129773eD5dBBcef8B34E0",
    "WETH": "0x390Db10e65b5ab920C19149C919D970ad9d18A41",
    "WBTC": "0x5ec47EE69BEde0b6C2A2fC0D9d094dF16C192498",
    # Deprecated Markets
    "UST v2": "0x59e9082e068ddb27fc5ef1690f9a9f22b32e573f",
    "yvUSDC v2": "0x6cbAFEE1FaB76cA5B5e144c43B3B50d42b7C8c8f",
    "yvUSDT v2": "0x551a7CfF4de931F32893c928bBc3D25bF1Fc5147",
    "yvWETH": "0x6Ff9061bB8f97d948942cEF376d98b51fA38B91f",
    "xSUSHI(deprecated)": "0xbb02A884621FB8F5BFd263A67F58B65df5b090f3",
    "sSPELL(deprecated)": "0xC319EEa1e792577C319723b5e60a15dA3857E7da",
    "yvYFI": "0xFFbF4892822e0d552CFF317F65e1eE7b5D3d9aE6",
    "cvx3pool (old)": "0x806e16ec797c69afa8590A55723CE4CC1b54050E",
    "cvx3pool (new)": "0x6371EfE5CD6e3d2d7C477935b7669401143b7985",
    "UST": "0xbc36fde44a7fd8f545d459452ef9539d7a14dd63",
}



class AbracadabraTVLOutput(DTO):
    balances : dict
    tvl : float


# Fetching Collateral of each market of abracadabra on ethereum chain
@Model.describe(slug="contrib.abracadabra-tvl",
                version="1.0",
                display_name="Get TVL for abracadabra",
                description="Get TVL for abracadabra",
                input=EmptyInput,
                output=AbracadabraTVLOutput)
class AbracadabraGetTVL(Model):
    def run(self, input) -> AbracadabraTVLOutput:

        # Dict of coin balances
        balances = {}
        # Total Value Locked
        tvl = float(0)
        # Keys of ethereum_active_markets
        ethereum_active_markets_keys = list(ethereum_active_markets.keys())

        # Looping through all the ethereum active markets to fetch token balance
        for key in ethereum_active_markets_keys:
            # Contract address of market
            market_address = Address(ethereum_active_markets[key]).checksum

            # Contract Instance
            market_contract = Contract(address=market_address, abi=ABRACADABRA_CAULDRON_ABI)

            # Contract address of collateral
            collateral = Address(market_contract.functions.collateral().call()).checksum

            # Balance of BENTOBOX
            _name, _symbol, bento_balance = ethereum_token_balance_of_address(
                                                        contract_address = collateral,
                                                        account_address = BENTOBOX_ADDRESS_ETH)
            # Balance OF DEGENBOX
            _name, _symbol, degen_balance = ethereum_token_balance_of_address(
                                                        contract_address = collateral,
                                                        account_address = DEGENBOX_ADDRESS_ETH)
            # Total Balance
            _balance = bento_balance + degen_balance
            # Token Price
            _price = self.context.run_model(
                                slug = 'token.price',
                                input = Token(address=collateral)
                            )['price']
            if _price is None:
                _price = 0

            # Updating balances of vaults
            balances.update({ key : [_symbol, _balance, _price]})
            # Updating TVL
            tvl += _balance * _price

        return AbracadabraTVLOutput(
            balances = balances,
            tvl = tvl
        )


class AbracadabraHistoricalInput(DTO):
    date_range: Tuple[date, date]

@Model.describe(slug="contrib.abracadabra-tvl-historical",
                version="1.0",
                display_name="Get TVL for abracadabra",
                description="Get TVL for abracadabra",
                input=AbracadabraHistoricalInput,
                output=dict)
class AbracadabraGetTVLHistorical(Model):
    def run(self, input: Tuple) -> dict:
        d_start, d_end = input.date_range
        if d_start > d_end:
            d_start, d_end = d_end, d_start

        dt_start = datetime.combine(d_start, datetime.max.time(), tzinfo=timezone.utc)
        dt_end = datetime.combine(d_end, datetime.max.time(), tzinfo=timezone.utc)

        interval = (dt_end - dt_start).days + 1
        window = f'{interval} days'
        interval = '1 day'

        # TODO: add two days to the end as work-around to current start-end-window
        ts_as_of_end_dt = self.context.block_number.from_timestamp(
            ((dt_end + timedelta(days=2)).timestamp())).timestamp

        output = self.context.historical.run_model_historical(
            model_slug='contrib.abracadabra-tvl',
            model_input={},
            model_return_type=AbracadabraTVLOutput,
            window=window,
            interval=interval,
            end_timestamp=ts_as_of_end_dt)

        return output
