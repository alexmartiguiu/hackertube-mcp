# HackerTube brief: output and figure guide

How to turn hackertube tool results into a **brief**: one video worth watching, a figure of that
video's core idea, and a figure of the user's problem built from everything retrieved. Adapt the
layout to the user's question, client and medium, but always draw the figures and keep the
grounding rules.

**Visual first, very little prose.** The figures carry the content. Outside them, write only:
- the card's one-sentence "why it fits you" and its one quote
- a one-line caption for each figure
- a one-line source note under each figure
- at most one sentence of caveats, and only if the corpus is thin
- for a "how does X work" question, at most 4 short bullets of key facts the figures can't hold

Don't add anything else: no bulleted "what HN says" lists, no paragraphs explaining a figure,
no section intros. If a point matters, put it in a figure block or a thumbnail chip.

**The figures are the brief: always draw both.** Thin data changes what a figure shows, never
whether you draw it. Sections 2 and 3 say what to draw when the evidence is thin. A text-only answer
is a failure of this guide, unless the client truly can't show visuals (see section 7).

**Explaining a topic is not an exception.** When the user wants to understand something ("how do US
elections work"), the figures carry the explanation: Figure 2 in the learning layout is the concept
ladder, and its blocks may hold general knowledge, flagged in the source note. Don't write a prose
explainer instead of the figures, or before them.

## 0. Gather

1. `recommend(situation, k=4, also_phrased=[2-3 topical rephrasings])`. A brief needs four picks to
   choose from, even though a quick "what should I watch" answer uses only 2-3.
2. Pick the hero (see 1). Call `get_video(hero)` for the real HN comments: they carry most of the
   substance for Figure 1.
3. Optionally `get_video` on one or two supporting picks, and `similar_videos(hero)` if the
   picks look thin.
4. **Sanity-check the picks by their titles and summaries, not only by `match`.** An off-topic pick
   can still score 0.5+ on a shared word ("trees" matching parsers and APL). If picks drift off
   topic, run `search_videos` on 2-3 specific subtopics and `top_in_topic` on the matching
   category (`list_topics` gives the ids). The hero can come from any of these calls.
5. If every relevant pick's `match` is below ~0.4, say the corpus is thin on this, in one caveat
   sentence. Still draw both figures, using the thin-data forms in sections 2 and 3.

## 1. Watch this one (card)

- Title, channel, type, and the link (`url`).
- **One sentence on why it fits this user's situation.** Write it for them, not a generic summary.
- The best HN quote (`quote`), attributed to HN with its year.
- The HN signal: `hn_recommenders` and `hn_years`.
- **Pick the hero by fit to the situation, not by rank.** Rank is topical match times HN
  popularity. A course introduction can outrank the talk that actually answers the question.
- When a short pick and a deep pick both fit (a 1-hour intro and a 3-hour deep dive), name both:
  "Watch X; if you have an evening, Y."

## 2. Figure 1: the hero video in one picture

Purpose: depth. The user should get the video's core idea from the figure and know what they'll
gain by watching.

Grammar, left to right:

| zone | color | content |
|---|---|---|
| Inputs or forces | peach | at most 3 blocks: what pushes on the system, or what the video starts from |
| Mechanism | lavender, inside a dashed container | the core idea **drawn as a picture**: dots drifting, a boundary, a pipeline, a loop. Not a list of boxes. Coral marks danger or failure. |
| What you'll get | green | at most 3 blocks: what understanding the idea lets you do |

Then add a small legend for the meaning of the three colors, and an italic serif caption:
*Figure 1. <video title>, in one picture.*

When the hero is a course, series or overview rather than one idea, draw the **structure of what it
covers** (layers, a syllabus arc) using only the parts the comments or summary name. Leave the
unnamed parts as unlabeled shapes, and say in the source note if the ordering comes from general
knowledge.

Fallback (thin data): if the card, `hn_says` and comments don't describe the mechanism, draw the
"what you'll get" form instead. Keep the inputs and outcomes columns, put a simple labeled center
in the middle (the video's own title, or the topics its summary lists, in order), and say so in the
source note. **Never invent the mechanism, and never skip the figure because of that rule:** the
fallback is the figure.

## 3. Figure 2: the user's problem, across all sources

Purpose: breadth. The user's problem as a chain of concepts assembled from every retrieved video,
with each piece credited to the video that explains it best. They can stop at the figure, or jump
to the right video for the piece they need.

- **2 or 3 concept columns**, read left to right as a causal or logical chain. Use 2 when that's
  all the evidence supports; don't pad a third column with an off-topic video. With only one usable
  video, draw 2 columns from its own summary and comments, and credit both to it.
- **Top row**, inside a dashed container: what's going on. One lavender block per concept, each
  with a small glyph built from simple shapes (a grid with a few coral cells, a trail of dots, a
  command hitting a target).
- **Bottom row:** a green block under each column. What it holds depends on the layout (see the
  table below): what to do, the video to watch, or the trade-off. Connect it upward with a short
  green arrow, and label the relation once ("counters", "teaches", "pick it when").
- **Under each column**, a thumbnail chip for the video that teaches that piece: at most 2 per
  column, the second one smaller. Use the chip row markup below as is, so the chips line up with
  the columns (see "Chip row").
- Finish with a legend (what goes wrong / what to do / where it's explained) and an italic caption.
- Under each figure, add a one-line **source note** of at most about 25 words, in small muted text: name
  the sources, and flag any of your own framing ("Sources: HN comments on the CMU course; layer
  order is general knowledge."). The chips already credit each column, so don't explain them
  again.

The column layout follows the question type:

| question | columns | rows |
|---|---|---|
| Situation ("outages keep happening") | stages of the problem | what goes wrong → what to do |
| Learning ("understand LLMs") | a concept ladder: basics → mechanism → frontier | the idea → the video to watch, in watch order |
| Choosing ("SQL or NoSQL") | the options | "pick it when" → the trade-off |

### Chip row

Paste this under the Figure 2 SVG and fill in the placeholders. Set `--cols` to the number of
concept columns, give one `ht-col` per column in the same order, and draw the SVG's columns at
equal widths across the full 680 viewBox, so each `ht-col` sits under its column. Add
`class="ht-chip small"` for a column's second chip, and the `ht-tag` only on the hero's chip.
The grey background stands in for the thumbnail when images are blocked.

```html
<div class="ht-chips" style="--cols:3">
  <div class="ht-col">
    <a class="ht-chip" href="URL" target="_blank" rel="noopener">
      <img src="https://i.ytimg.com/vi/VID/mqdefault.jpg" alt="">
      <span class="ht-meta">
        <span class="ht-title">TITLE</span>
        <span class="ht-sub">CHANNEL</span>
        <span class="ht-sub">N HN recommenders</span>
        <span class="ht-tag">Figure 1</span>
      </span>
    </a>
  </div>
  <!-- one more .ht-col per column -->
</div>
<style>
  .ht-chips { display: grid; grid-template-columns: repeat(var(--cols), minmax(0, 1fr)); gap: 12px;
              max-width: 680px; margin: 6px auto 0; font: 12px/1.3 system-ui, sans-serif; }
  .ht-col { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
  .ht-chip { display: flex; gap: 8px; align-items: flex-start; min-width: 0; color: inherit; text-decoration: none; }
  .ht-chip img { flex: none; width: 76px; height: 43px; object-fit: cover; border-radius: 6px; background: #D3D1C7; }
  .ht-chip.small img { width: 56px; height: 32px; }
  .ht-meta { display: flex; flex-direction: column; min-width: 0; }
  .ht-title { font-weight: 600; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .ht-sub { opacity: .7; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ht-tag { font-size: 10px; padding: 0 5px; border-radius: 4px; background: #EEEDFE; color: #3C3489; align-self: flex-start; margin-top: 2px; }
</style>
```

## 4. Visual style

Clean, aesthetic, paper-figure look: soft pastel blocks, generous whitespace, thin gray
connectors, a dashed container around the core mechanism, a legend and a caption.

- **One idea per block.** Titles at most 4 words, subtitles at most 5. Keep to about 12 text items per
  figure, not counting the legend, caption and source note. If it feels crowded, cut text, never
  shrink it.
- **Color means something, and nothing else.** Use three roles (lavender, peach, green) in both
  figures. Coral is an accent for danger or failure only; leave it out when nothing fails.
- Blocks have rounded corners (10 px radius) and no border, or a 0.5 px border on green. Connectors
  are 1 px `#888780`, with at most one arrow between neighbors.
- Sans-serif for labels (14 px titles, 12 px subtitles); a serif italic only for the caption.
- Flat fills: no gradients, shadows or rotated text.
- Support dark mode by switching to the dark stops.

| role | light fill | light title / subtitle | dark fill | dark title / subtitle |
|---|---|---|---|---|
| Lavender: mechanism, evidence | `#EEEDFE` | `#3C3489` / `#534AB7` | `#3C3489` | `#EEEDFE` / `#CECBF6` |
| Peach: forces, inputs | `#FAEEDA` | `#633806` / `#854F0B` | `#633806` | `#FAEEDA` / `#FAC775` |
| Green: outcomes, actions | `#EAF3DE` (border `#97C459`) | `#27500A` / `#3B6D11` | `#27500A` | `#EAF3DE` / `#C0DD97` |
| Coral: danger, failure | `#F5C4B3`, accent `#D85A30` | `#712B13` | `#993C1D` | `#FAECE7` |
| Dashed container | stroke `#AFA9EC`, dash `6 5` | | stroke `#7F77DD` | |

Use an SVG `viewBox` 680 wide. Figure 1 is about 680×460 and Figure 2 about 680×340, plus the
chip row in HTML below it.

## 5. Grounding

- Every claim about a video (what it covers, why it's worth watching) must trace back to a card
  `summary`, `why_hn`, `hn_says` line or HN comment.
- General background (how a system works, a definition, a number) may come from your own knowledge.
  Use it where the videos don't cover a piece, and say so in the figure's source note.
- These are summaries and comments, not transcripts. Never claim what's said at a specific minute.
- Use at most one verbatim HN quote per video, under about 15 words, attributed to "HN" and the year.
  Paraphrase everything else.
- Credit HackerTube (https://hackertube.org) when you publish or share a brief.

## 6. On a live board

Some clients present results on a live board: a tool that narrates aloud while it draws, one beat
at a time. There, skip the card and the two static figures. Instead, build **one evolving figure**
in about a minute (5 to 7 beats):

1. **Title:** the visitor's outcome in their words ("Nail your five-minute talk").
2. **Their problem today**, in their own terms.
3. **The hero video's core idea**, drawn as a picture in the centre (a timeline, a mechanism, a
   loop), from its summary, `hn_says` and comments.
4. **Two or three concrete takeaways**, one per beat, each traceable to a card or comment. Name
   the talk it comes from as you say it.
5. **Each video's thumbnail** (`https://i.ytimg.com/vi/<vid>/mqdefault.jpg`, or the board's own
   thumbnail support) next to the idea it teaches, linked to its `url`. Mark the hero "watch first".
6. **Close** by naming the one video to watch first and offering a follow-up.

While narrating, mention the HN signal briefly ("seventeen commenters recommend it"), and flag
anything that comes from your own knowledge rather than the data. The board's own style and
timing rules come first; this section only says what to show and in what order.

## 7. Delivery

Use the first of these the client supports:
1. **A live board** (a connected tool that narrates while it draws): follow section 6 instead of
   the card and static figures.
2. **Inline visuals:** you have a tool that renders SVG or HTML widgets in the conversation (for
   example a "show widget" or "visualize" tool). Draw the card and both figures with it. SVG or
   HTML pasted into your reply text doesn't count: most clients show it as code.
3. **A file:** if you can write files, write one self-contained HTML page with the card and both
   figures, and give its path.
4. **Plain text** only if none of the above exists: give the card as text and describe the
   figures in a few lines.
