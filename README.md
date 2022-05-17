# Credmark Models and Model Framework

Credmark has created a Model Framework for creators to allow them easy access to Credmark's inhouse integrated, curated, and historical blockchain data via standard data models and to enable creators to leverage these models to build their own models and publish them.

It contains dependencies to the [Credmark Model Framework repo](https://github.com/credmark/credmark-model-framework-py) as well as the credmark-dev command-line tool, that lets you list the models in the local repo and run local models as you develop. It will also run remote non-local models on the server by automatically doing API calls when models are not present locally. Once the Credmark model framework is installed you can use this command-line tool.

# Quickstart
To install the Model Framework, please follow these [instructions](https://developer-docs.credmark.com/en/latest/usage.html).

# How to...
After installation, please follow the instructions [here](https://developer-docs.credmark.com/en/latest/how_to.html) on how to create, run, and submit new models as well as the modeling guidelines.

# Command Line Tool
Please find more details on the CLI [here](https://developer-docs.credmark.com/en/latest/credmark_dev.html).

# Model Overview
You can browse the models that are already deployed at the [Credmark Model Documentation](https://gateway.credmark.com/model-docs) site.

# Credmark API
The Credmark Framework provides access to remote models and access to on-chain data via Credmark API. Please find more details on the API [here](https://developer-docs.credmark.com/en/latest/api.html).

# Model Error Handling
When running a model, the top level framework code will catch any exceptions, convert it to a ModelRunError if needed, and output an error object in the response. Please find more details on this [here](https://developer-docs.credmark.com/en/latest/errors.html#).

# Bugs, Issues and Support
The Credmark Model Framework is under active development, thus there will be some bugs or issues that may cause problems. 

We encourage all modelers to join our [Discord](https://discord.com/invite/3dSfMqP3d4), pick the role "Engineering" and post any issues the in the channel [#framework-help](https://discord.com/channels/827615638540910622/965655586513485835). The Discord shall be the place to ask general questions about how to do something or if you have data-related questions.

If you want to report a bug, unexpected behavior, or feature request, you can raise an issue in Github directly but we encourage you in this case as well to notify the community in Discord.
