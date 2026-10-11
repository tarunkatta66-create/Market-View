import os
import re
import json
from collections import defaultdict
from typing import List, Tuple
import pandas as pd
from marketpulse.storage.mongo_client import MongoStore

STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "and", "or", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "it", "its", "this", "that", "these", "those", "as", "at", "up", "down"
}


def mapper(doc: str) -> List[Tuple[str, int]]:
    """Map step: tokenize headline text and output (word, 1) key-value pairs."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', doc.lower())
    kvs = []
    for w in words:
        if w not in STOPWORDS:
            kvs.append((w, 1))
    return kvs


def shuffle_and_sort(mapped_kvs: List[Tuple[str, int]]) -> Dict[str, List[int]]:
    """Shuffle step: group key-value pairs by word."""
    grouped = defaultdict(list)
    for k, v in mapped_kvs:
        grouped[k].append(v)
    return grouped


def reducer(key: str, values: List[int]) -> Tuple[str, int]:
    """Reduce step: sum counts for each word key."""
    return (key, sum(values))


def run_headline_mapreduce(news_json_path: str = None) -> pd.DataFrame:
    path = news_json_path or os.path.join("data", "raw", "news_headlines.json")
    if not os.path.exists(path):
        from marketpulse.ingest.download_data import fetch_news_rss
        news_items = fetch_news_rss()
    else:
        with open(path, "r", encoding="utf-8") as f:
            news_items = json.load(f)

    # Step 1: Map
    all_mapped = []
    for item in news_items:
        title = item.get("title", "")
        all_mapped.extend(mapper(title))

    # Step 2: Shuffle & Sort
    grouped = shuffle_and_sort(all_mapped)

    # Step 3: Reduce
    reduced = [reducer(word, counts) for word, counts in grouped.items()]

    # Sort descending by count
    reduced.sort(key=lambda x: x[1], reverse=True)

    df = pd.DataFrame(reduced, columns=["word", "count"])

    # Store results
    proc_dir = os.path.join("data", "processed")
    os.makedirs(proc_dir, exist_ok=True)
    df.to_csv(os.path.join(proc_dir, "headline_wordcount.csv"), index=False)

    store = MongoStore()
    records = df.head(100).to_dict(orient="records")
    store.clear_collection("headline_wordcount")
    store.insert_records("headline_wordcount", records)

    return df


if __name__ == "__main__":
    df = run_headline_mapreduce()
    print("MapReduce Headline Wordcount completed. Top 10 words:")
    print(df.head(10).to_string(index=False))
