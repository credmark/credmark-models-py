# Examples of Model Composability

These simple geometry examples demonstrate:

1. two forms of composability available to model developers,
2. a hierarchical model organization that can be used to organize related modesls, and
3. the relationship between models and their manifests.

The two forms of composability are:

1. sharing classes across models, and
2. sharing models (by calling models from models).

## Sharing classes across models

Our *circle* models, *CircleCircumference* and *CircleArea* derive from a common class, *Circle*, which is itself a model.

Note that any class in the model engine can be accessed starting from the engines's root, which is automatically added to sys.path. Our *Circle* class can therefore be imported using:

```
from models.geometry.circle import Circle
```

The superclass *Circle*:

* retrieves a required input variable,
* logs an error, if it's missing, and
* returns the model's result.

Subclasses only perform the computation, making them easy to implement and read.

## Sharing models (by calling models from models)

Our *sphere* models, *SphereArea* and *SphereVolume* take a different approch. They don't share a superclass, although they could of course. Instead, they demonstrate how a model can use another model's output.

In the parent directory (geometry), we've implemented a *pi* model that simply returns the constant math.pi. That model is invoked as follows:

```
pi = self.context.run_model('pi')['value']
```

This uses the object's context to have the engine run the *pi* model. The *pi* model, like every model, returns a dictionary of values that include:

* the model's name,
* its output, and
* a list of model dependencies, including itself.

The output's key is "result" which, by convention, is a dictionary with includes the key confusingly called "value". In this case, "value"'s value is math.pi. We use this value when computing the area and volumes of our spheres.

## Model name clashes.

We can run the *pi* model as follows:

```
echo {} | ./run_model.py --chain_id=1 --block_number=1 --model_name=pi --model_path=models/geometry --provider=https://mainnet.infura.io/v3/12345
```

Note that we've set model_path to "models/geometry". Normally we can invoke any model simply using the model_path to "models". The engine traverses the hierarchy until it finds a model with a matching name, in this case, "pi".

This is the output we expect when running the model *pi* using the command above:

```
{"name": "pi", "version": "1.1", "result": {"value": 3.141592653589793}, "dependencies": {"pi": "1.1"}}
```

Notice that the model's version number is 1.1.

If you look through the model hierarchy, however, you'll discover that there are other models named "pi" in "models/pi". Their manifests show that they are version 1.0 and 2.0.

This is why we have to be careful when setting the engine's model_path. If, instead of using "models/geometry" we'd used "models", the engine finds versions 1.0 and 2.0 and looks no further.

So,

```
echo {} | ./run_model.py --chain_id=1 --block_number=1 --model_name=pi --model_path=models --provider=https://mainnet.infura.io/v3/12345 | awk '{print $0}'
```

returns

```
{"name": "pi", "version": "2.0", "result": {"value": 3.1415, "v2": true}, "dependencies": {"pi": ["1.0", "2.0"]}}
```

It's clear from this output that we did not run our version of *pi* (1.1). Instead we ran version 2.0 found in "models/pi". Version 2.0 depends on 1.0, as shown in the output above.

By default the engine always runs the latest version. This can be overriden if you want to run a particular version.

By explicitly telling the engine to look for models under "models/geometry", we avoided any ambiguity and ensured that our version of the *pi* model was run.

## Models and Manifests

A model is described by its manifest, a yaml file. For example, our circle area model is described in "models/geometry/circles/area.yaml". Our circle circumference models is described in "models/geometry/circles/circumference.yaml".

Both of those models, however, are implemented in the same python file, "modesl/geometry/circles/circles.py".
