# Intelligent SHL Assessment Recommendation System

An AI-powered recommendation system that helps hiring managers find the most relevant SHL assessments for their hiring needs using Retrieval-Augmented Generation (RAG) architecture.

## 🎯 Overview

This system transforms the tedious process of manually searching for SHL assessments into an intelligent, conversational experience. Simply describe your hiring needs in natural language, and the system will recommend the most relevant assessments with detailed explanations.

## ✨ Features

- **Natural Language Queries**: Describe your hiring needs in plain English
- **Intelligent Recommendations**: AI-powered analysis using RAG pipeline
- **Balanced Results**: Automatically balances technical and behavioral assessments
- **Detailed Explanations**: Each recommendation includes:
  - Assessment description
  - Why it's a great fit for your query
  - Assessment length/completion time
  - Direct links to assessment pages
- **Real-time Processing**: Fast inference using Groq's Llama 3.1 8B Instant model
- **Interactive Web Interface**: User-friendly Streamlit frontend

## 🏗️ Architecture

### System Components

1. **Data Scraper** (`scraper.py`): Crawls SHL website and extracts assessment data
2. **Vector Store Builder** (`build_vector_store.py`): Creates FAISS index for semantic search
3. **Recommendation Engine** (`engine.py`): RAG pipeline with Groq LLM
4. **FastAPI Backend** (`main.py`): REST API server
5. **Streamlit Frontend** (`app.py`): Interactive web interface

### RAG Pipeline Flow

```
User Query → Embedding → FAISS Search (Top 20) → LLM Re-ranking → Final Recommendations (5-10)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Groq API key ([Get one here](https://console.groq.com/))
- `uv` package manager (or use `pip`)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/UTSAVS26/Intelligent-SHL-Assessment-Recommendation-System.git
   cd shl-recommender
   ```

2. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```
   Or with pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY="your_groq_api_key_here"
   ```

4. **Scrape assessment data**
   ```bash
   python scraper.py
   ```
   
   This will:
   - Read assessment URLs from `Gen_AI_Dataset.xlsx`
   - Scrape each assessment page for details
   - Save data to `data/shl_assessments.csv`

5. **Build vector store**
   ```bash
   python build_vector_store.py
   ```
   
   This will:
   - Generate embeddings using sentence transformers
   - Create FAISS index
   - Save index and mappings to `data/` directory

6. **Start the FastAPI server**
   ```bash
   uvicorn main:app --reload
   ```
   
   Server will be available at `http://127.0.0.1:8000`

7. **Launch Streamlit frontend** (in a new terminal)
   ```bash
   streamlit run app.py
   ```
   
   Frontend will be available at `http://localhost:8501`

## 📁 Project Structure

```
shl-recommender/
│
├── scraper.py                 # Web scraper for SHL assessments
├── build_vector_store.py     # FAISS vector index builder
├── engine.py                  # RAG pipeline and recommendation logic
├── main.py                    # FastAPI backend server
├── app.py                     # Streamlit frontend
│
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
├── .gitignore                 # Git ignore rules
│
├── Gen_AI_Dataset.xlsx        # Input dataset with assessment URLs
│
└── data/                      # Generated data files
    ├── shl_assessments.csv    # Scraped assessment data
    ├── faiss_index.bin        # FAISS vector index
    └── index_to_data.pkl      # Index to assessment mapping
```

## 🔧 Configuration

### Environment Variables

- `GROQ_API_KEY`: Your Groq API key (required)

### Model Configuration

The system uses:
- **Embedding Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **LLM Model**: `llama-3.1-8b-instant` (Groq API)
- **Vector Database**: FAISS (IndexFlatL2)

### API Endpoints

- `GET /health`: Health check endpoint
- `POST /recommend`: Get assessment recommendations
  ```json
  {
    "query": "I need to hire a senior Java developer with leadership skills"
  }
  ```

## 📊 Data Flow

1. **Data Collection**: Scraper extracts assessment information from SHL website
2. **Vectorization**: Text data converted to embeddings using sentence transformers
3. **Indexing**: Embeddings stored in FAISS for fast similarity search
4. **Retrieval**: User query embedded and top 20 similar assessments retrieved
5. **Generation**: LLM re-ranks and selects final 5-10 recommendations
6. **Response**: Recommendations returned with descriptions and explanations

## 🎨 Features in Detail

### Intelligent Recommendation

