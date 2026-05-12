# Vector Database Plan: Async Pedagogy Insight Engine

**Project:** Asynchronous Learning + AI Framework — Knowledge Retrieval & Insight Generation  
**Working directory:** `c:\Users\adamw\coding_workspaces\one_off_bot_projects\async\`  
**Author context:** Adam Pryor, Pryor Consulting — AI Strategy for Higher Education  
**Status:** Ready for implementation handoff

---

## What This Is

Three files encode a pedagogical framework about asynchronous learning and AI's role in degrading vs. optimizing human presence online:

| File | Contents |
|---|---|
| [async.json](async.json) | 6 learning outcomes × 4 degrading patterns × 4 optimizing patterns = 48 application cells |
| [async_kg.json](async_kg.json) | Flat topological knowledge graph: 14 nodes, 12 edges with typed relations |
| [auditing_async.md](auditing_async.md) | 5-section narrative outline of the generative Gemini conversation that produced the above |

The framework's **central distinction** — which must drive all insight generation — is:

- **AI's capability:** "The Omnipresent Matrix" — holds all rules, theories, and constraints **simultaneously** with perfect apathy. No active subject.
- **Human's capability:** "Focal Depth" — acts as the ethical and emotional center of gravity. Allocates care. Introduces the "touch" of lived, localized, time-bound reality into the apathetic matrix.

The vector database **is** the Omnipresent Matrix. Queries **are** the Focal Depth. The insight engine should make this explicit.

---

## Why a Vector Database

The existing KG has 12 explicit edges across 14 nodes. The semantic space it implies has hundreds more latent relationships. AI can uniquely:

1. **Hold the entire conceptual space simultaneously** — every pattern, outcome, and application in embedding space at once
2. **Find proximity across categories** — detect when a degrading application is structurally similar to an optimizing one (adversarial isomorphism)
3. **Identify missing edges** — high-similarity node pairs with no explicit KG relationship
4. **Generate novel nodes** — infer what a 7th learning outcome might look like from the latent space of O1–O6
5. **Cluster by hidden axis** — which degrading patterns attack time vs. space vs. embodiment vs. signal authenticity?

These are things the original human-AI conversation explicitly couldn't do in real-time (see Section V of the outline: "Temporal Flattening" critique of premature synthesis). The vector DB enables **non-linear, retrospective, multi-axis analysis** — the machine's native strength, activated after the human has introduced focal depth.

---

## Environment Setup (Conda-First)

```bash
conda create -n async-vecdb python=3.11 -y
conda activate async-vecdb

# Core dependencies
conda install -c conda-forge chromadb sentence-transformers -y
conda install -c conda-forge anthropic python-dotenv gitpython -y
```

**environment.yml** (create this in the `async/` folder):

```yaml
name: async-vecdb
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - chromadb
  - sentence-transformers
  - anthropic
  - python-dotenv
  - gitpython
