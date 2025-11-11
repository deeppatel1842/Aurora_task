"""
Real-time QA Engine with LLM Pipeline:
1. Extract person name from question
2. Fetch their messages from external API (or use cache)
3. Retrieve relevant messages using semantic/BM25/hybrid search
4. Generate natural language answer using LLM
"""
import re
from typing import Dict, List, Optional, Literal
import logging

try:
    from data_fetcher import DataFetcher
    from hybrid_retriever import HybridRetriever
    from llm_generator import LLMGenerator
    from config import settings
except ImportError:
    from .data_fetcher import DataFetcher
    from .hybrid_retriever import HybridRetriever
    from .llm_generator import LLMGenerator
    from .config import settings

logger = logging.getLogger(__name__)


class RealtimeQAEngine:
    """Real-time QA Engine with LLM generation."""
    
    def __init__(self, retrieval_method: Optional[Literal["bm25", "semantic", "hybrid"]] = None,
                 top_k: Optional[int] = None):
        """
        Initialize the QA engine.
        
        Args:
            retrieval_method: Method for retrieving relevant messages (default from config)
            top_k: Number of messages to retrieve (default from config)
        """
        self.data_fetcher = DataFetcher()
        self.retriever = HybridRetriever(method=retrieval_method)
        self.llm_generator = LLMGenerator()
        self.retrieval_method = retrieval_method or settings.retrieval_method
        self.top_k = top_k or settings.retrieval_top_k
        self.known_users = settings.known_users
        
        # Test Ollama connection
        if not self.llm_generator.test_connection():
            logger.warning("Ollama not available - will use fallback answers")
    
    def answer_question(self, question: str, use_cached_data: bool = True) -> Dict:
        """
        Answer a question using the full pipeline.
        
        Args:
            question: User's question
            use_cached_data: If True, use cached messages; if False, fetch fresh from API
            
        Returns:
            Dict with answer and metadata
        """
        logger.info(f"Processing question: '{question}'")
        
        # Step 1: Extract person name from question
        person_name = self._extract_person_name(question)
        logger.info(f"Extracted person name: {person_name}")
        
        # Step 2: Fetch messages for this person
        if person_name:
            if use_cached_data:
                messages = self.data_fetcher.get_messages_by_user(person_name)
                logger.info(f"Retrieved {len(messages)} cached messages for {person_name}")
            else:
                messages = self.data_fetcher.fetch_user_messages_realtime(person_name)
                logger.info(f"Fetched {len(messages)} fresh messages for {person_name}")
        else:
            # No specific person - use all cached messages
            messages = self.data_fetcher.get_all_messages()
            logger.info(f"No specific person - using all {len(messages)} messages")
        
        if not messages:
            return {
                'answer': f"I couldn't find any messages" + (f" for {person_name}" if person_name else ""),
                'confidence': 0.0,
                'person_name': person_name,
                'messages_found': 0,
                'retrieval_method': self.retrieval_method
            }
        
        # Step 3: Retrieve most relevant messages
        relevant_messages = self.retriever.retrieve(question, messages, top_k=self.top_k)
        logger.info(f"Retrieved {len(relevant_messages)} relevant messages")
        
        if not relevant_messages:
            return {
                'answer': "I couldn't find relevant information to answer that question.",
                'confidence': 0.0,
                'person_name': person_name,
                'messages_found': len(messages),
                'retrieval_method': self.retrieval_method
            }
        
        # Step 4: Generate answer using LLM
        llm_result = self.llm_generator.generate_answer(
            question=question,
            context_messages=relevant_messages,
            user_name=person_name
        )
        
        # Build response
        response = {
            'answer': llm_result['answer'],
            'person_name': person_name,
            'messages_found': len(messages),
            'relevant_messages': len(relevant_messages),
            'retrieval_method': self.retrieval_method,
            'llm_model': llm_result.get('model', 'N/A'),
            'success': llm_result.get('success', False)
        }
        
        # Add confidence based on retrieval scores
        if relevant_messages:
            avg_score = sum(m.get('retrieval_score', 0) or m.get('hybrid_score', 0) 
                          for m in relevant_messages) / len(relevant_messages)
            response['confidence'] = float(min(avg_score, 1.0))
        else:
            response['confidence'] = 0.0
        
        logger.info(f"Answer generated successfully with confidence {response['confidence']:.2f}")
        return response
    
    def _extract_person_name(self, question: str) -> Optional[str]:
        """
        Extract person name from the question.
        
        Args:
            question: User's question
            
        Returns:
            Person name if found, None otherwise
        """
        question_lower = question.lower()
        
        # Check for each known user (case-insensitive)
        for user_name in self.known_users:
            # Check for full name
            if user_name.lower() in question_lower:
                return user_name
            
            # Check for first name only
            first_name = user_name.split()[0].lower()
            if first_name in question_lower:
                return user_name
            
            # Check for last name only
            if len(user_name.split()) > 1:
                last_name = user_name.split()[-1].lower()
                if last_name in question_lower:
                    return user_name
        
        return None
    
    def get_stats(self) -> Dict:
        """Get statistics about the QA system."""
        messages = self.data_fetcher.get_all_messages()
        
        user_counts = {}
        for msg in messages:
            user = msg.get('user_name', 'Unknown')
            user_counts[user] = user_counts.get(user, 0) + 1
        
        return {
            'total_messages': len(messages),
            'total_users': len(user_counts),
            'known_users': self.known_users,
            'retrieval_method': self.retrieval_method,
            'llm_available': self.llm_generator.test_connection(),
            'user_message_counts': user_counts
        }


if __name__ == '__main__':
    # Test the new QA engine
    print("Testing Real-time QA Engine with LLM...")
    print("=" * 70)
    
    # Initialize engine
    print("\n1. Initializing QA Engine (hybrid retrieval)...")
    qa = RealtimeQAEngine(retrieval_method="hybrid")
    
    # Get stats
    stats = qa.get_stats()
    print(f"✓ Engine initialized")
    print(f"  - Total messages: {stats['total_messages']}")
    print(f"  - Total users: {stats['total_users']}")
    print(f"  - Retrieval method: {stats['retrieval_method']}")
    print(f"  - LLM available: {stats['llm_available']}")
    
    # Test questions
    print("\n2. Testing Questions:")
    print("=" * 70)
    
    test_questions = [
        "When is Layla planning her trip to Santorini?",
        "What are Vikram's preferences?",
        "Tell me about Sophia's restaurant reservations",
        "What does Armand need?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[Q{i}] {question}")
        result = qa.answer_question(question, use_cached_data=True)
        
        print(f"Person: {result.get('person_name', 'N/A')}")
        print(f"Answer: {result['answer']}")
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        print(f"Messages found: {result.get('messages_found', 0)}")
        print(f"Relevant: {result.get('relevant_messages', 0)}")
        print(f"Method: {result.get('retrieval_method', 'N/A')}")
        print("-" * 70)
    
    print("\n✅ All tests completed!")
