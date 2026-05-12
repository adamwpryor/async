-- Enable pgvector
create extension if not exists vector with schema extensions;

-- Create the chunks table
create table public.chunks (
    id uuid primary key default gen_random_uuid(),
    chunk_id text unique not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    embedding halfvec(1024) -- Upgrading to Qwen3-Embedding-8B with MRL truncation (1024 dimensions)
);

-- Create a vector index for faster querying (using hnsw)
create index on public.chunks using hnsw (embedding halfvec_cosine_ops);
