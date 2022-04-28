# Credmark Models and Model Framework

Credmark has created a Model Framework for creators to allow them easy access to Credmark's inhouse integrated, curated, and historical blockchain data via standard data models and to enable creators to leverage these models to build their own models and publish them.

It contains dependencies to the [Credmark Model Framework repo](https://github.com/credmark/credmark-model-framework-py), that are installed by following the description below.

Moreover, the Credmark Model Framework includes the credmark-dev command-line tool that lets you list the models in the local repo and run local models as you develop. It will also run remote non-local models on the server by automatically doing API calls when models are not present locally. Once the Credmark model framework is installed you can use this command-line tool.

You can browse the models that are already deployed at the [Credmark Model Documentation](https://gateway.credmark.com/model-docs) site.

# Quickstart

## Prerequisites

- [Python 3.9+](https://www.python.org/downloads/) or [Miniconda 4.10+](https://docs.conda.io/en/latest/miniconda.html) installed
- Personal web3 provider url ([Alchemy](https://docs.alchemy.com/alchemy/introduction/getting-started) or other) if you need to use your own web3 provider instance to run any model
- [Visual studio 2019+](https://visualstudio.microsoft.com/de/downloads/) installed for Windows users

## Fork Repository

Fork [credmark-models-py](https://github.com/credmark/credmark-models-py) repository

## Virtual Env

Create a virtual env (if you want).

sh or bash:

```sh
python3 -m venv venv
source venv/bin/activate
```

zsh:

```sh
python3 -m venv venv
. venv/bin/activate
```

If you wish, you can run it on miniconda. Simply install the miniconda version mentioned in the prerequisite, open Anaconda prompt, navigate to the repo folder and continue with steps (commands) as mentioned below.

## Install Dependencies

Then run:

```sh
pip install -r requirements.txt
```

For development, you can also run:

```sh
pip install -r requirements-dev.txt
```

## Configure environment variables

Some configuration is done with environment variables. They can be set in your shell or a `.env` file, which can be created at the root folder of the cloned repository.

**Environment variables**

The `CREDMARK_WEB3_PROVIDER_CHAIN_ID_{N}` is a JSON object where the keys are chain ids (as strings) and the values are URLs to HTTP providers.

Set {N} with a chain id, for example `CREDMARK_WEB3_PROVIDER_CHAIN_ID_1` and set the value as the URL of the HTTP provider.

For example, a `.env` file can contain the following:

```
CREDMARK_WEB3_PROVIDER_CHAIN_ID_1=https://eth-mainnet.alchemyapi.io/v2/ABC123
CREDMARK_WEB3_PROVIDER_CHAIN_ID_137=https://polygon-mainnet.g.alchemy.com/v2/ABC123
```

**ALTERNATIVELY** you may set all your providers in a single env var:

For example, a `.env` file can contain the following:

```
CREDMARK_WEB3_PROVIDERS='{1:"https://eth-mainnet.alchemyapi.io/v2/ABC123","137":"https://polygon-mainnet.g.alchemy.com/v2/ABC123"}'
```

This variable is used to run models which require web3. It can be ignored for those models which do not require web3.

## Run a Model

To see a list of all models available, use the command:

```sh
credmark-dev list
```

You can then pick a model name (slug) and run the model by using the command:

```sh
credmark-dev run <Specify Slug> -b <Specify block number>  -i <Specify Input>
```

so for example

```sh
credmark-dev run cmk.circulating-supply -b 14000000  -i “{}”
```

Tip: you can run the command

```sh
credmark-dev list --manifests
```

to see the input data format required for each model. It will also show the output formats.

## Develop a Model

A model is essentially a python code file which implements the model class by subclassing from a base class. See some examples [here](https://github.com/credmark/credmark-models-py/tree/main/models/examples).

**Steps**

1. Create a folder in the [models/contrib folder](https://github.com/credmark/credmark-models-py/tree/main/models) that will hold all of your models, for example `models/contrib/my_models`. You can add models directly there or create subfolders as desired. Do not work in another contributer's folder.
2. Create a python file, for example `model_foo.py` (again it can have any name as long as it ends in .py) in the folder you created in step 1.
3. Ensure your model class inherits from the base Model class `credmark.cmf.model.Model`. Also, use decorator `@Model.describe` to define the metadata for your model.
   Example:

```py
from credmark.cmf.model import Model

@Model.describe(slug='contrib.echo',
                version='1.0',
                display_name='Echo',
                description="A test model to echo the message property sent in input.",
                developer='Credmark',
                input=EchoDto,
                output=EchoDto)
class EchoModel(Model):
    def run(self, input: EchoDto) -> EchoDto:
        return input
```

The model class implements a `run(self, input)` method, which takes input data (as a dict or DTO (Data Transfer Object)) and returns a result dict or DTO (see later section DTO), with various properties and values, potentially nested with other JSON-compatible data structures.

A special DTO `EmptyInput`, which is an empty DTO, is created for model with no input required. The model input is EmptyInput by default if `input` is not specified in the decorator `@Model.describe`. If the model takes non-empty input, modeller can specify `input=dict` or create a DTO for more structured data.

A model can optionally implement a `init(self)` method which will be called when the instance is initialized and the `self.context` is available.

Models can call other python code, in imported python files (in your models folder or below) or from packages, as needed. You may not import code from other model folders. One thing to keep in mind is that different instances of a model may or may not be run in the same python execution so do not make use of global or class variables unless they are meant to be shared across model instances.

A model instance has access to the following instance variables:

- `self.context` - A context which holds state and provides functionality. Details on the [Model Context](#model-context) are below.
- `self.logger` - Python logger instance for logging to stderr(optional) A model should never write/print to stdout.

Please find more detailed examples [here](https://github.com/credmark/credmark-models-py/blob/main/models/examples/address_examples.py).

**Constraints**

- Model slugs MUST start with `"contrib."` and the rest of the string can contain letters (upper and lowercase), numbers, and hyphens. In general, use a hyphen between words. Slugs must be unique in a case-insensitive manner across all models running within Credmark.
- Input variables and Output data fields should use camel-cased names.

**DTO**

For the DTOs (Data Transfer Objects) we use the python module `pydantic` to define and validate the data. We have aliased `pydantic`'s `BaseModel` as DTO and `Field` as `DTOField` to avoid confusion with Credmark models but all the functionality of `pydantic` is available.

The DTO used in the example above, for both the input and output, looks like this:

```py
from credmark.dto import DTO, DTOField

class EchoDto(DTO):
    message: str = DTOField('Hello', description='A message')
```

The `credmark-model-framework` defines many common data objects as DTOs and fields such as Address, Contract, Token, Position, Portfolio etc. They can be found [here](https://github.com/credmark/credmark-model-framework-py/blob/main/credmark/cmf/types)

- Example 1: Use Address in input/ouput DTOs

The input data, e.g. `{"poolAddress":"0x..."}`, is converted to `Address` type. The property `.checksum` to get its checksum address.

```py
from credmark.cmf.model import Model
from credmark.cmf.types import Address

class PoolAddress(DTO):
    poolAddress: Address = DTOField(..., description='Address of Pool')

@Model.describe(...
                         input=PoolAddress)
class AModel(Model):
  def run(self, input: PoolAddress):
    address = input.poolAddress.checksum
```

- Example 2: Use Address to auto-convert to checksum address.

```py
from credmark.cmf.types import Address

def run(self, input):
    address = Address(wallet_adress)
    address.checksum
```

- Example 3: Pre-defined financial DTO to define input. Use it as object in the `run(self, input)`

```py
from credmark.cmf.model import Model
from credmark.cmf.types import Portfolio

"""
# Portfolio is defined in the framework
# class Portfolio(DTO):
#    positions: List[Position] = DTOField([], description='List of positions')

class PortfolioSummary(DTO):
    num_tokens: int = DTOField(..., description='Number of different tokens')
"""

@Model.describe(slug='contrib.type-test-1',
                         version='1.0',
                         display_name='Test Model',
                         description='A Test Model',
                         input=Portfolio,
                         output=PortfolioSummary)
class TestModel(Model):

    def run(self, input: Portfolio) -> PortfolioSummary:
        return PortfolioSummary(num_tokens=len(input.positions))

```

We strongly encourage you to create DTOs and/or make use of the common objects, either as your top-level DTO or as sub-objects and in lists etc. as needed.

You may use `credmark-dev describe {model_slug}` to show the input/output schema and examples for specific model(s). For example

```
credmark-dev describe aave-v2.token-asset-historical

(...omit the output header)

Loaded models:

 - slug: aave.token-asset-historical
 - version: 1.0
 - tags: None
 - display_name: Aave V2 token liquidity
 - description: Aave V2 token liquidity at a given block number
 - developer:
 - input schema:
   Token(object)
     └─address(string)
 - input example:
   #01: {'symbol': 'USDC'}
   #02: {'symbol': 'USDC', 'decimals': 6}
   #03: {'address': '0x1F98431c8aD98523631AE4a59f267346ea31F984'}
   #04: {'address': '0x1F98431c8aD98523631AE4a59f267346ea31F984', 'abi': '(Optional) contract abi JSON string'}
 - output schema:
   BlockSeries(object)
     └─series(List[BlockSeriesRow])
         └─blockNumber(integer)
         └─blockTimestamp(integer)
         └─sampleTimestamp(integer)
         └─output(object)
 - output example:
   #01: {'series': [{'blockNumber': 'integer', 'blockTimestamp': 'integer', 'sampleTimestamp': 'integer', 'output': 'object'}]}
 - class: models.credmark.protocols.aave-v2.aave_v2.AaveV2GetTokenAssetHistorical
```

## Submit a Model

If you are a contributor external to credmark, you should create your folder in [credmark-models-py/models/contrib].

You should create and keep your models under this folder. Note that we have applied additional conditions for model slug names under this folder. Slug name must start with `contrib.<model-name>`, so for example: `Slug = ‘contrib.sample-model`.

If you are a contributor external to credmark, you should create your folder in [credmark-models-py/models/contrib].

You should create and keep your models under this folder. Note that we have applied additional conditions for model slug names under this folder. Slug name must start with `contrib.<model-name>`, so for example: `Slug = ‘contrib.sample-model`.

Once your model is ready to submit, simply create a pull request on the github repo and let us know in our [Discord](https://discord.com/invite/BJbYSRDdtr).

# Model Library

See a list of the [existing models](https://github.com/credmark/credmark-models-py/tree/main/models/credmark) in the repository.

# API Gateway

The Credmark Framework provides access to remote models and access to on-chain data via [Credmark API Gateway](https://gateway.credmark.com/api/).

## Interactive HTTP requests

If you go to the popup in the top right of the window you can now choose between the different model groups:

- [Credmark Models](https://gateway.credmark.com/api/?urls.primaryName=Credmark%20Models)
- [Utility Models](https://gateway.credmark.com/api/?urls.primaryName=Utility%20Models)
- [Contributor Models](https://gateway.credmark.com/api/?urls.primaryName=Contributor%20Models)
- [Example Models](https://gateway.credmark.com/api/?urls.primaryName=Example%20Models)

For each group, you will get the docs for all the models within the group and you are able to run them interactively. Note that not all models are fully documented yet.

## Model documentation

If you're just looking for model documentation (without all the API details), please refer to the [Credmark Model Documentation](https://gateway.credmark.com/model-docs). This documentation contains the description of the models as well as example requests and responses and is searchable (by name and slug).

# Framework Command Documentation

## Help command

All the commands accept `-h` parameter for help, e.g.:

```
>credmark-dev -h

usage: credmark-dev [-h] [--log_level LOG_LEVEL] [--model_path MODEL_PATH] [--manifest_file MANIFEST_FILE]
                    {list,list-models,models,deployed-models,describe,describe-models,man,run,run-model,build,build-manifest,clean,remove-manifest} ...

Credmark developer tool

optional arguments:
  -h, --help            show this help message and exit
  --log_level LOG_LEVEL
                        Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  --model_path MODEL_PATH
                        Semicolon separated paths to the model folders (or parent) or model python file. Defaults to models folder.
  --manifest_file MANIFEST_FILE
                        Name of the built manifest file. Defaults to models.json. [Not required during development]

Commands:
  Supported commands

  {list,list-models,models,deployed-models,describe,describe-models,man,run,run-model,build,build-manifest,clean,remove-manifest}
                        additional help
    list (list-models)  List models in this repo
    models (deployed-models)
                        List models deployed on server
    describe (describe-models, man)
                        Show documentation for local and deployed models
    run (run-model)     Run a model
    build (build-manifest)
                        Build model manifest [Not required during development]
    clean (remove-manifest)
                        Clean model manifest
```

## `run`command

Below -h command shows the details of options available for run commands.

```
>credmark-dev run -h

usage: credmark-dev run [-h] [-b BLOCK_NUMBER] [-c CHAIN_ID] [-i INPUT] [-v MODEL_VERSION] [--provider_url_map PROVIDER_URL_MAP] [--api_url API_URL] model-slug

positional arguments:
  model-slug            Slug for the model to run.

optional arguments:
  -h, --help            show this help message and exit
  -b BLOCK_NUMBER, --block_number BLOCK_NUMBER
                        Block number used for the context of the model run. If not specified, it is set to the latest block of the chain.
  -c CHAIN_ID, --chain_id CHAIN_ID
                        [OPTIONAL] The chain ID. Defaults to 1.
  -i INPUT, --input INPUT
                        [OPTIONAL] Input JSON or if value is "-" it will read input JSON from stdin.
  -v MODEL_VERSION, --model_version MODEL_VERSION
                        [OPTIONAL] Version of the model to run. Defaults to latest.
  --provider_url_map PROVIDER_URL_MAP
                        [OPTIONAL] JSON object of chain id to Web3 provider HTTP URL. Overrides settings in env vars.
  --api_url API_URL     [OPTIONAL] Credmark API url. Defaults to the standard API gateway. You do not normally need to set this.
  --api_url API_URL     [OPTIONAL] Credmark API url
```

To call any model we can specify the output by providing below parameters (they're not necessarily required):

- `-b` or `–block_number` : to define against which block number the model should run. If not specified, it uses the "latest" block from our ledger db.
- `-i` or `–input` : to provide input for a model in a predefined structure.(you can run command `credmark-dev list --manifests` to see the input format required for each model. See example below). If not provided it will default to “{}”.
  Model-slug: Name of the model (slug) to call the model.

Note: if chain ID is not mentioned explicitly in the parameter, it defaults to 1. If the model is using web 3 instance then chain id (and blockchain) will be picked from the .env file we defined during setup (refer to “configure environment variable” section). If the model is using Credmark database then, by default, it will refer to the Ethereum blockchain.

See the example below. Here, we are running the model “cmk.circulating-supply” at block_number 14000000.

```
>Credmark-dev run -b 14000000 cmk.circulating-supply -i "{}"

{"slug": "cmk.circulating-supply", "version": "1.0", "output": {"result": 28314402605762084044696668}, "dependencies": {"cmk.total-supply": {"1.0": 1}, "cmk.circulating-supply": {"1.0": 1}}}
```

## `list`command

Below `-h` command shows the details of options available for list commands.

```
>credmark-dev list -h

usage: credmark-dev list [-h] [--manifests] [--json]

optional arguments:
  -h, --help   show this help message and exit
  --manifests
  --json
```

Note: You can also run `list-models` command alternatively.

Example below shows simple output (list of all models and their version) of list command:

```
>credmark-dev list -h

Loaded models:

 - var: ['1.0']
 - cmk.total-supply: ['1.0']
 - cmk.circulating-supply: ['1.0']
 - xcmk.total-supply: ['1.0']
[...]
```

You can also get the list result in different formats using `--json` or `--manifest`.

**Note:** the commands `build` and `clean` does not need to be used.

# Credmark Model Framework Core Components

In the following you will find the key components of every model.

## Model Class

Credmark uses a simple base class called ‘Model’ class to set up a model. The actual code can be found [here](https://github.com/credmark/credmark-model-framework-py/blob/main/credmark/cmf/model/__init__.py).

All Models should import this class `import credmark.cmf.model` and can override the run() method. See examples [here](https://github.com/credmark/credmark-models-py/tree/main/models/examples).

The `@Model.describe()` decorator provides a simple interface to define the model properties such as slug, version, display_name, description, developer, input, output etc so that it can be used easily by consumers and other models.

If description is not specified, the `__doc__` string of the model's class is used for the model description.

See example [here](https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_01_model.py).

## Model Context

Each model runs with a particular context, including the name of the blockchain, block number, and a configured web3 instance (among other things). The context can be passed along when the model calls other models. The context’s web3 instance can be used to make RPC calls.
The `ModelContext()` Class sets up the context for the model to run and can be accessed from a model as `self.context`.
The base code can be found [here](https://github.com/credmark/credmark-model-framework-py/blob/main/credmark/cmf/model/context.py). It provides an interface for models to run other models, call contracts, get ledger data, use a web3 instance etc.

It also enforces deterministic behavior for Models. The key utilities in `ModelContext` are

- web3
- contract
- ledger
- block number
- historical utility

### Calling Other Models

A model can call other models and use their results. You can pass the input as an input arg and the model output is returned as a dict (or DTO if `return_type` is specified.)

If an error occurs during a call to run a model, an exception is raised. See [Error handling](#error-handling)

There are 2 ways to call another model:

- Using `context.models` (Recommended)
- Calling `context.run_model()`

#### `context.models`

Models are exposed on `context.models` by their slug (with any "-" (hyphens) in the slug replaced with "\_" (underscores)) and can be called like a function, passing the input as a DTO or dict or as standard keyword args (kwargs).

For example, here we use keyword args:

```py
# Returns a dict with output of the model
result = self.context.models.example.model(message='Hello world')
```

You can use a DTO for the output by initializing it with the output dict.

Here we use a DTO instance as the input and convert the output to another DTO instance:

```py
class ExampleEchoInput(DTO):
    message: str = DTOField('Hello', description='A message')


class ExampleEchoOutput(DTO):
    echo: str

input = ExampleEchoInput(message='Hello world')
output = ExampleEchoOutput(**self.context.models.example.model(input))

output.echo # will equal 'Hello world from block: 14661701'
```

You can run a model at a different block number by using the `context.models(block_number=12345)` syntax, for example:

```py
# Runs the model with a context of block number 12345
result = self.context.models(block_number=12345).example.model(message='Hello world')
```

#### `context.run_model()`

Alternatively you can run a model by slug string using the `context.run_model` method:

```py
def run_model(name: str,
              input: Union[dict, DTO] = EmptyInput(),
              return_type: Union[Type[dict], Type[DTO], None],
              block_number: Union[int, None] = None,
              version: Union[str, None] = None)
```

If `return_type` is None or dict, then the method returns the model output as a dict. If it's a DTO class, the method returns a DTO instance. As above, you can use a dict result with `**` to initialize a DTO instance yourself.

For example:

```py
# token = Token( ) instance

price = Price(**self.context.run_model('price', token))

# has the same effect as:

price = self.context.run_model('price', token, return_type=credmark.cmf.types.Price)
```

### Web3

`context.web3` will return a configured web3 instance with the default block set to the block number of context.
The web3 providers are determined from the environment variables as described in the configuration section above. Currently users will need to use their own alchemy account (or other web3 provider) to access web3 functionality.

### Contract

Credmark simplified the process of getting web3 instances of any contract from any chain. So you don't need to find and hardcode chain specific attributes and functions within these chains to run your models.

The model context exposes the `context.contracts` property which can be used to get contracts by metadata or address. The contracts are instances of the `Contract` class which are configured and use the web3 instance at specified block number and specified chain id along with additional data based on `constructor_args`.

Example code for contact class can be found [here](https://github.com/credmark/credmark-model-framework-py/blob/main/credmark/cmf/types/contract.py).

Currently below parameters as argument are supported to fetched using Contracts:

- name: name of the contract
- address: address of the contract
- deploy_tx_hash: transaction hash at which contract was deployed
- Constructor_args
- protocol: protocol name
- product: product name
- abi_hash
- abi

Contract functions are accessible using the `contract.functions` property.

Tip: the contract object returned from contract class can be used to fetch any specific web3 attributes of the contract and call contract functions. As well it can be used as a DTO (see details below) so it can be returned as part of the output of a model.

### Ledger

Credmark allows access to in-house blockchain ledger data via ledger interface (`context.ledger`), so that any model can fetch/use ledger data if required. This is done via `Ledger` class which currently supports below functions:

- get_transactions
- get_traces
- get_logs
- get_contracts
- get_blocks
- get_receipts
- get_erc20_tokens
- get_erc20_transfers

Please refer [here](https://github.com/credmark/credmark-model-framework-py/blob/main/credmark/cmf/model/ledger/__init__.py) for the code of the `Ledger` class.

### Block number

The `context.block_number` holds the block number for which a model is running. Models only have access to data at (by default) or before this block number (by instantiating a new context). In other words models cannot see into the future and ledger queries etc. will restrict access to data by this block number.
As a subclass of int, the `block_number` class allows the provided block numbers to be treated as integers and hence enables arithmetic operations on block numbers. It also allows you to fetch the corresponding datetime and timestamp properties for the block number. This can be super useful in case we want to run any model iteratively for a certain block-interval or time-interval backwards from the block number provided in the context.

Example code for the block-number class can be found [here](https://github.com/credmark/credmark-model-framework-py/blob/main/credmark/cmf/types/block_number.py).

**Block number, Timestamp and Python datetime**

In blockchain, every block is created with a timestamp (in Unix epoch). In Python there are two types for date, date and datetime, with datetime can be with tzinfo or without. To provide convienent tools to query between the three and resolve the confusion around time, we have a few tools with `BlockNumber` class.

1. property, `block_number.timestamp_datetime`: Return the Python datetime with UTC of the block.

2. property, `block_number.timestamp`: Return the Unix epoch of the block.

3. class method: `from_datetime(cls, timestamp: int)`: Return a BlockNumber instance to be less or equal to the input timestamp.

   Be cautious when we obtain a timestamp from a Python datetime, we should attach a tzinfo (e.g. timezone.utc) to the datetime. Otherwise, Python take account of the local timezone when converting to a timestamp. See the model [`example.block-time`](https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_08_blocknumber.py).

4. Use a BlockNumber instance: Obtain a Python datetime with UTC of the block. The block number should be less or equal to the context block.

   ```py
   from credmark.types import ( BlockNumber )

   dt = BlockNumber(14234904).timestamp_datetime
   ```

More example code for the block-number class can be found in [here](https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_08_blocknumber.py)

### Historical Utility

The historical utility, available at `context.historical` (see [here](https://github.com/credmark/credmark-model-framework-py/blob/main/credmark/cmf/model/utils/historical_util.py)), allows you to run a model over a series of blocks for any defined range and interval.

Block ranges can be specified by blocks (either a window from current block or a start and end block) or by time (a window from the current block’s time or start and end time.) Times can be specified different units, i.e. year, month, week, day, hour, minute and second.

See [e_11_historical.py](https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_11_historical.py) on how to use this class.

## Error handling

When running a model, the top level framework code will catch any exceptions, convert it to a ModelRunError if needed, and output an error object in the response.

Models can raise a `ModelRunError` (or other Exception) to terminate a run.

When a model calls `self.context.run_model()` to run another model, an exception can be raised by the called model which will be received by the caller. `run_model()` can raise `ModelDataError`, `ModelRunError`, `ModelInputError`, `ModelNotFoundError` and various other sublasses of `ModelBaseError`.

The standard models are in `credmark.cmf.model.errors`.

In order for models to be consistently deterministic, the ONLY type of exception a model should catch and handle from a call to `run_model()` is a `ModelDataError`, which is considered a permanent error for the given context. All other errors are considered transient resource issues, coding errors, or conditions that may change in the future.

Because of this behavior, if a model raises a `ModelRunError` somewhere down a model run stack, the entire run will end up being aborted. This is by design.

### ModelBaseError

The `ModelBaseError` defines a set of properties that are common to all errors. The data associated with an error is available from an error instance at `error.data`. The following properties are available:

- `type` (string) Short identifying name for type of error

- `message` (string) A message about the error

- `code` (string) A short string, values to specific to the error type

- `detail` (object | null) - An object or null. Some errors may have a detail object containing error-specific data.

- `permanent` (boolean) If true the error is considered derministically permanent. This is currently only true for ModelDataErrors

- `stack` (list) The model run call stack. First element is the first called model and last element is the model that raised the error. An array of objects containing:

  - `slug` (string) Short identifying name for the model

  - `version` (string) Version of the model

  - `chainId` (number) Context chain id

  - `blockNumber` (number) Context block number

  - `trace` (string | null) Human-readable code trace that generated the error

### ModelDataError

A `ModelDataError` is an error that occurs during the lookup, generation, or processing of data this is considered deterministic and permanent, in the sense that for the given context, the same error will always occur.

A model may raise a ModelDataError in situations such as:

- the requested data does not exist or is not available for
  the current context block number.
- the input data is inconsistent, references non-existent
  items, or cannot be processed

A model may (and often should) catch and handle `ModelDataError`s raised from calls to `context.run_model()`.

Some standard `code`s have been defined for `ModelDataError`s, available at `ModelDataError.Codes`:

- `Codes.GENERIC = 'generic'` Default error code
- `Codes.NO_DATA = 'no_data'` Requested data does not exist (and never will for the given context)
- `Codes.CONFLICT = 'conflict'` There is an inherent conflict in the data for the given context that can never be resolved.

#### Raising ModelDataError Errors

If you want your model to raise ModelDataError errors, you should add a `ModelDataErrorDesc` to the `errors` arg of your model `describe()` decorator with a description of the codes you are using and what they mean. For example:

```py
from credmark.cmf.model import Model, EmptyInput, ModelDataErrorDesc

@Model.describe(slug='example.data-error',
                version='1.0',
                display_name='Data Error Example',
                description="A test model to generate a ModelDataError.",
                input=EmptyInput,
                errors=ModelDataErrorDesc(
                code=ModelDataError.Codes.NO_DATA,
                code_desc='Data does not exist'))
class ExampleModel(Model):
```

If you're using multiple codes, `ModelDataErrorDesc` also lets you pass in `codes` as a list of `(code, code_description)` tuples.

Then in your model `run()` code you simply raise a ModelDataError, for example:

```py
raise ModelDataError('Data does not exist', ModelDataError.Codes.NO_DATA)
```

### ModelInputError

If a model is using an input DTO, the expected model input parameters are automatically validated and a `ModelInputError` will be raised on error. `ModelInputError` is a non-permanent error because it's considered a coding error by the calling model.

The `ModelInputError` will contain a stack with the latest entry in the stack being the model that received the bad input data.

## Logging

Models should never write to stdout or use `print()`. They should use a logger to write to stderr. From a model, you can use `self.logger`.

## Data Transfer Object (DTO)

Input and output data for models are json-serializable objects of arbitrary depth and complexity. Objects can have 0 or more keys whose values can be null, number, string, array, or another object.

Although you can use dictionaries for model input and output data in your python code, we strongly encourage the use of DTOs (Data Transfer Objects.)

DTOs are classes with typed properties which will serialize and deserialize to and from JSON. They also automatically produce a JSON-schema that is used to document the input and output of a model. Each model may have their own DTOs or may share or inherit a DTO from another model that you have developed.

To create a DTO, simply subclass the DTO base class and use DTOFields to annotate your properties. Under the hood, the Credmark Model Framework uses the pydantic python module (DTO is simply an alias for pydantic BaseModel and DTOField an alias for Field) so almost anything that works with pydantic will work for your DTO.

Please see the [pydantic docs](https://pydantic-docs.helpmanual.io/usage/models/) for more information.

### Model Error Detail DTO

Besides input and output, subclases of `ModelBaseError` can use a DTO for the `data.detail` object instead of a dict. You can simply pass a DTO as the `detail` arg in a model constructor:

```py
address = Address(some_address_string)
e = ModelDataError(message='Address is not a contract',
                   code=ModelDataError.Codes.CONFLICT,
                   detail=address)
```

If your detail object has many properties and you want to document the error and details, you can create a custom DTO and error class:

- Create a DTO subclass that defines the data you want to store in the detail.

For example:

```py
class TokenAddressNotFoundDetailDTO(DTO):
    address: Address = DTOField(...,description='Address for token not found')
```

- Create a DTO subclass that defines the new error DTO. (This step is not strictly necessary but it lets you document the error.) The trick is to use the generic properties of the `ModelErrorDTO` to specify the detail's DTO class: `ModelErrorDTO[TokenAddressNotFoundDetailDTO]`

```py
class TokenAddressNotFoundDTO(ModelErrorDTO[TokenAddressNotFoundDetailDTO]):
  """
  This error occurs when there is no token at the specified address.
  The detail contains the address.
  """
```

- Then create a `ModelDataError` (or `ModelRunError`) subclass and set the class property `dto_class` to your new error DTO class:

```py
class TokenAddressNotFoundError(ModelDataError):
    dto_class = TokenAddressNotFoundDTO
```

- You can now create an error instance with:

```py
# bad_address is set to an Address instance
error = TokenAddressNotFoundError(message='Bad address',
                                detail=TokenAddressNotFoundDetailDTO(address=bad_address))
# You can now access: error.data.detail.address
```

## Additional Useful Modules

We also have some built-in reusable type classes available under [Credmark.cmf.types](https://github.com/credmark/credmark-model-framework-py/tree/main/credmark/cmf/types).

We have created and grouped together different classes to manage input and output types to be used by models. These types include some standard blockchain and financial data structures as well as some standard input and output objects for Credmark models.

### models

1. ledger.py : DTOs and data used by the ledger models
2. series.py: DTOs for the series models

### data

**1. Address:** this class is a subclass of string and holds a blockchain address.

`Address` class is inherited from `str` to help with web3 address conversion. It's highly recommended to use it instead of a baremetal address.

✔️: Address("0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9").checksum # checksum version to be used

❌: Address("0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9") # lower case version

❌:"0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9" # lower case version

Example:

```py
from credmark.cmf.types import (Address, Contract)

contract = Contract(
    # lending pool address
    address=Address("0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9").checksum,
    abi=AAVE_V2_TOKEN_CONTRACT_ABI
)
```

The address can be provided in lower case, upper case or checksum hex format. This class will normalize the address into lower case. Note that It can be used as a normal string but it also has a "checksum" property which returns a web3 ChecksumAddress.

See [e_03_address.py](https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_03_address.py) on how to use this class.

**2. Account(s):** Account simply holds an address. Accounts is a list of account instances which allows iteration through each account.

See [e_04_account.py](https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_04_account.py) on how to use this class.

**3. Contract:** a contract is a subclass of Account which has a name, deployed transaction hash, abi, protocol name etc..

Object instantiation of this class will load all information available for the contract (against contract address provided as input) in our database and you can access whatever information you want from the object.

See [e_05_contract.py](https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_05_contract.py) on how to use this class.

**4. Token:** Token is a specific kind of contract; hence the Token class inherits from Contract class.

This class allows you to load token information with an address or symbol as well as get its price in USD Currently this class supports data load for erc20 token but we will support erc721 as well soon.

See [e_06_token.py](https://github.com/credmark/credmark-models-py/blob/main/models/examples/e_06_token.py) on how to use this class. Token_data.py lists all erc20 tokens currently supported.

**5. Price and TokenPairPrice:** these classes can be used to hold a price or a price of a token against a reference token (such as CMK-BTC, CMK-ETH etc.)

**6. Position:** this class holds a Token and an amount It can calculate its value based on the token price in USD. You can also access the scaled amount property if you need the scaled amount of the erc20 token.

Token_data.py lists all erc20 tokens currently supported.

**7. Portfolio:** This class holds a list of positions. So, it can be used to calculate all positions within a wallet.
