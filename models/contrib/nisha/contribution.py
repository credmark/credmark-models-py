from credmark.cmf.model import Model
from credmark.cmf.types import Token, Address, Price

SynthetixAddress = [
    "0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f"
]

# List of chains for Synthetix
Synthetix_chains = ["Optimism", "Ethereum"]


@Model.describe(
    slug='contrib.nisha',
    display_name='Total Value Locked Extractor Model',
    description="This model gives examples of the functionality to get TVL of given Prototype",
    version='1.0',
    developer='nisha',
    output=dict
)
class GetTotalTVL(Model):

    def run(self, input="Synthetix") -> dict:
        # Based upon input prototype we can get address and chains
        # Hardcoded Synthetix for now
        address = Address(SynthetixAddress[0])
        chains = Synthetix_chains
        stx_token = Token(address=address)
        total_tvl = self.context.run_model(slug='token.categorized-supply', input=stx_token, return_type=Price)
        # Get TVL for each chain
        for chain in chains:
            total_tvl = total_tvl + self.context.run_model(slug='token.price', input=chain, return_type=Price)

        return {"total_value_locked": total_tvl}
