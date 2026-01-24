import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader

# --------------------------------------------------
# Configuration
# --------------------------------------------------
DOCUMENT_SOURCE_DIR = "../think/knowledge_base/"
INDEX_FILE_NAME = "index.faiss"
MAPPING_FILE_NAME = "index_to_doc.pkl"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# --------------------------------------------------
# 1. Load documents
# --------------------------------------------------
print("📂 Loading documents...")
loader = DirectoryLoader(
    DOCUMENT_SOURCE_DIR,
    glob="**/*.txt",
    loader_cls=TextLoader,
    show_progress=True
)

documents = loader.load()
if not documents:
    raise RuntimeError("❌ No documents found in knowledge_base")

print(f"✅ Loaded {len(documents)} documents")

# --------------------------------------------------
# 2. Split into chunks
# --------------------------------------------------
print("✂️ Splitting documents into chunks...")
text_splitter = CharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100
)

docs = text_splitter.split_documents(documents)
print(f"✅ Created {len(docs)} chunks")

# --------------------------------------------------
# 3. Embed locally using Sentence Transformers
# --------------------------------------------------
print(f"🧠 Loading embedding model: {EMBEDDING_MODEL_NAME}")
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

texts = [doc.page_content for doc in docs]

print("🔢 Embedding chunks locally...")
embeddings = model.encode(
    texts,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)

vector_dimension = embeddings.shape[1]
print(f"✅ Embedding dimension: {vector_dimension}")

# --------------------------------------------------
# 4. Create FAISS index
# --------------------------------------------------
print("📦 Creating FAISS index...")
index = faiss.IndexFlatL2(vector_dimension)
index.add(embeddings)

print(f"✅ FAISS index contains {index.ntotal} vectors")

# --------------------------------------------------
# 5. Save index + document mapping
# --------------------------------------------------
print("💾 Saving FAISS index...")
faiss.write_index(index, INDEX_FILE_NAME)

index_to_doc_mapping = {
    i: docs[i].page_content for i in range(len(docs))
}

print("💾 Saving document mapping...")
with open(MAPPING_FILE_NAME, "wb") as f:
    pickle.dump(index_to_doc_mapping, f)

print("\n🎉 VECTOR STORE READY")
print(f"📁 {INDEX_FILE_NAME}")
print(f"📁 {MAPPING_FILE_NAME}")
print("➡️ Package these two files with your Lambda")
