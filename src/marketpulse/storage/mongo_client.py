import os
import json
from typing import List, Dict, Any, Optional

try:
    import pymongo
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
except ImportError:
    pymongo = None


class MongoStore:
    """
    MongoDB abstraction for MarketPulse with local filesystem fallback.
    """

    def __init__(self, db_name: str = "marketpulse", uri: str = "mongodb://localhost:27017/"):
        self.db_name = db_name
        self.uri = uri
        self.use_mongo = False
        self.client = None
        self.db = None
        self.fallback_dir = os.path.join("data", "db")
        os.makedirs(self.fallback_dir, exist_ok=True)

        if pymongo:
            try:
                self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=1500)
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client[self.db_name]
                self.use_mongo = True
            except (ConnectionFailure, ServerSelectionTimeoutError, Exception):
                self.use_mongo = False
                self.client = None
                self.db = None

    def insert_records(self, collection_name: str, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0

        if self.use_mongo:
            try:
                coll = self.db[collection_name]
                res = coll.insert_many(records, ordered=False)
                return len(res.inserted_ids)
            except Exception:
                pass

        # Local fallback store
        path = os.path.join(self.fallback_dir, f"{collection_name}.json")
        existing = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        
        existing.extend(records)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, default=str, indent=2)
        return len(records)

    def get_records(self, collection_name: str, query: Optional[Dict[str, Any]] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        if self.use_mongo:
            try:
                coll = self.db[collection_name]
                q = query or {}
                cursor = coll.find(q, {"_id": 0}).limit(limit)
                return list(cursor)
            except Exception:
                pass

        path = os.path.join(self.fallback_dir, f"{collection_name}.json")
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if query:
                filtered = []
                for doc in data:
                    match = True
                    for k, v in query.items():
                        if doc.get(k) != v:
                            match = False
                            break
                    if match:
                        filtered.append(doc)
                return filtered[:limit]
            return data[:limit]
        except Exception:
            return []

    def clear_collection(self, collection_name: str):
        if self.use_mongo:
            try:
                self.db[collection_name].delete_many({})
            except Exception:
                pass

        path = os.path.join(self.fallback_dir, f"{collection_name}.json")
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
