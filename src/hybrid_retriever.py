"""
Hybrid Retrieval Module - combines BM25 and Semantic Search
"""
from typing import List, Dict, Literal, Optional
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

try:
    from config import settings
except ImportError:
    from .config import settings

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Retrieve relevant messages using BM25 or Semantic Search."""
    
    def __init__(self, method: Optional[Literal["bm25", "semantic", "hybrid"]] = None,
                 semantic_model: Optional[str] = None,
                 semantic_threshold: Optional[float] = None,
                 bm25_weight: Optional[float] = None,
                 semantic_weight: Optional[float] = None):
        """
        Initialize retriever.
        
        Args:
            method: Retrieval method (default from config)
            semantic_model: SentenceTransformer model name (default from config)
            semantic_threshold: Minimum similarity score (default from config)
            bm25_weight: Weight for BM25 in hybrid (default from config)
            semantic_weight: Weight for semantic in hybrid (default from config)
        """
        self.method = method or settings.retrieval_method
        self.semantic_threshold = semantic_threshold or settings.semantic_threshold
        self.bm25_weight = bm25_weight or settings.bm25_weight
        self.semantic_weight = semantic_weight or settings.semantic_weight
        self.semantic_model = None
        
        if self.method in ["semantic", "hybrid"]:
            model_name = semantic_model or settings.semantic_model
            logger.info(f"Loading SentenceTransformer model: {model_name}")
            self.semantic_model = SentenceTransformer(model_name)
    
    def retrieve(self, query: str, messages: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Retrieve top-k most relevant messages for the query.
        
        Args:
            query: User's question
            messages: List of messages to search through
            top_k: Number of top results to return
            
        Returns:
            List of most relevant messages with scores
        """
        if not messages:
            return []
        
        if self.method == "bm25":
            return self._retrieve_bm25(query, messages, top_k)
        elif self.method == "semantic":
            return self._retrieve_semantic(query, messages, top_k)
        else:  # hybrid
            return self._retrieve_hybrid(query, messages, top_k)
    
    def _retrieve_bm25(self, query: str, messages: List[Dict], top_k: int) -> List[Dict]:
        """Retrieve using BM25 algorithm."""
        logger.info(f"Using BM25 retrieval for query: '{query}'")
        
        # Tokenize messages
        corpus = [msg.get('message', '').lower().split() for msg in messages]
        
        # Initialize BM25
        bm25 = BM25Okapi(corpus)
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get scores
        scores = bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        # Build results with scores
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include messages with positive scores
                msg = messages[idx].copy()
                msg['retrieval_score'] = float(scores[idx])
                msg['retrieval_method'] = 'BM25'
                results.append(msg)
        
        logger.info(f"BM25 retrieved {len(results)} messages")
        return results
    
    def _retrieve_semantic(self, query: str, messages: List[Dict], top_k: int) -> List[Dict]:
        """Retrieve using semantic similarity."""
        logger.info(f"Using semantic retrieval for query: '{query}'")
        
        # Extract message texts
        message_texts = [msg.get('message', '') for msg in messages]
        
        # Encode query and messages
        query_embedding = self.semantic_model.encode([query])
        message_embeddings = self.semantic_model.encode(message_texts)
        
        # Calculate cosine similarities
        similarities = cosine_similarity(query_embedding, message_embeddings)[0]
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Build results with scores
        results = []
        for idx in top_indices:
            if similarities[idx] > self.semantic_threshold:
                msg = messages[idx].copy()
                msg['retrieval_score'] = float(similarities[idx])
                msg['retrieval_method'] = 'Semantic'
                results.append(msg)
        
        logger.info(f"Semantic search retrieved {len(results)} messages")
        return results
    
    def _retrieve_hybrid(self, query: str, messages: List[Dict], top_k: int) -> List[Dict]:
        """Retrieve using hybrid approach - combines BM25 and semantic."""
        logger.info(f"Using hybrid retrieval for query: '{query}'")
        
        # Get results from both methods
        bm25_results = self._retrieve_bm25(query, messages, top_k * 2)
        semantic_results = self._retrieve_semantic(query, messages, top_k * 2)
        
        # Normalize BM25 scores to 0-1 range
        if bm25_results:
            bm25_scores = [msg['retrieval_score'] for msg in bm25_results]
            bm25_max = max(bm25_scores) if bm25_scores else 1.0
            bm25_min = min(bm25_scores) if bm25_scores else 0.0
            score_range = bm25_max - bm25_min
            
            if score_range > 0:
                for msg in bm25_results:
                    msg['normalized_score'] = (msg['retrieval_score'] - bm25_min) / score_range
            else:
                for msg in bm25_results:
                    msg['normalized_score'] = 1.0
        
        # Semantic scores are already 0-1, just copy them
        for msg in semantic_results:
            msg['normalized_score'] = msg['retrieval_score']
        
        # Combine and deduplicate
        combined = {}
        
        # Add BM25 results with normalized scores
        for msg in bm25_results:
            msg_id = msg.get('id', msg.get('message', '')[:50])
            if msg_id not in combined:
                combined[msg_id] = msg
                combined[msg_id]['hybrid_score'] = msg['normalized_score'] * 0.4  # 40% weight
            else:
                combined[msg_id]['hybrid_score'] += msg['normalized_score'] * 0.4
        
        # Add semantic results with normalized scores
        for msg in semantic_results:
            msg_id = msg.get('id', msg.get('message', '')[:50])
            if msg_id not in combined:
                combined[msg_id] = msg
                combined[msg_id]['hybrid_score'] = msg['normalized_score'] * 0.6  # 60% weight
            else:
                combined[msg_id]['hybrid_score'] += msg['normalized_score'] * 0.6
        
        # Sort by hybrid score and return top-k
        results = sorted(combined.values(), key=lambda x: x.get('hybrid_score', 0), reverse=True)[:top_k]
        
        for r in results:
            r['retrieval_method'] = 'Hybrid'
        
        logger.info(f"Hybrid retrieval returned {len(results)} messages")
        return results


