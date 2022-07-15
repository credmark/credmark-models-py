import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from credmark.cmf.model import Model
from credmark.cmf.types import Token
from credmark.dto import DTO


class TransactionTagInput(DTO):
    hash: str
    block_number: int


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
            dig.add_edge(r.from_address, r.to_address, txn_data=data + txn_data)
        else:
            dig.add_edge(r.from_address, r.to_address, txn_data=txn_data)
    return dig


def classify_dig(logger, dig: nx.DiGraph, df_txn, debug=False):
    input_nodes = {u for u, deg in dig.in_degree() if not deg}
    output_nodes = {u for u, deg in dig.out_degree() if not deg}
    in_and_out_nodes = {u for u, _deg in dig.in_degree()} & {u for u, _deg in dig.out_degree()}

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

    pos = nx.spring_layout(dig, seed=9)  # positions for all nodes - seed for reproducibility

    # nodes
    nx.draw_networkx_nodes(dig, pos, node_size=1400, node_color='#FFFFFF', edgecolors='#000000')

    # edges
    nx.draw_networkx_edges(dig, pos, edgelist=etwo, width=3,
                           edge_color="black", connectionstyle='Arc3, rad=0.2', arrowsize=12)
    nx.draw_networkx_edges(dig, pos, edgelist=eone, width=3,
                           edge_color="blue", connectionstyle='Arc3, rad=0.2', arrowsize=12)

    # node labels
    nx.draw_networkx_labels(dig, pos, labels={n: n[:5] for n in dig},
                            font_size=11, font_family="sans-serif")

    # edge weight labels
    edge_labels = nx.get_edge_attributes(dig, "txn_data")
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

    nx.draw_networkx_edge_labels(dig, pos, edge_labels=new_edge_labels, rotate=False, font_size=11)

    # ax = plt.gca()
    # ax.margins(0.08)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


@Model.describe(slug='token.transaction',
                version='0.1',
                display_name='Token Transactin',
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
        if input.block_number != self.context.block_number:
            return self.context.run_model(self.slug, input=input, block_number=input.block_number)

        with self.context.ledger.TokenTransfer as q:
            df_txn = q.select(columns=q.columns,
                              where=q.TRANSACTION_HASH.eq(input.hash).and_(
                                  q.BLOCK_NUMBER.eq(input.block_number))).to_dataframe()

        return self.context.run_model('token.txn-classify', input=df_txn.to_dict())


@Model.describe(slug='token.txn-classify',
                version='0.0',
                display_name='Token Transactin',
                description='Tagged transactions for token transfer',
                developer='Credmark',
                category='transaction',
                tags=['token'],
                input=dict,
                output=dict)
class ClassifyTxn(Model):
    def run(self, input: dict) -> dict:
        df_txn = pd.DataFrame.from_dict(input)
        df_txn.value = df_txn.value.astype(float)
        df_txn.log_index = df_txn.log_index.astype(float)
        df_txn.log_index = df_txn.log_index.astype(float)
        dig = create_graph_from_txn(df_txn)
        df_txn_new = classify_dig(self.logger, dig, df_txn)
        # plot_dig(dig)
        return df_txn_new.to_dict()
