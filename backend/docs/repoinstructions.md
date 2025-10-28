1) Map→Reduce prompting workflow (recommended)

You’ll get the most reliable results by running two passes:

Pass A (MAP): One request per file → extract a compact JSON summary of that file’s integration edges.
Pass B (REDUCE): One request that merges all JSON summaries → outputs the final PlantUML sequence diagram(s) + an edge table.

This keeps context small and avoids hallucinations.

⸻

Pass A (MAP) — System message:
You are a COBOL repository integration mapper. Given ONE COBOL source file, you must extract ONLY verifiable integration facts (program ID, static/dynamic calls, CICS links/XCTLs, SQL CALLs, file/queue usage, entry points). Do not infer missing details. If uncertain, mark fields as "unknown" and set "confidence": "low".

Pass A (MAP) — User message template (run once per file)

Replace the placeholders. Keep the schema exactly—your reducer depends on it.

INPUT METADATA
- repo: {{REPO_NAME}}
- file: {{FILENAME}}
- language: COBOL
- goal: extract inter-program integration edges

<<<CODE>>>
{{COBOL_SOURCE}}
<<<END-CODE>>>

RESPONSE FORMAT (STRICT JSON)
Return ONLY a JSON object with this schema:

{
  "program_id": "string | null",               // from PROGRAM-ID
  "alternate_entry_points": ["..."],           // from ENTRY statements (if any)
  "static_calls": [                            // CALL 'LITERAL' USING ...
    {
      "callee": "string",                      // literal program name
      "using_params": ["BY REFERENCE|BY CONTENT|BY VALUE|unknown"],
      "on_exception": "handled|not_present|unknown",
      "conditional_invocation": "brief predicate or 'no'",
      "source_paragraph": "paragraph-name-or-line",
      "confidence": "high|medium|low"
    }
  ],
  "dynamic_calls": [                           // CALL var USING ...
    {
      "callee_expr": "source identifier/expression",
      "possible_values": ["if discernible from VALUE/88-levels"], 
      "source_paragraph": "paragraph-or-line",
      "conditional_invocation": "brief predicate or 'unknown'",
      "confidence": "medium|low"
    }
  ],
  "cics_links": [                              // EXEC CICS LINK/XCTL/START/RETURN
    {
      "type": "LINK|XCTL|START|RETURN|SEND|RECEIVE",
      "target": "program/transaction if literal; else 'dynamic'",
      "commarea_length": "bytes|unknown",
      "source_paragraph": "paragraph-or-line",
      "confidence": "high|medium|low"
    }
  ],
  "sql_calls": [                               // EXEC SQL CALL proc(...) or DB2 usage
    {
      "verb": "CALL|SELECT|INSERT|UPDATE|DELETE",
      "object": "proc|table|view if literal",
      "source_paragraph": "paragraph-or-line",
      "confidence": "high|medium|low"
    }
  ],
  "io_resources": {                            // optional but useful for context
    "files": [{"name": "FD/SELECT name", "type": "VSAM|SEQ|unknown"}],
    "queues": [{"name": "TDQ|TSQ|MQ queue", "type": "TSQ|TDQ|MQ|unknown"}]
  },
  "copybooks": ["literal COPY names"],
  "top_level_paragraphs": ["main entry paragraph(s)"],
  "notes": ["short, factual notes only"]
}

Pass B (REDUCE) — System message:
You are a COBOL repository integrator. You will be given a list of per-file JSON summaries (from a prior pass). Merge them to produce (1) a clean edge list across programs and (2) one or more PlantUML sequence diagrams that show end-to-end interactions. Do not invent targets. If a callee is dynamic/unknown, show it distinctly and list candidates if provided. Cluster batch vs. online flows when evident (e.g., CICS).

Pass B (REDUCE) — User message template
INPUT
You are given N JSON blobs, each created from a different COBOL file. Merge them.

<<<MAP-SUMMARIES>>>
{{JSON_SUMMARIES_ARRAY}}   // e.g., [ {program_id:"A", ...}, {program_id:"B", ...}, ... ]
<<<END-SUMMARIES>>>

OUTPUT REQUIREMENTS
1) "Repository Edge Table" (markdown table)
   - Columns: Source | Edge Type | Target | Invocation (static/dynamic/cics/sql) | Condition | Paragraph/Line | Confidence
   - Include file names if present in the summaries; group by Source.

2) "Unresolved & Dynamic Calls"
   - Bulleted list of dynamic callers with their callee_expr, any possible_values, and where found.
   - Suggest likely targets only if they exactly match another program_id in the set.

