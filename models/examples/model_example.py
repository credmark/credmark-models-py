from credmark.cmf.model import Model
from credmark.dto import DTO, DTOField


class EchoDto(DTO):
    message: str = DTOField('Hello', description='A message')


@Model.describe(slug='example.model',
                version='1.0',
                display_name='Example (Model)',
                description="A test model to echo the message property sent in input.",
                developer='Credmark',
                input=EchoDto,
                output=EchoDto)
class EchoModel(Model):
    def run(self, input: EchoDto) -> EchoDto:
        return input
