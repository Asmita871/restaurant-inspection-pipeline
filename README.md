# NYC Restaurant Inspection Risk & Insight Pipeline

An end-to-end data pipeline that ingests NYC restaurant inspection records, builds a
question-answering layer grounded in real inspection data (RAG), and an anomaly-flagging
agent for repeat critical violations — with a documented, honest evaluation of where the
AI components succeeded and failed.

## Business question

Critical food-safety violations across NYC restaurants rose from 2024 to 2025
(41,747 → 46,949), driven primarily by temperature control and food-contamination
failures rather than pest or administrative issues. This project investigates which
establishments and conditions are associated with this rise, and whether AI-assisted
tools can support earlier, better-targeted intervention.

## Hypotheses tested and ruled out

Before settling on the final question above, three other hypotheses were tested and
found not to hold up:

- **Cuisine type as a risk factor** — critical violation rates across the top 15
  cuisines clustered tightly between 50-57%, too narrow a spread to be a meaningful
  differentiator.
- **Borough as a risk factor** — similarly narrow spread (48-55%), not a strong signal.
- **Individual restaurant "worsening trend"** — an initial check using restaurant name
  (`DBA`) as the grouping key produced a misleading result (chain restaurants like
  Dunkin and McDonald's all appeared "rising" due to a grouping bug, not real behavior).
  Re-grouping by unique establishment ID (`CAMIS`) corrected this, and the resulting
  pattern showed most of the apparent "rise" was actually a citywide spike concentrated
  in 2025, not steady individual decline.

## Data quality issue found and handled

Initial full-history data (2007-2026) showed an implausible 45x jump in critical
violation counts between 2021 (193) and 2022 (8,813) — a discontinuity almost certainly
caused by COVID-related inspection disruption and a subsequent reporting/methodology
change, not a real-world shift in restaurant safety. Years before 2022 were excluded
from all trend analysis. This reduced the dataset from 295,079 to 288,602 rows
(under 3% loss) while making all year-over-year comparisons valid.

## Pipeline stages

1. **Ingest** — NYC DOHMH Restaurant Inspection Results, pulled via Socrata bulk export
   (295,079 rows, 27 columns).
2. **Clean** — deduplicated, fixed invalid borough codes, parsed dates, filtered to
   2022+ for the data quality reason above.
3. **Feature building** — aggregated to 27,301 unique establishments with per-restaurant
   inspection counts, critical violation rates, temperature-violation flags, and
   year-over-year change metrics.
4. **RAG layer** — embedded per-establishment violation summaries (sentence-transformers
   + ChromaDB), with a local LLM (Qwen2.5-1.5B-Instruct, chosen to keep the project fully
   free and reproducible) generating grounded answers to natural-language questions.
5. **Agent layer** — a rule-based anomaly detector (flags a new violation count as
   anomalous if it exceeds 2x an establishment's historical average) paired with an LLM
   explanation layer.
6. **Packaging** — FastAPI endpoints (`/establishment/{id}`, `/check-anomaly/{id}`) and a
   Dockerfile for portability.

## AI evaluation — where I caught the model being wrong

This is the part most projects skip. I tested both AI layers against known ground truth
rather than trusting output at face value.

**RAG grounding test** — 4 test queries, checking whether every restaurant named in the
generated answer actually appeared in the retrieved context:

| Query | Fabricated restaurant names found |
|---|---|
| Restaurants with mice/rodent problems | 1 ("Maggie Reilly's") |
| Restaurants with temperature control violations | 2 ("Belaire Cafe", "Max Restaurant") |
| Restaurants with the most critical violations | 2 ("Beney's Chao King Restaurant", "Kayla Restaurant") |
| Restaurants where violations increased in 2025 | 0 confirmed (initial regex flags were false positives from generic words) |

**Result: the local model fabricated at least one non-existent restaurant name in 3 of 4
test queries**, even when the retrieval step itself was accurate. This directly
motivated building an automated grounding-check function rather than relying on
prompting alone.

**Agent reasoning test** — 3 test cases, checking whether the LLM's explanation of an
anomaly flag stayed grounded in the specific numbers provided:

| Case | Result |
|---|---|
| Morris Park Bake Shop | Correctly grounded — referenced actual average (0.45) and new count (5), sound reasoning |
| Asia Plaza Café | Facts correct, but reasoning was logically backwards (cited a *low* average as the reason for an anomalous flag) |
| P & S Deli Grocery | Fabricated a "national average of 1.25" that was never provided in the prompt |

**Result: only 1 of 3 agent explanations was both factually grounded and logically
coherent.** This led to the final architecture decision below.

## Architecture decision: rules decide, LLM explains, humans review

Given the evaluation results above, the rule-based logic — not the LLM — makes the
actual anomaly determination. The LLM's role is limited to generating a first-draft,
human-reviewable explanation, never an autonomous decision. This is a deliberate,
evidence-based design choice, not a limitation I'm glossing over.

## Known limitations

- The local LLM (Qwen2.5-1.5B) was chosen to keep the project free and reproducible;
  a larger or paid model (e.g. Claude, GPT-4) would likely reduce — though not
  eliminate — the hallucination rate observed above.
- The RAG and agent layers were prototyped on a 5,000-row sample of establishments for
  speed; the pipeline is designed to scale to the full 27,301 via the same code path.
- CSV was used for intermediate storage for simplicity; a production version would use
  a format like Parquet to preserve dtypes (datetime columns currently need re-parsing
  on every reload) and a real warehouse (BigQuery/Snowflake) instead of flat files.

## Recommendation

Inspection resources would likely be better targeted by monitoring individual
establishments' temperature-control violation trends rather than by cuisine or borough,
which showed no meaningful risk difference. An early-warning system based on the
rule-based anomaly logic here — with LLM-generated explanations reviewed by a human,
not acted on automatically — is a realistic, low-risk way to pilot this.

**What would make me wrong:** the 2025 spike may partly reflect a change in inspection
methodology or staffing rather than a genuine rise in food-safety failures — this
project did not have access to inspector staffing or policy-change data to fully rule
that out.

## Stack

Python, pandas, SQL, sentence-transformers, ChromaDB, Hugging Face Transformers
(Qwen2.5-1.5B-Instruct), FastAPI, Docker, Git. Built and prototyped in Google Colab,
version-controlled in GitHub.
