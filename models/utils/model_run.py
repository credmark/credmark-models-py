# pylint: disable=line-too-long
from typing import Any, Optional

from credmark.cmf.model.errors import ModelDataError
from credmark.dto.encoder import json_dumps


def get_latest_run(context, slug, version) -> Optional[Any]:
    prev_run = context.run_model(
        'model.latest-usage',
        {'slug': slug, 'version': version, 'input': json_dumps(context.__dict__['original_input'])})

    if 'blockNumber' in prev_run and prev_run['blockNumber'] is not None and \
            int(prev_run['blockNumber']) <= context.block_number and prev_run['result'] is not None:
        try:
            return prev_run
        except ModelDataError:
            return None

    return None
