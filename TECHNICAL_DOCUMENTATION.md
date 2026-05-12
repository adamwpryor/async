# Technical Documentation & System Architecture

## System Overview

The **Async Pedagogy Insight Engine** transforms flat, human-authored pedagogical texts and JSON-based knowledge graphs into a queryable, high-dimensional semantic space. 

It accomplishes this by chunking structured academic concepts, generating embeddings using a local Large Language Model (LLM), and storing them in a PostGres database (via Supabase) with pgvector enabled.

## Technical Architecture

The architecture consists of three core components:

1. **Data Sources (Flat Files):**
   - `data/async.json`: A matrix of 6 learning outcomes and application cells.
   - `data/async_kg.json`: A flat topological knowledge graph defining nodes and edges.
   - `docs/auditing_async.md`: The generative narrative conversation context.

2. **Embedding Engine (Dual Support):**
   - **Local Native:** `Qwen/Qwen3-Embedding-8B` via PyTorch, SentenceTransformers, and `bitsandbytes` (4-bit quantization). Sliced to a Matryoshka dimension of 1024.
   - **Cloud API:** Google `text-embedding-004` via `google-generativeai` (768 dimensions). This allows for side-by-side comparison of local vs. cloud embedding representations.

3. **Vector Database:**
   - Provider: **Supabase** (PostgreSQL + pgvector).
   - *Note on Architecture Drift:* While initial design documents (`async_vector_db_plan.md`) specify ChromaDB, the implemented system utilizes Supabase for robust remote/local scaling and dual table support.

## Data Structure

Data is stored in the `chunks` (Qwen3) and `chunks_google` (Google) tables within Supabase. Each record adheres to the following schema:

```json
{
  "chunk_id": "string (unique identifier)",
  "content": "string (the text payload)",
  "embedding": "vector(1024) or vector(768)",
  "metadata": {
    "type": "string (concept_node | kg_edge | application_cell | narrative)",
    "node_id": "string (optional)",
    "pattern_type": "string (optional, degrading/optimizing)",
    "outcome_id": "string (optional)"
  }
}
```

## Query Typology

The `query.py` script executes 7 distinct insights based on the embedded semantic space:

1. **Gap Detection:** Finds node pairs with high cosine similarity (>0.65) lacking explicit KG edges.
2. **Polarity Inversion:** Identifies cross-category adversarial isomorphisms between degrading and optimizing applications.
3. **Axis Clustering:** Utilizes K-Means clustering (k=4) to categorize degrading patterns on latent axes.
4. **Seventh Outcome Generation:** Interpolates latent space to find the furthest relevant concept outside existing outcomes.
5. **Human Irreplaceability Ranking:** Ranks degrading patterns based on their structural threat (similarity to learning outcomes).
6. **Optimizing Pattern Generalization:** Aggregates optimizing cells to form higher-level meta-principles.
7. **Narrative-to-Graph Bridging:** Maps narrative text sentences back to explicit KG nodes to identify unrepresented semantic concepts.

## Configuration & Security (Zero-Trust)

- **Secrets Management:** The architecture strictly requires externalizing all secrets (`SUPABASE_URL`, `SUPABASE_KEY`, `HF_TOKEN`). 
- **Dependencies:** The environment relies on a Conda `environment.yml` lock, mixing `conda-forge` packages with `pip` for specific HuggingFace tooling.
- **Outputs:** All synthesized queries output to the local `/outputs/` directory as structured JSON to ensure downstream systems can safely ingest the insights.