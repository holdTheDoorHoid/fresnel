# Writer pilot (2026-10-21)

The owner decided (DESIGN §1, "Writer"): the same stations are researched and written end to end by
**Haiku** and by **Sonnet**, each fact-checked by its own model, and shown side by side; the owner
picks the writer for the big run.

Output goes to `data/pilot_compare/<model>/stories/<id>.md` and `data/pilot_compare/<model>/research/<id>.json`
(git-ignored), never to `data/stories/` or `data/research/`. The owner's pick is published afterwards.

## Stations

One of each kind, from rich to thin evidence:

| id | why |
|---|---|
| `us-mn-split-rock` | a famous, richly documented US light |
| `us-mn-duluth-south-breakwater-outer` | a Great Lakes breakwater (pier) light |
| `us-de-cape-henlopen` | a lost light: an 18th-century tower lost to erosion; 61 roster lines |
| `ca-ns-sambro-island` | Canada: a very old, well-documented light; no USLHS roster |
| `us-pr-punta-higuero` | a Spanish-era Puerto Rico faro; Spanish sources |
| `us-nj-five-fathom-bank` | a lightship station |
| `us-nc-chicamacomico-life-saving-station` | a life-saving station with a famous rescue |

## Research prompt (one agent per station)

> You are researching and writing the history of one station for **Fresnel** (repo
> `/home/hoid/Desktop/fresnel`), a public site mapping every lighthouse, lightship station and
> life-saving station in the US and Canada with long, footnoted histories of each place and its people.
> Today is {today}. Station: `{id}`.
>
> 1. Read `research/STORY_GUIDE.md` in full: it is the specification (outputs, chapters, the atmosphere
>    rule, the keepers roster, evidence quotes, where to look, what not to use, budget). Read DESIGN.md
>    §1 rows "Stories" and "Atmosphere".
> 2. Brief: `python3 research/queue.py --briefs {id}` (the record may be wrong).
> 3. Research with the guide's tools, in its order. Put several shell commands in one Bash call.
> 4. Write **`data/pilot_compare/{model}/stories/{id}.md`** and
>    **`data/pilot_compare/{model}/research/{id}.json`** (this pilot's folders; NOT data/stories or
>    data/research). Nothing else; no git; do not call spawn_task or any notification tool.
> 5. Check your own quotes before you finish:
>    `python3 research/check_quotes.py --dir data/pilot_compare/{model} {id} --verbose`; fix any missing.
>
> Return: words, chapters used, number of sources, roster lines, confidence, and a one-line note on what
> you could not find.

## Fact-check prompt (one agent per station, same model)

> You are the independent fact-checker for one Fresnel story (repo `/home/hoid/Desktop/fresnel`). Today
> is {today}. Station `{id}`; files `data/pilot_compare/{model}/stories/{id}.md` and
> `data/pilot_compare/{model}/research/{id}.json`. Read `research/STORY_GUIDE.md` first.
>
> 1. `python3 research/check_quotes.py --dir data/pilot_compare/{model} {id} --verbose`.
> 2. For each missing quote, find the real wording at the source (`research/fetch_text.py`,
>    `research/corpus.py grep`, `research/newspapers.py --page`); replace it, or remove the claim.
> 3. Check every footnoted sentence against its evidence: numbers, names, dates and meaning. Fix or remove.
> 4. **Atmosphere audit:** for every vivid sentence ask "which footnote says this happened here?". Remove
>    or reframe anything imagined, any guessed feeling, any general context written as if local, and any
>    banned phrase (the guide's list). General context must be marked as general and cited.
> 5. Rewrite any sentence that copies a source's wording (beyond a marked quotation). Check footnote URLs
>    match the JSON sources. Check the roster lines against the evidence. Check units and place names.
> 6. Edit both files in place; re-run the quote check; add `"verification": {"checked": "{today}",
>    "claims_checked": n, "unsupported_removed": n, "errors_fixed": n, "atmosphere_fixes": n,
>    "quotes_not_found": n, "verdict": "pass|fixed|fail"}` to the JSON.
>
> Edit only those two files; no git. Return the verification block and a one-line note.
