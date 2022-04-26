from random import choice
from credmark.cmf.model import Model
from credmark.cmf.types import Address
from models.dtos.example import ExampleAddressInput, ExampleModelOutput


@Model.describe(
    slug='example.address',
    version='1.2',
    display_name='Example - Address',
    description='This model gives examples of the functionality available on the Address class',
    developer='Credmark',
    input=ExampleAddressInput,
    output=ExampleModelOutput)
class ExampleAddress(Model):
    def run(self, input: ExampleAddressInput) -> ExampleModelOutput:
        output = ExampleModelOutput(
            title="3. Example - Address",
            description="This model gives examples of the functionality available "
            "on the Address class",
            github_url="https://github.com/credmark/credmark-models-py/blob/main/"
            "models/examples/e_03_address.py",
            documentation_url="https://developer-docs.credmark.com/en/latest/"
            "reference/credmark.cmf.types.address.Address.html")

        address = input.address

        output.log("Address automatically normalizes to lowercase")
        output.log_io(input="address", output=address)

        output.log_io(input=f"Address('{address}').checksum", output=address.checksum)

        output.log("Address equality exists for string and Address")
        output.log_io(input=f"address == '{address}'",
                      output=address == str(address))
        output.log_io(input=f"address == Address('{address}')",
                      output=address == Address(str(address)))

        random_case_address = '0x'+(''.join(
            choice((str.upper, str.lower))(char) for char in address[2:]))
        output.log("Address equality is case-insensitive")
        output.log_io(input=f"{random_case_address} == {address}",
                      output=random_case_address == address)

        output.log("You can hash the address")
        output.log_io(input="hash(address)", output=hash(address))

        output.log(
            f"Address.null() returns the NULL Address : {Address.null()}")
        output.log(
            "Address.valid() checks whether a string is a valid address format")
        output.log_io(input=f"Address.valid('{address}')",
                      output=Address.valid(address))

        output.log(
            f"Address.valid('0xThIsIsNoTaVaLiDaDdReSsItSGaRbaGeLeTtErSs') : "
            f"{Address.valid('0xThIsIsNoTaVaLiDaDdReSsItSGaRbaGeLeTtErSs')}")

        return output
