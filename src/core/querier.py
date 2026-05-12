import os
import json
from datetime import datetime
from typing import Dict, Any, List, Union

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from supabase import create_client, Client

from src.utils.logger import setup_logger
from src.utils.security import load_secure_key

logger = setup_logger("querier")

class Querier:
    def __init__(self, model_type: str):
        self.model_type = model_type
        
        self.supabase_url = load_secure_key("SUPABASE_URL")
        self.supabase_key = load_secure_key("SUPABASE_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        if self.model_type == "qwen":
            self.table_name = "chunks"
            self.output_dir = "./outputs"
        elif self.model_type == "google":
            self.table_name = "chunks_google"
            self.output_dir = "./outputs_google"
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def save_result(self, query_name: str, data: Union[List[Any], Dict[str, Any]]) -> None:
        timestamp = datetime.utcnow().isoformat()
        output = {
            "query_type": query_name,
            "model_type": self.model_type,
            "generated_at": timestamp,
            "results": data
        }
        file_path = os.path.join(self.output_dir, f"{query_name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        logger.info("Saved results", extra={"query_name": query_name, "file_path": file_path})

    @staticmethod
    def parse_metadata(meta_str: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(meta_str, dict):
            return meta_str
        if isinstance(meta_str, str):
            return json.loads(meta_str)
        return meta_str

    @staticmethod
    def parse_embedding(emb: Union[str, List[float]]) -> List[float]:
        if isinstance(emb, str):
            return json.loads(emb)
        return emb

    def query_1_gap_detection(self) -> None:
        logger.info("Running Query 1: Gap Detection...")
        res_nodes = self.supabase.table(self.table_name).select("*").eq("metadata->>type", "concept_node").execute()
        nodes = res_nodes.data
        
        res_edges = self.supabase.table(self.table_name).select("*").eq("metadata->>type", "kg_edge").execute()
        edges = res_edges.data
        
        existing_pairs = set()
        for e in edges:
            m = self.parse_metadata(e['metadata'])
            existing_pairs.add(tuple(sorted([m['source_node'], m['target_node']])))
                
        embeddings = np.array([self.parse_embedding(n['embedding']) for n in nodes])
        if len(embeddings) == 0: return
        sim_matrix = cosine_similarity(embeddings)
        
        results = []
        n_count = len(nodes)
        for i in range(n_count):
            for j in range(i+1, n_count):
                meta_i = self.parse_metadata(nodes[i]['metadata'])
                meta_j = self.parse_metadata(nodes[j]['metadata'])
                id_i = meta_i['node_id']
                id_j = meta_j['node_id']
                pair = tuple(sorted([id_i, id_j]))
                
                if pair not in existing_pairs:
                    sim = float(sim_matrix[i, j])
                    if sim > 0.65:
                        results.append({
                            "node_a": id_i,
                            "node_b": id_j,
                            "label_a": nodes[i]['content'],
                            "label_b": nodes[j]['content'],
                            "cosine_similarity": round(sim, 3)
                        })
                        
        results.sort(key=lambda x: x['cosine_similarity'], reverse=True)
        self.save_result("query_1_gap_detection", results)

    def query_2_polarity_inversion(self) -> None:
        logger.info("Running Query 2: Polarity Inversion Detection...")
        res_degrading = self.supabase.table(self.table_name).select("*").eq("metadata->>pattern_type", "degrading").execute()
        degrading_apps = res_degrading.data
        
        res_optimizing = self.supabase.table(self.table_name).select("*").eq("metadata->>pattern_type", "optimizing").execute()
        optimizing_apps = res_optimizing.data
        
        if not degrading_apps or not optimizing_apps:
            return
            
        op_embeddings = np.array([self.parse_embedding(o['embedding']) for o in optimizing_apps])
        dp_embeddings = np.array([self.parse_embedding(d['embedding']) for d in degrading_apps])
        
        sim_matrix = cosine_similarity(dp_embeddings, op_embeddings)
        
        results = []
        for i, dp in enumerate(degrading_apps):
            dp_meta = self.parse_metadata(dp['metadata'])
            top_indices = np.argsort(sim_matrix[i])[-5:][::-1]
            matches = []
            for j in top_indices:
                op = optimizing_apps[j]
                op_meta = self.parse_metadata(op['metadata'])
                sim = float(sim_matrix[i, j])
                if dp_meta['outcome_id'] != op_meta['outcome_id']:
                    matches.append({
                        "optimizing_app_id": op['chunk_id'],
                        "optimizing_outcome": op_meta['outcome_id'],
                        "similarity": round(sim, 3)
                    })
            if matches:
                results.append({
                    "degrading_app_id": dp['chunk_id'],
                    "degrading_outcome": dp_meta['outcome_id'],
                    "degrading_pattern": dp_meta['pattern_id'],
                    "cross_outcome_matches": matches
                })
        self.save_result("query_2_polarity_inversion", results)

    def query_3_axis_clustering(self) -> None:
        logger.info("Running Query 3: Axis Clustering...")
        res = self.supabase.table(self.table_name).select("*").eq("metadata->>pattern_type", "degrading").execute()
        degrading_apps = res.data
        if len(degrading_apps) < 4:
            return
        embeddings = np.array([self.parse_embedding(d['embedding']) for d in degrading_apps])
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(embeddings)
        
        clustered_results = {f"Cluster_{i}": [] for i in range(4)}
        for i, c in enumerate(clusters):
            meta = self.parse_metadata(degrading_apps[i]['metadata'])
            clustered_results[f"Cluster_{c}"].append({
                "id": degrading_apps[i]['chunk_id'],
                "text": degrading_apps[i]['content'],
                "pattern": meta['pattern_id']
            })
        self.save_result("query_3_axis_clustering", clustered_results)

    def query_4_seventh_outcome(self) -> None:
        logger.info("Running Query 4: 7th Outcome Generation (Latent Space)...")
        res = self.supabase.table(self.table_name).select("*").eq("metadata->>node_type", "Outcome").execute()
        outcomes = res.data
        if not outcomes:
            return
        embeddings = np.array([self.parse_embedding(o['embedding']) for o in outcomes])
        centroid = np.mean(embeddings, axis=0).tolist()
        
        res_others = self.supabase.table(self.table_name).select("*").neq("metadata->>node_type", "Outcome").execute()
        others = res_others.data
        if not others:
            return
        other_embeddings = np.array([self.parse_embedding(o['embedding']) for o in others])
        centroid_array = np.array([centroid])
        sims = cosine_similarity(centroid_array, other_embeddings)[0]
        
        top_indices = np.argsort(sims)[-10:][::-1]
        results = []
        for i in top_indices:
            sim = float(sims[i])
            results.append({
                "id": others[i]['chunk_id'],
                "text": others[i]['content'],
                "similarity_to_outcome_centroid": round(sim, 3)
            })
        self.save_result("query_4_seventh_outcome", results)

    def query_5_human_irreplaceability(self) -> None:
        logger.info("Running Query 5: Human Irreplaceability Ranking...")
        res_dps = self.supabase.table(self.table_name).select("*").eq("metadata->>node_type", "Degrading_Pattern").execute()
        dps = res_dps.data
        res_outcomes = self.supabase.table(self.table_name).select("*").eq("metadata->>node_type", "Outcome").execute()
        outcomes = res_outcomes.data
        if not dps or not outcomes:
            return
        dp_embeddings = np.array([self.parse_embedding(d['embedding']) for d in dps])
        out_embeddings = np.array([self.parse_embedding(o['embedding']) for o in outcomes])
        
        sim_matrix = cosine_similarity(dp_embeddings, out_embeddings)
        mean_sims = np.mean(sim_matrix, axis=1)
        
        results = []
        for i, dp in enumerate(dps):
            meta = self.parse_metadata(dp['metadata'])
            results.append({
                "pattern_id": meta['node_id'],
                "text": dp['content'],
                "average_similarity_to_outcomes": round(float(mean_sims[i]), 3)
            })
        results.sort(key=lambda x: x['average_similarity_to_outcomes'], reverse=True)
        self.save_result("query_5_human_irreplaceability", results)

    def query_6_optimizing_generalization(self) -> None:
        logger.info("Running Query 6: Optimizing Pattern Generalization...")
        res = self.supabase.table(self.table_name).select("*").eq("metadata->>pattern_type", "optimizing").execute()
        ops = res.data
        if not ops: return
        grouped = {}
        for op in ops:
            meta = self.parse_metadata(op['metadata'])
            pid = meta['pattern_id']
            if pid not in grouped:
                grouped[pid] = []
            grouped[pid].append(op['content'])
        self.save_result("query_6_optimizing_generalization", grouped)

    def query_7_narrative_bridging(self) -> None:
        logger.info("Running Query 7: Narrative-to-Graph Bridging...")
        res_narrative = self.supabase.table(self.table_name).select("*").eq("metadata->>type", "narrative").execute()
        narratives = res_narrative.data
        res_nodes = self.supabase.table(self.table_name).select("*").eq("metadata->>type", "concept_node").execute()
        nodes = res_nodes.data
        if not narratives or not nodes:
            return
        narrative_embeddings = np.array([self.parse_embedding(n['embedding']) for n in narratives])
        node_embeddings = np.array([self.parse_embedding(n['embedding']) for n in nodes])
        
        sim_matrix = cosine_similarity(narrative_embeddings, node_embeddings)
        max_sims = np.max(sim_matrix, axis=1)
        best_match_idx = np.argmax(sim_matrix, axis=1)
        
        results = []
        for i, n in enumerate(narratives):
            n_meta = self.parse_metadata(n['metadata'])
            node_meta = self.parse_metadata(nodes[best_match_idx[i]]['metadata'])
            sim = float(max_sims[i])
            results.append({
                "narrative_section": n_meta['section'],
                "closest_node": node_meta['node_id'],
                "similarity": round(sim, 3),
                "flagged_as_gap": sim < 0.6
            })
        self.save_result("query_7_narrative_bridging", results)

    def run_all(self) -> None:
        self.query_1_gap_detection()
        self.query_2_polarity_inversion()
        self.query_3_axis_clustering()
        self.query_4_seventh_outcome()
        self.query_5_human_irreplaceability()
        self.query_6_optimizing_generalization()
        self.query_7_narrative_bridging()
        logger.info(f"All queries completed for {self.model_type}!")
