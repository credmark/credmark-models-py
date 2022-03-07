import credmark.model
from credmark.types import Address, Wallet


@credmark.model.describe(slug='example-address',
                         version='1.0',
                         display_name='(Example) Address',
                         description='Input an address and output the same address',
                         developer='Credmark',
                         input=Wallet,
                         output=Wallet)
class AddressExample(credmark.model.Model):
    def run(self, input: Wallet) -> Wallet:
        """
            This model demonstrates how to take in an address as an input, and output an address as an output.
        """
        result = input
        return result


@credmark.model.describe(slug='example-address-transforms',
                         version='1.0',
                         display_name='(Example) Address Transforms',
                         description='Input an address and output the same address',
                         developer='Credmark',
                         input=Wallet)
class AddressTransformsExample(credmark.model.Model):
    def run(self, input: Wallet) -> dict:
        """
            This model demonstrates how to take in an address as an input, and output an address as an output.
        """
        return {"inputAddress": input.address, "checksumAddress": input.address.checksum, "lowerAddress": input.address.lower()}
