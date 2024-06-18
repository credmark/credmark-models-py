# pylint: disable=line-too-long

import matplotlib.pyplot as plt
import networkx as nx
from credmark.cmf.model import Model
from credmark.cmf.types import Records, Token
from credmark.dto import DTO


class TransactionTagInput(DTO):
    hash: str
    block_number: int

    class Config:
        schema_extra = {
            'example': {
                "hash": "0x7ee67c4b2b5540a503fdf3b2f3a44c955c22884c0e286f5d89e67d4d8989264a",
                        "block_number": 13984858}
        }


def create_graph_from_txn(df_txn) -> nx.DiGraph:
    dig = nx.DiGraph()
    for _n, r in df_txn.iterrows():
        tok = Token(address=r.token_address)
        txn_data = [{'token_address': r.token_address, 'value_scaled': tok.scaled(
            float(r.value)), 'log_index': r.log_index}]
        if dig.has_edge(r.from_address, r.to_address):
            data = dig.get_edge_data(r.from_address, r.to_address)
            if data is None:
                raise ValueError('Missing edge data')
            data = data['txn_data']
            dig.remove_edge(r.from_address, r.to_address)
            dig.add_edge(r.from_address, r.to_address,
                         txn_data=data + txn_data)
        else:
            dig.add_edge(r.from_address, r.to_address, txn_data=txn_data)
    return dig


def classify_dig(logger, dig: nx.DiGraph, df_txn, debug=False):
    input_nodes = {u for u, deg in dig.in_degree() if not deg}  # type: ignore
    output_nodes = {u for u, deg in dig.out_degree() if not deg}  # type: ignore
    in_and_out_nodes = ({u for u, _deg in dig.in_degree()} &  # type: ignore
                        {u for u, _deg in dig.out_degree()})  # type: ignore

    swap_nodes = set()
    link_1to1_nodes = set()
    link_1ton_nodes = set()
    link_nto1_nodes = set()
    link_nton_nodes = set()
    for node in in_and_out_nodes:
        in_edges = {u for u, _ in dig.in_edges([node])}  # type: ignore
        out_edges = {v for _, v in dig.out_edges([node])}  # type: ignore
        if in_edges == out_edges:
            swap_nodes.add(node)
        elif len(in_edges) == 1 and len(out_edges) == 1:
            link_1to1_nodes.add(node)
        elif len(in_edges) == 1:
            link_1ton_nodes.add(node)
        elif len(out_edges) == 1:
            link_nto1_nodes.add(node)
        else:
            link_nton_nodes.add(node)

    if debug:
        logger.info('swap_nodes', swap_nodes)
        logger.info('input_nodes', input_nodes)
        logger.info('output_nodes', output_nodes)
        logger.info('link_1to1_nodes', link_1to1_nodes)
        logger.info('link_1ton_nodes', link_1ton_nodes)
        logger.info('link_nto1_nodes', link_nto1_nodes)
        logger.info('link_nton_nodes', link_nton_nodes)

    df_txn_out = df_txn.copy()
    types = []
    values_scaled = []
    for _n, r in df_txn_out.iterrows():
        tok = Token(address=r.token_address)
        values_scaled.append(tok.scaled(float(r.value)))

        if r.from_address in input_nodes and r.to_address in output_nodes:
            types.append('transfer')
        elif r.from_address in input_nodes:
            types.append('in')
        elif r.to_address in output_nodes:
            types.append('out')
        elif r.from_address in swap_nodes:
            types.append('swap_in')
        elif r.to_address in swap_nodes:
            types.append('swap_out')
        else:
            types.append([])
            if r.to_address in link_1to1_nodes:
                types[-1].append('link_11_in')
            if r.from_address in link_1to1_nodes:
                types[-1].append('link_11_out')

            if r.to_address in link_1ton_nodes:
                types[-1].append('link_1n_in')
            if r.from_address in link_1ton_nodes:
                types[-1].append('link_1n_out')

            if r.to_address in link_nto1_nodes:
                types[-1].append('link_n1_in')
            if r.from_address in link_nto1_nodes:
                types[-1].append('link_n1_out')

            if r.to_address in link_nton_nodes:
                types[-1].append('link_nn_in')
            if r.from_address in link_nton_nodes:
                types[-1].append('link_nn_out')

            if len(types[-1]) == 0:
                raise ValueError('Unclassifiable row:', r)

    df_txn_out.loc[:, 'type'] = types
    df_txn_out.loc[:, 'value_scaled'] = values_scaled

    return df_txn_out


