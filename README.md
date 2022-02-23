# credmark-models-py

The Credmark Models Repository

## Install

### Virtual Env

Create a virtual env if you want:

```
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

You will need to set a `GITHUB_TOKEN` with a github personal access token.

Then run:

```
pip install -r requirements.txt
```

For development, you can also run:

```
pip install -r requirements-dev.txt
```

## Configuration

Some configuration is done with environment variables.
They can be set in your shell or a `.env` file.

Environment variables:

`CREDMARK_WEB3_PROVIDERS` [OPTIONAL] is a JSON object where the keys are chain ids (as strings) and the values are URLs to HTTP providers. You must use your own provider URLs. This is not required if your model does not use web3.

For example, a `.env` file can contain the following:

```
CREDMARK_WEB3_PROVIDERS={"1":"https://eth-mainnet.alchemyapi.io/v2/ABC123","137":"https://polygon-mainnet.g.alchemy.com/v2/ABC123"}
```

## Run a Model

- `credmark-dev` script is a tool for developers.

* List models:

```bash
credmark-dev list-models
```

Note: The `--model_path` argument can be used to limit the search for models. It must be a folder relative to the current directory. It defaults to "models" so normally you won't need to change it.

- Run model:

When running a model, you use args and can specify the input JSON as an arg (--input or -i) or it will read the input JSON from stdin.

An example run of a model:

```bash
credmark-dev run pi --input "{}"
```

Another example where we pass input to stdin:

```
echo {"model":"pi"} | credmark-dev run --chain_id=1 --block_number=1 run-test
```

## Develop a Model

A model is a python code file which implements the model class. See an example in the `models/examples/echo` folder.

Standards:

- Model slugs can contain letters (upper and lowercase), numbers, and hyphen. In general, use a hypen between words. They must be unique in a case-insensitive manner.

- Input variables and Output data fields should use camel-cased names.

### Model Code

First create a folder in the `models` folder that will hold all of your models, for example `models/my_models`.

Then create a python file `model_foo.py` (again it can have any name as long as it ends in .py)

A model is a python class that inherits from the base Model class `credmark.model.Model` and decorated with the `@credmark.model.it` decorator. The decorator lets you define the metadata for your model.

It looks something like this:

```py
import credmark.model

@credmark.model.it(slug='echo',
                   version='1.0',
                   display_name='Echo',
                   description="A test model to echo the message property sent in input.",
                   developer='Credmark',
                   input=EchoDto,
                   output=EchoDto)
class EchoModel(credmark.model.Model):
    def run(self, input: EchoDto) -> EchoDto:
        return input
```

The model class implements a `run(self, input)` method, which takes input data (as a dict or DTO (Data Transfer Object)) and returns a result dict or DTO, with various properties and values, potentially nested with other JSON-compatible data structures.

For the DTOs (Data Transfer Objects) we use the python module `pydantic` to define and validate the data. We have aliased `pydantic`'s `BaseModel` as DTO and `Field` as `DTOField` to avoid confusion with Credmark models but all the functionality of `pydantic` is available.

The DTO used in the example above, for both the input and output, looks like this:

```py
from credmark.types.dto import DTO, DTOField

class EchoDto(DTO):
    message: str = DTOField('Hello', description='A message')
```

The `credmark-model-sdk` defines many common data objects as DTOs.
We strongly encourage you to create DTOs and/or make use of the common objects, either as your top-level DTO or as subobjects or in lists etc. as needed.

A model can optionally implement a `init(self)` method which will be called when the instance is initialized and the `self.context` is available.

Models can call other python code, in imported python files (in your models folder or below) or from packages, as needed. You may not import code from other model folders. One thing to keep in mind is that different instances of a model may or may not be run in the same python execution so do not make use of global or class variables unless they are meant to be shared across model instances.

A model instance has access to the following instance variables:

- `self.context` - A context which holds state and provides functionality
- `self.logger` - Python logger instance for logging to stderr(optional) A model should never write/print to stdout.

### Model Context

The model context provides access to context variables, web3, and other models.

Instance attributes:

- `chain_id` (`int`): chain ID, ex 1
- `block_number` (`int`): default block number
- `web3` (`Web3`): a configured web3 instance for RPC calls
- `ledger` (`Ledger`): a class for doing ledger data queries

Methods:

- `run_model(name: str, input: Union[dict, None] = None, return_type: Union[Type[dict], Type[DTO], None], block_number: Union[int, None] = None, version: Union[str, None] = None)` - A model can call other models and use their results. `run_model()` calls the specified model and returns the results as a dict or DTO (if `return_type` is specified) (or raises an error if the called model was unavailable or had an error.)

### Error handling

The top level will catch any exceptions and output error JSON to stdout and exit with an error code.

Models can raise a `credmark.model.ModelRunError` (or other Exception) to terminate a run.

Models that run another model will terminate if the requested model has an error.

Models should never write to stdout. They may use a logger to write to stderr.
