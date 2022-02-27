from typing import Union
import credmark.model
from credmark.types.data import Address
from credmark.types.dto import DTO


@credmark.model.describe(slug='example-address',
                         version='1.0',
                         display_name='(Example) Load Contract by Name',
                         description='Load a Contract By Name and Return it',
                         developer='Credmark',
                         input=Address,
                         output=Address)
class AddressExample(credmark.model.Model):
    def run(self, input: Union[dict, DTO]) -> Union[dict, DTO]:

        return input
