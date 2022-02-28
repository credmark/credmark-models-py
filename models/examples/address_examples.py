import credmark.model
from credmark.types import Address


@credmark.model.describe(slug='example-address',
                         version='1.0',
                         display_name='(Example) Address',
                         description='Input an address and output the same address',
                         developer='Credmark',
                         input=Address,
                         output=Address)
class AddressExample(credmark.model.Model):
    def run(self, input: Address) -> Address:
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
                         input=Address)
class AddressTransformsExample(credmark.model.Model):
    def run(self, input: Address) -> dict:
        """
            This model demonstrates how to take in an address as an input, and output an address as an output.
        """
        return {"inputAddress": input.address, "checksumAddress": input.checksum, "lowerAddress": input.lower()}
