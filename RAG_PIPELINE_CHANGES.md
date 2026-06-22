# RAG Pipeline Changes — 2026-06-20

Two commits landed today, working bottom-up through the pipeline: first **ingestion/chunking**, then **retrieval, prompting, source-scoping, and reranking**.

- `fc5b781` — *Better chunking strategy; handle headers & tables much better* (ingestion)
- `35c2741` — *Improvements to RAG pipeline* (retrieval → reranking, citations, source filter)

Everything new is **additive and OFF by default** — the unscoped, no-rerank path is byte-identical to before, so existing behavior is unchanged until the new env flags are flipped.

---

## 1. Smarter chunking (`ingestion_service.py`)

Replaced the naive fixed-size char slicer with a structure-aware pipeline. Public surface (`IngestedChunk`, `ingest_file/pdf/pptx/png`, `detect_pdf_encrypted`) is unchanged; only the chunk **text quality** and two new metadata keys changed.

**Tables stay intact.** Detected natively (PyMuPDF `page.find_tables()` / PPTX `shape.has_table`), rendered to Markdown, and emitted as *atomic* chunks (`metadata["kind"] == "table"`). Table regions are excluded from the prose stream so they're never duplicated as garbled run-on text. Single-row/single-col "tables" are dropped as false positives. Has a fallback Markdown renderer (`_rows_to_md`) when `to_markdown()` isn't available.

**Structure-aware splitting.** New `_split` = `_atomize` + `_merge_with_overlap`:
- `_atomize` recursively backs off **paragraph → line → sentence → hard-slice** (LangChain-style recursion, no dependency), so definitions/worked examples aren't cut mid-thought.
- `_merge_with_overlap` greedily packs atoms up to `chunk_size`, carrying a trailing-atom overlap (~150 chars) into the next chunk.
- Sizing bumped to `DEFAULT_CHUNK_SIZE = 1000`, `DEFAULT_OVERLAP = 150` (char-based, ~250 tokens, no tokenizer dependency).

**Heading breadcrumbs.** PDF headings detected by **font size** (`_looks_like_heading`: ≥1.18× body size, short, no terminal punctuation), where body size = the font carrying the most *characters* (robust on sparse pages). Heading is prepended to each chunk as `[Section Title]\n…` (`_with_breadcrumb`) and stored in `metadata["section"]`. Headings are **threaded across page boundaries** so a section spanning pages keeps its breadcrumb. PPTX uses the slide title as the heading (and excludes it from body text).

**Gentler cleaning.** `_clean` no longer flattens single newlines into spaces (paragraph structure is what the splitter keys off); it only drops bare page-number lines, de-hyphenates words split across lines, and collapses runs of spaces/blank lines.

New per-chunk metadata: `kind` (`"text"` | `"table"`) and `section` (heading or `None`).

> Note: there are two definitions of `_mode` in the diff (the second shadows the first); harmless but worth a cleanup.

---

## 2. Citations & shared prompt builders (`rag_service.py`, templates)

**Chunks now carry provenance into the prompt.** New `_citation_vars` pulls `source` (prefers human-readable `material_name` over the randomized storage filename), `section`, and `page`/`slide` off each retrieved chunk; missing keys degrade to `-`.

**Document prompt template** changed from bare `## Document No: N` to:
```
## Document [N] - source: <file>, section: <section>, page: <page>
### Content: <chunk_text>
```
The **footer** now instructs the model to cite the source filename + section, e.g. `(Lecture03.pdf, Third Normal Form)`.

**Shared prompt builders.** `RAGService.build_system_prompt(...)` and `build_docs_block(...)` are now the single source of truth for prompt shape, reused by both the non-agent path **and** the agent's synthesis step (which previously duplicated the templating). Guarantees identical, source-attributed output on both paths.

**Subject manifest** (`$subject_manifest`) added to the system/planner/direct/no-context prompts — a short list of the subject's indexed materials so the model knows what it can actually ground answers in.

---

## 3. Source-scoped retrieval — "Phase 2" (OFF by default)

Lets the planner scope retrieval to specific materials the student is asking about.

