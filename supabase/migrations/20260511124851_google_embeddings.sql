-- Create the chunks_google table
create table public.chunks_google (
    id uuid primary key default gen_random_uuid(),
    chunk_id text unique not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    embedding vector(768) -- Google text-embedding-004 defaults to 768 dimensions
);

-- Create a vector index for faster querying (using hnsw)
create index on public.chunks_google using hnsw (embedding vector_cosine_ops);
