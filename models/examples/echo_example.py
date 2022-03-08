import credmark.model
from credmark.types.dto import DTO, DTOField


class EchoDto(DTO):
    message: str = DTOField('Hello', description='A message')


@credmark.model.describe(slug='example.echo',
                         version='1.0',
                         display_name='Echo',
                         description="A test model to echo the message property sent in input.",
                         input=EchoDto,
                         output=EchoDto)
class EchoModel(credmark.model.Model):
    """
    This test simply echos back the input.
    The DTO message field defines a default value so that is
    used if no input is sent.
    """

    def run(self, input: EchoDto) -> EchoDto:
        return input
