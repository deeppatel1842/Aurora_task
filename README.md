# Member QA System

A production-ready natural language question-answering system that answers questions about member data using advanced NLP, semantic search, and LLM generation.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![LLM](https://img.shields.io/badge/LLM-Llama_3.2-orange.svg)](https://ollama.com)
[![Status](https://img.shields.io/badge/Status-Deployed-green.svg)](#live-service)

## Quick Links

- **Live API**: https://comfortless-undefiant-aaron.ngrok-free.dev
- **Interactive Docs**: https://comfortless-undefiant-aaron.ngrok-free.dev/docs
- **Health Check**: https://comfortless-undefiant-aaron.ngrok-free.dev/health

## Live Service

**The system is currently deployed and publicly accessible!**

### Try It Now

Visit the interactive documentation: https://comfortless-undefiant-aaron.ngrok-free.dev/docs

**Using cURL:**
``ash
curl -X POST "https://comfortless-undefiant-aaron.ngrok-free.dev/ask?use_cached_data=true" \
  -H "Content-Type: application/json" \
  -d '{"question": "When is Layla planning her trip to London?"}'
``

### Example Questions

- **"When is Layla planning her trip to London?"**
  - Answer: "Layla is planning her trip to London starting Monday, March 11th, and staying at Claridge's for five nights."

- **"What does Vikram need?"**
  - Answer: "Vikram needs a yoga instructor for their stay at the villa in Tuscany."

- **"How many cars does Vikram Desai have?"**

- **"What are Amira's favorite restaurants?"**

### Response Example

``json
{
  "answer": "Layla is planning her trip to London starting Monday, March 11th, and staying at Claridge's for five nights.",
  "confidence": 0.35,
  "metadata": {
    "person_name": "Layla Kawaguchi",
    "messages_found": 330,
    "relevant_messages": 10,
    "retrieval_method": "semantic",
    "llm_model": "llama3.2:3b",
    "used_cached_data": true
  }
}
``

## Architecture

### System Pipeline

``
User Question
     ?
Extract Person Name (10 known users)
     ?
Fetch Messages from Cache/Local File/API
     ?
Semantic Similarity Search (Top-10 relevance)
     ?
LLM Answer Generation (Llama 3.2)
     ?
Return Answer with Confidence Score
``

## API Endpoints

### Ask Question
``ash
POST https://comfortless-undefiant-aaron.ngrok-free.dev/ask?use_cached_data=true
Content-Type: application/json

{
  "question": "When is Layla planning her trip to London?"
}
``

### Health Check
``ash
GET https://comfortless-undefiant-aaron.ngrok-free.dev/health
``

### Other Endpoints
- GET /docs - Interactive API documentation (Swagger UI)
- GET /stats - System statistics
- GET /users - List all known users
- POST /refresh-data - Force refresh from external API

## Technical Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.104+ |
| Language | Python 3.11 |
| LLM | Llama 3.2:3b (via Ollama) |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) |
| Retrieval | Semantic similarity search |
| Caching | diskcache |
| Deployment | Docker + ngrok |

## Project Structure

- pp.py - Entry point
- src/main.py - FastAPI application with all endpoints
- src/qa_engine.py - QA pipeline orchestration
- src/llm_generator.py - Llama 3.2 integration
- src/hybrid_retriever.py - Semantic search retrieval
- src/data_fetcher.py - Data loading with caching
- src/config.py - Configuration management
- messages_checkpoint.ndjson - Dataset (3,349 messages)
- 
equirements.txt - Python dependencies

## Getting Started

### Prerequisites
- Python 3.11+
- Ollama with Llama 3.2 model
- Docker (optional)

### Installation

1. Install Ollama and pull model
``ash
ollama pull llama3.2:3b
ollama serve
``

2. Install dependencies
``ash
pip install -r requirements.txt
``

3. Run the server
``ash
python app.py
``

4. Access at http://localhost:8000

### Using Docker

``ash
docker-compose up
``

## Performance

- **Messages Loaded**: 3,349 from local file
- **Response Time**: 12-15 seconds per query
- **Memory Usage**: ~500MB (with embeddings)
- **Warm Cache**: <1 second response

## Data Management

- **Source**: messages_checkpoint.ndjson (permanent, never overwritten)
- **Cache**: In-memory with diskcache (1-hour TTL)
- **Refresh**: Optional API update (updates cache only)
- **Loading Priority**: Cache ? Local File ? API (only on force refresh)

## Bonus 1: Design Notes

### Approaches Evaluated

1. **Rule-Based Pattern Matching** [REJECTED] - Too rigid for natural language variation
2. **BM25 Keyword Search** [REJECTED] - Misses semantic meaning
3. **Hybrid BM25 + Semantic** [REJECTED] - Complex score normalization
4. **Pure Semantic Search** [CHOSEN] - Understands intent, handles paraphrasing
5. **Gemma 3 QA** [REJECTED] - Overly cautious, refused to answer
6. **Llama 3.2** [CHOSEN] - Confident, conversational, better date inference

## Bonus 2: Data Insights

Dataset: 3,349 messages from 10 users

### Key Anomalies

1. **Inconsistent User Naming** - Different name formats in messages
2. **Temporal Inconsistency** - Relative dates without absolute timestamps
3. **Ambiguous Pronouns** - No clear antecedents in messages
4. **Data Quality** - No nulls, all IDs unique, 2-3 exact duplicates
5. **Semantic Ambiguity** - Ownership vs preference queries
6. **Multi-Event Confusion** - Multiple trips to same location

### User Distribution

| User | Messages |
|------|----------|
| Lily O'Sullivan | 365 |
| Thiago Monteiro | 361 |
| Fatima El-Tahir | 349 |
| Sophia Al-Farsi | 346 |
| Amina Van Den Berg | 342 |
| Vikram Desai | 335 |
| Layla Kawaguchi | 330 |
| Armand Dupont | 319 |
| Hans M�ller | 314 |
| Lorenzo Cavalli | 288 |

## Requirements Checklist

### Core [COMPLETE]
- Natural Language QA engine
- POST /ask endpoint
- JSON response format
- External API integration
- Public deployment
- Error handling

### Bonus [COMPLETE]
- Design notes (6 approaches evaluated)
- Data insights (6 anomalies identified)

## Configuration

All settings in src/config.py or .env:
- LLM_MODEL=llama3.2:3b
- RETRIEVAL_METHOD=semantic
- SEMANTIC_THRESHOLD=0.2
- API_BASE_URL=https://november7-730026606190.europe-west1.run.app

## License

MIT License

---

**Status**: Production Ready
**Version**: 2.0.0
**Deployed**: https://comfortless-undefiant-aaron.ngrok-free.dev
**Last Updated**: November 2024
