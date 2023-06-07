# pylint:disable=line-too-long

"""
Uni V2 Pool
"""

import sys
from datetime import datetime

import pandas as pd
from credmark.cmf.types import Contract
from requests.exceptions import HTTPError


class UniswapPoolBase:
    """
    Uniswap Pool Base
    """

    def __init__(self, pool_addr, abi, event_list):
        self.pool = Contract(address=pool_addr).set_abi(abi, set_loaded=True)
        self.df_evt = {}
        self._event_list = event_list

    def load_events(self, from_block, to_block, use_async: bool, async_worker: int):
        """
        load events from node
        """
        pool = self.pool
        if pool.abi is None:
            raise ValueError(f'Pool abi missing for {pool.address}')

        for event_name in self._event_list:
            df_evt = fetch_events_with_cols(
                pool, getattr(pool.events, event_name), event_name,
                from_block, to_block, getattr(pool.abi.events, event_name).args,
                use_async, async_worker)
            self.df_evt[event_name] = df_evt

        df_comb_evt = pd.concat(self.df_evt.values())

        if df_comb_evt.empty:
            return df_comb_evt

        df_comb_evt = df_comb_evt.sort_values(['blockNumber', 'logIndex']).reset_index(drop=True)

        print(('[load_events]', [(k, v.shape[0]) for k, v in self.df_evt.items()]),
              ('_comb_evt', df_comb_evt.shape[0],
               'block_number', df_comb_evt.blockNumber.nunique()),
              file=sys.stderr, flush=True)

        return df_comb_evt

    def load_events_db(self, pool_id, protocol, from_block, to_block, fix_df_events, _get_uniswap_event):
        """
        load events from db
        """
        for event_name in self._event_list:
            df_evt = _get_uniswap_event(pool_id, event_name, fix_df_events, protocol, from_block, to_block)
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

    try:
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
    except HTTPError:
        try:
            print('[fetch_events_with_cols] trying 100_000')
            df2 = pd.DataFrame(pool.fetch_events(
                    event,
                    from_block=_from_block,
                    to_block=_to_block,
                    by_range=100_000))
        except HTTPError:
            try:
                print('[fetch_events_with_cols] trying 50_000')
                df2 = pd.DataFrame(pool.fetch_events(
                        event,
                        from_block=_from_block,
                        to_block=_to_block,
                        by_range=50_000))
            except HTTPError:
                try:
                    print('[fetch_events_with_cols] trying 30_000')
                    df2 = pd.DataFrame(pool.fetch_events(
                            event,
                            from_block=_from_block,
                            to_block=_to_block,
                            by_range=30_000))
                except HTTPError:
                    try:
                        print('[fetch_events_with_cols] trying 20_000')
                        df2 = pd.DataFrame(pool.fetch_events(
                                event,
                                from_block=_from_block,
                                to_block=_to_block,
                                by_range=20_000))
                    except HTTPError:
                        print('[fetch_events_with_cols] trying 10_000')
                        df2 = pd.DataFrame(pool.fetch_events(
                                event,
                                from_block=_from_block,
                                to_block=_to_block,
                                by_range=10_000))

    end_t = datetime.now() - start_t
    print((event_name, 'node', pool.address, _from_block,
          _to_block, end_t.seconds, df2.shape), file=sys.stderr)

    if df2.empty:
        return pd.DataFrame()

    df2 = (df2.sort_values(['blockNumber', 'logIndex'])
           .loc[:, ['blockNumber', 'logIndex'] + _cols]
           .assign(event=event_name))
    return df2
