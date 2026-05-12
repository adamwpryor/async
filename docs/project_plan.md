# Project Plan: Async Pedagogy Insight Engine (100% Local)

## Phase 1: Environment & Source Control
- [x] Initialize Git repository
- [x] Create `.gitignore` (ignoring `.env`, `chroma_db/`, `outputs/`, etc.)
- [x] Create `environment.yml` for Conda (`python=3.11`, `chromadb`, `sentence-transformers`, `gitpython`). *Removed Anthropic/OpenAI dependencies to ensure 100% local execution.*
- [x] Create GitHub repository and push initial setup.

## Phase 2: Ingestion Pipeline (`ingest.py`)
- [x] Parse `async_kg.json` (Level 1 Concept Nodes & Level 3 Edges)
- [x] Parse `async.json` (Level 2 Application Cells)
- [x] Parse `auditing_async.md` (Level 4 Narrative Chunks)
- [x] Implement deduplication logic for Concept Nodes.
- [x] Set up local embedding model (`all-MiniLM-L6-v2` via `sentence-transformers`).
- [x] Initialize local `ChromaDB` persistent client.
- [x] Embed and upsert all chunks with structured metadata.
- [x] Validate ingestion (chunk counts, dimensional checks).

## Phase 3: Query Engine (`query.py`)
*Note: Since execution must be 100% local without APIs, queries that previously required Claude for "labeling" or "synthesis" will output the raw vector similarities, latent space centroids, and nearest neighbors. We can later integrate a local LLM (like Llama 3 via Ollama) if text generation is strictly required.*

- [x] Implement Query 1: Gap Detection (Missing KG Edges)
- [x] Implement Query 2: Polarity Inversion Detection
- [x] Implement Query 3: Axis Clustering (K-Means on DP chunks)
- [x] Implement Query 4: 7th Outcome Generation (Latent space interpolation, returning nearest textual neighbors to the centroid)
- [x] Implement Query 5: Human Irreplaceability Ranking (Graph degree × Semantic centrality)
- [x] Implement Query 6: Optimizing Pattern Generalization (Grouping chunks for abstraction)
- [x] Implement Query 7: Narrative-to-Graph Bridging (Sentence-level semantic gap detection)

## Phase 4: Output & Validation
- [x] Generate structured JSON outputs for all queries into `outputs/`
- [x] Push final codebase to GitHub (excluding local DB and outputs).
