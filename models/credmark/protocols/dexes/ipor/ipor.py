# pylint: disable=too-many-lines, unsubscriptable-object, line-too-long
from collections import namedtuple
from typing import Any, Generator, NamedTuple

from credmark.cmf.model import Model
from credmark.cmf.model.errors import ModelRunError
from credmark.cmf.types import (
    Address,
    BlockNumber,
    Contract,
    Contracts,
    Network,
    Token,
)
from credmark.dto import DTO, DTOField
from eth_abi.abi import encode_abi
from eth_typing.evm import ChecksumAddress


@Model.describe(slug='ipor.get-oracle-and-calculator',
                version='0.1',
                display_name='IPOR Oracle and Calculator',
                description='The Oracle and Calculator for IPOR index',
                category='protocol',
                subcategory='ipor',
                output=Contracts)
class IPOROracle(Model):
    IPOR_ORACLE = {
        Network.Mainnet: '0x421C69EAa54646294Db30026aeE80D01988a6876'

    }

    IPOR_CALCULATOR = {
        Network.Mainnet: '0x9D4BD8CB9DA419A9cA1343A5340eD4Ce07E85140'

    }

    def run(self, _) -> Contracts:
        return Contracts(contracts=[Contract(address=self.IPOR_ORACLE[self.context.network]),
                                    Contract(address=self.IPOR_CALCULATOR[self.context.network]), ]
                         )


# pd.DataFrame(cc.fetch_events(cc.proxy_for.events.IporIndexUpdate, from_block=0, contract_address=cc.address))


IPORIndexValue = namedtuple(
    'IPORIndexValue',
    "indexValue ibtPrice exponentialMovingAverage exponentialWeightedMovingVariance lastUpdateTimestamp")


@Model.describe(slug='ipor.get-index',
                version='0.2',
                display_name='IPOR Index',
                description='The IPOR Index from publication and per block',
                category='protocol',
                subcategory='ipor',
                output=dict)
class IPORIndex(Model):
    # IPOR_ASSETS holds the block number of the last update
    IPOR_ASSETS = {
        Network.Mainnet: [
            (999_999_999, ['USDC', 'USDT', 'DAI'])
        ]
    }

    def run(self, _) -> dict:
        assets = None
        for last_block_number, asset_list in self.IPOR_ASSETS[self.context.network]:
            assets = asset_list
            if self.context.block_number <= last_block_number:
                break

        if assets is None:
            raise ModelRunError('No IPOR assets found')

        # TODO: we can replace above with the following to use the IporIndexAddAsset, IporIndexRemoveAsset to know the assets
        # pd.DataFrame(cc.fetch_events(cc.proxy_for.events.IporIndexAddAsset, from_block=0, contract_address=cc.address)) # ('address', ...)
        # pd.DataFrame(cc.fetch_events(cc.proxy_for.events.IporIndexRemoveAsset, from_block=0, contract_address=cc.address)) # 'address'

        oracle, calculator = self.context.run_model(
            'ipor.get-oracle-and-calculator', {}, return_type=Contracts)

        index_collectors = {}

        for asset_symbol in assets:
            asset = Token(symbol=asset_symbol)
            is_asset_supported = oracle.functions.isAssetSupported(
                asset.address.checksum).call()
            assert is_asset_supported, f'Asset {asset_symbol} is not supported by IPOR on {self.context.block_number}'

            # ipor_index.ibtPrice was the last published.
            index = IPORIndexValue(
                *(oracle.functions.getIndex(asset.address.checksum).call()))._asdict()

            ipor_current = calculator.functions.calculateIpor(
                asset.address.checksum).call()

            # We need ibtPrice_current from getAccruedIndex() or calculateAccruedIbtPrice(). Both are the same.
            # oracle.functions.getAccruedIndex(self.context.block_number.timestamp, asset).call()
            ibtPrice_current = oracle.functions.calculateAccruedIbtPrice(
                asset.address.checksum, self.context.block_number.timestamp).call()

            index['indexValue_scaled'] = index['indexValue'] / 1e18
            index['ibtPrice_scaled'] = index['ibtPrice'] / 1e18
            index['exponentialMovingAverage_scaled'] = index['exponentialMovingAverage'] / 1e18
            index['exponentialWeightedMovingVariance_scaled'] = index['exponentialWeightedMovingVariance'] / 1e18

            index['blockTimestampDifference'] = self.context.block_number.timestamp - index['lastUpdateTimestamp']
            index['index_current'] = ipor_current
            index['index_current_scaled'] = ipor_current / 1e18
            index['ibtPrice_current'] = ibtPrice_current
            index['ibtPrice_current_scaled'] = ibtPrice_current / 1e18
            index['address'] = asset.address.checksum
            index_collectors[asset.address] = index

        # getAccruedIndex(uint256, calcTimestamp, address asset)
        # It returns the structure with
        # - the most recent IPOR value
        # - exponential moving average
        # - exponential moving variance
        # - IBT as calculated to the current timestamp. Change in IBT is made based on the recently published IPOR

        # calculateAccruedIbtPrice(address asset, uint256 calcTimestamp)
        # For a given asset it calculates the current value of IBT considering the time passed from the last IPOR publication.

        return index_collectors


