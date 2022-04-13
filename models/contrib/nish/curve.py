from typing import List, Optional
from credmark.cmf.model import Model
from credmark.cmf.types import (
    Address,
    Contract,
    Token
)


# Get token balance of an address on ethereum chain


def ethereum_token_balance_of_address(_contractAddress, _accountAddress):
    '''
            Get token balance of an address method
            Args::
                _contractAddress: Ethereum Address of the token contract
                _accountAddress: Ethereum Address of account whose token balance is to be fetched
                _apiKey: Etherscan API Key
            Returns::
                _name: Name of token
                _balance: Token Balance of Account
    '''

    _contractAddress = Address(_contractAddress).checksum

    _contract = Token(address=_contractAddress)

    _name = _contract.functions.name().call()
    _balance = _contract.functions.balanceOf(_accountAddress).call()
    _decimals = _contract.functions.decimals().call()
    _symbol = _contract.functions.symbol().call()

    _balance = float(_balance)/pow(10, _decimals)

    return (_name, _symbol, _balance)


pool_addresses = ['0xD51a44d3FaE010294C616388b506AcdA1bfAAE46',
                  '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
                  '0xCEAF7747579696A2F0bb206a14210e3c9e6fB269',
                  '0xd632f22692FaC7611d2AA1C0D552930D43CAEd3B',
                  '0x5a6A4D54456819380173272A5E8E9B9904BdF41B',
                  '0x890f4e345B1dAED0367A877a1612f86A1f86985f',
                  '0xEd279fDD11cA84bEef15AF5D39BB4d4bEE23F0cA',
                  '0x752eBeb79963cf0732E9c0fec72a49FD1DEfAEAC',
                  '0x8301AE4fc9c624d1D396cbDAa1ed877821D7C511',
                  '0x45F783CCE6B7FF23B2ab2D70e416cdb7D6055f51',
                  '0x55A8a39bc9694714E2874c1ce77aa1E599461E18',
                  '0xA5407eAE9Ba41422680e2e00537571bcC53efBfD',
                  '0x80466c64868E1ab14a1Ddf27A676C3fcBE638Fe5',
                  '0x1c65bA665ce39cfe85639227eccf17Be2B167058',
                  '0x52EA46506B9CC5Ef470C5bf89f17Dc28bB35D85C']


# Function to catch naming error while fetching mandatory data
def try_or(func, default=None, expected_exc=(Exception,)):
    try:
        return func()
    except expected_exc:
        return default


class CurvePoolInfo(Contract):
    name: str
    address: Address
    A: float
    chi: float
    ratio: float


@Model.describe(slug="contrib.nish-curve-get-pegging-ratio",
                version="1.0",
                display_name="Get pegging ratio for all of Curve's pools",
                description="Get pegging ratio for all of Curve's pools",
                input=dict,
                output=CurvePoolInfo)
class CurveGetPeggingRatio(Model):
    def run(self, input) -> CurvePoolInfo:
        # Converting to CheckSum Address
        # pool = Address(input.address).checksum

        pool = Address(pool_addresses[1]).checksum

        # Pool name
        pool_name = str('None')

        # Amplification Coeffecient A
        A = float(0)

        # Leverage X(chi)
        chi = float(0)

        # Ratio of pegging
        ratio = float(0)

        # Initiating the contract instance
        pool_contract_instance = Contract(address=pool)

        # Fetching A for Pool
        A = pool_contract_instance.functions.A().call()

        # Number of tokens in pool (Initial no. of tokens=2)
        n = 2

        # initiating token counter and fetching balance of each asset in pool
        token0 = pool_contract_instance.functions.coins(0).call()
        token1 = pool_contract_instance.functions.coins(1).call()
        # If third token present
        token2 = try_or(lambda: pool_contract_instance.functions.coins(2).call())
        # If fourth token present
        token3 = try_or(lambda: pool_contract_instance.functions.coins(3).call())

        token0_name, token0_symbol, token0_balance = ethereum_token_balance_of_address(token0, pool)
        token1_name, token1_symbol, token1_balance = ethereum_token_balance_of_address(token1, pool)

        # Pool Name
        pool_name = 'Curve.fi : {}/{}'.format(str(token0_symbol), str(token1_symbol))

        # Calculating D
        D = token0_balance + token1_balance

        # Product of tokens' quantity
        product = token0_balance * token1_balance

        if token2 is None:
            pass
        else:
            token2_name, token2_symbol, token2_balance = ethereum_token_balance_of_address(token2, pool)
            # Updating number of tokens present
            n += 1
            # Updating quantity product
            product *= token2_balance
            # Updating D
            D += token2_balance
            # Updating pool name
            pool_name = pool_name + '/{}'.format(str(token2_symbol))

        if token3 is None:
            pass
        else:
            token3_name, token3_symbol, token3_balance = ethereum_token_balance_of_address(token3, pool)
            # Updating number of tokens present
            n += 1
            # Updating quantity product
            product *= token3_balance
            # Updating D
            D += token3_balance
            # Updating pool name
            pool_name = pool_name + '/{}'.format(str(token3_symbol))

        # Calculating ratio, this gives information about peg
        ratio = product / pow((D/n), n)

        # Calculating 'chi'
        chi = A * ratio

        return CurvePoolInfo(
            address=Address(pool),
            name=pool_name,
            A=A,
            chi=chi,
            ratio=ratio)
