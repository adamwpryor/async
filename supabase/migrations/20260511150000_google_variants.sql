-- Test 7: Full native 3072-dim Gemini embeddings (no Matryoshka truncation)
create table if not exists public.chunks_google_full (
    id uuid primary key default gen_random_uuid(),
    chunk_id text unique not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    embedding vector(3072)
);
-- Note: HNSW index omitted. vector(3072) exceeds pgvector's default 2000-dim HNSW
-- limit. Sequential scan is sufficient for 80 rows and avoids index creation errors.

-- Test 8: 768-dim Gemini embeddings ingested with semantic_similarity task type
create table if not exists public.chunks_google_sim (
    id uuid primary key default gen_random_uuid(),
    chunk_id text unique not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    embedding vector(768)
);
create index if not exists chunks_google_sim_embedding_idx
    on public.chunks_google_sim using hnsw (embedding vector_cosine_ops);