if __name__ == '__main__':
    # Test the retriever
    print("Testing Hybrid Retriever...")
    print("=" * 60)
    
    # Sample messages
    sample_messages = [
        {"id": 1, "message": "I'm planning a trip to Santorini in December"},
        {"id": 2, "message": "Please book a flight with aisle seats"},
        {"id": 3, "message": "I need a hotel near the beach"},
        {"id": 4, "message": "What restaurants are available for dinner?"},
        {"id": 5, "message": "Can you arrange a car rental in Santorini?"}
    ]
    
    query = "When is the trip to Santorini?"
    
    # Test BM25
    print("\n1. Testing BM25 Retrieval:")
    retriever_bm25 = HybridRetriever(method="bm25")
    results = retriever_bm25.retrieve(query, sample_messages, top_k=3)
    for i, msg in enumerate(results, 1):
        print(f"  {i}. [Score: {msg.get('retrieval_score', 0):.3f}] {msg['message']}")
    
    # Test Semantic
    print("\n2. Testing Semantic Retrieval:")
    retriever_semantic = HybridRetriever(method="semantic")
    results = retriever_semantic.retrieve(query, sample_messages, top_k=3)
    for i, msg in enumerate(results, 1):
        print(f"  {i}. [Score: {msg.get('retrieval_score', 0):.3f}] {msg['message']}")
    
    # Test Hybrid
    print("\n3. Testing Hybrid Retrieval:")
    retriever_hybrid = HybridRetriever(method="hybrid")
    results = retriever_hybrid.retrieve(query, sample_messages, top_k=3)
    for i, msg in enumerate(results, 1):
        print(f"  {i}. [Score: {msg.get('hybrid_score', 0):.3f}] {msg['message']}")
    
    print("\n" + "=" * 60)
    print("✅ All retrieval methods tested!")
