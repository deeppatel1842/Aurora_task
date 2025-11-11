"""
LLM Answer Generator using Ollama
Generates natural language answers from retrieved context
"""
import requests
import json
from typing import List, Dict, Optional
import logging

try:
    from config import settings
except ImportError:
    from .config import settings

logger = logging.getLogger(__name__)


class LLMGenerator:
    """Generate answers using Ollama LLM."""
    
    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None, 
                 temperature: Optional[float] = None, max_tokens: Optional[int] = None,
                 timeout: Optional[int] = None):
        """
        Initialize LLM generator.
        
        Args:
            model_name: Ollama model name (default from config)
            base_url: Ollama API base URL (default from config)
            temperature: Sampling temperature (default from config)
            max_tokens: Maximum tokens to generate (default from config)
            timeout: Request timeout in seconds (default from config)
        """
        self.model_name = model_name or settings.llm_model
        self.base_url = base_url or settings.llm_base_url
        self.temperature = temperature or settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.timeout = timeout or settings.llm_timeout
        self.api_url = f"{self.base_url}/api/generate"
        
    def generate_answer(self, question: str, context_messages: List[Dict], user_name: Optional[str] = None) -> Dict:
        """
        Generate answer using LLM based on question and retrieved context.
        
        Args:
            question: User's question
            context_messages: List of relevant messages for context
            user_name: Name of person question is about
            
        Returns:
            Dict with 'answer' and metadata
        """
        # Build context from messages
        context = self._build_context(context_messages, user_name)
        
        # Create prompt
        prompt = self._create_prompt(question, context, user_name)
        
        # Call Ollama
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "top_p": 0.9,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                
                return {
                    'answer': answer,
                    'model': self.model_name,
                    'context_used': len(context_messages),
                    'success': True
                }
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return {
                    'answer': 'Sorry, I encountered an error generating the answer.',
                    'error': f"API returned {response.status_code}",
                    'success': False
                }
                
        except requests.exceptions.Timeout:
            logger.error("Ollama API timeout")
            return {
                'answer': 'Sorry, the answer generation took too long.',
                'error': 'Timeout',
                'success': False
            }
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return {
                'answer': 'Sorry, I encountered an error.',
                'error': str(e),
                'success': False
            }
    
    def _build_context(self, messages: List[Dict], user_name: Optional[str] = None) -> str:
        """Build context string from messages, sorted by relevance with emphasis on top message."""
        if not messages:
            return "No messages found."
        
        # Sort by relevance score - most relevant first (LLMs pay more attention to early context)
        sorted_messages = sorted(
            messages[:10],  # Consider top 10
            key=lambda m: m.get('hybrid_score', m.get('retrieval_score', 0)),
            reverse=True
        )[:5]  # Take top 5 most relevant
        
        context_parts = []
        
        for i, msg in enumerate(sorted_messages, 1):
            message_text = msg.get('message', '')
            timestamp = msg.get('timestamp', '')
            
            # Format with date for context
            if timestamp:
                date = timestamp.split('T')[0]  # YYYY-MM-DD
                # Emphasize the most relevant message
                if i == 1:
                    context_parts.append(f"MOST RELEVANT: [{date}] {message_text}")
                else:
                    context_parts.append(f"{i}. [{date}] {message_text}")
            else:
                if i == 1:
                    context_parts.append(f"MOST RELEVANT: {message_text}")
                else:
                    context_parts.append(f"{i}. {message_text}")
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str, user_name: Optional[str] = None) -> str:
        """Create the prompt for the LLM."""
        name = user_name if user_name else "this person"
        prompt = f"""{name}'s messages (sorted by relevance):

{context}

Question: {question}

Instructions:
- Focus on the most specific and relevant message that directly answers the question
- Don't combine or link unrelated messages from different dates unless they're clearly about the same event
- Include specific details from the most relevant message: dates, places, durations, names
- If a message mentions "Monday" or relative dates, use the message timestamp [YYYY-MM-DD] to identify the actual date
- Give a clear, concise answer based on the best matching message

Answer:"""
        
        return prompt
    
    def test_connection(self) -> bool:
        """Test if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name') for m in models]
                if self.model_name in model_names:
                    logger.info(f"Ollama connected, model {self.model_name} available")
                    return True
                else:
                    logger.warning(f"Model {self.model_name} not found. Available: {model_names}")
                    return False
            return False
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {e}")
            return False


if __name__ == '__main__':
    # Test the LLM generator
    print("Testing LLM Generator with Llama 3.2...")
    print("=" * 60)
    
    generator = LLMGenerator()
    
    # Test connection
    print("\n1. Testing Ollama connection...")
    if generator.test_connection():
        print("✓ Connected to Ollama successfully!")
    else:
        print("✗ Failed to connect to Ollama")
        print("Make sure Ollama is running: 'ollama serve'")
        exit(1)
    
    # Test with sample data
    print("\n2. Testing answer generation...")
    sample_messages = [
        {"message": "I'm planning a trip to Santorini in the first week of December."},
        {"message": "Please book a flight with aisle seats, I prefer those."},
        {"message": "I need a hotel near the beach with ocean view."}
    ]
    
    question = "When is the person planning to go to Santorini?"
    
    print(f"\nQuestion: {question}")
    print("\nGenerating answer...")
    
    result = generator.generate_answer(question, sample_messages, "Layla")
    
    print(f"\n{'='*60}")
    print(f"Answer: {result['answer']}")
    print(f"Model: {result.get('model', 'N/A')}")
    print(f"Context used: {result.get('context_used', 0)} messages")
    print(f"Success: {result.get('success', False)}")
    print(f"{'='*60}")
