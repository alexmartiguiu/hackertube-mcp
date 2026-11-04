"""Eyeball recommendation quality on a fixed set of situations.

    uv run python scripts/try_queries.py            # embeddings only (the default)
    uv run python scripts/try_queries.py --rerank   # also mix in the cross-encoder
"""

import sys
import time

from hackertube_mcp.data import Corpus
from hackertube_mcp.search import Index

QUERIES = [
    "Simple Made Easy Rich Hickey",  # sanity: exact title should come first
    "I'm about to design the database schema for a new web app",
    "learn how transformers and large language models work from scratch",
    "I have to give a technical talk at a conference next month",
    "debugging a memory leak in production",
    "how to think about distributed systems and consensus",
    "I'm starting a startup and need to find product market fit",
    "negotiating my salary for a new engineering job",
    "writing fast code: CPU caches and data-oriented design",
    "I'm becoming an engineering manager for the first time",
    "understanding cryptography and how TLS works",
    "learning Rust coming from Python",
    "how does a CPU actually work at the transistor level",
    "why software projects are late and estimation is hard",
    "intuition for calculus",
    "improving my focus and productivity as a programmer",
    "security vulnerabilities and how hackers exploit them",
    "building a compiler or interpreter",
    "the history of Unix and Bell Labs",
    "how to cook a perfect steak",  # off-topic for HN: match should be low
    # situation plus the topical rephrasings an agent would pass as `also_phrased`
    ["I'm becoming an engineering manager for the first time", "engineering management", "leading a software team"],
    ["negotiating my salary for a new engineering job", "salary negotiation", "getting paid what you're worth"],
    ["I have to give a technical talk at a conference next month", "public speaking", "how to give a good talk"],
    ["learning Rust coming from Python", "Rust programming language introduction"],
    ["I want to understand how databases work internally so I can build a small one myself",
     "database internals", "building a database from scratch", "storage engines B-trees and LSM trees"],
]


def main() -> None:
    ix = Index(Corpus.load(), rerank="--rerank" in sys.argv)
    for q in QUERIES:
        t = time.perf_counter()
        hits = ix.search(q, k=3)
        ms = (time.perf_counter() - t) * 1000
        print(f"\n## {q if isinstance(q, str) else ' | '.join(q)}  ({ms:.0f} ms)")
        for v, final, rel in hits:
            print(f"  {rel:.2f} rel  {final:.2f} final  score={v['score']:<4}  {v['title'][:70]}  [{v['channel'][:24]}]")


if __name__ == "__main__":
    main()
