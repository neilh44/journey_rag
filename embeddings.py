import torch
from transformers import AutoTokenizer, AutoModel
from typing import List
import chromadb
from datetime import datetime
import json
from typing import Dict, Any

class CustomEmbedding:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        self.model = AutoModel.from_pretrained('bert-base-uncased')
        
    def mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def generate_embedding(self, text: str) -> List[float]:
        inputs = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt')
        with torch.no_grad():
            outputs = self.model(**inputs)
        embeddings = self.mean_pooling(outputs, inputs['attention_mask'])
        return embeddings[0].tolist()

class ChromaDBManager:
    def __init__(self, embedding_model: CustomEmbedding):
        self.embedding_model = embedding_model
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.text_collection = self.chroma_client.get_or_create_collection(
            name="text_embeddings",
            metadata={"description": "Store text embeddings"}
        )
        self.api_collection = self.chroma_client.get_or_create_collection(
            name="api_responses",
            metadata={"description": "Store API response embeddings"}
        )

    def store_text_embeddings(self, text: str, metadata: Dict[str, Any] = None) -> str:
        embeddings = self.embedding_model.generate_embedding(text)
        doc_id = f"text_{datetime.now().timestamp()}"
        self.text_collection.add(
            embeddings=[embeddings],
            documents=[text],
            ids=[doc_id],
            metadatas=[metadata or {}]
        )
        return doc_id

    def store_api_response(self, response: Dict[str, Any], query_text: str) -> str:
        response_str = json.dumps(response)
        embeddings = self.embedding_model.generate_embedding(response_str)
        response_id = f"response_{datetime.now().timestamp()}"
        self.api_collection.add(
            embeddings=[embeddings],
            documents=[response_str],
            ids=[response_id],
            metadatas=[{"original_query": query_text}]
        )
        return response_id

    def query_similar_responses(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.embedding_model.generate_embedding(query)
        results = self.api_collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        similar_responses = []
        for idx, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            similar_responses.append({
                "response": json.loads(doc),
                "metadata": metadata,
                "similarity_score": results['distances'][0][idx]
            })
        return similar_responses
