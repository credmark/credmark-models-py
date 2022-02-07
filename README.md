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

IMPORTANT: The Credmark SDK does not exist yet so for now, in the parent folder to this one run `git clone credmark-model-engine` (or ensure the credmark-model-engine folder exists there.)

Then run:

```
pip install -r requirements.txt
```

For development, you can also run:

```
pip install -r requirements-dev.txt
```

## Run a Model

- `run_model.py` python script that runs a model.

The script takes args and reads the input JSON from stdin.

The `--model_path` can be a folder to search for models. It must be relative to the current directory. It defaults to "." so normally you won't need to change it.

An example run of a model:

```
echo '{}' | ./run_model.py --chain_id=1 --block_number=1 --model_name=pi --model_path=credmark/models --provider=https://mainnet.infura.io/v3/12345
```

Another example where we pass input:

```
echo '{"model":"pi"}' | ./run_model.py --chain_id=1 --block_number=1 --model_name=run-test --model_path=credmark/models
```

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
from credmark import Model

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

See `credmark/types/model/context.py` for more details.

### Error handling

The top level `run_model.py` will catch any exceptions and output error JSON to stdout and exit with an error code.

Models can raise an exception to terminate a run. Models that do
an API request to run another model will terminate if the requested model has an error.

Models should never write to stdout. They may use a logger to write to stderr.