def plot_dig(dig: nx.DiGraph, figsize=(7, 7)):
    _ax = plt.figure(3, figsize=figsize)

    etwo = [(u, v) for (u, v, d) in dig.edges(data=True) if len(d["txn_data"]) > 1]  # type: ignore
    eone = [(u, v) for (u, v, d) in dig.edges(data=True) if len(d["txn_data"]) == 1]  # type: ignore

    # positions for all nodes - seed for reproducibility
    pos = nx.spring_layout(dig, seed=9)  # type: ignore

    # nodes
    nx.draw_networkx_nodes(dig, pos, node_size=1400,  # type: ignore
                           node_color='#FFFFFF', edgecolors='#000000')

    # edges
    nx.draw_networkx_edges(dig, pos, edgelist=etwo, width=3,  # type: ignore
                           edge_color="black", connectionstyle='Arc3, rad=0.2', arrowsize=20)
    nx.draw_networkx_edges(dig, pos, edgelist=eone, width=3,  # type: ignore
                           edge_color="blue", connectionstyle='Arc3, rad=0.2', arrowsize=20)

    # node labels
    nx.draw_networkx_labels(dig, pos, labels={n: n[:5] for n in dig},  # type: ignore
                            font_size=11, font_family="sans-serif")

    # edge weight labels
    edge_labels = nx.get_edge_attributes(dig, "txn_data")  # type: ignore
    edge_set = set()
    new_edge_labels = {}
    for e, v in edge_labels.items():
        e_sorted = tuple(sorted(e))
        if e_sorted not in edge_set:
            new_edge_labels[e_sorted] = v
            edge_set.add(e_sorted)
        else:
            new_edge_labels[e_sorted] += v
    new_edge_labels = {e: ', '.join([(f"[{x['log_index']}: {x['token_address'][:5]}, "
                                      f"{float(x['value_scaled']):.1f}]")
                                     for x in v])
                       for e, v in new_edge_labels.items()}

    nx.draw_networkx_edge_labels(  # type: ignore
        dig, pos, edge_labels=new_edge_labels, rotate=False, font_size=11)

    # ax = plt.gca()
    # ax.margins(0.08)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


# credmark-dev run token.transaction -i '{"hash": "0x319552805d5f3d0c97e7b6c1e40d0c42817c49406fbff41af0f3ac88b590aa34", "block_number": 15125867}'

@Model.describe(slug='token.transaction',
                version='0.3',
                display_name='Token Transaction',
                description='Tagged transactions for token transfer',
                developer='Credmark',
                category='transaction',
                tags=['token'],
                input=TransactionTagInput,
                output=dict)
class TokenTransferTransactionTag(Model):
    """
    Add tags to token transfer transactions:
    - swap_in / swap_out
    - in / out
    - link_11_in / link_11_out
    - link_1n_in / link_1n_out
    - link_n1_in / link_n1_out
    - link_nn_in / link_nn_out
    """

    def run(self, input: TransactionTagInput) -> dict:
        input_block_number = input.block_number

        if input_block_number != int(self.context.block_number):
            return self.context.run_model(self.slug, input=input, block_number=input_block_number)

        with self.context.ledger.TokenTransfer as q:
            df_txn = q.select(
                aggregates=[(q.RAW_AMOUNT, 'value')],
                columns=q.columns,
                where=q.TRANSACTION_HASH.eq(input.hash).and_(
                    q.BLOCK_NUMBER.eq(input_block_number))).to_dataframe()

        return self.context.run_model('token.txn-classify', input=Records.from_dataframe(df_txn))


