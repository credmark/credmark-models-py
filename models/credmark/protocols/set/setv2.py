# pylint: disable=line-too-long, protected-access

import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.types import Address, Contract, Network
from credmark.dto import DTO

from models.credmark.chain.contract import ContractEventsInput, ContractEventsOutput


class SetV2ModulesOutput(DTO):
    basic_issuance: Contract
    streaming_fee: Contract
    debt_issuance: Contract


@Model.describe(slug='set-v2.modules',
                version='0.1',
                display_name='SetV2 modules',
                description='The contracts for SetV2',
                category='protocol',
                subcategory='set-v2',
                output=SetV2ModulesOutput)
class SetV2Modules(Model):
    Basic_Issuance = {
        Network.Mainnet: '0xd8EF3cACe8b4907117a45B0b125c68560532F94D'
    }

    Streaming_Fee = {
        Network.Mainnet: '0x08f866c74205617B6F3903EF481798EcED10cDEC'
    }

    Debt_Issuance = {
        Network.Mainnet: '0x39F024d621367C044BacE2bf0Fb15Fb3612eCB92'
    }

    def run(self, _) -> SetV2ModulesOutput:
        return SetV2ModulesOutput(
            basic_issuance=Contract(self.Basic_Issuance[self.context.network]),
            streaming_fee=Contract(self.Streaming_Fee[self.context.network]),
            debt_issuance=Contract(self.Debt_Issuance[self.context.network]),
        )


def setv2_fee(_context, _setv_module, _start_block, _end_block, _set_token_addr):
    """
    To calculate the AUM, we need to get all Mint/Burn events start from block = 0, i.e. _start_block = 0.
    Total supply number does not corresponds to it.
    """

    set_token_addr = Address(_set_token_addr).checksum

    def _use_fetch_events():
        df_mint = pd.DataFrame(
            _setv_module.fetch_events(
                _setv_module.events.SetTokenIssued,
                from_block=_start_block,
                to_block=_end_block,
                argument_filters={'_setToken': set_token_addr},
                contract_address=_setv_module.address,
            )
        )

        df_burn = pd.DataFrame(
            _setv_module.fetch_events(
                _setv_module.events.SetTokenRedeemed,
                from_block=_start_block,
                to_block=_end_block,
                argument_filters={'_setToken': set_token_addr},
                contract_address=_setv_module.address,
            )
        )

        return df_mint, df_burn

    def use_contract_events(_start_block, _end_block):
        assert _setv_module.abi

        df_mint = _context.run_model(
            'contract.events',
            ContractEventsInput(
                address=_setv_module.address,
                event_name='SetTokenIssued',
                event_abi=_setv_module.abi.events.SetTokenIssued.raw_abi,
                argument_filters={'_setToken': str(set_token_addr)}),
            return_type=ContractEventsOutput).records.to_dataframe()

        df_burn = _context.run_model(
            'contract.events',
            ContractEventsInput(
                address=_setv_module.address,
                event_name='SetTokenRedeemed',
                event_abi=_setv_module.abi.events.SetTokenRedeemed.raw_abi,
                argument_filters={'_setToken': str(set_token_addr)}),
            return_type=ContractEventsOutput).records.to_dataframe()

        if not df_mint.empty:
            df_mint = df_mint.query(
                '(blockNumber >= @_start_block) & ((blockNumber <= @_end_block))')

        if not df_burn.empty:
            df_burn = df_burn.query(
                '(blockNumber >= @_start_block) & ((blockNumber <= @_end_block))')

        return df_mint, df_burn

    df_mint, df_burn = use_contract_events(_start_block, _end_block)

    if not df_burn.empty:
        df_burn = df_burn.assign(_quantity=lambda r: -1 * r._quantity)
    else:
        df_burn = pd.DataFrame(
            data=[(0, 0, 0, 0, '')],
            columns=['blockNumber', 'logIndex',
                     'transactionIndex', '_quantity', '_redeemer'],
        ).query('_redeemer != ""')

    df_mint_burn = (pd
                    .concat([df_mint, df_burn])
                    .reset_index(drop=True)
                    .loc[:, ['blockNumber', 'logIndex', 'transactionIndex', '_quantity', '_redeemer']]
                    .sort_values(['blockNumber', 'logIndex', 'transactionIndex'])
                    )

    return df_mint_burn
