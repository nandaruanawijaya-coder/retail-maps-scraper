import csv
import json
import os
import logging
from .config import OUTPUT_FIELDS

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self, output_dir: str, raw_dir: str, progress_file: str):
        self.output_dir = output_dir
        self.raw_dir = raw_dir
        self.progress_file = progress_file
        self._progress: dict = self._load_progress()
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(raw_dir, exist_ok=True)

    def save_raw(self, response, district_id: str, category: str) -> None:
        district_raw_dir = os.path.join(self.raw_dir, district_id)
        os.makedirs(district_raw_dir, exist_ok=True)
        path = os.path.join(district_raw_dir, f"{category}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=2)

    def save_csv(self, merchants: list[dict], district_id: str) -> None:
        path = os.path.join(self.output_dir, f"{district_id}.csv")
        write_header = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
            if write_header:
                writer.writeheader()
            writer.writerows(merchants)
        logger.info("Saved %d merchants to %s", len(merchants), path)

    def save_json(self, merchants: list[dict], district_id: str) -> None:
        path = os.path.join(self.output_dir, f"{district_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(merchants, f, ensure_ascii=False, indent=2)

    def mark_done(self, district_id: str, category: str) -> None:
        if district_id not in self._progress:
            self._progress[district_id] = []
        if category not in self._progress[district_id]:
            self._progress[district_id].append(category)
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self._progress, f, indent=2)

    def is_done(self, district_id: str, category: str) -> bool:
        return category in self._progress.get(district_id, [])

    def _load_progress(self) -> dict:
        if os.path.exists(self.progress_file):
            with open(self.progress_file, encoding="utf-8") as f:
                return json.load(f)
        return {}
