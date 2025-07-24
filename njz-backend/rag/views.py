# Create your views here.
import os
import json
from typing import List, Tuple
from pathlib import Path
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import faiss
import numpy as np
import spacy
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json as dj_json
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from .models import Chat, KnowledgeGraph
from .serializers import ChatSerializer, KnowledgeGraphSerializer
from django.shortcuts import get_object_or_404

# Load local embedding model (downloaded once, then reused)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")  # ~384 dims

# Adjust FAISS index to match model dimensions
d = 384
index = faiss.IndexFlatL2(d)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Neo4j connection
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "abcdefgh"))

# ========== TEXT EXTRACTION & CHUNKING ==========
# ========== TEXT EXTRACTION & SMART CHUNKING ==========

def semantic_chunking(text: str, max_tokens: int = 300) -> List[str]:
    """
    Split text into semantically meaningful chunks using spaCy sentence boundaries,
    limiting each chunk by token count (not character count).
    """
    doc = nlp(text)
    chunks = []
    current_chunk = ""
    current_token_count = 0

    for sent in doc.sents:
        sent_token_count = len(sent.text.split())
        if current_token_count + sent_token_count > max_tokens:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sent.text
            current_token_count = sent_token_count
        else:
            current_chunk += " " + sent.text
            current_token_count += sent_token_count

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def extract_and_chunk(file_path: str):
    reader = PdfReader(file_path)
    full_text = "\n\n".join([page.extract_text() or "" for page in reader.pages])
    chunks = semantic_chunking(full_text, max_tokens=300)
    return chunks, full_text


# ========== EMBEDDING & INDEXING ==========
all_metadata = []  # to collect all metadata across all PDFs

def store_metadata(meta: List[dict]):
    all_metadata.extend(meta)

def save_metadata_json(path="metadata.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved metadata to {path}")

def embed_and_index(chunks: List[str], meta: List[dict]):
    vecs = embedding_model.encode(chunks, convert_to_numpy=True)
    index.add(vecs.astype("float32"))
    store_metadata(meta)

def save_faiss_index(path="faiss_index.idx"):
    faiss.write_index(index, path)
    print(f"✅ Saved FAISS index to {path}")

# ========== KNOWLEDGE GRAPH ==========
def build_graph(text: str, doc_id: str):
    doc = nlp(text)
    relations = []
    for sent in doc.sents:
        for ent1 in sent.ents:
            for ent2 in sent.ents:
                if ent1 != ent2:
                    relations.append((ent1.text, "co_occurs_with", ent2.text))
    with driver.session() as session:
        for subj, rel, obj in relations:
            session.run(
                "MERGE (a:Entity {name:$subj}) "
                "MERGE (b:Entity {name:$obj}) "
                "MERGE (a)-[:REL {type:$rel, source:$doc_id}]->(b)",
                {"subj": subj, "obj": obj, "rel": rel, "doc_id": doc_id}
            )

