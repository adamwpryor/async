import json
import os
import re
from typing import List, Dict, Any, Callable

from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from transformers import BitsAndBytesConfig
from google import genai

from src.utils.logger import setup_logger
from src.utils.security import load_secure_key

logger = setup_logger("ingester")

class Ingester:
    def __init__(self, model_type: str):
        self.model_type = model_type
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.ids: List[str] = []
        
        self.supabase_url = load_secure_key("SUPABASE_ASYNC_URL")
        self.supabase_key = load_secure_key("SUPABASE_ASYNC_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        if self.model_type == "qwen":
            import os
            os.environ["HF_TOKEN"] = load_secure_key("HF_TOKEN_READ_ONLY")
            self.table_name = "chunks"
            self.truncate_dim = 1024
            logger.info("Loading Qwen3-8B Model in 4-bit...")
            quantization_config = BitsAndBytesConfig(load_in_4bit=True)
            self.model = SentenceTransformer(
                "Qwen/Qwen3-Embedding-8B",
                model_kwargs={"quantization_config": quantization_config},
                trust_remote_code=True
            )
        elif self.model_type == "google":
            self.table_name = "chunks_google"
            self.google_api_key = load_secure_key("GOOGLE_API_KEY")
            logger.info("Configuring Google GenAI (gemini-embedding-001)...")
            self.client = genai.Client(api_key=self.google_api_key)
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

    def add_chunk(self, chunk_id: str, text: str, metadata: Dict[str, Any]) -> None:
        self.documents.append(text)
        self.metadatas.append(metadata)
        self.ids.append(chunk_id)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if self.model_type == "qwen":
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings[:, :self.truncate_dim].tolist()
        elif self.model_type == "google":
            result = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts,
                config={"task_type": "retrieval_document"}
            )
            return [emb.values[:768] for emb in result.embeddings]
        return []

    def load_data(self) -> None:
        logger.info("Parsing files from data/ and docs/...")
        
        # Load KG
        with open('data/async_kg.json', 'r', encoding='utf-8') as f:
            kg = json.load(f)
        for node in kg['graph']['nodes']:
            self.add_chunk(
                chunk_id=f"node_{node['id']}",
                text=f"Concept Node: {node['label']}. Type: {node['type']}.",
                metadata={"type": "concept_node", "node_id": node['id'], "node_type": node['type']}
            )
        node_lookup = {n['id']: n['label'] for n in kg['graph']['nodes']}
        for edge in kg['graph']['edges']:
            source_id = edge['source']
            target_id = edge['target']
            relation = edge['relation']
            context = edge['context']
            text = f"{node_lookup.get(source_id, source_id)} is {relation.replace('_', ' ')} {node_lookup.get(target_id, target_id)}. Context: {context}."
            self.add_chunk(
                chunk_id=f"edge_{source_id}_{target_id}",
                text=text,
                metadata={"type": "kg_edge", "source_node": source_id, "target_node": target_id, "relation": relation}
            )

        # Load Applications
        with open('data/async.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        for outcome in data.get('asynchronous_learning_outcomes', []):
            outcome_id = f"O{outcome['id']}"
            outcome_name = outcome['outcome']
            for app_key, app_text in outcome.get('degrading_applications', {}).items():
                pattern_id = app_key.split('_')[0]
                text = f"Learning Outcome: {outcome_name}. Degraded by {app_key.replace('_', ' ')}: {app_text}"
                self.add_chunk(
                    chunk_id=f"app_{outcome_id}_{pattern_id}",
                    text=text,
                    metadata={"type": "application_cell", "outcome_id": outcome_id, "pattern_id": pattern_id, "pattern_type": "degrading"}
                )
            for app_key, app_text in outcome.get('optimizing_applications', {}).items():
                pattern_id = app_key.split('_')[0]
                text = f"Learning Outcome: {outcome_name}. Optimized by {app_key.replace('_', ' ')}: {app_text}"
                self.add_chunk(
                    chunk_id=f"app_{outcome_id}_{pattern_id}",
                    text=text,
                    metadata={"type": "application_cell", "outcome_id": outcome_id, "pattern_id": pattern_id, "pattern_type": "optimizing"}
                )

        # Load Narrative
        with open('docs/auditing_async.md', 'r', encoding='utf-8') as f:
            content = f.read()
        sections = re.split(r'\*\*(I{1,3}|IV|V)\.\s', content)
        intro = sections[0].strip()
        if intro:
            self.add_chunk("narrative_intro", intro, {"type": "narrative", "section": "intro"})
        for i in range(1, len(sections), 2):
            numeral = sections[i]
            sec_content = sections[i+1].strip()
            lines = sec_content.split('\n')
            text = f"Section {numeral} — {lines[0].replace('**', '').strip()}\n" + '\n'.join(lines[1:]).strip()
            self.add_chunk(f"narrative_{numeral}", text, {"type": "narrative", "section": numeral})

        # Append descriptions
        node_descriptions = {}
        for dp in data.get('degrading_patterns', []):
            node_descriptions[dp['pattern_id']] = dp['description']
        for op in data.get('optimizing_patterns', []):
            node_descriptions[op['pattern_id']] = op['description']
        for outcome in data.get('asynchronous_learning_outcomes', []):
            node_descriptions[f"O{outcome['id']}"] = outcome['definition']

        for i, cid in enumerate(self.ids):
            if cid.startswith("node_"):
                base_id = cid.replace("node_", "")
                desc = node_descriptions.get(base_id, "")
                if desc:
                    self.documents[i] += f" Description: {desc}"

        logger.info("Total chunks parsed", extra={"total_chunks": len(self.documents)})

    def run(self) -> None:
        logger.info(f"Clearing existing chunks in Supabase table '{self.table_name}'...")
        self.supabase.table(self.table_name).delete().neq("chunk_id", "nothing").execute()

        self.load_data()

        logger.info(f"Embedding chunks ({self.model_type})...")
        batch_size = 32
        all_embeddings = []
        for i in range(0, len(self.documents), batch_size):
            batch = self.documents[i:i+batch_size]
            batch_embs = self.get_embeddings(batch)
            all_embeddings.extend(batch_embs)

        logger.info("Generated embeddings", extra={"count": len(all_embeddings), "dimension": len(all_embeddings[0]) if all_embeddings else 0})

        logger.info(f"Upserting to Supabase (Postgres) table '{self.table_name}'...")
        db_batch_size = 100
        for i in range(0, len(self.ids), db_batch_size):
            batch_records = []
            for j in range(i, min(i + db_batch_size, len(self.ids))):
                batch_records.append({
                    "chunk_id": self.ids[j],
                    "content": self.documents[j],
                    "metadata": self.metadatas[j],
                    "embedding": all_embeddings[j]
                })
            self.supabase.table(self.table_name).upsert(batch_records, on_conflict="chunk_id").execute()

        logger.info(f"Ingestion complete for {self.model_type}!")
