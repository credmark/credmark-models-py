# pylint: disable=line-too-long
from typing import Any, Optional
from credmark.dto.encoder import json_dumps
from credmark.cmf.model.errors import ModelDataError


def get_latest_run(model_run) -> Optional[Any]:
    prev_run = model_run.context.run_model(
        'model.latest-usage',
        {'slug': model_run.slug, 'version': model_run.version, 'input': json_dumps(model_run.context.__dict__['original_input'])})

    if 'blockNumber' in prev_run and prev_run['blockNumber'] is not None and \
            int(prev_run['blockNumber']) <= model_run.context.block_number and prev_run['result'] is not None:
        try:
            return prev_run
        except ModelDataError:
            return None

    return None
