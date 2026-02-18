"""
Local Vector Store for Energy Safety Knowledge Base.

Replaces AWS Bedrock Knowledge Base with a local ChromaDB instance.
Loads all .md files from the knowledge_base directory, chunks them
by markdown headers, and provides semantic search via embeddings.
"""

import os
import re
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

# --- CONFIGURATION ---
KB_DIR = Path(__file__).parent  # knowledge_base/ directory
COLLECTION_NAME = "energy_safety_kb"
PERSIST_DIR = str(KB_DIR / ".chroma_db")

# Use the default sentence-transformer embedding (runs locally, no API needed)
# Model: all-MiniLM-L6-v2 (~80MB, fast, good quality)
_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# --- CHUNKING LOGIC ---
def _chunk_markdown(filepath: Path) -> list[dict]:
    """
    Split a markdown file into chunks by ## and ### headers.
    Each chunk includes: the parent header (##) as context prefix + the child content.
    """
    text = filepath.read_text(encoding="utf-8")
    filename = filepath.stem  # e.g. "operational_safety_protocols"

    chunks = []
    current_parent = filename  # fallback parent = filename
    current_header = ""
    current_content = []

    for line in text.split("\n"):
        # Detect ## Parent Header
        if line.startswith("## "):
            # Flush previous chunk
            if current_content:
                chunks.append({
                    "text": f"[{current_parent}] {current_header}\n" + "\n".join(current_content),
                    "source": str(filepath.name),
                    "section": current_header or current_parent
                })
                current_content = []
            current_parent = line.strip("# ").strip()
            current_header = current_parent

        # Detect ### Child Header
        elif line.startswith("### "):
            # Flush previous chunk
            if current_content:
                chunks.append({
                    "text": f"[{current_parent}] {current_header}\n" + "\n".join(current_content),
                    "source": str(filepath.name),
                    "section": current_header or current_parent
                })
                current_content = []
            current_header = line.strip("# ").strip()

        else:
            if line.strip():  # skip empty lines
                current_content.append(line.strip())

    # Flush last chunk
    if current_content:
        chunks.append({
            "text": f"[{current_parent}] {current_header}\n" + "\n".join(current_content),
            "source": str(filepath.name),
            "section": current_header or current_parent
        })

    return chunks


def _load_all_kb_files() -> list[dict]:
    """Load and chunk all .md files in the knowledge_base directory."""
    all_chunks = []
    for md_file in KB_DIR.glob("*.md"):
        chunks = _chunk_markdown(md_file)
        all_chunks.extend(chunks)
        print(f"  📄 {md_file.name}: {len(chunks)} chunks")
    return all_chunks


# --- VECTOR STORE ---
_client = chromadb.Client(chromadb.Settings(
    anonymized_telemetry=False,
    is_persistent=True,
    persist_directory=PERSIST_DIR
))

_collection = None


def _get_or_create_collection():
    """Get or create the ChromaDB collection, ingesting KB files if needed."""
    global _collection

    if _collection is not None:
        return _collection

    # Check if collection already exists with data
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # If empty, ingest all KB files
    if _collection.count() == 0:
        print("🔄 Ingesting Knowledge Base files into local vector store...")
        chunks = _load_all_kb_files()

        if not chunks:
            print("⚠️ No .md files found in knowledge_base directory!")
            return _collection

        _collection.add(
            ids=[f"chunk_{i}" for i in range(len(chunks))],
            documents=[c["text"] for c in chunks],
            metadatas=[{"source": c["source"], "section": c["section"]} for c in chunks]
        )
        print(f"✅ Ingested {len(chunks)} chunks into local vector store.")
    else:
        print(f"✅ Local vector store loaded ({_collection.count()} chunks).")

    return _collection


def rebuild_index():
    """Force re-ingest all KB files. Call this after updating .md files."""
    global _collection
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = None
    return _get_or_create_collection()


# --- PUBLIC API (drop-in replacement for AWS Bedrock) ---
def query_knowledge_base(query: str, n_results: int = 3) -> str:
    """
    Search the local knowledge base for relevant safety protocols.
    Returns concatenated text snippets (same interface as the old AWS retriever).
    """
    collection = _get_or_create_collection()

    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    if not results["documents"] or not results["documents"][0]:
        return "No specific safety protocols found for this query. Default to SAFE_MODE."

    # Combine retrieved snippets (same format as the old AWS retriever)
    snippets = results["documents"][0]
    return "\n\n---\n\n".join(snippets)


# Auto-initialize on import
_get_or_create_collection()
