"""
Uni V2 Pool
"""

import sys
from datetime import datetime

import pandas as pd


def fetch_events(pool, event, event_name, _from_block, _to_block, _cols):
    """
    fetch events for uniswap

    start_time = datetime.now()
    df1 = pd.DataFrame(pool.fetch_events(
        event,
        from_block=_from_block,
        to_block=_to_block))
    df1_time = datetime.now() - start_time

    df2_time = datetime.now() - start_time - df1_time
    print(f'{df1_time.seconds=} {df2_time.seconds=}')

    assert df1.shape == df2.shape
    """

    start_t = datetime.now()

    df2 = pd.DataFrame(pool.fetch_events(
        event,
        from_block=_from_block,
        to_block=_to_block,
        use_async=True))

    end_t = datetime.now() - start_t
    print((event_name, 'node', pool.address, _from_block,
          _to_block, end_t.seconds, df2.shape), file=sys.stderr)

    if df2.empty:
        return pd.DataFrame()

    df2 = (df2.sort_values(['blockNumber', 'logIndex'])
           .loc[:, ['blockNumber', 'logIndex'] + _cols]
           .assign(event=event_name))
    return df2