@Model.describe(slug='ipor.get-lp-exchange',
                version='0.2',
                display_name='IPOR LP token exchange rate',
                description='The ratio between LP Token exchange rate and the underlying assets',
                category='protocol',
                subcategory='ipor',
                output=dict)
class IPORLpExchange(Model):
    IPOR_JOSEPH = {
        Network.Mainnet: [
            (999_999_999, [
                '0x086d4daab14741b195deE65aFF050ba184B65045',  # Joseph DAI
                '0xC52569b5A349A7055E9192dBdd271F1Bd8133277',  # Joseph USDC
                '0x33C5A44fd6E76Fc2b50a9187CfeaC336A74324AC',  # Joseph USDT
            ])
        ]
    }

    def run(self, _) -> dict:
        josephs = None
        for last_block_number, joseph_list in self.IPOR_JOSEPH[self.context.network]:
            josephs = joseph_list
            if self.context.block_number <= last_block_number:
                break

        if josephs is None:
            raise ModelRunError('No IPOR Joseph found')

        exchange_rates = {}

        for address in josephs:
            joseph = Contract(address=address)
            asset = Token(joseph.functions.getAsset().call())
            lp_token = Token(joseph.functions.getIpToken().call())
            exchange_rate = joseph.functions.calculateExchangeRate().call() / 1e18
            exchange_rates[lp_token.address] = {
                'exchangeRate': exchange_rate,
                'asset': asset.address.checksum,
            }

        return exchange_rates

# Pricing a swap
# https://ipor-labs.notion.site/The-IPOR-Automated-Market-Maker-AMM-2d1e187f699d4ce7a5d00dfc1b52b194
# https://ipor-labs.notion.site/Estimating-Fair-Value-of-IPOR-SWAPs-a3f27ff952564934913c59119564a6d8
# https://ipor-labs.notion.site/The-Fair-Price-of-IPOR-SWAPs-via-Longstaff-Schwartz-b319eb6bbb9d4dbd834a2018704438ca
# https://ipor-labs.notion.site/Simulating-DeFi-Interest-Rate-Swap-trades-with-Hawkes-Process-and-Synthetic-data-ebffce62f7fe4e19961604b10ea94391

# Quote_{leg}(t) = r_t = f_leg(\sigma^2, r_t - \theta)
# f_leg(x, y) = max(B_1^{leg} + V_1 x + M_1 y, B_2 + V_2 x + M_2 y)

# collateral, leverage, notional = collateral * leverage, asset, max_payoff, 2 * collateral.


class IporSwapMemory(NamedTuple):
    id: int
    buyer: ChecksumAddress
    openTimestamp: int
    endTimestamp: int
    idsIndex: int
    collateral: int
    notional: int
    ibtQuantity: int
    fixedInterestRate: int
    liquidationDepositAmount: int
    state: int

    def encode_abi(self) -> bytes:
        return encode_abi(
            [
                "(uint256,address,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)"
            ],
            [tuple(self)],
        )

    def __iter__(self) -> Generator[Any, None, None]:
        yield self.id
        yield self.buyer
        yield self.openTimestamp
        yield self.endTimestamp
        yield self.idsIndex
        yield self.collateral
        yield self.notional
        yield self.ibtQuantity
        yield self.fixedInterestRate
        yield self.liquidationDepositAmount
        yield self.state


class IPORSwapInput(DTO):
    timestamp: int
    notional: int
    leverage: int = DTOField(default=10)
    asset: Address

    class Config:
        schema_extra = {
            'example': {"timestamp": 1676688179,
                        "asset": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                        "notional": 1000000}
        }


@Model.describe(slug='ipor.get-swap',
                version='0.3',
                display_name='IPOR LP token exchange rate',
                description='Calculate the fair price of an IPOR swap',
                category='protocol',
                subcategory='ipor',
                input=IPORSwapInput,
                output=dict)
