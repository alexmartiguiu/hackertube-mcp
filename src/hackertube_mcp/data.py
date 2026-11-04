"""Download and load the HackerTube data export.

The export is fetched once into a cache directory (override with HACKERTUBE_DATA_DIR)
and loaded fully into memory: it is ~50 MB unpacked.
"""

from __future__ import annotations

import io
import json
import os
import sys
import urllib.request
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

EXPORT_URL = "https://hackertube.org/download/hackertube-data.zip"
REQUIRED = [
    "videos.jsonl",
    "mentions.jsonl",
    "related.jsonl",
    "taxonomy.json",
    "embeddings.npy",
    "embedding_ids.json",
]


def data_dir() -> Path:
    env = os.environ.get("HACKERTUBE_DATA_DIR")
    if env:
        return Path(env).expanduser()
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "hackertube-mcp" / "data"


def ensure_data(path: Path | None = None) -> Path:
    """Return a directory holding the export, downloading it if any file is missing."""
    path = path or data_dir()
    if all((path / name).exists() for name in REQUIRED):
        return path
    path.mkdir(parents=True, exist_ok=True)
    print(f"Downloading HackerTube export to {path} ...", file=sys.stderr)
    with urllib.request.urlopen(EXPORT_URL, timeout=120) as resp:
        blob = resp.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for info in zf.infolist():
            name = Path(info.filename).name  # flatten, and never write outside `path`
            if info.is_dir() or not name:
                continue
            (path / name).write_bytes(zf.read(info))
    missing = [n for n in REQUIRED if not (path / n).exists()]
    if missing:
        raise RuntimeError(f"HackerTube export is missing files: {missing}")
    return path


def _jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@dataclass
class Corpus:
    videos: list[dict]
    by_vid: dict[str, dict]
    mentions: dict[str, list[dict]]
    related: dict[str, list[dict]]
    taxonomy: dict
    embeddings: np.ndarray  # float32 [n, 384], row i <-> videos[i]
    row: dict[str, int] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> "Corpus":
        path = ensure_data(path)
        videos = _jsonl(path / "videos.jsonl")

        mentions: dict[str, list[dict]] = defaultdict(list)
        for m in _jsonl(path / "mentions.jsonl"):
            mentions[m["vid"]].append(m)

        related = {r["vid"]: r["related"] for r in _jsonl(path / "related.jsonl")}
        taxonomy = json.loads((path / "taxonomy.json").read_text(encoding="utf-8"))

        # Reorder embedding rows to match `videos`, so masks over videos index embeddings directly.
        emb = np.load(path / "embeddings.npy", allow_pickle=False).astype(np.float32)
        ids = json.loads((path / "embedding_ids.json").read_text(encoding="utf-8"))
        src = {v: i for i, v in enumerate(ids)}
        keep = [v for v in videos if v["vid"] in src]
        emb = emb[[src[v["vid"]] for v in keep]]

        return cls(
            videos=keep,
            by_vid={v["vid"]: v for v in keep},
            mentions=dict(mentions),
            related=related,
            taxonomy=taxonomy,
            embeddings=emb,
            row={v["vid"]: i for i, v in enumerate(keep)},
        )
