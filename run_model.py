#! /usr/bin/env python3
import argparse
import logging
import sys
import json
from credmark.engine.context import EngineModelContext
from credmark.engine.model_loader import ModelLoader
from credmark.types.model.errors import MaxModelRunDepthError, MissingModelError, ModelRunRequestError

logger = logging.getLogger(__name__)


def main():
    exit_code = 0

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Run a model.')
    parser.add_argument('--chain_id', type=int, default=1, required=False,
                        help='[OPTIONAL] The chain ID. Defaults to 1.')
    parser.add_argument('--block_number', type=int, required=False, default=1,
                        help='[OPTIONAL] Web3 default block number.')
    parser.add_argument('--provider_url', required=False, default=None,
                        help='[OPTIONAL] Web3 provider HTTP URL')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--model_name', required=False, default='(use --model_name arg)',
                       help='Name of the model to run.')
    group.add_argument('--list_models', action='store_true', default=False, required=False,
                       help='[OPTIONAL] Show the loaded models.')
    parser.add_argument('--model_version', default=None, required=False,
                        help='[OPTIONAL] Version of the model to run. Defaults to latest.')
    parser.add_argument('--run_id', default=None, required=False,
                        help='[OPTIONAL] The run ID. Part of the run context.')
    parser.add_argument('--model_path', default="models", required=False,
                        help='[OPTIONAL] Semicolon separated paths to the model folders (or parent), the manifest file, or model python file.')
    parser.add_argument('--api_url', required=False, default=None,
                        help='[OPTIONAL] Credmark API url')
    parser.add_argument('--depth', type=int, default=0, required=False,
                        help='[OPTIONAL] The depth of a recursive model call.')
    parser.add_argument('--log_level', default='INFO', required=False,
                        help='[OPTIONAL] Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL')

    try:
        args = vars(parser.parse_args())

        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=args['log_level'])

        model_path = args['model_path']
        model_loader = ModelLoader([model_path])
        model_loader.log_errors()

        if args['list_models']:
            sys.stderr.write('\nLoaded models:\n\n')
            models = model_loader.loaded_model_version_lists()
            for m, v in models.items():
                sys.stderr.write(f' - {m}: {v}\n')
            sys.stderr.write('\n')
            sys.stderr.write(
                f'{len(model_loader.errors)} errors, {len(model_loader.warnings)} warnings\n\n')
            sys.exit(0)

        chain_id = args['chain_id']
        block_number = args['block_number']
        provider_url = args['provider_url']
        model_name = args['model_name']
        model_version = args['model_version']
        run_id = args['run_id']
        api_url = args['api_url']
        depth = args['depth']

        input = json.load(sys.stdin)

        result = EngineModelContext.create_context_and_run_model(chain_id=chain_id,
                                                                 block_number=block_number,
                                                                 model_name=model_name,
                                                                 model_version=model_version,
                                                                 input=input,
                                                                 model_loader=model_loader,
                                                                 provider_url=provider_url,
                                                                 api_url=api_url,
                                                                 run_id=run_id,
                                                                 depth=depth)
        print(json.dumps(result))

    except (MaxModelRunDepthError, MissingModelError) as e:
        msg = {
            "statusCode": 500,
            "error": "Model run error",
            "message": str(e)
        }
        json.dump(msg, sys.stdout)
        exit_code = 1
    except ModelRunRequestError as e:
        sys.stdout.write(str(e))
        exit_code = 1
    except Exception as e:
        logger.exception('Run error')
        msg = {
            "statusCode": 500,
            "error": "Model run error",
            "message": str(e)
        }
        json.dump(msg, sys.stdout)
        exit_code = 1
    finally:
        sys.stdout.flush()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