class IPORSwap(Model):
    IPOR_MILTONS = {
        Network.Mainnet: [
            (999_999_999, [
                # AMM (Milton) DAI
                '0xEd7d74AA7eB1f12F83dA36DFaC1de2257b4e7523',
                # AMM (Milton) USDC
                '0x137000352B4ed784e8fa8815d225c713AB2e7Dc9',
                # AMM (Milton) USDT
                '0x28BC58e600eF718B9E97d294098abecb8c96b687',
            ])
        ]
    }

    def run(self, input: IPORSwapInput) -> dict:
        """
        struct IporSwapMemory {
            /// @notice Swap's unique ID
            uint256 id;
            /// @notice Swap's buyer
            address buyer;
            /// @notice Swap opening epoch timestamp
            uint256 openTimestamp;
            /// @notice Swap's collateral
            /// @dev value represented in 18 decimals
            uint256 collateral;
            /// @notice Swap's notional amount
            /// @dev value represented in 18 decimals
            uint256 notional;
            /// @notice Swap's notional amount denominated in the Interest Bearing Token (IBT)
            /// @dev value represented in 18 decimals
            uint256 ibtQuantity;
            /// @notice Fixed interest rate at which the position has been opened
            /// @dev value represented in 18 decimals
            uint256 fixedInterestRate;
            /// @notice Liquidation deposit amount
            /// @dev value represented in 18 decimals
            uint256 liquidationDepositAmount;
            /// @notice State of the swap
            /// @dev 0 - INACTIVE, 1 - ACTIVE
            uint256 state;
        }

        # Block 16652629 @ 1676688179
        credmark-dev run ipor.get-swap -b 16652629 -i '{"timestamp":1676688179, "asset": "0x6B175474E89094C44Da98b954EedeAC495271d0F", "notional": 1000000}' -j
        swap1 = IporSwapMemory(1,
                               Address('0x90ce434bA83442Dfe639d0E47fed6b96B61ba1fc').checksum,
                               1676688179,
                               1679107379,
                               0,
                               1450495049504950495050,
                               725247524752475247525000,
                               725247524752475247525000 * int(1e18) // ibtPrice_current,  # 718510097558899043537076
                               int(ipor_index.indexValue) + int(spreadPayFixed),  # 23870746852871384,
                               25000000000000000000,
                               1)

        # Block 16639079 @ 1676523767
        credmark-dev run ipor.get-swap -b 16639079 -i '{"timestamp":1676523767, "asset": "0x6B175474E89094C44Da98b954EedeAC495271d0F", "notional": 1000000}' -j
        swap2 = IporSwapMemory(230,
                               Address('0x7A62D6cF2517aF31032a947FFDD8A385B45C80Ce').checksum,
                               1676523767,
                               1678942967,
                               4,
                               1000000000000000000000,
                               500000000000000000000000,
                               500000000000000000000000 * int(1e18) // ibtPrice_current,  # 495415511598920822787404,
                               int(ipor_index.indexValue) + int(spreadPayFixed),  # 23834396957475357,
                               25000000000000000000,
                               1)

        milton_storage = Contract(milton.functions.getMiltonStorage().call())
        # milton_storage.functions.getSwapPayFixed(230).call()
        # milton_storage.functions.getSwapReceiveFixed(230).call()

        [calculateSoap method Response]
        soapPayFixed   int256: -401278664769285539099
        soapReceiveFixed   int256: -15215288042699434908
        soap   int256: -416493952811984974008
        """

        miltons = None
        for last_block_number, milton_list in self.IPOR_MILTONS[self.context.network]:
            miltons = milton_list
            if self.context.block_number <= last_block_number:
                break

        if miltons is None:
            raise ModelRunError(
                f'No IPOR milton found for {input.asset} for {self.context.block_number}')

        milton_addr = None
        for milton_address in miltons:
            try_milton = Contract(address=milton_address)
            try_asset = try_milton.functions.getAsset().call()
            if try_asset == Address(input.asset).checksum:
                milton_addr = try_milton.address
                break

        if milton_addr is None:
            raise ModelRunError(f'No IPOR milton found for {input.asset}')

        asset = Token(input.asset)

        prev_block_number = BlockNumber.from_timestamp(input.timestamp)

        def _use_call(asset, prev_block_number, milton_addr):
            default_block = self.context.web3.eth.default_block
            self.context.web3.eth.default_block = prev_block_number
            milton = Contract(milton_addr)
            spreadPayFixed, spreadReceiveFixed = milton.functions.calculateSpread().call()
            oracle = Contract(milton.functions.getIporOracle().call())
            ipor_index = IPORIndexValue(
                *oracle.functions.getIndex(input.asset.checksum).call())
            ibtPrice_current = oracle.functions.calculateAccruedIbtPrice(
                asset.address.checksum, BlockNumber(prev_block_number).timestamp).call()
            self.context.web3.eth.default_block = default_block
            return spreadPayFixed, spreadReceiveFixed, ipor_index, ibtPrice_current

        # Alternative way to get the index value
        def _use_model(asset, prev_block_number, milton_addr):
            default_block = self.context.web3.eth.default_block
            milton = Contract(milton_addr)
            self.context.web3.eth.default_block = prev_block_number
            spreadPayFixed, spreadReceiveFixed = milton.functions.calculateSpread().call()
            self.context.web3.eth.default_block = default_block

            ipor_index_for_asset = self.context.run_model(
                'ipor.get-index', {}, block_number=prev_block_number)[asset.address]
            ibtPrice_current = ipor_index_for_asset['ibtPrice_current']
            ipor_index = IPORIndexValue(
                **{f: ipor_index_for_asset[f] for f in IPORIndexValue._fields})
            return spreadPayFixed, spreadReceiveFixed, ipor_index, ibtPrice_current

        milton = Contract(milton_addr)
        oracle = Contract(milton.functions.getIporOracle().call())
        ipor_index_current = IPORIndexValue(
            *oracle.functions.getIndex(input.asset.checksum).call())
        spreadPayFixed_current, spreadReceiveFixed_current = milton.functions.calculateSpread().call()

        spreadPayFixed, spreadReceiveFixed, ipor_index, ibtPrice_current = _use_call(
            asset, prev_block_number, milton_addr)

        owner = milton.functions.owner().call()

        swap3 = IporSwapMemory(
            id=0,
            buyer=owner,
            openTimestamp=self.context.block_number.timestamp,
            endTimestamp=self.context.block_number.timestamp + 60 * 60 * 24 * 28,
            idsIndex=0,
            collateral=input.notional * int(1e18),
            notional=input.notional * int(1e18) * input.leverage,
            ibtQuantity=input.notional *
            int(1e18) * 10 * int(1e18) // ibtPrice_current,
            fixedInterestRate=int(ipor_index.indexValue) + int(spreadPayFixed),
            liquidationDepositAmount=25000000000000000000,
            state=1
        )

        swap4 = IporSwapMemory(
            id=0,
            buyer=owner,
            openTimestamp=self.context.block_number.timestamp,
            endTimestamp=self.context.block_number.timestamp + 60 * 60 * 24 * 28,
            idsIndex=0,
            collateral=input.notional * int(1e18),
            notional=input.notional * int(1e18) * input.leverage,
            ibtQuantity=input.notional *
            int(1e18) * 10 * int(1e18) // ibtPrice_current,
            fixedInterestRate=int(ipor_index.indexValue) +
            int(spreadReceiveFixed),
            liquidationDepositAmount=25000000000000000000,
            state=1
        )

        payFixedPayoff = milton.functions.calculatePayoffPayFixed(
            tuple(swap3)).call()
        self.logger.info(
            f'Pay Fixed {swap3.fixedInterestRate}, Receive Floating (then {ipor_index.indexValue}, now {ipor_index_current.indexValue}) = {payFixedPayoff}')

        receiveFixedPayoff = milton.functions.calculatePayoffReceiveFixed(
            tuple(swap4)).call()
        self.logger.info(
            f'Receive Fixed {swap3.fixedInterestRate}, Pay Floating (then {ipor_index.indexValue}, now {ipor_index_current.indexValue}) = {receiveFixedPayoff}')

        return {
            'notional': input.notional,
            'leverage': input.leverage,
            'iporIndex_inception': ipor_index.indexValue / 1e18,
            'iporIndex_current': ipor_index_current.indexValue / 1e18,
            'spreadPayFixed_inception': spreadPayFixed / 1e18,
            'spreadReceiveFixed_inception': spreadReceiveFixed / 1e18,
            'spreadPayFixed_current': spreadPayFixed_current / 1e18,
            'spreadReceiveFixed_current': spreadReceiveFixed_current / 1e18,
            'payFixedRate': swap3.fixedInterestRate / 1e18,
            'receiveFixedRate': swap4.fixedInterestRate / 1e18,
            'payFixedPayoff': payFixedPayoff / 1e18,
            'receiveFixedPayoff': receiveFixedPayoff / 1e18,
        }
