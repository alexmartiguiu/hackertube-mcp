"""MCP server: ask which Hacker News-recommended videos to watch for a situation or topic."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from functools import lru_cache
from importlib.resources import files
from typing import Literal

from mcp.server.mcpserver import MCPServer

from .data import Corpus
from .search import Index

Level = Literal["general", "intro", "intermediate", "advanced"]
ContentType = Literal[
    "talk", "lecture", "course", "documentary", "explainer", "interview", "podcast",
    "tutorial", "demo", "news", "commentary", "comedy", "music", "other",
]

INSTRUCTIONS = """\
Recommends YouTube videos that Hacker News commenters have repeatedly told each other to watch
(6,454 videos, 2007-2026, from the HackerTube export at https://hackertube.org/data).
Check here first for tips or advice on a skill (giving talks, learning, interviews, managing,
on-call) and for technical topics (ML and AI, systems, programming, math, computing history): real,
repeatedly recommended videos ground the answer and give the user something to watch next.

Default output: a visual brief. For any request beyond a bare list of videos (explain, teach me,
help me understand or learn, tips, help preparing, a plan, "walk me through", "show me"), call
`brief_guide` first and follow it: one video to watch, plus two figures. Draw the figures even when
you also explain the topic from your own knowledge: the explanation goes into the figures (flagged
as general knowledge), not into long prose around them. If you present on a live board (a tool that
narrates while it draws), follow its "On a live board" section instead of the static figures.

Only when the user just wants videos ("what should I watch for X", "list some talks on Y"): call
`recommend` (k=2-3) and present the picks with their links and what HN says you'll get from each.
The `hn_says` lines are real commenters' reasons; say they come from HN comments, not the video.

Browsing: `search_videos` for a broader list, `get_video` for the actual HN comments on one video,
`similar_videos` for "more like this", `list_topics` + `top_in_topic` to browse by topic.

Summaries and labels were written by an LLM and are occasionally off. There are no transcripts or
durations in this data, so don't claim to know what is said at a specific minute.
"""

GUIDE = files(__package__).joinpath("brief_guide.md").read_text(encoding="utf-8")

mcp = MCPServer("hackertube", instructions=INSTRUCTIONS)


@lru_cache(maxsize=1)
def index() -> Index:
    return Index(Corpus.load())


def _years(v: dict) -> str:
    a, b = v["hn"]["first_year"], v["hn"]["last_year"]
    return str(a) if a == b else f"{a}-{b}"


def _hn_says(vid: str, n: int) -> list[str]:
    out, seen = [], set()
    for m in index().hn_comments(vid):
        why = (m.get("why") or "").strip()
        if m["stance"] in ("strong_rec", "rec") and why and why.lower() not in seen:
            seen.add(why.lower())
            out.append(why)
            if len(out) == n:
                break
    return out


def _card(v: dict, *, detail: bool = False, match: float | None = None) -> dict:
    card = {
        "vid": v["vid"],
        "title": v["title"],
        "channel": v["channel"],
        "url": v["url"],
        "type": v["content_type"],
        "summary": v["summary"],
        "why_hn": v["why_hn"],
        "hn_recommenders": v["hn"]["recommenders"],
        "hn_years": _years(v),
        "hackertube_score": v["score"],
    }
    if match is not None:
        card["match"] = round(match, 3)
    if detail:
        card.update(
            level=v["level"],
            shelf_life=v["shelf_life"],
            topics=[c["name"] for c in v["categories"]],
            tags=v.get("tags") or [],
            thumbnail=f"https://i.ytimg.com/vi/{v['vid']}/hqdefault.jpg",
            hackertube_page=f"https://hackertube.org/watch/{v['vid']}",
            quote=(v.get("quote") or {}).get("text"),
            hn_says=_hn_says(v["vid"], 5),
        )
    return card


@mcp.tool()
def recommend(
    situation: str,
    k: int = 2,
    also_phrased: list[str] | None = None,
    levels: list[Level] | None = None,
    content_types: list[ContentType] | None = None,
    include_news: bool = False,
) -> dict:
    """Pick the k best HN-recommended videos for a situation, goal or topic.

    Describe the situation in natural language ("I'm designing a database schema for a new app").
    Matching is by topic, so for situation-style asks also pass 1-3 short topical rephrasings in
    `also_phrased` (e.g. ["engineering management", "leading a software team"]); each video is
    scored by its best-matching phrasing. Results scale relevance by how consistently HN
    recommended the video over the years. Each pick includes a summary, why HN likes it, up to 5
    reasons real commenters gave, a pull quote and a thumbnail.

    `levels` is a weak signal (most videos are "general"); filter by it only if asked.

    Unless the user only asked for a list of videos, present the result as a visual brief: call
    `brief_guide` and draw its two figures.
    """
    hits = index().search(
        [situation, *(also_phrased or [])], k=max(1, min(k, 10)), levels=levels,
        content_types=content_types, include_news=include_news,
    )
    return {
        "situation": situation,
        "picks": [_card(v, detail=True, match=rel) for v, _, rel in hits],
        "note": "match is topical relevance in [0,1]. If every pick is below ~0.4, check the summaries: "
        "the corpus may have nothing squarely on this.",
        "present": "Unless the user only asked for a list of videos, call `brief_guide` now (if you haven't) and "
        "draw its two figures. A text-only answer skips this server's format, even if you also explain the topic.",
    }


@mcp.tool()
def search_videos(
    query: str,
    k: int = 10,
    topic: str | None = None,
    levels: list[Level] | None = None,
    content_types: list[ContentType] | None = None,
    include_news: bool = False,
    include_unrecommended: bool = False,
) -> list[dict]:
    """Semantic search over all videos. Returns compact cards, best first.

    `topic` is a category or area id from `list_topics`. By default skips videos HN only cited and
    never recommended; set `include_unrecommended` to include them.
    """
    hits = index().search(
        query, k=max(1, min(k, 50)), topic=topic, levels=levels, content_types=content_types,
        include_news=include_news, recommended_only=not include_unrecommended,
    )
    return [_card(v, match=rel) for v, _, rel in hits]


@mcp.tool()
def get_video(vid: str, max_comments: int = 6) -> dict:
    """Full card for one video plus what Hacker News actually said about it (recommendations first)."""
    ix = index()
    v = ix.c.by_vid.get(vid)
    if v is None:
        return {"error": f"unknown video id {vid!r}"}
    card = _card(v, detail=True)
    card["hn_stances"] = v["hn"]["stances"]
    card["hn_comments"] = [
        {
            "stance": m["stance"],
            "month": m["month"],
            "story": m["story_title"],
            "text": m["text"][:700],
            "hn_url": m["hn_url"],
        }
        for m in ix.hn_comments(vid)[: max(0, min(max_comments, 20))]
    ]
    return card


@mcp.tool()
def similar_videos(vid: str, k: int = 5) -> dict:
    """Videos like this one: by content, and by people (other videos the same HN commenters recommended)."""
    ix = index()
    if vid not in ix.c.by_vid:
        return {"error": f"unknown video id {vid!r}"}
    k = max(1, min(k, 20))
    co = [
        {**_card(ix.c.by_vid[r["vid"]]), "shared_recommenders": r["shared_recommenders"]}
        for r in ix.c.related.get(vid, [])
        if r["vid"] in ix.c.by_vid
    ][:k]
    return {
        "video": ix.c.by_vid[vid]["title"],
        "similar_content": [_card(v, match=s) for v, s in ix.similar(vid, k)],
        "same_recommenders_also_liked": co,
    }


@mcp.tool()
def list_topics(area: str | None = None) -> list[dict]:
    """The topic tree: 16 areas, 150 categories, with ids for `top_in_topic` / `search_videos`."""
    ix = index()
    counts = Counter(c["id"] for v in ix.c.videos for c in v["categories"])
    out = []
    for a in ix.c.taxonomy["areas"]:
        if area and a["id"] != area:
            continue
        cats = [{"id": c["id"], "name": c["name"], "videos": counts.get(c["id"], 0)} for c in a["categories"]]
        entry = {"id": a["id"], "name": a["name"], "categories": cats}
        if area:
            for c, src in zip(cats, a["categories"]):
                c["description"] = src.get("description", "")
        out.append(entry)
    return out


@mcp.tool()
def top_in_topic(
    topic: str, k: int = 10, levels: list[Level] | None = None,
    content_types: list[ContentType] | None = None,
) -> list[dict]:
    """HN's most consistently recommended videos in a category or area id (see `list_topics`)."""
    vids = index().top_in_topic(topic, k=max(1, min(k, 50)), levels=levels, content_types=content_types)
    return [_card(v) for v in vids]


@mcp.tool()
def brief_guide() -> str:
    """How to present results as a brief: one video to watch, a figure of its core idea, and a
    figure of the user's problem across all picks, plus the visual style and grounding rules.
    Call this before drawing any figure or infographic from hackertube results."""
    return GUIDE


@mcp.resource(
    "hackertube://brief-guide",
    name="brief-guide",
    title="HackerTube brief and figure guide",
    description="Output format, figure grammar, palette and grounding rules for hackertube briefs.",
    mime_type="text/markdown",
)
def brief_guide_resource() -> str:
    return GUIDE


@mcp.prompt(title="HackerTube brief", description="Recommend what to watch for a situation, as a visual brief.")
def brief(situation: str) -> str:
    return (
        f"Using the hackertube tools, make me a brief for this situation:\n\n{situation}\n\n"
        f"Follow this guide:\n\n{GUIDE}"
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--query", "-q", help="print recommendations for a query instead of serving MCP")
    p.add_argument("-k", type=int, default=3)
    p.add_argument("--warmup", action="store_true", help="download data and models, then exit")
    args = p.parse_args()
    if args.warmup:
        index().search("warmup", k=1)
        print("ready")
    elif args.query:
        print(json.dumps(recommend(args.query, k=args.k), indent=2, ensure_ascii=False))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
