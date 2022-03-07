import credmark.model
from credmark.types import Address, Wallet
from credmark.types.dto import DTO


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
            This model demonstrates how to take in an address as an input, 
            and output an address as an output. 

            We use the wallet class in order to format them with any wallet
        """
        result = input
        return result


class AddressTransformsExampleOutput(DTO):
    inputAddress: Address
    checksumAddress: str
    lowerAddress: str


@credmark.model.describe(slug='example-address-transforms',
                         version='1.0',
                         display_name='(Example) Address Transforms',
                         description='Input an address and output transformations we can make to that address',
                         developer='Credmark',
                         input=Wallet,
                         output=AddressTransformsExampleOutput)
class AddressTransformsExample(credmark.model.Model):
    def run(self, input: Wallet) -> AddressTransformsExampleOutput:
        """
            This model demonstrates how to take in an address as an input, and output an address as an output.
        """
        return AddressTransformsExampleOutput(
            inputAddress=input.address,
            checksumAddress=input.address.checksum,
            lowerAddress=input.address.lower()
        )