```

**Secrets:** Never hardcoded. Use `.env` file (not committed). Provide `.env.example`:

```
ANTHROPIC_API_KEY=your_key_here
# Optional: OPENAI_API_KEY=your_key_here  (if switching to OpenAI embeddings)
```

Load keys via `src.utils.security.load_secure_key()` per project standard, or minimally via `python-dotenv` with `load_dotenv()`.

---

## Chunking Strategy

The most critical architectural decision. Three levels of granularity, each serving a different query type.

### Level 1 — Concept Nodes (14 chunks from async_kg.json)
Each KG node as its own chunk. Includes label + type.

```python
# Example chunk
{
    "id": "OP2",
    "text": "Optimizing Pattern: Simultaneous Constraint Formalization (The Omnipresent Matrix). "
            "Mastering the intersection of human focal depth and artificial omnipresence. "
            "The AI holds all rules, theories, and constraints simultaneously in perfect suspension, "
            "while the human acts as the active subject, providing the singular, localized 'touching' "
            "that anchors the abstract matrix to a tangible reality.",
    "metadata": {
        "type": "Optimizing_Pattern",
        "node_id": "OP2",
        "source_file": "async_kg.json"
    }
}
```

### Level 2 — Application Cells (48 chunks from async.json)
Each `(outcome × pattern)` application as a chunk. These are the richest semantic units.

```python
# Example: Outcome 1 × DP1
{
    "id": "O1_DP1",
    "text": "Learning Outcome: Deliberate Inefficiency (Friction). "
            "Degraded by The Eradication of the Verb: "
            "Bypasses the physical and cognitive friction of drafting entirely, "
            "allowing the student to teleport to the final draft without doing the work of formulation.",
    "metadata": {
        "type": "application_cell",
        "outcome_id": "O1",
        "pattern_id": "DP1",
        "pattern_type": "degrading",
        "source_file": "async.json"
    }
}
```

### Level 3 — KG Edges as Relational Triples (12 chunks from async_kg.json)
Each edge encoded as a semantic sentence. Essential for gap-detection queries.

```python
# Example edge chunk
{
    "id": "edge_O1_OP3",
    "text": "Deliberate Inefficiency (Friction) is OPTIMIZED BY AUDITING through Forensic Pedagogy. "
            "Context: Grading the exhaust of friction rather than the final product.",
    "metadata": {
        "type": "kg_edge",
        "source_node": "O1",
        "target_node": "OP3",
        "relation": "OPTIMIZED_BY_AUDITING",
        "source_file": "async_kg.json"
    }
}
```

### Level 4 — Narrative Sections (5 chunks from auditing_async.md)
Each Roman-numeral section as a chunk. Provides conceptual framing for synthesis queries.

```python
{
    "id": "narrative_IV",
    "text": "Section IV — The Breakthrough: Simultaneous Suspension vs. Focal Depth. "
            "AI holds all rules, theories, and constraints simultaneously present, but with absolute apathy. "
            "It has no active subject. The student's role is focal depth — acting as the ethical and emotional "
            "center of gravity, deciding what matters, and introducing the 'touch' of lived context and "
            "deliberate time (latency) into the machine's flattened, apathetic matrix.",
    "metadata": {
        "type": "narrative",
        "section": "IV",
        "source_file": "auditing_async.md"
    }
}
```

**Total corpus:** ~79 chunks before any deduplication.

---

## Embedding Model Selection

| Option | Model | Tradeoff |
|---|---|---|
| **Local (preferred)** | `all-MiniLM-L6-v2` via `sentence-transformers` | Fast, free, offline. 384-dim. Good for this corpus size. |
| **Local (higher quality)** | `nomic-ai/nomic-embed-text-v1` | 768-dim, better semantic nuance. Conda-installable. |
| **API (highest quality)** | OpenAI `text-embedding-3-small` | Requires key. 1536-dim. Best for subtle conceptual proximity. |

**Recommendation:** Start with `all-MiniLM-L6-v2` for development; switch to `nomic-embed-text-v1` for production queries. The corpus is small enough that local is fast and free.

---

## Vector DB Setup (ChromaDB)

ChromaDB runs locally with no external infrastructure. Persistent storage keeps embeddings across sessions.

```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="async_pedagogy",
    metadata={"hnsw:space": "cosine"}  # cosine similarity for semantic proximity
)
```

Collections to create:
- `async_pedagogy` — all 79 chunks, queryable by type via metadata filtering

---

## Ingestion Pipeline

**File:** `ingest.py` (place in `async/`)

High-level logic:

```
1. Load async.json → generate Level 1 (concept) + Level 2 (application cell) chunks
2. Load async_kg.json → generate Level 1 (nodes) + Level 3 (edge) chunks
3. Load auditing_async.md → parse by section header → Level 4 (narrative) chunks
4. Deduplicate Level 1 (nodes appear in both JSON files)
5. Embed all chunks via sentence-transformers
6. Upsert into ChromaDB with metadata
7. Log ingestion stats (chunk count, embedding dim, collection size) as structured JSON
```

Metadata schema per document:

```python
{
    "type": str,          # "Optimizing_Pattern" | "Degrading_Pattern" | "Outcome" | 
                          #  "application_cell" | "kg_edge" | "narrative"
    "node_id": str,       # e.g., "OP1", "O3", "DP2" (where applicable)
    "pattern_type": str,  # "degrading" | "optimizing" (for application_cells)
    "outcome_id": str,    # e.g., "O1" (for application_cells and edges)
    "section": str,       # Roman numeral (for narrative chunks)
    "source_file": str    # original file name
}
```

---

## Insight Generation Queries

These are the **seven core query types** that exploit AI's distinctive capabilities — things the original chat conversation couldn't produce due to "temporal flattening" constraints.

### Query 1: Gap Detection (Missing KG Edges)
*AI unique capability: simultaneous comparison of all node pairs*

> Find all node pairs with cosine similarity > 0.75 that have NO explicit edge in the KG. Return as candidate edges with a generated `relation` label.

Implementation: Embed all 14 nodes → compute pairwise similarity matrix → filter against existing 12 edges → flag high-similarity pairs.

### Query 2: Polarity Inversion Detection
*AI unique capability: cross-category semantic proximity*

> Find cases where a degrading application is semantically closest to an optimizing application from a DIFFERENT outcome. These are "adversarial isomorphisms" — the pattern that degrades one outcome might optimize another.

Implementation: For each DP application chunk, find top-3 nearest neighbors that are OP application chunks across any outcome.

### Query 3: Axis Clustering
*AI unique capability: latent dimension extraction*

> Cluster all degrading patterns by which human dimension they attack: Time (latency, incubation), Space (embodiment, locality), Signal (authenticity, spontaneity), or Social (relational fabric). No human labeled these clusters.

Implementation: Embed DP application chunks only → k-means clustering (k=4) → label each cluster with Claude → compare against intuitive axes.

### Query 4: 7th Outcome Generation
*AI unique capability: latent space interpolation*

> Given the six existing outcomes occupy a semantic region, what concept would sit in the largest gap in that region? Generate a candidate 7th learning outcome.

Implementation: Embed O1–O6 centroids → compute the semantic "center" → find text in embedding space maximally distant from existing centroids while still within the framework's semantic domain → generate with Claude.

### Query 5: Human Irreplaceability Ranking
*AI unique capability: cross-outcome aggregation*

> Rank the four degrading patterns by how many outcomes they threaten AND how semantically central they are to the corpus. Which degrading force is the most structurally corrosive?

Implementation: Count DP node degree in KG → weight by average embedding similarity to all outcome nodes → rank.

### Query 6: Optimizing Pattern Generalization
*AI unique capability: semantic abstraction across instances*

> For each optimizing pattern, retrieve all its application cells and generate an abstracted "meta-principle" — the pattern at one level of abstraction higher than its current description.

Implementation: For each OP, retrieve its 6 application cells (one per outcome) → send to Claude with prompt: "These are 6 manifestations of one optimizing pattern. What is the single meta-principle that unifies them?"

### Query 7: Narrative-to-Graph Bridging
*AI unique capability: multi-level semantic synthesis*

> Identify concepts in the narrative sections (auditing_async.md) that have NO corresponding node in the KG. These are implicit concepts that could become new nodes.

Implementation: For each sentence in narrative chunks, find nearest KG node → flag sentences with max similarity < 0.6 as "unrepresented concepts" → cluster and label with Claude.

---

## Output Format

All insights returned as structured JSON for downstream use:

```json
{
    "query_type": "gap_detection",
    "generated_at": "ISO-8601 timestamp",
    "git_commit": "from gitpython",
    "git_branch": "from gitpython",
    "results": [
        {
            "candidate_edge": {
                "source": "O2",
                "target": "DP4",
                "inferred_relation": "DEGRADED_BY_FLATTENING",
                "cosine_similarity": 0.81,
                "rationale": "..."
            }
        }
    ]
}
```

Logs: structured JSON only. No `print()` statements.

---

## Project File Structure (Final)

```
async/
├── async.json                    # Source data: outcomes × patterns matrix
├── async_kg.json                 # Source data: knowledge graph
├── auditing_async.md             # Source: narrative outline
├── async_vector_db_plan.md       # This file
├── environment.yml               # Conda environment spec
├── .env.example                  # Secret key template (committed)
├── .env                          # Actual keys (never committed)
├── ingest.py                     # Chunking + embedding + ChromaDB upsert
├── query.py                      # Seven insight query implementations
├── chroma_db/                    # Persisted ChromaDB storage (gitignored)
└── outputs/                      # Generated insight JSON files
```

Add to `.gitignore`:
```
.env
chroma_db/
outputs/
```

---

## Implementation Order

1. **Create `environment.yml`** and activate the `async-vecdb` Conda environment
2. **Write `ingest.py`**: parse → chunk → embed → upsert, with structured logging
3. **Validate ingestion**: query `collection.count()` and spot-check a few nearest-neighbor retrievals manually
4. **Write `query.py`**: implement the 7 query types as discrete functions
5. **Run Query 1 (Gap Detection)** first — it is the most concrete and validates the pipeline
6. **Run Queries 2–7** iteratively, reviewing Claude-generated insights for coherence with the framework
7. **Document insights** that surprise — these are the ones worth writing about

---

## Philosophical Note for Agent Context

The framework argues that AI's "Omnipresent Matrix" holds everything simultaneously but with apathy — no allocation of care, no focal depth. This pipeline **demonstrates** that principle rather than just theorizing it. The vector DB holds every node, edge, and application cell simultaneously. The seven query types are acts of focal depth — choosing which axis to touch, which gap to illuminate, which pattern to generalize.

The goal is not to produce a conclusion. It is to produce the **conditions for human insight** — a persistent, queryable memory state where the framework can continue to evolve through future human-AI collisions.

---

*Generated: 2026-05-10 | Working directory: `async/` | Gemini source chat: https://gemini.google.com/share/200f60bfa22f (requires auth — content summarized in auditing_async.md)*
