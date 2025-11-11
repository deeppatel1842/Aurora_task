# 🧠 Member QA System

A **production-ready Natural Language Question Answering (QA)** system for querying **member data** using advanced **semantic search**, **retrieval-augmented LLM reasoning**, and **FastAPI**.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![LLM](https://img.shields.io/badge/LLM-Llama_3.2-orange.svg)](https://ollama.com)
[![Status](https://img.shields.io/badge/Status-Deployed-success.svg)](#live-demo)

---

## 🚀 Live Demo

> The system is **live and publicly accessible**.

| Resource | URL |
|-----------|------|
| 🌐 **Live API** | [comfortless-undefiant-aaron.ngrok-free.dev](https://comfortless-undefiant-aaron.ngrok-free.dev) |
| 📘 **Interactive Docs** | [Swagger UI](https://comfortless-undefiant-aaron.ngrok-free.dev/docs) |
| 🩺 **Health Check** | [Check Status](https://comfortless-undefiant-aaron.ngrok-free.dev/health) |

### Quick Test (cURL)
```bash
curl -X POST "https://comfortless-undefiant-aaron.ngrok-free.dev/ask?use_cached_data=true"   -H "Content-Type: application/json"   -d '{"question": "When is Layla planning her trip to London?"}'
```

---

## 💡 Example Questions

| Question | Example Answer |
|-----------|----------------|
| “When is Layla planning her trip to London?” | Layla is planning her trip to London starting Monday, March 11th, and staying at Claridge’s for five nights. |
| “What does Vikram need?” | Vikram needs a yoga instructor for their stay at the villa in Tuscany. |

### Example Response
```json
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
```

---

## ⚙️ System Architecture

```
┌─────────────────────────────┐
│        User Question        │
└──────────────┬──────────────┘
               ▼
     🔍 Extract Person Name
               ▼
    🧠 Semantic Message Search
               ▼
   🗣️  LLM Answer Generation
               ▼
   ✅ JSON Answer + Confidence
```

**Key Components**
- **Person Extraction:** Identifies which of 10 known members the query is about.  
- **Retriever:** Performs semantic similarity search across ~3,349 messages.  
- **Generator:** Uses *Llama 3.2 (3B)* via **Ollama** for reasoning and answer synthesis.  
- **Cache:** `diskcache` for performance and persistence.  

---

## 🧩 API Endpoints

| Method | Endpoint | Description |
|--------|-----------|-------------|
| `POST` | `/ask` | Ask a question (uses cache by default) |
| `GET` | `/health` | Health and uptime check |
| `GET` | `/docs` | Interactive Swagger UI |
| `GET` | `/stats` | Returns dataset and performance stats |
| `GET` | `/users` | Lists all known members |
| `POST` | `/refresh-data` | Forces data reload from API |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-------------|
| **Framework** | FastAPI 0.104+ |
| **Language** | Python 3.11 |
| **LLM** | Llama 3.2 (3B) via Ollama |
| **Embeddings** | SentenceTransformers *(all-MiniLM-L6-v2)* |
| **Retrieval** | Semantic Similarity Search |
| **Caching** | diskcache (1-hour TTL) |
| **Deployment** | Docker + ngrok Tunnel |

---

## 🗂️ Project Structure

```
member-qa-system/
├── app.py                   # Entry point
├── src/
│   ├── main.py              # FastAPI app setup
│   ├── qa_engine.py         # Core QA pipeline orchestration
│   ├── llm_generator.py     # Llama 3.2 integration
│   ├── hybrid_retriever.py  # Semantic search & ranking
│   ├── data_fetcher.py      # Cached data loader
│   ├── config.py            # Configuration management
│   └── utils/
├── messages_checkpoint.ndjson  # Dataset (3,349 messages)
├── requirements.txt
└── Dockerfile
```

---

## ⚡ Performance Overview

| Metric | Value |
|--------|--------|
| **Messages Loaded** | 3,349 |
| **Average Response Time** | 12–15 seconds |
| **Warm Cache Response** | <1 second |
| **Memory Usage** | ~500 MB |
| **Confidence Threshold** | 0.2 |

---

## 🧮 Data Management

- **Primary Source:** `messages_checkpoint.ndjson` (immutable dataset)
- **Cache Layer:** diskcache (with TTL = 1 hour)
- **Load Order:** Cache → Local File → External API (on force refresh)
- **Data Integrity:** No nulls, unique IDs, minor duplicates (2–3 max)

---

## 🧠 Design Notes

### Approaches Considered

| Approach | Verdict | Notes |
|-----------|----------|-------|
| Rule-Based Pattern Matching | ❌ Rejected | Rigid, fails with paraphrasing |
| BM25 Keyword Search | ❌ Rejected | Misses semantic intent |
| Hybrid (BM25 + Semantic) | ⚠️ Evaluated | Slightly better, slower |
| **Pure Semantic Search** | ✅ Chosen | Best recall and flexibility |
| Gemma 3 QA | ❌ Rejected | Overly cautious, frequent refusals |
| **Llama 3.2 (3B)** | ✅ Deployed | Natural, contextual reasoning |

---

## 🔍 Data Insights

| Observation | Description |
|--------------|-------------|
| **User Naming Variants** | Inconsistent formats per message thread |
| **Temporal Ambiguity** | Relative terms (e.g., “next week”) |
| **Pronoun Confusion** | Unclear referents (“she”, “they”) |
| **Data Quality** | Clean — no nulls, minimal duplication |
| **Semantic Ambiguity** | “Owns” vs “likes” confusion in queries |
| **Event Overlap** | Multiple similar trips per user |

### User Distribution

| User | Message Count |
|------|----------------|
| Lily O’Sullivan | 365 |
| Thiago Monteiro | 361 |
| Fatima El-Tahir | 349 |
| Sophia Al-Farsi | 346 |
| Amina Van Den Berg | 342 |
| Vikram Desai | 335 |
| Layla Kawaguchi | 330 |
| Armand Dupont | 319 |
| Hans Miller | 314 |
| Lorenzo Cavalli | 288 |

---

## ✅ Requirements Checklist

| Category | Status |
|-----------|--------|
| Core QA Engine | ✅ Complete |
| REST Endpoints | ✅ Complete |
| JSON Schema | ✅ Complete |
| Semantic Retrieval | ✅ Complete |
| Public Deployment | ✅ Complete |
| Error Handling | ✅ Complete |
| Bonus: Design Notes | ✅ Complete |
| Bonus: Data Insights | ✅ Complete |

---

## 🧰 Setup & Installation

### Prerequisites
- Python ≥ 3.11  
- [Ollama](https://ollama.com) with **Llama 3.2**  
- Docker (optional, for containerized deployment)

### Local Setup

```bash
# 1. Pull Llama 3.2
ollama pull llama3.2:3b
ollama serve

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
python app.py
```

Visit → [http://localhost:8000](http://localhost:8000)

### Using Docker
```bash
docker-compose up
```

---

## 🧭 Configuration

Environment variables are stored in `.env` or `src/config.py`:

| Key | Example |
|-----|----------|
| `LLM_MODEL` | `llama3.2:3b` |
| `RETRIEVAL_METHOD` | `semantic` |
| `SEMANTIC_THRESHOLD` | `0.2` |
| `API_BASE_URL` | `https://november7-730026606190.europe-west1.run.app` |

---

