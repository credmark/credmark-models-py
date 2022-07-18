# credmark-models-notebook

Credmark modeling framework can be loaded in to Jupyter notebook via below lines code.

	%reload_ext credmark.cmf.ipython

	param = {'chain_id': 1,
 			 'block_number': None,
			 'model_loader_path': ['path_to_credmark-models-py/models'],
			 'chain_to_provider_url': {'1': 'Your node provider'},
			 'api_url': None,
			 'use_local_models': None,
			 'register_utility_global': True}

	context, model_loader = %cmf param

More examples can be found in repo

https://github.com/credmark/credmark-models-notebook

