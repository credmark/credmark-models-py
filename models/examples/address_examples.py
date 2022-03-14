import credmark.model
from credmark.types import Address, Account
from credmark.types.dto import DTO


class AddressTransformsExampleOutput(DTO):
    inputAddress: Address
    checksumAddress: str
    lowerAddress: str


@credmark.model.describe(slug='example.address-transforms',
                         version='1.0',
                         display_name='(Example) Address Transforms',
                         description='Input an address and output transformations we can make to that address',
                         developer='Credmark',
                         input=Account,
                         output=AddressTransformsExampleOutput)
class AddressTransformsExample(credmark.model.Model):
    def run(self, input: Account) -> AddressTransformsExampleOutput:
        """
            This model demonstrates how to take in an address as an Account input, and output the various transformations.
        """
        return AddressTransformsExampleOutput(
            inputAddress=input.address,
            checksumAddress=input.address.checksum,
            lowerAddress=input.address.lower()
        )