# ========== MAIN ==========
def ingestion(pdf_folder: str):
    pdf_folder = Path(pdf_folder)
    pdf_files = list(pdf_folder.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in the folder.")
        return

    for pdf_path in pdf_files:
        print(f"\n📄 Processing {pdf_path.name}...")
        try:
            chunks, full_text = extract_and_chunk(str(pdf_path))
            metadata = [{"source": pdf_path.name, "chunk_id": i, "chunk_text": chunk}
                        for i, chunk in enumerate(chunks)]
            embed_and_index(chunks, metadata)
            build_graph(full_text, doc_id=pdf_path.name)
            print(f"✅ Done processing: {pdf_path.name}")
        except Exception as e:
            print(f"❌ Error processing {pdf_path.name}: {e}")

    # Save FAISS index and metadata after all files
    save_faiss_index("faiss_index.idx")
    save_metadata_json("metadata.json")



import os
import json
from typing import List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

MEDIA_DIR = getattr(settings, 'MEDIA_ROOT', 'media')
os.makedirs(MEDIA_DIR, exist_ok=True)
INDEX_PATH = os.path.join(MEDIA_DIR, 'faiss_index.idx')
METADATA_PATH = os.path.join(MEDIA_DIR, 'metadata.json')
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5

genai.configure(api_key="gemini-key")
# Load FAISS index and metadata

def load_resources() -> Tuple[faiss.IndexFlatL2, List[dict], SentenceTransformer]:
    # load FAISS index
    d = 384  # embedding dimension
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
    else:
        index = faiss.IndexFlatL2(d)

    # load metadata
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = []

    # load embedding model
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return index, metadata, embedder

# --------------------------------------------------
# Retrieve context chunks by similarity
# --------------------------------------------------
def retrieve_context(query: str,
                     index: faiss.IndexFlatL2,
                     metadata: List[dict],
                     embedder: SentenceTransformer,
                     top_k: int = TOP_K) -> List[str]:
    # encode query
    q_emb = embedder.encode([query], convert_to_numpy=True).astype('float32')
    
    # search
    distances, indices = index.search(q_emb, top_k)
    
    # gather chunk texts
    chunks = []
    for idx in indices[0]:
        chunks.append(metadata[idx]["chunk_text"])
    return chunks

# --------------------------------------------------
# Ask Gemini with retrieved context
# --------------------------------------------------
def answer_with_gemini(query: str, context: List[str]) -> str:
    prompt = (
        "You are an expert assistant. Use the following document excerpts to answer the question precisely.\n\n"
        "Excerpts:\n" + "\n---\n".join(context) + "\n\n"
        "Question: " + query + "\nAnswer:"
    )

    # Load model (only once ideally, can move this outside function for efficiency)
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(prompt)
    
    return response.text


# --------------------------------------------------
# End-to-end query function
# --------------------------------------------------
class RAGService:
    def __init__(self):
        self.index, self.metadata, self.embedder = load_resources()

    def query(self, question: str) -> str:
        context = retrieve_context(question, self.index, self.metadata, self.embedder)
        return answer_with_gemini(question, context)

# --------------------------------------------------
# CLI example
# --------------------------------------------------
if __name__ == "__main__":
    service = RAGService()
    while(True):
        user_q = input("Enter your question: ")
        print("\nAnswer:\n", service.query(user_q))




# Initialize RAG service once (global)
rag_service = RAGService()

class RagQueryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            question = request.data.get("question")
            if not question:
                return Response({"error": "No question provided"}, status=400)
            answer = rag_service.query(question)
            return Response({"answer": answer})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    def get(self, request):
        return Response({"error": "Only POST allowed"}, status=405)
    def put(self, request):
        return Response({"error": "Only POST allowed"}, status=405)
    def delete(self, request):
        return Response({"error": "Only POST allowed"}, status=405)

class ChatListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        chats = Chat.objects.filter(user=request.user)
        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ChatSerializer(data={**request.data, 'user': request.user.id})
        if serializer.is_valid():
            chat = serializer.save()
            return Response(ChatSerializer(chat).data, status=201)
        return Response(serializer.errors, status=400)

class KnowledgeGraphRetrieveView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        if hasattr(chat, 'knowledge_graph'):
            serializer = KnowledgeGraphSerializer(chat.knowledge_graph)
            return Response(serializer.data)
        return Response({'error': 'No knowledge graph for this chat.'}, status=404)

# Update UploadPDFView to create Chat and KnowledgeGraph
class UploadPDFView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        pdf_file = request.FILES.get("file")
        chat_name = request.data.get("chat_name") or pdf_file.name
        if not pdf_file:
            return Response({"error": "No file uploaded"}, status=400)
        save_dir = MEDIA_DIR
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, pdf_file.name)
        file_path = default_storage.save(save_path, ContentFile(pdf_file.read()))
        # Create Chat
        chat = Chat.objects.create(user=request.user, name=chat_name)
        # Ingest the single PDF and create per-file metadata
        try:
            chunks, full_text = extract_and_chunk(file_path)
            metadata = [{"source": pdf_file.name, "chunk_id": i, "chunk_text": chunk} for i, chunk in enumerate(chunks)]
            embed_and_index(chunks, metadata)
            build_graph(full_text, doc_id=pdf_file.name)
            # Save per-file metadata
            metadata_path = os.path.join(save_dir, f"{os.path.splitext(pdf_file.name)[0]}_metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            # Optionally, update global index/metadata as well
            save_faiss_index(INDEX_PATH)
            save_metadata_json(METADATA_PATH)
            # Store knowledge graph (for demo, just store metadata, but you can store graph structure)
            KnowledgeGraph.objects.create(chat=chat, graph_data={"metadata_path": metadata_path})
        except Exception as e:
            chat.delete()
            return Response({"error": f"Ingestion failed: {str(e)}"}, status=500)
        return Response({"message": "PDF uploaded, chat and knowledge graph created successfully", "chat_id": chat.id})
    def get(self, request):
        return Response({"error": "Only POST allowed"}, status=405)
    def put(self, request):
        return Response({"error": "Only POST allowed"}, status=405)
    def delete(self, request):
        return Response({"error": "Only POST allowed"}, status=405)



