"""
Uni V2 Pool
"""

import sys
from datetime import datetime

import pandas as pd
from credmark.cmf.types import Contract


def fetch_events_with_cols(pool: Contract, event, event_name, _from_block, _to_block, _cols,
                           use_async, async_worker):
    """
    fetch events for uniswap
    """

    start_t = datetime.now()

    if use_async:
        df2 = pd.DataFrame(pool.fetch_events(
            event,
            from_block=_from_block,
            to_block=_to_block,
            use_async=use_async,
            async_worker=async_worker
        ))
    else:
        df2 = pd.DataFrame(pool.fetch_events(
            event,
            from_block=_from_block,
            to_block=_to_block))

    end_t = datetime.now() - start_t
    print((event_name, 'node', pool.address, _from_block,
          _to_block, end_t.seconds, df2.shape), file=sys.stderr)

    if df2.empty:
        return pd.DataFrame()

    df2 = (df2.sort_values(['blockNumber', 'logIndex'])
           .loc[:, ['blockNumber', 'logIndex'] + _cols]
           .assign(event=event_name))
    return df2
