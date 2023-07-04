from typing import List
from credmark.cmf.model import CachePolicy, Model
from credmark.cmf.types import Network
from credmark.dto import DTO, DTOField, EmptyInput, IterableListGenericDTO
from pydantic import PrivateAttr


class Chain(DTO):
    chain_id: int = DTOField(description="Chain ID.")
    name: str = DTOField(description="Name of the chain")
    has_ledger: bool = DTOField(description="Whether the chain has ledger data available")
    has_node: bool = DTOField(description="Whether the chain has node available")


class ChainListOutput(IterableListGenericDTO[Chain]):
    chains: List[Chain] = DTOField(description='List of chains')
    _iterator: str = PrivateAttr('positions')


@Model.describe(slug="chain.list",
                version="0.1",
                display_name="Chain list",
                description='Get list of supported chains by CMF',
                category='chain',
                cache=CachePolicy.SKIP,
                input=EmptyInput,
                output=ChainListOutput)
class GetBlockTimestamp(Model):
    def run(self, _) -> ChainListOutput:
        return ChainListOutput(
            chains=[Chain(chain_id=network.chain_id,
                          name=network.name,
                          has_ledger=network.has_ledger,
                          has_node=network.has_node)
                    for network in Network if network.has_node or network.has_ledger]
        )