- **Indexing** stamps every chunk with `material_id` (and `material_name`) via `RAGService.index_chunks(..., material_name=...)`.
- **Vector search** gained an optional `material_ids` filter, threaded through `VectorDBInterface` → `PgVectorProvider` / `QdrantDBProvider`. In pgvector it's a separate parameterized `AND metadata->>'material_id' = ANY($n)` clause, so the **unscoped query stays byte-identical**.
- **Planner** may now emit an optional `"sources": [...]` array of exact material names (prompt instructs it never to invent names). `_coerce_sources` normalizes string/list/garbage; `_resolve_sources` maps names → ids against the subject allowlist, dropping hallucinated names.
- **Corpus/allowlist** built by `TutorChatService._build_corpus` from `MaterialRepository.processed_materials_for_subject` (`(id, name)`, newest first, capped at `_MANIFEST_MAX_ITEMS = 30`).
- **Bounded fallback:** if a scoped search returns nothing, it retries **once** unfiltered over the whole subject before giving up (caps extra cost at one vector query).
- `AgentResult.sources_filter` records the applied scope; logged in `tutor_chat_service`.
- Gated by `AGENT_SOURCE_FILTER_ENABLED` (default `False`).

**Migration:** chunks indexed before today lack `material_id`, so a filtered search wouldn't match them. New script `scripts/reindex_materials.py` rebuilds each subject's collection from files on disk (resets per subject on first material, idempotent):
```
python -m scripts.reindex_materials            # all subjects
python -m scripts.reindex_materials SUBJECT_ID # one subject
python -m scripts.reindex_materials --dry-run  # report only
```
Run this once before enabling `AGENT_SOURCE_FILTER_ENABLED=true`.

---

## 4. Cross-encoder reranking — "Phase 3" (OFF by default)

New provider layer `stores/rerank/` mirroring the existing factory pattern (`RerankInterface`, `RerankEnums`, `RerankProviderFactory`, `providers/CrossEncoderReranker`).

- **Strategy:** over-fetch by recall (`limit * RERANK_OVERFETCH` rows from vector search), then truncate by precision (cross-encoder keeps the best `limit`) — the small generation model gets fewer, cleaner chunks within the same budget.
- **Backend** `LOCAL_CROSS_ENCODER` uses `sentence-transformers` (CrossEncoder), **lazy-imported** so torch only loads when selected; the dep is intentionally kept out of `requirements.txt` to keep the image lean. `model.predict` runs via `asyncio.to_thread` to stay off the event loop.
- **Soft-degrade:** any reranker fault (or empty output) falls back to vector ordering — it never 500s a chat turn.
- **Wiring:** `main._startup` builds `app.rerank_client` (and `app.state.rerank_client`) only when `RERANK_ENABLED` + `RERANK_BACKEND` are set; `RAGService.search` over-fetches + reranks only when a client is present.
- **Config:** `RERANK_ENABLED`, `RERANK_BACKEND`, `RERANK_MODEL_ID` (e.g. `BAAI/bge-reranker-base`), `RERANK_DEVICE` (`cuda`/`cpu`/auto), `RERANK_OVERFETCH=3`, `RERANK_TOP_N`. A `field_validator` (`_blank_to_none`) treats blank `.env` values as unset so empty strings don't break int parsing.

---

## 5. Tests & misc

- `tests/test_rag_rerank.py` (+171 lines) and extended `tests/fakes.py` cover the rerank over-fetch/truncate/soft-degrade behavior.
- `.env.example` documents all new `AGENT_SOURCE_FILTER_*` / `RERANK_*` knobs.
- `chat_doc_router.py` / `chat_tutor_router.py` pass the rerank client through; `material_service.py` passes `material_name` into indexing.

## Net effect

Better-formed chunks (intact tables, heading context, sentence-aware boundaries) → richer, citable retrieved context → and two opt-in precision levers (source scoping + reranking) ready to enable once legacy materials are re-indexed.

## To enable the new features
1. `python -m scripts.reindex_materials` (backfills `material_id`/`material_name`).
2. Set `AGENT_SOURCE_FILTER_ENABLED=true` for source scoping.
3. For reranking: `pip install sentence-transformers`, then set `RERANK_ENABLED=true`, `RERANK_BACKEND=LOCAL_CROSS_ENCODER`, `RERANK_MODEL_ID=BAAI/bge-reranker-base`.
