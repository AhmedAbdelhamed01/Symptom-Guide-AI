
# SymptoGuide AI

Symptoguide is a research & educational prototype: a retrieval-augmented medical assistant built with Streamlit and vector search. This repository contains scrapers, processing scripts, vector DB builders, and a Streamlit UI prototype.

IMPORTANT: This project is for research and educational purposes only. It is NOT a medical diagnostic tool. Always consult qualified healthcare professionals for medical advice.

Repository layout (key files)

- `src/app/app.py` — Streamlit UI and main application logic.
- `src/vector_db/create_vector_db.py` — build the Chroma vector database from processed JSONL data.
- `src/scrapers/` — web scrapers (NHS, Mayo, etc.).
- `src/processing/` — data cleaning and dataset creation scripts.
- `data/processed/` — processed JSON/JSONL files used for indexing.
- `chroma_db/` — persisted Chroma database (should not be committed for large DBs).
- `requirements.txt` — Python dependencies.
- `.github/workflows/python-package.yml` — CI workflow to run tests.

Prerequisites

- Python 3.10+ recommended.
- Git and an internet connection for downloading models/data when required.
- Optional: GPU + CUDA if you plan to run local embedding models faster.

Quick start (development)

1. Clone the repository:

```powershell
git clone <repo-url>
cd symptoguide-ai
```

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Run the Streamlit UI:

```powershell
streamlit run src/app/app.py
```

Configuration and environment

- If you use HuggingFace Hub models, set the `HUGGINGFACEHUB_API_TOKEN` environment variable or enter it in the app sidebar when prompted.
- Default paths are relative to the project root. See `src/vector_db/create_vector_db.py` for expected `data/processed/` and `chroma_db/` paths.

Data pipeline (from raw scraping → vector DB)

1. Scrape raw data

- Run scraper scripts in `src/scrapers/` to collect content from sources. Example:

```powershell
python src/scrapers/scrape_nhs.py
```

2. Process and clean

- Use scripts in `src/processing/` to clean, normalize, and create the master JSONL dataset. Example flow:

```powershell
python src/processing/process_nhs_symptoms_final.py
python src/processing/create_master_dataset.py
```

3. Build embeddings / vector DB

- After producing `data/processed/symptoguide_master.jsonl`, build the Chroma DB:

```powershell
python src/vector_db/create_vector_db.py
```

- The script writes a persistent Chroma DB under `chroma_db/` by default. Large DB files should not be committed; see `.gitignore`.

Running the app (detailed)

- Start the app with:

```powershell
streamlit run src/app/app.py
```

- Sidebar options allow switching model backends (local Ollama vs cloud HuggingFace). Provide tokens or credentials when using cloud services.

Testing

- Basic tests are in `tests/`. Run them with:

```powershell
pytest -q
```

Packaging

- This repository uses the `src/` layout. To build a wheel:

```powershell
pip install build
python -m build
```

- The packaging metadata files are `setup.cfg`, `pyproject.toml`, and `MANIFEST.in`.

CI

- A GitHub Actions workflow is included at `.github/workflows/python-package.yml` that installs dependencies and runs `pytest` on pushes/PRs to `main`/`master`.

Security & privacy

- Do not commit `chroma_db/`, `data/`, or `logs/` containing raw scraped text or PII. These paths are included in `.gitignore`.
- If you plan to share the project, remove any personal or sensitive data from the working copy first.

Notes about changes I made

- Renamed and moved `src/Vector_db/` → `src/vector_db/` and added `src/vector_db/create_vector_db.py` using relative paths.
- Added packaging + CI scaffolding (`setup.cfg`, `pyproject.toml`, `MANIFEST.in`, `.github/workflows/...`).
- Added small unit test placeholder in `tests/test_basic.py`.

Troubleshooting

- If the app fails to locate the vector DB, confirm `chroma_db/` exists and has data. You can rebuild it with `python src/vector_db/create_vector_db.py`.
- If HuggingFace downloads fail, check `HUGGINGFACEHUB_API_TOKEN` and network access.

Contributing

- See `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` for contribution guidelines.

License

- This repository is licensed under the MIT License (`LICENSE`).

