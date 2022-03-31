from credmark.cmf.model import Model, EmptyInput
from credmark.cmf.types import Address


@Model.describe(
    slug='example.address',
    version='1.0',
    display_name='Address Usage Examples',
    description='This model gives examples of the functionality available on the Address class',
    developer='Credmark',
    input=EmptyInput,
    output=dict)
class ExampleAddress(Model):
    def run(self, input) -> dict:
        """
            This model demonstrates the functionality of the Address class
        """

        address = Address("0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf")

        self.logger.info(
            f"Address automatically normalizes to lowercase : {address}")
        self.logger.info(
            f"Address('0xeb2629a2734e272bcc07bda959863f316f4bd4cf').checksum : {address.checksum}")
        self.logger.info(
            "Address equality exists for string and Address, and is case insensitive")
        self.logger.info(
            f"address == '0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf' : "
            f"{address == '0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf'}")
        self.logger.info(
            f"Address equality for strings is case-insensitive : "
            f"{address == '0xeb2629a2734e272bcc07bda959863f316f4bd4cf'}")
        self.logger.info(
            f"You can hash the address : {hash(address)}")

        self.logger.info(
            f"Address.null() returns the NULL Address : {Address.null()}")
        self.logger.info(
            "Address.valid() is whether a string is a valid address format")
        self.logger.info(
            f"Address.valid('0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf') : "
            f"{Address.valid('0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf')}")
        self.logger.info(
            f"Address.valid('0xThIsIsNoTaVaLiDaDdReSsItSGaRbaGeLeTtErSs') : "
            f"{Address.valid('0xThIsIsNoTaVaLiDaDdReSsItSGaRbaGeLeTtErSs')}")

        return {"message": "see https://github.com/credmark/credmark-models-py"
                "/blob/main/models/examples/address_examples.py for examples of Address usage"}