class TxnRecords(Records):
    class Config:
        schema_extra = {
            'example': {'records':
                        [('0xccd114339b0fd76fbb94d6f19c7fdc6fea928cce66cfd57d9a2508325aff8dfa', '15125867', '2022-07-12T05:03:39.000Z', '0x08f68110f1e0ca67c80a24b4bd206675610f445d', '1',
                          '0x0ab87046fbb341d058f17cbc4c1133f25a20a52f', '0xeef86c2e49e11345f1a693675df9a38f7d880c8f', '0x319552805d5f3d0c97e7b6c1e40d0c42817c49406fbff41af0f3ac88b590aa34', 1844102876259671339),
                         ('0xccd114339b0fd76fbb94d6f19c7fdc6fea928cce66cfd57d9a2508325aff8dfa', '15125867', '2022-07-12T05:03:39.000Z', '0xeef86c2e49e11345f1a693675df9a38f7d880c8f', '2',
                          '0x0ab87046fbb341d058f17cbc4c1133f25a20a52f', '0x0000000000000000000000000000000000000000', '0x319552805d5f3d0c97e7b6c1e40d0c42817c49406fbff41af0f3ac88b590aa34', 1844102691849383713),
                         ('0xccd114339b0fd76fbb94d6f19c7fdc6fea928cce66cfd57d9a2508325aff8dfa', '15125867', '2022-07-12T05:03:39.000Z', '0xb63cac384247597756545b500253ff8e607a8020', '3',
                          '0x64aa3364f17a4d01c6f1751fd97c2bd3d7e7f1d5', '0x055475920a8c93cffb64d039a8205f7acc7722d3', '0x319552805d5f3d0c97e7b6c1e40d0c42817c49406fbff41af0f3ac88b590aa34', 345335597976),
                         ('0xccd114339b0fd76fbb94d6f19c7fdc6fea928cce66cfd57d9a2508325aff8dfa', '15125867', '2022-07-12T05:03:39.000Z', '0x055475920a8c93cffb64d039a8205f7acc7722d3', '4',
                          '0x6b175474e89094c44da98b954eedeac495271d0f', '0x5777d92f208679db4b9778590fa3cab3ac9e2168', '0x319552805d5f3d0c97e7b6c1e40d0c42817c49406fbff41af0f3ac88b590aa34', 4835471113735542742314),
                         ('0xccd114339b0fd76fbb94d6f19c7fdc6fea928cce66cfd57d9a2508325aff8dfa', '15125867', '2022-07-12T05:03:39.000Z', '0x5777d92f208679db4b9778590fa3cab3ac9e2168', '0',
                          '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', '0xeef86c2e49e11345f1a693675df9a38f7d880c8f', '0x319552805d5f3d0c97e7b6c1e40d0c42817c49406fbff41af0f3ac88b590aa34', 4835192242),
                         ('0xccd114339b0fd76fbb94d6f19c7fdc6fea928cce66cfd57d9a2508325aff8dfa', '15125867', '2022-07-12T05:03:39.000Z', '0xeef86c2e49e11345f1a693675df9a38f7d880c8f', '7',
                          '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', '0x08f68110f1e0ca67c80a24b4bd206675610f445d', '0x319552805d5f3d0c97e7b6c1e40d0c42817c49406fbff41af0f3ac88b590aa34', 4820143723)],
                        'fields': ['block_hash', 'block_number', 'block_timestamp', 'from_address', 'log_index', 'token_address', 'to_address', 'transaction_hash', 'value'], 'n_rows': 6, 'fix_int_columns': []}
        }


@Model.describe(slug='token.txn-classify',
                version='0.2',
                display_name='Token Transaction',
                description='Tagged transactions for token transfer',
                developer='Credmark',
                category='transaction',
                tags=['token'],
                input=TxnRecords,
                output=dict)
class ClassifyTxn(Model):
    def run(self, input: TxnRecords) -> dict:
        df_txn = input.to_dataframe()
        df_txn.value = df_txn.value.astype(float)
        df_txn.log_index = df_txn.log_index.astype(float)
        df_txn.log_index = df_txn.log_index.astype(float)
        dig = create_graph_from_txn(df_txn)
        df_txn_new = classify_dig(self.logger, dig, df_txn)
        # plot_dig(dig)
        return df_txn_new.to_dict()
