# Credmark Models and Model Framework

Credmark has created a Model Framework for creators to allow them easy access to Credmark's inhouse integrated, curated, and historical blockchain data via standard data models and to enable creators to leverage these models to build their own models and publish them.

It contains dependencies to the [Credmark Model Framework repo](https://github.com/credmark/credmark-model-framework-py) as well as the credmark-dev command-line tool, that lets you list the models in the local repo and run local models as you develop. It will also run remote non-local models on the server by automatically doing API calls when models are not present locally. Once the Credmark model framework is installed you can use this command-line tool.

# Get Started
### Quickstart
To install the Model Framework, please follow these [instructions](https://docs.credmark.com/cmf-model-guide/getting-started/installation-and-setup).

### Command Line Tool
Please find more details on the CLI [here](https://developer-docs.credmark.com/en/latest/credmark_dev.html).

### Jupyter Notebook
You can as well configure the Credmark Model Framework to run within a Jupyter Notebook. Please have a look [here](https://docs.credmark.com/cmf-model-guide/getting-started/setup-of-jupyter-notebook).

# How to...
After installation, please follow the instructions on how to
- [create](https://docs.credmark.com/cmf-model-guide/how-to-build-a-model/create-the-model-skeleton),
- [run](https://docs.credmark.com/cmf-model-guide/how-to-build-a-model/create-the-output-and-run-the-model),
- [test](https://docs.credmark.com/cmf-model-guide/testing/unit-tests),
- [submit new models](https://docs.credmark.com/cmf-model-guide/how-to-submit-a-model/model-submission-process)

Please also have a look at our [modeling guidelines](https://docs.credmark.com/cmf-model-guide/model-guidelines/the-good-model-checklist).

# Credmark API
The Credmark Framework provides access to remote models and access to on-chain data via the different Credmark APIs. Currently there are three APIs for token, portfolio and DeFi data.

### API Basics
To get started with the setup of the API keys, please refer to our [get-started guide](https://docs.credmark.com/api-how-to-guide/account-setup/initial-sign-up) and learn how to make some first [API Calls](https://docs.credmark.com/api-how-to-guide/make-an-api-call/request).

### Token API
Understand the [core concepts](https://docs.credmark.com/token-api-concepts/basics/introduction) of the Token API and find an [interactive technical documentation](https://gateway.credmark.com/api/#/Token%20API) of every endpoint.

### Portfolio API
Coming soon...

### DeFi API
Understand the [core concepts](https://docs.credmark.com/defi-api-concepts/basics/introduction) of the DeFi API and find an [interactive technical documentation](https://gateway.credmark.com/api/#/DeFi%20API) of every endpoint.

# Additional resources

### Model Overview
You can browse the models that are already deployed at the [Credmark Model Documentation](https://gateway.credmark.com/model-docs) site.

### Model Error Handling
When running a model, the top level framework code will catch any exceptions, convert it to a ModelRunError if needed, and output an error object in the response. Please find more details on this [here](https://developer-docs.credmark.com/en/latest/errors.html#).

### Bugs, Issues and Support
The Credmark Model Framework is under active development, thus there will be some bugs or issues that may cause problems.

We encourage all modelers to join our [Discord](https://discord.com/invite/3dSfMqP3d4), pick the role "Engineering" and post any issues the in the channel [#product-help](https://discord.com/channels/827615638540910622/965655586513485835). The Discord shall be the place to ask general questions about how to do something or if you have data-related questions.

If you want to report a bug, unexpected behavior, or feature request, you can raise an issue in Github directly but we encourage you in this case as well to notify the community in Discord.

# Docker

### Build the Image

You can build the image by running the following command at the root level of the directory:

```{bash}
docker build -t credmark/credmark-cli .
```

### Run the Container

You can either run the container in an interactive shell process by running:

```{bash}
docker run -it --entrypoint /bin/bash credmark/credmark-cli
```

And then form within the container you can now run `credmark-dev` commands.

Alternatively, you can run the container each time you want to run a `credmark-dev` command:

```{bash}
docker run credmark/credmark-cli credmark-dev list
```
