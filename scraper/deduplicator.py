class Deduplicator:
    def __init__(self):
        self._seen: dict[str, dict] = {}

    def add(self, merchant: dict) -> None:
        merchant_id = merchant.get("google_id") or merchant.get("osm_id")
        if merchant_id not in self._seen:
            self._seen[merchant_id] = merchant.copy()
        else:
            existing_cat = self._seen[merchant_id].get("our_category") or self._seen[merchant_id].get("category")
            new_cat = merchant.get("our_category") or merchant.get("category")
            if new_cat and new_cat not in existing_cat:
                cat_field = "our_category" if "our_category" in self._seen[merchant_id] else "category"
                self._seen[merchant_id][cat_field] = f"{existing_cat}, {new_cat}"

    def get_unique(self) -> list[dict]:
        return list(self._seen.values())

    def reset(self) -> None:
        self._seen = {}

    def __len__(self) -> int:
        return len(self._seen)
