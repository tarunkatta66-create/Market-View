import os
import pandas as pd
import numpy as np
import networkx as nx
from typing import Dict, List, Any


def compute_correlation_matrix(daily_returns_df: pd.DataFrame) -> pd.DataFrame:
    pivoted = daily_returns_df.pivot(index="Date", columns="Ticker", values="DailyReturn")
    corr_matrix = pivoted.corr().fillna(0.0)
    return corr_matrix


def get_similar_stocks(ticker: str, corr_matrix: pd.DataFrame, top_n: int = 4) -> List[Dict[str, Any]]:
    if ticker not in corr_matrix.columns:
        return []
    series = corr_matrix[ticker].drop(ticker)
    top_series = series.sort_values(ascending=False).head(top_n)
    
    similar = []
    for t, score in top_series.items():
        similar.append({"ticker": t, "similarity": round(float(score), 3)})
    return similar


def build_correlation_graph(corr_matrix: pd.DataFrame, threshold: float = 0.3) -> Dict[str, Any]:
    G = nx.Graph()
    tickers = list(corr_matrix.columns)
    for t in tickers:
        G.add_node(t)

    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            t1, t2 = tickers[i], tickers[j]
            weight = corr_matrix.loc[t1, t2]
            if weight >= threshold:
                G.add_edge(t1, t2, weight=round(float(weight), 3))

    nodes = [{"id": n, "label": n} for n in G.nodes()]
    edges = [{"source": u, "target": v, "weight": d["weight"]} for u, v, d in G.edges(data=True)]

    return {"nodes": nodes, "links": edges}