The system uses a sophisticated RAG pipeline:
- **Semantic Search**: Finds assessments similar to your query
- **Contextual Re-ranking**: LLM analyzes query requirements and assessment details
- **Balanced Selection**: Ensures mix of technical and behavioral assessments when needed

### Rich Recommendations

Each recommendation includes:
- **Assessment Name**: Full name of the assessment
- **Description**: What the assessment measures
- **Why Great Fit**: Explanation connecting query requirements to assessment capabilities
- **Assessment Length**: Completion time information
- **Direct Link**: URL to assessment page

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance async web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### AI/ML
- **Groq API**: Fast LLM inference (Llama 3.1 8B Instant)
- **Sentence Transformers**: Text embeddings
- **FAISS**: Vector similarity search

### Frontend
- **Streamlit**: Interactive web application

### Data Processing
- **Pandas**: Data manipulation
- **BeautifulSoup**: Web scraping
- **Requests**: HTTP library

## 📝 Usage Examples

### Example Query 1: Technical Role
```
Query: "I am hiring for Java developers who can also collaborate 
effectively with my business teams. Looking for an assessment(s) 
that can be completed in 40 minutes."

Result: System recommends a mix of:
- Technical assessments (Java skills, coding abilities)
- Behavioral assessments (collaboration, communication)
- All within the 40-minute time constraint
```

### Example Query 2: Sales Role
```
Query: "I want to hire new graduates for a sales role in my company, 
the budget is for about an hour for each test. Give me some options"

Result: System recommends:
- Sales-specific assessments
- Entry-level appropriate tests
- All within 1-hour completion time
```

### Example Query 3: Cultural Fit
```
Query: "I am looking for a COO for my company in China and I want 
to see if they are culturally a right fit for our company. Suggest 
me an assessment that they can complete in about an hour"

Result: System recommends:
- Leadership assessments
- Cultural fit assessments
- Appropriate for COO level
- Within 1-hour timeframe
```

## 🔍 How It Works

### Step 1: Data Ingestion
The scraper reads assessment URLs from `Gen_AI_Dataset.xlsx` and extracts:
- Assessment name
- Description
- Job levels
- Languages
- Assessment length
- Type (Knowledge & Skills, Personality & Behavior, etc.)

### Step 2: Vectorization
Each assessment is converted to a rich text document:
```
Name: [Assessment Name]
Type: [Assessment Type]
Description: [Description]
Job Levels: [Job Levels]
Languages: [Languages]
Assessment Length: [Length]
```

This document is embedded using `all-MiniLM-L6-v2` to create a 384-dimensional vector.

### Step 3: Indexing
All embeddings are stored in a FAISS index for fast similarity search.

### Step 4: Query Processing
When a user submits a query:
1. Query is embedded using the same model
2. FAISS searches for top 20 most similar assessments
3. Retrieved assessments and query are sent to Groq LLM
4. LLM analyzes and re-ranks to select final 5-10 recommendations
5. LLM generates explanations for each recommendation

### Step 5: Response
Recommendations are returned with:
- Assessment details
- Why it's a great fit
- Assessment length
- Direct links

## 🚧 Troubleshooting

### Common Issues

**Issue**: `GROQ_API_KEY not found`
- **Solution**: Ensure `.env` file exists with `GROQ_API_KEY="your_key"`

**Issue**: `Vector store files not found`
- **Solution**: Run `python build_vector_store.py` after scraping data

**Issue**: `ImportError: cannot import name 'PydanticUndefined'`
- **Solution**: Update pydantic: `uv pip install --upgrade pydantic pydantic-core`

**Issue**: Server port already in use
- **Solution**: Change port: `uvicorn main:app --port 8001`

## 📈 Performance

The system is optimized for:
- **Speed**: Fast inference using Groq's optimized models
- **Accuracy**: Semantic search + LLM re-ranking for high relevance
- **Balance**: Automatic balancing of technical and behavioral assessments

## 🔐 Security

- API keys stored in `.env` file (not committed to git)
- `.env` file included in `.gitignore`
- CORS configured for frontend access

## 📄 License

[Specify your license here]

## 👥 Contributing

[Add contribution guidelines if applicable]

## 📧 Contact

[Add contact information]

## 🙏 Acknowledgments

- SHL for providing the assessment catalog
- Groq for fast LLM inference
- Sentence Transformers for embeddings
- FAISS for efficient vector search

---

**Built with ❤️ using Python, FastAPI, Streamlit, and Groq AI**

