export const meta = {
  name: 'fresnel-story-batch',
  description: 'Fresnel station histories: research and write, then an independent fact-check by the same model; model and group size from args',
  phases: [
    { title: 'Research', detail: 'one agent per group of stations writes the stories and research files' },
    { title: 'Fact-check', detail: 'one checker per group, same model, edits in place and adds a verification block' },
  ],
}

// args: { today: 'YYYY-MM-DD', model: 'sonnet' | 'haiku', ids: [...], group: 1 }
const ROOT = '/home/hoid/Desktop/fresnel'
const today = args.today
const ids = args.ids
const MODEL = args.model || 'haiku'
const GROUP = args.group || (MODEL === 'sonnet' ? 1 : 3)
const OPTS = MODEL === 'haiku' ? { model: MODEL } : { model: MODEL, effort: 'medium' }
const groups = []
for (let i = 0; i < ids.length; i += GROUP) groups.push(ids.slice(i, i + GROUP))
const short = (id) => id.replace(/^(us|ca)-/, '')

const COMMON = `
- **The specification is ${ROOT}/research/STORY_GUIDE.md. Read it in full first**, including "Mistakes the pilot found" and "Where to look". DESIGN.md §1 rows "Stories" and "Atmosphere" are the owner's rules behind it.
- **Scratch files:** use a private folder only: \`${ROOT}/research/.work/<station-id>-<research|check>/\` (git-ignored). Never write scratch files anywhere else, and never use generic file names in shared places: other agents run at the same time.
- **Search:** \`python3 ${ROOT}/research/websearch.py "<query>" -n 8\` (add \`--country CA\` for Canada, \`--lang fr\` for French), never the WebSearch tool. Newspapers only through \`research/newspapers.py\`, never loc.gov directly.
- Tools: Bash, Read, Write, Edit; WebFetch only if \`research/fetch_text.py\` fails. No git. Do not call spawn_task or any task, chip or notification tool.`

const RESEARCH_SCHEMA = {
  type: 'object',
  properties: { stations: { type: 'array', items: { type: 'object', properties: {
    id: { type: 'string' }, words: { type: 'integer' }, sources: { type: 'integer' }, roster: { type: 'integer' },
    confidence: { type: 'string' }, note: { type: 'string' } }, required: ['id', 'words', 'sources', 'roster', 'confidence', 'note'] } } },
  required: ['stations'],
}
const CHECK_SCHEMA = {
  type: 'object',
  properties: { stations: { type: 'array', items: { type: 'object', properties: {
    id: { type: 'string' }, verdict: { type: 'string', enum: ['pass', 'fixed', 'fail'] }, claims_checked: { type: 'integer' },
    unsupported_removed: { type: 'integer' }, errors_fixed: { type: 'integer' }, atmosphere_fixes: { type: 'integer' },
    quotes_not_found: { type: 'integer' }, note: { type: 'string' } },
    required: ['id', 'verdict', 'claims_checked', 'unsupported_removed', 'errors_fixed', 'atmosphere_fixes', 'quotes_not_found', 'note'] } } },
  required: ['stations'],
}

const researchPrompt = (g) => `Research and write the histories of ${g.length === 1 ? 'one station' : g.length + ' stations'} for Fresnel (repo ${ROOT}), a public site mapping every lighthouse, lightship station and life-saving station in the US and Canada with long, footnoted histories of each place and its people. Today is ${today}.
${COMMON}

Stations: ${g.join(', ')}. Compact briefs of our records (they may be wrong): \`cd ${ROOT} && python3 research/queue.py --briefs ${g.join(' ')}\`

For each station: research it in the guide's order, write \`${ROOT}/data/stories/<id>.md\` and \`${ROOT}/data/research/<id>.json\`, then run \`python3 research/check_quotes.py <id> --verbose\` and fix any missing quote before moving on. Length follows the evidence (a thin station gets a short honest story). ${g.length > 1 ? `**Finish all ${g.length} before you return.**` : ''} Write only those files. Return one row per station.`

const checkPrompt = (g) => `You are the independent fact-checker for ${g.length === 1 ? 'one Fresnel story' : g.length + ' Fresnel stories'} (repo ${ROOT}). Today is ${today}. Stations: ${g.join(', ')}; files \`data/stories/<id>.md\` and \`data/research/<id>.json\`.
${COMMON}

For each station:
1. If either file is missing, verdict "fail" and move on. Confirm the story is about this station.
2. \`cd ${ROOT} && python3 research/check_quotes.py <id> --verbose\`. For each missing quote, find the real wording at its source (\`research/fetch_text.py\`, \`research/corpus.py grep\`, a cached newspaper page); replace it, or remove the claim.
3. The quote script only proves each quote is somewhere in its source. **Read the story sentence by sentence against its evidence and sources**: numbers, names, dates, page numbers and meaning must match. Spot-check at least five quotes in the sources yourself, and read the page image (\`corpus.py page\`) for any name or date the researcher matched by column position in an OCR'd table. Fix or remove anything unsupported.
4. Check every item in the guide's "Mistakes the pilot found": disagreements stated, no unsourced details, Wikipedia not cited as a source, second-hand quotes footnoted to the page actually read, fiscal years, same-name stations, people linked only when a source connects them, no first person.
5. **Atmosphere audit:** for every vivid sentence ask "which footnote says this happened here?". Remove or reframe anything imagined, any guessed feeling, general context written as if local, and the guide's banned phrases.
6. Rewrite sentences that follow a source's wording too closely. Footnote URLs must match the JSON sources. Roster lines must match their evidence. Living-people rule (service after about 1960). Units (US feet first, Canada metres first, sea distances in nautical miles where the source says so).
7. Edit both files in place, re-run the quote check, and add \`"verification": {"checked": "${today}", "claims_checked": n, "unsupported_removed": n, "errors_fixed": n, "atmosphere_fixes": n, "quotes_not_found": n, "verdict": "pass|fixed|fail"}\` to the JSON (quotes_not_found = missing on your FIRST run). "pass" only if you changed nothing.

Edit only those files. Return one row per station.`

const results = await pipeline(
  groups,
  (g, _o, i) => agent(researchPrompt(g), { label: `research ${i + 1}: ${g.map(short).join(', ')}`, phase: 'Research', schema: RESEARCH_SCHEMA, ...OPTS }),
  (r, g, i) => agent(checkPrompt(g), { label: `check ${i + 1}: ${g.map(short).join(', ')}`, phase: 'Fact-check', schema: CHECK_SCHEMA, ...OPTS })
    .then((v) => ({ research: r && r.stations, check: v && v.stations })),
)
const rows = []
for (const x of results.filter(Boolean)) for (const v of x.check || []) rows.push(v)
const verdicts = {}
for (const v of rows) verdicts[v.verdict] = (verdicts[v.verdict] || 0) + 1
const fixes = rows.reduce((a, v) => a + v.unsupported_removed + v.errors_fixed + v.atmosphere_fixes, 0)
log(`Checked ${rows.length} of ${ids.length} (${MODEL}): ${JSON.stringify(verdicts)}, ${fixes} fixes`)
const problems = rows.filter((v) => v.verdict === 'fail' || v.quotes_not_found > 0).map((v) => ({ id: v.id, verdict: v.verdict, nf: v.quotes_not_found, note: (v.note || '').slice(0, 300) }))
const missing = ids.filter((id) => !rows.some((v) => v.id === id))
return { model: MODEL, verdicts, checked: rows.length, of: ids.length, fixes, problems, missing }