3) "PlantUML Diagrams"
   - Provide 1..3 ```plantuml code blocks:
     A) High-Level Repository Integration (all programs as participants).
     B) Batch Flow(s) (if any): show job/driver program(s) triggering downstream calls.
     C) Online/CICS Flow(s) (if any): show transactions → programs via LINK/XCTL, queues, DB calls.
   - Guidelines:
     * One participant per program_id (use the literal ID).
     * For dynamic/unresolved calls: route to a participant named "UnknownTarget(<expr>)".
     * Represent edge types:
       - Static CALL: solid arrow
       - Dynamic CALL: dashed arrow
       - CICS LINK/XCTL: arrow labeled «CICS LINK» / «XCTL»
       - SQL CALL/DB: arrow to participant "DB2" (or "Database") with label (verb/object)
       - Queue IO: arrow to "TSQ"/"TDQ"/"MQ" participant with label (PUT/GET)
     * Group lifelines with 'box "Batch"' and 'box "CICS/Online"' when detectable.
     * Avoid decorative text; prefer concise labels: e.g., "CALL USING BY REF X,Y".

4) "Assumptions & Gaps"
   - Short bullets listing any low-confidence or missing links.

RULES
- Only merge edges that are explicitly present in the inputs.
- De-duplicate identical edges.
- Preserve program_id spelling exactly.
- If multiple root flows exist, generate separate sequence diagrams (A/B/C) rather than a single tangled one.


2) Chunking strategy (how to feed context)

Even with 10 files, some can be large. Use this three-tier plan:

Tier 1 — File-level chunking (Pass A)
	•	Unit of work = one source file.
	•	Never split inside a paragraph if you can avoid it. If the file is huge:
	•	Chunk by COBOL divisions: IDENTIFICATION + ENVIRONMENT + DATA + PROCEDURE.
	•	If PROCEDURE is still large, chunk by paragraph groups (e.g., 3–6 paragraphs per chunk), but always ensure any CALL statement and its surrounding conditions stay in the same chunk.
	•	Send one request per file. If you had to split that file, merge the chunk results locally into a single JSON for that file (still in the Pass-A schema) before moving to Pass B.

Tier 2 — Map summary collation
	•	After Pass A, you’ll have N JSON summaries (one per file).
	•	Validate quickly: ensure program_id uniqueness; if duplicates exist, attach the filename to disambiguate in the reducer (e.g., program_id: “FOO”, "file_hint": "src/pay/FOO.cbl").

Tier 3 — Reduce to diagram(s)
	•	Feed the array of JSON summaries to the Pass-B prompt in a single call (usually well within context limits).
	•	The reducer outputs:
	•	the consolidated edge table,
	•	unresolved/dynamic list,
	•	1–3 PlantUML blocks,
	•	assumptions/gaps.


3) Example orchestration (Python-ish pseudocode)
from openai import OpenAI
import json, pathlib

client = OpenAI()
map_system = "..."  # Pass A system (from above)
reduce_system = "..."  # Pass B system (from above)

def map_one_file(path):
    code = path.read_text(encoding="utf-8", errors="ignore")
    user = f"""INPUT METADATA
- repo: MyRepo
- file: {path.name}
- language: COBOL
- goal: extract inter-program integration edges

<<<CODE>>>
{code}
<<<END-CODE>>>

RESPONSE FORMAT (STRICT JSON)
...  # (schema text from Pass A)
"""
    resp = client.chat.completions.create(
        model="gpt-5-thinking",
        temperature=0.0,
        messages=[{"role":"system","content":map_system},
                  {"role":"user","content":user}]
    )
    return json.loads(resp.choices[0].message.content)

# Pass A
summaries = []
for path in pathlib.Path("repo/src").glob("**/*.cbl"):
    summaries.append(map_one_file(path))

# Pass B
reduce_user = f"""INPUT
You are given N JSON blobs, each created from a different COBOL file. Merge them.

<<<MAP-SUMMARIES>>>
{json.dumps(summaries, ensure_ascii=False, indent=2)}
<<<END-SUMMARIES>>>

OUTPUT REQUIREMENTS
...  # (Pass B text above)
"""

resp = client.chat.completions.create(
    model="gpt-5-thinking",
    temperature=0.1,
    messages=[{"role":"system","content":reduce_system},
              {"role":"user","content":reduce_user}]
)
final_report = resp.choices[0].message.content
print(final_report)


5) PlantUML conventions (what your UI can expect)
	•	Participants: one per program_id, plus DB2/Database, TSQ/TDQ/MQ, and UnknownTarget(<expr>) for dynamic calls.
	•	Arrows:
	•	Static CALL: ProgramA -> ProgramB: CALL USING ...
	•	Dynamic CALL: ProgramA --> UnknownTarget(var): dynamic CALL
	•	CICS: ProgramA -> ProgramB: «CICS LINK»
	•	DB: ProgramA -> DB2: SELECT table / CALL proc
	•	Queue: ProgramA -> TSQ: PUT item / TSQ -> ProgramA: GET item
	•	Grouping:
    box "Batch"
  participant PAYDRV
  participant CALC01
end box

box "CICS/Online"
  participant TRXABCD
  participant CUSQRY
end box

Persist the Pass A JSON; it’s a reusable integration index for your repo.

When you add new programs, just map the new files and re-reduce—no need to remap everything.





