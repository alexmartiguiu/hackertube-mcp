# hackertube-mcp

An MCP server that answers *"what should I watch for this?"* with the YouTube videos Hacker News
keeps telling each other to watch.

Huge props to [Andrej Karpathy](https://x.com/karpathy): this is built entirely on
[HackerTube](https://hackertube.org), his weekend hack ([announcement on X](https://x.com/karpathy/status/2116957135661945283)),
and on his decision to release all of its data for anyone to build on. hackertube-mcp just puts it inside your agent.

It runs over the open data export from [HackerTube](https://hackertube.org): 6,454 videos that at
least three different HN commenters recommended across at least three different months, from 2007 to 2026,
with LLM-written cards, 39,834 labeled HN comments, a 150-category topic tree and the
"same people also recommended" graph. Ask your agent something like *"I'm about to give my first
conference talk, what should I watch?"* and it gets back the two best picks, each with links and the reasons real HN
commenters gave for watching it.

Everything runs locally. There are no API keys and no LLM calls on the server, and queries take a few milliseconds.

> Unofficial. Not affiliated with HackerTube, Hacker News, Y Combinator, YouTube or Google.

## Quick start

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/alexmartiguiu/hackertube-mcp
cd hackertube-mcp
uv run hackertube-mcp --warmup   # one-off: downloads the 18 MB export + a 70 MB embedding model
uv run hackertube-mcp -q "I need to learn how transformers work"   # try it from the terminal
```

### Claude Code

```bash
claude mcp add hackertube -- uv --directory /path/to/hackertube-mcp run hackertube-mcp
```

### Claude Desktop / Cursor / any MCP client

```json
{
  "mcpServers": {
    "hackertube": {
      "command": "uv",
      "args": ["--directory", "/path/to/hackertube-mcp", "run", "hackertube-mcp"]
    }
  }
}
```

## Tools

| tool | what it does |
|---|---|
| `recommend(situation, k=2, also_phrased=[...])` | The k best picks for a situation or goal: summary, why HN likes it, up to 5 commenter reasons, pull quote, thumbnail. |
| `search_videos(query, k=10, topic=...)` | A broader semantic search that returns compact cards. |
| `get_video(vid)` | One video's full card plus the actual HN comments about it, recommendations first, with thread links. |
| `similar_videos(vid)` | Videos with similar content, and other videos the same HN commenters also recommended. |
| `list_topics(area=None)` | The topic tree: 16 areas and 150 categories, with video counts. |
| `top_in_topic(topic)` | HN's most consistently recommended videos in a category or area. |

| `brief_guide()` | The output and figure guide (see below). Agents call it before drawing anything. |

All search tools take optional `levels` and `content_types` filters. Videos that only matter around a
single news event, and videos HN only cited without recommending, are hidden by default.

## Briefs: what to watch, as figures

Ask for guidance rather than a list ("I keep having outages on call, what should I watch?") and the
agent builds a **brief**:

1. **Watch this one:** a single video, chosen for your situation, with why it fits and the best HN
   quote.
2. **Figure 1, the video in one picture:** the video's core idea drawn as a paper-style figure, with
   inputs, the mechanism in a dashed container, and what you'll get.
3. **Figure 2, your problem across all sources:** up to three concept columns (what goes wrong,
   then what to do), each with a small thumbnail of the video that explains that piece.

**Example:** [`examples/brief_5min_talk.html`](examples/brief_5min_talk.html)
([rendered](https://htmlpreview.github.io/?https://github.com/alexmartiguiu/hackertube-mcp/blob/main/examples/brief_5min_talk.html))
is what a fresh agent produced for *"I have a 5-minute presentation in two weeks. Make me a brief."* It
was given nothing but this MCP. It found the guide through the server instructions and picked Patrick
Winston's *How to Speak* as the one to watch. Figure 1 shows the lecture as one talk's timeline, and
Figure 2 shows what goes wrong in a short talk and what counters it. One CSS line was fixed by hand, so
the chip captions stack.

The format lives in [`brief_guide.md`](src/hackertube_mcp/brief_guide.md) and reaches agents three ways:
- the server instructions point agents to it
- the `brief_guide` tool returns it
- it's exposed as the resource `hackertube://brief-guide` and the prompt `brief(situation)`
  (`/mcp__hackertube__brief` in Claude Code)

It covers the figure grammar, the palette (light and dark), the layouts for each question type, and grounding rules
(every claim about a video must trace back to a card summary or HN comment, general background is flagged as such, and the agent may not invent a video's mechanism). Agents
are expected to adapt it to their client. Fork the file to change the house style.

## On a live board

hackertube works on its own. It also pairs with any live-board MCP server, meaning one that draws while it
narrates: connect both to your agent. `brief_guide` has an "On a live board" section that tells the agent
what to show and in what order: the hero video's core idea, grounded takeaways, and thumbnails next to the
ideas they teach.

## How ranking works

1. The query is embedded with `BAAI/bge-small-en-v1.5`, the model HackerTube used for
   `embeddings.npy`. `recommend` also embeds each `also_phrased` rephrasing. A video scores the average
   of its best and its mean similarity across the phrasings, so one stray phrasing can't pull in
   off-topic hits.
2. Cosine similarity is mapped to a relevance score in [0, 1].
3. That relevance is scaled by HackerTube's quality score: the number of distinct months HN
   recommended the video, log-squashed, with weight 0.3. Quality reorders relevant videos, but it can't push an off-topic
   classic to the top.
4. Re-uploads are removed by deduplicating on normalized title.

A cross-encoder reranker (`jinaai/jina-reranker-v1-turbo-en`) is available with
`HACKERTUBE_RERANK=1`. It's off by default. In testing it was better on exact titles but scored
situation-style questions ("I'm becoming an engineering manager") close to zero, and it adds a 130 MB
model and about 600 ms per query.

`scripts/try_queries.py` runs 24 sample questions so you can eyeball the results.

**What it's good at:** technical topics HN loves, such as distributed systems, performance,
compilers, cryptography, ML, computing history and math intuition.

**What's thin:** career and soft skills (salary negotiation, management), and anything HN doesn't link
to much. Situation-style questions work much better when the agent passes topical rephrasings in
`also_phrased`, and the tool description tells it to.

## Configuration

| env var | default | meaning |
|---|---|---|
| `HACKERTUBE_DATA_DIR` | `~/.cache/hackertube-mcp/data` | where the export is downloaded and read from |
| `HACKERTUBE_RERANK` | `0` | set to `1` to mix in the cross-encoder |

## Tests

```bash
uv run python tests/test_stdio.py     # launches the server over stdio and calls every tool
uv run python scripts/try_queries.py  # eyeball ranking quality
```

## Roadmap

The export has no transcripts, so the current "tips" are what HN commenters said about each video,
not what the video itself says. Next steps:

- **Transcripts → tips with timestamps.** Fetch captions, have a small model (for example Gemini Flash-Lite)
  write 5–10 concrete takeaways per video with timestamp links, and embed transcript chunks for
  passage-level search. Rough cost for the whole corpus is about 60M input tokens, or roughly $5–30 depending on the model.
  Raw transcripts won't be redistributed; each user regenerates them locally.
- **YouTube metadata** (durations, so you can filter by "under 20 minutes") through a free YouTube Data API key. See
  `DATA.md` in the export.
- **A `render_brief` tool** that fills a fixed HTML template from the agent's content, so every client
  gets the same polished page, even a plain terminal.

## Acknowledgements

This project stands entirely on [HackerTube](https://hackertube.org), the weekend hack by
[Andrej Karpathy](https://x.com/karpathy) ([announcement on X](https://x.com/karpathy/status/2116957135661945283)).
He had Claude Opus 5.5 filter 43M comments from 20 years of Hacker News down to the 6,454 videos people
keep recommending, then released the cards, labeled comments, topic tree and embeddings for anyone to
build on. All of the curation, the video cards and the vectors this server searches come from that work.
Thank you to Andrej, to the Claude-built HackerTube pipeline, and to the HN commenters who have been
pointing each other at great talks for two decades.

## License and credits

Code: MIT.

The data isn't included in this repo. It's downloaded at runtime from
[hackertube.org/data](https://hackertube.org/data) under
[ODC-By 1.0](https://opendatacommons.org/licenses/by/1-0/). Credit goes to **HackerTube**
(https://hackertube.org) and the
[open-index/hacker-news](https://huggingface.co/datasets/open-index/hacker-news) dataset. HN comments
remain the work of their authors. Video titles and channel names belong to their creators. The
summaries and labels were written by an LLM, so expect a few to be off.
