"""End-to-end smoke test: launch the server over stdio and call every tool.

    uv run python tests/test_stdio.py
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def _payload(result) -> object:
    if result.structured_content is not None:
        sc = result.structured_content
        return sc.get("result", sc) if isinstance(sc, dict) and set(sc) == {"result"} else sc
    return json.loads(result.content[0].text)


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "hackertube_mcp.server"], env=dict(os.environ)
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as s:
        init = await s.initialize()
        assert "Hacker News" in (init.instructions or "")
        tools = {t.name for t in (await s.list_tools()).tools}
        assert tools == {"recommend", "search_videos", "get_video", "similar_videos", "list_topics", "top_in_topic", "brief_guide"}, tools
        assert "brief_guide" in (init.instructions or "")

        guide = (await s.call_tool("brief_guide", {})).content[0].text
        assert "Figure 1" in guide and "Grounding" in guide
        resources = {str(r.uri) for r in (await s.list_resources()).resources}
        assert "hackertube://brief-guide" in resources, resources
        res = await s.read_resource("hackertube://brief-guide")
        assert res.contents[0].text == guide
        prompts = {p.name for p in (await s.list_prompts()).prompts}
        assert "brief" in prompts, prompts
        msg = await s.get_prompt("brief", {"situation": "on call with outages"})
        assert "on call with outages" in msg.messages[0].content.text and "Figure 2" in msg.messages[0].content.text

        rec = _payload(await s.call_tool("recommend", {
            "situation": "I have to give a technical talk at a conference",
            "also_phrased": ["public speaking", "how to give a good talk"],
        }))
        picks = rec["picks"]
        assert len(picks) == 2 and picks[0]["title"] == "How to Speak", picks[0]["title"]
        assert picks[0]["hn_says"] and picks[0]["url"].startswith("https://www.youtube.com/")
        vid = picks[0]["vid"]

        hits = _payload(await s.call_tool("search_videos", {"query": "distributed consensus", "k": 5, "topic": "software"}))
        assert isinstance(hits, list)

        video = _payload(await s.call_tool("get_video", {"vid": vid, "max_comments": 3}))
        assert len(video["hn_comments"]) == 3 and video["hn_comments"][0]["stance"] == "strong_rec"
        assert "error" in _payload(await s.call_tool("get_video", {"vid": "nope"}))

        sim = _payload(await s.call_tool("similar_videos", {"vid": vid, "k": 3}))
        assert len(sim["similar_content"]) == 3 and all(v["vid"] != vid for v in sim["similar_content"])

        areas = _payload(await s.call_tool("list_topics", {}))
        assert len(areas) == 16
        cat = areas[0]["categories"][0]["id"]
        top = _payload(await s.call_tool("top_in_topic", {"topic": cat, "k": 3}))
        assert len(top) == 3

        print(f"ok: {len(tools)} tools; recommend -> {[p['title'] for p in picks]}")
        print(json.dumps(picks[0], indent=2, ensure_ascii=False)[:1500])


asyncio.run(main())
