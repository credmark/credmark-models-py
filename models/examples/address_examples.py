import credmark.model
from credmark.types import Address


@credmark.model.describe(slug='example-address',
                         version='1.0',
                         display_name='(Example) Load Contract by Name',
                         description='Load a Contract By Name and Return it',
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
