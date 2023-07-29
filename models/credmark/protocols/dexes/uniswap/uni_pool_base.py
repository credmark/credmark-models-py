# pylint:disable=line-too-long

"""
Uni V2 Pool
"""

import sys
from datetime import datetime

import pandas as pd
from credmark.cmf.model import ModelContext
from credmark.cmf.types import Contract
from requests.exceptions import HTTPError

from models.credmark.chain.contract import fetch_events_with_range


class UniswapPoolBase:
    """
    Uniswap Pool Base
    """

    def __init__(self, event_list, _protocol):
        self.df_evt = {}
        self._event_list = event_list
        self.protocol = _protocol

    def load_events_etl(self, _chain_id, _pool_addr, _protocol, _start_block, _end_block, pool_id, _get_uniswap_event_etl):
        """
        load events from etl
        """
        for event_name in self._event_list:
            # no fix for types, will fix when insertion
            df_evt = _get_uniswap_event_etl(
                _chain_id, _pool_addr, _protocol, event_name, _start_block, _end_block, pool_id, _fix_df_events=None)
            self.df_evt[event_name] = df_evt

        print(('[load_events_etl]', [(k, v.shape[0]) for k, v in self.df_evt.items()]),
              file=sys.stderr, flush=True)

    def load_events(self, _pool, from_block, to_block, use_async: bool, async_worker: int):
        """
        load events from node
        """
        if not _pool.abi:
            raise ValueError(f'Pool abi missing for {_pool.address}')

        for event_name in self._event_list:
            # no fix for types, will fix when insertion
            df_evt = fetch_events_with_cols(
                _pool, getattr(_pool.events, event_name), event_name,
                from_block, to_block, getattr(_pool.abi.events, event_name).args,
                use_async, async_worker)
            self.df_evt[event_name] = df_evt

        print(('[load_events]', [(k, v.shape[0]) for k, v in self.df_evt.items()]),
              file=sys.stderr, flush=True)

    def load_events_db(self, pool_id, protocol, from_block, to_block, fix_df_events, _get_uniswap_event_db):
        """
        load events from db
        """
        for event_name in self._event_list:
            df_evt = _get_uniswap_event_db(
                pool_id, event_name, fix_df_events, protocol, from_block, to_block)
            self.df_evt[event_name] = df_evt

        df_comb_evt = pd.concat(self.df_evt.values())

        if df_comb_evt.empty:
            return df_comb_evt

        df_comb_evt = df_comb_evt.sort_values(['blockNumber', 'logIndex']).reset_index(drop=True)

        print(('[load_events_db]', [(k, v.shape[0]) for k, v in self.df_evt.items()]),
              ('_comb_evt', df_comb_evt.shape[0],
               'block_number', df_comb_evt.blockNumber.nunique()),
              file=sys.stderr, flush=True)

        return df_comb_evt


def fetch_events_with_cols(pool: Contract, event, event_name, _from_block, _to_block, _cols,
                           use_async, async_worker):
    """
    fetch events for uniswap
    """

    start_t = datetime.now()

    if use_async:
        df2 = pd.DataFrame(pool.fetch_events(
            event=event,
            from_block=_from_block,
            to_block=_to_block,
            contract_address=pool.address,
            use_async=use_async,
            async_worker=async_worker
        ))
    else:
        df2 = fetch_events_with_range(
            None, pool, event, from_block=_from_block,  to_block=_to_block, contract_address=pool.address)

    end_t = datetime.now() - start_t
    print((event_name, 'node', pool.address, _from_block,
          _to_block, end_t.seconds, df2.shape), file=sys.stderr)

    if df2.empty:
        return pd.DataFrame()

    df2 = (df2.sort_values(['blockNumber', 'logIndex'])
           .loc[:, ['blockNumber', 'logIndex'] + _cols]
           .assign(event=event_name))
    return df2
