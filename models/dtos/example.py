from datetime import datetime
from typing import List, Optional, Union

from credmark.cmf.model.errors import ModelBaseError
from credmark.cmf.types import Address, Token
from credmark.cmf.types.ledger import LedgerModelOutput
from credmark.cmf.types.series import BlockSeries
from credmark.dto import DTO, DTOField, IterableListGenericDTO, PrivateAttr
from models.utils.term_colors import TermColors


class _ExampleModelOutput(DTO):

    # TODO: Replace it with a Discriminated Union
    class Log(DTO):
        type: str
        message: Optional[str] = None
        input: Optional[str] = None
        output: Optional[str] = None
        error: Optional[str] = None

    title: str
    description: Optional[str] = None
    github_url: str
    documentation_url: Optional[str] = None
    logs: List[Log] = []

    def __init__(self, **data):
        super().__init__(**data)
        self._log('\n' + TermColors.apply(data["title"], invert=True))
        if "description" in data and data["description"] is not None and data["description"] != "":
            self._log(TermColors.apply(data["description"], faint=True))
        self._log('\n')

        if ("documentation_url" in data
                and data["documentation_url"] is not None
                and data["documentation_url"] != ""):
            self._log(f'> {TermColors.apply("Docs", underline=True)}   '
                      f'{data["documentation_url"]}')

        self._log(f'> {TermColors.apply("Source", underline=True)} {data["github_url"]}')

    def _log(self, message: str):
        print(message)

    def log(self, message: str):
        self._log('\n' + TermColors.apply(message, TermColors.BLUE))
        self.logs.append(self.Log(type="message", message=message))

    def log_io(self, input: str, output):
        str_to_log = ""
        normalized_input = input.lstrip("\n").replace("\n", "\n\t")
        if normalized_input != "":
            str_to_log += "\n>>> "
            highlighted_input = TermColors.apply(normalized_input, TermColors.GREEN)
            str_to_log += highlighted_input

        if isinstance(output, DTO):
            output = output.dict()

        if output != "":
            highlighted_output = TermColors.apply(str(output), TermColors.YELLOW)
            str_to_log += "\n"
            str_to_log += highlighted_output

        self._log(str_to_log)
        self.logs.append(self.Log(type="io", input=input, output=str(output)))

    def log_error(self, error: Union[str, Exception]):
        error_str = ""
        if isinstance(error, str):
            error_str = error
        elif isinstance(error, ModelBaseError):
            error_str = error.data.message
        else:
            error_str = str(error)
        self._log('\n' + TermColors.apply(error_str, TermColors.RED))
        self.logs.append(self.Log(type="error", error=error_str))


# __init__ with kwargs disables type hints
# This hack re-enables type hints
# TODO: Use `Unpacked` from typing_extensions for kwargs type
class ExampleModelOutput(_ExampleModelOutput):
    pass


class ExampleEchoInput(DTO):
    message: str = DTOField('Hello', description='A message')


class ExampleEchoOutput(ExampleModelOutput):
    echo: str


class ExampleAddressInput(DTO):
    address: Address = Address("0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf")


class ExampleAccountInput(DTO):
    address_1: Address = Address('0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf')
    address_2: Address = Address('0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB')


class ExampleTokenInput(DTO):
    address: Address = DTOField(default=Address('0x68cfb82eacb9f198d508b514d898a403c449533e'))
    symbol: str = DTOField(default='AAVE')


class ExampleLedgerOutput(ExampleModelOutput):
    ledger_output: LedgerModelOutput


class ExampleBlockTimeInput(DTO):
    blockTime: datetime = DTOField(
        title="Block time",
        description="Unix time, i.e. seconds(if >= -2e10 or <= 2e10) or milliseconds "
        "(if < -2e10 or > 2e10) since 1 January 1970 or string with format "
        "YYYY-MM-DD[T]HH: MM[:SS[.ffffff]][Z or [±]HH[:]MM]]]. "
        "The default value is set to 2022/02/19. "
        "So we can run this example with a past block number >= 14233162. ",
        default_factory=lambda: datetime(2022, 2, 19)
    )


class ExampleHistoricalInput(DTO):
    model_slug: str = 'example.model'
    model_input: dict = {}


class ExampleHistoricalOutput(ExampleModelOutput):
    model_slug: str
    model_historical_output: Optional[BlockSeries[dict]] = None


class ExampleIterationOutput(ExampleModelOutput):
    class Tokens(IterableListGenericDTO[Token]):
        tokens: List[Token] = []
        _iterator: str = PrivateAttr('tokens')

    tokens: Tokens


class ExampleLibrariesOutput(ExampleModelOutput):
    class LibraryDTO(DTO):
        name: str
        version: str

    libraries: List[LibraryDTO]


class ExampleAllModelsOutput(ExampleModelOutput):

    class ModelOutput(DTO):
        model_slug: str
        model_output: dict

    model_outputs: List[ModelOutput]
