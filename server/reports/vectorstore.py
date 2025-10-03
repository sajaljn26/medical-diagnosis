import os
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from ..config.db import reports_collection
from typing import List
from fastapi import UploadFile
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# Config
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "gemini-embedding-index")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploaded_reports")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
spec = ServerlessSpec(cloud="aws", region=PINECONE_ENV)
existing_indexes = [i["name"] for i in pc.list_indexes()]

if PINECONE_INDEX_NAME not in existing_indexes:
    print(f"Creating Pinecone index {PINECONE_INDEX_NAME} with dimension 3072...")
    pc.create_index(name=PINECONE_INDEX_NAME, dimension=3072, metric="dotproduct", spec=spec)
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        print("Waiting for index to be ready...")
        time.sleep(1)

index = pc.Index(PINECONE_INDEX_NAME)

# Upload + Embedding
async def load_vectorstore(uploaded_files: List[UploadFile], uploaded: str, doc_id: str):
    """
    Save files, chunk text, embed using Gemini, upsert into Pinecone, save metadata to MongoDB
    """
    # Initialize Gemini embeddings
    embed_model = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",  # Use your actual Gemini embedding model
        google_api_key=GOOGLE_API_KEY
    )

    for file in uploaded_files:
        filename = Path(file.filename).name
        file_dir = Path(UPLOAD_DIR) / doc_id
        os.makedirs(file_dir, exist_ok=True)
        save_path = file_dir / filename

        # Save uploaded file
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        # Load PDF pages
        loader = PyPDFLoader(str(save_path))
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_documents(documents)

        texts = [chunk.page_content for chunk in chunks]
        ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "source": filename,
                "doc_id": doc_id,
                "uploader": uploaded,
                "page": chunk.metadata.get("page", None),
                "text": chunk.page_content[:2000]
            } for chunk in chunks
        ]

        # Generate embeddings in thread
        embeddings = await asyncio.to_thread(embed_model.embed_documents, texts)

        # Upsert to Pinecone
        def upsert():
            index.upsert(vectors=list(zip(ids, embeddings, metadatas)))

        await asyncio.to_thread(upsert)

        # Save metadata to MongoDB
        reports_collection.insert_one({
            "doc_id": doc_id,
            "filename": filename,
            "uploader": uploaded,
            "uploaded_at": time.time(),
            "num_chunks": len(chunks)
        })

    print(f"Uploaded {len(uploaded_files)} file(s) successfully for doc_id {doc_id}")
