import networkx as nx
from typing import Dict, List, Any
from marketpulse.graph.correlation_graph import build_correlation_graph


def detect_stock_communities(corr_matrix_df) -> List[Dict[str, Any]]:
    graph_data = build_correlation_graph(corr_matrix_df, threshold=0.25)
    G = nx.Graph()
    for n in graph_data["nodes"]:
        G.add_node(n["id"])
    for e in graph_data["links"]:
        G.add_edge(e["source"], e["target"], weight=e["weight"])

    # Louvain / Greedy modularity community detection
    try:
        communities_generator = nx.community.greedy_modularity_communities(G)
        communities = [list(c) for c in communities_generator]
    except Exception:
        # Fallback connected components
        communities = [list(c) for c in nx.connected_components(G)]

    clusters = []
    for cid, members in enumerate(communities):
        clusters.append({
            "cluster_id": cid + 1,
            "tickers": members,
            "count": len(members)
        })
    return clusters
