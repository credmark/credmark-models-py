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

IMPORTANT: The Credmark SDK is not a published package yet so for now, in some folder (for example, one level up) run:

```
 git clone git@github.com:credmark/credmark-model-sdk-py.git
 cd credmark-model-sdk-py
 python setup.py sdist
```

Then in the credmark-models-py repo run:

```
pip install ../credmark-model-sdk-py/dist/*.gz
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

When running a model, you use args and can specify the input JSON as an arg (--input or -i) or it will read the input JSON from stdin.

An example run of a model:

```
credmark-dev run pi --input '{}'
```

Another example where we pass input to stdin:

```
echo '{"model":"pi"}' | credmark-dev run --chain_id=1 --block_number=1 run-test
```

List models:

```
credmark-dev list-models
```

The `--model_path` can be used to limit the search for models. It must be a folder relative to the current directory. It defaults to "models" so normally you won't need to change it.

## Develop a Model

A model is a python code file which implements the model and a `yaml` file which describes some metadata. See an example in the `models/pi` folder.

### Model Yaml

First create a folder in the `models` folder that will hold all of your models, for example `models/my_models`.

To make a new model `foo`, inside your models folder create a yaml file `model_foo.yaml` (it can have any name with a `.yaml` extension) with the following:

```yaml
credmark_model_manifest: v1
model:
name: foo
version: 1.0
display_name: My Foo Model
description: The foo model produces the best data.
class: models.my_models.model_foo.FooModel
```

Multiple models can be listed in the same manifest using the attribute `models` instead of `model`:

```yaml
credmark_model_manifest: v1
models:
- name: foo
version: 1.0
display_name: My Foo Model
description: The foo model produces the best data.
class: models.my_models.model_foo.FooModel
- name: goo
version: 1.3
display_name: My Goo Model
description: The goo model produces the best data.
class: models.my_models.model_goo.GooModel
```

## Model Python

Then create a python file `model_foo.py` (again it can have any name, just update the `class` property in the yaml file.)

A model is a python class that inherits from the base Model class and implements a `run(self, data)` method, which takes input data and returns a result dict with aribitrary properties and values, potentially nested with other JSON-compatible data structures.

A model can optionally implement a `init(self)` method which will be called when the instance is initialized and the context is available.

Models can call other python code, in imported python files (in your models folder or below) or from packages, as needed. You may not import code from other model folders. One thing to keep in mind is that different instances of a model may be run in the same python execution so do not make use of global or class variables unless they are meant to be shared across model instances.

```
from credmark.model import Model

class FooModel(Model):
   def run(self, data):
      return {'value': 42}
```

The model instance has access to the following instance variables:

- `self.context` - A context which holds state and provides functionality
- `self.logger` - Python logger instance for logging to stderr(optional) A model should never write/print to stdout.

Models

### Model Context

The model context provides access to context variables, web3, and other models.

Instance attributes:

- `chain_id` (`int`): chain ID, ex 1
- `block_number` (`int`): default block number
- `web3` (`Web3`): a configured web3 instance for RPC calls

Methods:

- `run_model(name: str, input: Union[dict, None] = None, block_number: Union[int, None] = None, version: Union[str, None] = None)` - A model can call other models and use their results. `run_model()` calls the specified model and returns the results as a dict (or raises an error if the called model was unavailable or had an error.)

### Error handling

The top level will catch any exceptions and output error JSON to stdout and exit with an error code.

Models can raise a `credmark.model.errors.ModelRunError` (or other Exception) to terminate a run.

Models that run another model will terminate if the requested model has an error.

Models should never write to stdout. They may use a logger to write to stderr.
