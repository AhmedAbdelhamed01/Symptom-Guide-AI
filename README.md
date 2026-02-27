
# SymptoGuide AI 🏥

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/AhmedAbdelhamed01/symptoguide-ai/workflows/Python%20Package/badge.svg)](https://github.com/AhmedAbdelhamed01/symptoguide-ai/actions)

A research & educational prototype of a **Retrieval-Augmented Generation (RAG)** medical assistant built with **Streamlit**, **LangChain**, and **Chroma** vector database. 

SymptoGuide aggregates medical information from NHS and Mayo Clinic, processes it through a vector search pipeline, and provides AI-powered symptom guidance through an interactive web interface.

⚠️ **IMPORTANT DISCLAIMER**: This project is for **research and educational purposes only**. It is **NOT** a medical diagnostic tool and should **never be used for actual medical diagnosis or treatment**. Always consult qualified healthcare professionals for medical advice.

## Features

- 🔍 **Vector-based semantic search** using Chroma and HuggingFace embeddings
- 🤖 **LLM integration** supporting both local (Ollama) and cloud-based models
- 📊 **Multi-source data aggregation** (NHS conditions, symptoms, medicines; Mayo Clinic tests/procedures)
- 🚀 **Interactive Streamlit UI** for symptom queries and medical information retrieval
- 📦 **Full data pipeline** with scrapers, processors, and vector DB builders
- ✅ **CI/CD ready** with GitHub Actions workflow for automated testing
- 🎯 **Production-ready packaging** with setuptools configuration

## Repository Structure

```
symptoguide-ai/
├── src/
│   ├── app/                          # Streamlit application
│   │   ├── app.py                   # Main UI and logic
│   │   ├── config.py                # Configuration management
│   │   ├── llm_utils.py             # LLM backend utilities
│   │   ├── medical_logic.py         # Medical data processing
│   │   └── vector_db.py             # Vector database interface
│   ├── processing/                  # Data transformation pipeline
│   │   ├── process_nhs_symptoms_final.py
│   │   ├── process_mayo_tests_final.py
│   │   ├── clean_nhs_medicines_final.py
│   │   └── create_master_dataset.py
│   ├── scrapers/                    # Web scraping modules
│   │   ├── scrape_nhs.py
│   │   ├── scrape_nhs_medicines.py
│   │   ├── scrape_nhs_symptoms_clean.py
│   │   └── scrape_symptoms.py
│   └── vector_db/                   # Vector database creation
├── data/
│   ├── raw/                         # Original scraped data
│   └── processed/                   # Cleaned JSONL for indexing
├── chroma_db/                       # Persisted vector database (.gitignored)
├── tests/                           # Unit tests
├── pyproject.toml                   # Project metadata & build config
├── setup.cfg                        # setuptools configuration
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Prerequisites

- **Python 3.10+**
- **Git** for version control
- **pip** (included with Python)
- Internet connection for downloading models and data
- *(Optional)* GPU + CUDA for faster local embeddings

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/AhmedAbdelhamed01/symptoguide-ai.git
cd symptoguide-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run src/app/app.py
```

The app will open at `http://localhost:8501`


## Configuration

### Environment Variables

Set these environment variables before running the app:

```bash
# For HuggingFace Hub models (if used)
export HUGGINGFACEHUB_API_TOKEN=your_token_here

# For Ollama (if running locally)
# No additional setup needed; configure in app sidebar
```

### Configuration File

Edit `src/app/config.py` to customize:
- Model provider (local Ollama or HuggingFace)
- Vector database paths
- Embedding model selection
- LLM parameters (temperature, max tokens, etc.)

## Data Pipeline

The data processing flow goes from raw scraped data → cleaned JSON → master JSONL → vector embeddings:

### Step 1: Scrape Raw Data

Run scrapers to collect content from NHS and Mayo Clinic:

```bash
python src/scrapers/scrape_nhs.py
python src/scrapers/scrape_nhs_medicines.py
python src/scrapers/scrape_nhs_symptoms_clean.py
```

Data is saved to `data/raw/`

### Step 2: Process & Clean

Transform raw data into uniform, clean formats:

```bash
python src/processing/process_nhs_symptoms_final.py
python src/processing/process_mayo_tests_final.py
python src/processing/clean_nhs_medicines_final.py
python src/processing/create_master_dataset.py
```

Output: `data/processed/symptoguide_master.jsonl`

### Step 3: Build Vector Database

Create embeddings and index in Chroma:

```bash
python src/vector_db/create_vector_db.py
```

Creates persistent database at `chroma_db/`

## Usage

### Running the Application

```bash
streamlit run src/app/app.py
```

**Features:**
- Enter symptom descriptions in the search box
- Select model backend (local/cloud) in sidebar
- View AI-generated guidance with source citations
- Optional: Adjust temperature and max tokens for model behavior

### Running Tests

```bash
pytest -q
```

## Architecture

### Components

- **Data Ingestion**: NHS/Mayo scrapers collect medical information
- **Data Processing**: Cleaning and normalization pipeline
- **Vector Database**: Chroma stores embeddings for semantic search
- **LLM Backend**: Dual support for local (Ollama) and cloud models (HuggingFace)
- **UI Layer**: Streamlit provides interactive interface
- **RAG Pipeline**: LangChain orchestrates retrieval + generation

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Framework** | Streamlit |
| **LLM Integration** | LangChain |
| **Vector DB** | Chroma |
| **Embeddings** | HuggingFace Transformers |
| **Local LLM** | Ollama |
| **Testing** | pytest |
| **Build** | setuptools, build |

## Packaging & Distribution

### Build a wheel

```bash
pip install build
python -m build
```

Output files go to `dist/`

### Install locally

```bash
pip install dist/symptoguide_ai-*.whl
```

## CI/CD

GitHub Actions workflow (`.github/workflows/python-package.yml`):
- Runs on every push to `main` and PRs
- Installs dependencies
- Runs test suite with pytest
- Validates Python packaging

## Security & Privacy

🔒 **Important**:
- Never commit `chroma_db/`, `data/`, or `logs/` directories (.gitignored)
- Don't share personal or sensitive medical data scraped from sources
- Remove any PII before deploying publicly


## Troubleshooting

### Vector Database Issues

**Problem**: App fails to locate the vector DB  
**Solution**: Rebuild with `python src/vector_db/create_vector_db.py`

### HuggingFace Download Issues

**Problem**: Model downloads fail  
**Solution**: 
- Verify `HUGGINGFACEHUB_API_TOKEN` is set (if needed)
- Check internet connection
- Manually download model: `huggingface-cli download <model-id>`

### Streamlit Port Already in Use

**Problem**: Port 8501 already in use  
**Solution**: `streamlit run src/app/app.py --server.port 8502`

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Proposing features
- Submitting pull requests
- Code style and testing requirements

## Code of Conduct

This project adheres to a Contributor Code of Conduct. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Authors

- Ahmed Abdelhamed - Core development
- Developed as part of **CSAI 810: Topics in Artificial Intelligence** (Queen's University)

## Acknowledgments

- **NHS**: For providing open medical data
- **Mayo Clinic**: For test/procedure information
- **LangChain**: For the RAG orchestration framework
- **Chroma**: For vector database functionality
- **Streamlit**: For the interactive UI framework

## References

- [LangChain Documentation](https://python.langchain.com/)
- [Chroma Vector Database](https://www.trychroma.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [NHS Health Information](https://www.nhs.uk/)

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## Disclaimer

⚠️ **Medical Disclaimer**:  
This software is provided as an **educational and research tool only**. It is:
- **NOT** a substitute for professional medical advice
- **NOT** intended for medical diagnosis or treatment decisions
- **NOT** reviewed or approved by medical professionals
- **NOT** a replacement for consulting healthcare providers

**Always consult a qualified healthcare professional for medical concerns.**

---

**Last Updated**: February 2026  
**Version**: 1.0.0  
**Status**: Research/Educational Prototype
