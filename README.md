# Async Pedagogy Insight Engine

**Author:** Adam Pryor, Pryor Consulting — AI Strategy for Higher Education  
**Status:** Alpha / Proof of Concept

## Executive Summary

The **Async Pedagogy Insight Engine** is a vector-backed knowledge retrieval system designed to analyze the intersection of asynchronous learning and AI. It encodes a pedagogical framework that categorizes AI's role in online learning as either degrading or optimizing human presence. 

By leveraging a native local embedding model (Qwen3-Embedding-8B) and a Supabase-backed vector database, this engine activates "The Omnipresent Matrix" — allowing AI to hold all theories and constraints simultaneously. It enables non-linear, multi-axis querying to identify latent relationships, generate novel outcomes, and detect adversarial isomorphisms across pedagogical strategies.

## Quickstart (Run Locally for Free)

This repository is designed to be fully reproducible on your local machine using Supabase Local and Conda.

> **💡 A Note for Windows Users & Pedagogy Professionals:** 
> If you are new to the technical side of AI, you might notice these instructions use terminal commands built for Linux or macOS. In the open-source AI ecosystem, running local machine learning models (like downloading the Qwen3-8B model directly from Hugging Face) is significantly smoother and more stable on Linux architectures. Native Windows environments often cause intense friction with these libraries. If you are on a Windows machine, we highly recommend installing and using **WSL 2 (Windows Subsystem for Linux)** to run this project seamlessly.

### 1. Prerequisites
- **Docker Desktop** (required to run the local Supabase vector database)
- **Supabase CLI** (`npm install -g supabase` or via Homebrew/Scoop)
- **Miniconda** or Anaconda (for Python environment management)

### 2. Start the Local Database
Clone the repository and start the local Supabase instance. The CLI will automatically read the `supabase/migrations/` folder and create the vector tables (`chunks` and `chunks_google`) with `pgvector` enabled.

```bash
git clone https://github.com/yourusername/async-insight-engine.git
cd async-insight-engine

# Start the local database container
supabase start
```
*(When this finishes, the CLI will output your local `API URL` and `service_role key`. Keep these handy for the next step.)*

### 3. Security & API Keys
This project enforces a Zero-Trust architecture. **Never commit your `.env` file.** 

Copy the example file and add your keys:
```bash
cp .env.example .env
```
Edit `.env` with your favorite text editor:
- `HF_TOKEN`: Get a free token from HuggingFace to download the Qwen model.
- `GOOGLE_API_KEY`: Get a free key from Google AI Studio (if you want to run the Google comparison).
- `SUPABASE_URL`: Paste the `API URL` from step 2.
- `SUPABASE_KEY`: Paste the `service_role key` from step 2.

### 4. Build the Environment
Scaffold the required Python environment using the provided lockfile.

```bash
conda env create -f environment.yml
conda activate async-vecdb
```

### 5. Running the Engine
The pipeline is split into two phases: Ingestion and Querying.

**Phase 1: Ingestion**
Parses the flat JSON knowledge graphs and Markdown narratives, chunks them, generates high-dimensional embeddings, and upserts them to your local Supabase database.

You can ingest using the local, open-source Qwen model (free, runs on your hardware) or Google's API:
```bash
# Ingest using local Qwen3-Embedding-8B (Downloads model on first run)
python main.py ingest --model qwen

# Ingest using Google gemini-embedding-001
python main.py ingest --model google
```

**Phase 2: Querying & Insight Generation**
Runs seven complex AI-driven queries against the vector database to extract novel pedagogical insights. Results are exported as structured JSON to the `./outputs/` or `./outputs_google/` directories.

```bash
# Query against Qwen3 embeddings (default)
python main.py query --model qwen

# Query against Google embeddings
python main.py query --model google
```

## Contributing
Please refer to the `audit_report.md` before making contributions, ensuring strict adherence to Zero-Trust security and JSON structured logging standards.