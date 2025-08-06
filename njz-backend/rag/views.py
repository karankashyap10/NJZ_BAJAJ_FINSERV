import os
import json
from typing import List, Tuple
from pathlib import Path
from pypdf import PdfReader

import faiss
import numpy as np
import spacy
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from datetime import datetime
import requests
import tempfile
import time
import functools
import logging

# Set up logging for timing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== TIMING DECORATOR ==========
def timing_decorator(func):
    """Decorator to track function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"⏱️ {func.__name__} took {execution_time:.4f} seconds")
        return result
    return wrapper

# ========== CONTEXT MANAGER FOR TIMING ==========
class Timer:
    """Context manager for timing code blocks"""
    def __init__(self, name):
        self.name = name
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        execution_time = end_time - self.start_time
        logger.info(f"⏱️ {self.name} took {execution_time:.4f} seconds")

# ========== MANUAL TIMING UTILITY ==========
def track_time(operation_name):
    """Manual timing utility - returns a function to call when done"""
    start_time = time.time()
    def end_tracking():
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"⏱️ {operation_name} took {execution_time:.4f} seconds")
    return end_tracking


# Load local embedding model (downloaded once, then reused)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")  # ~384 dims
model = genai.GenerativeModel("gemini-2.5-flash")
# Adjust FAISS index to match model dimensions
d = 384
index = faiss.IndexFlatL2(d)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Neo4j connection
driver = GraphDatabase.driver("neo4j+s://e4746836.databases.neo4j.io", auth=("neo4j", "mMEzzIJOOBuXLoc9o-mMOryYRq2YWJU9324ynlsGTi4"))

# ========== TEXT EXTRACTION & CHUNKING ==========
# ========== TEXT EXTRACTION & SMART CHUNKING ==========

from typing import List

#@timing_decorator
def semantic_chunking(text: str, max_tokens: int = 400, overlap: int = 100) -> List[str]:
    """
    Split text into semantically meaningful chunks using spaCy sentence boundaries,
    limiting each chunk by token count (not character count), and using token overlap.
    """
    doc = nlp(text)
    chunks = []
    current_chunk_sents = []
    current_token_count = 0

    token_queue = []

    for sent in doc.sents:
        sent_tokens = sent.text.split()
        sent_token_count = len(sent_tokens)

        if current_token_count + sent_token_count > max_tokens:
            # Create the chunk
            chunk_text = " ".join(current_chunk_sents).strip()
            if chunk_text:
                chunks.append(chunk_text)

            # Implement token overlap from the end of the last chunk
            overlap_tokens = token_queue[-overlap:] if overlap > 0 else []
            overlap_text = " ".join([tok.text for tok in overlap_tokens])
            overlap_doc = nlp(overlap_text)
            overlap_sents = [sent.text for sent in overlap_doc.sents]

            # Reset for next chunk
            current_chunk_sents = overlap_sents + [sent.text]
            current_token_count = len(" ".join(current_chunk_sents).split())
        else:
            current_chunk_sents.append(sent.text)
            current_token_count += sent_token_count

        # Update token queue
        token_queue.extend(list(sent))

    # Add remaining chunk
    if current_chunk_sents:
        chunk_text = " ".join(current_chunk_sents).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks


#@timing_decorator
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

#@timing_decorator
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
            # Knowledge graph creation commented out for now
            # build_graph(full_text, doc_id=pdf_path.name)
            print(f"✅ Done processing: {pdf_path.name}")
        except Exception as e:
            print(f"❌ Error processing {pdf_path.name}: {e}")

    # Save FAISS index and metadata after all files
    save_faiss_index("faiss_index.idx")
    save_metadata_json("metadata.json")

# ========== GLOBAL VARIABLES ==========
MEDIA_DIR = getattr(settings, 'MEDIA_ROOT', 'media')
os.makedirs(MEDIA_DIR, exist_ok=True)
INDEX_PATH = os.path.join(MEDIA_DIR, 'faiss_index.idx')
METADATA_PATH = os.path.join(MEDIA_DIR, 'metadata.json')
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 3

genai.configure(api_key="AIzaSyCiAWJw41BYAPi6qs4aJqjID_P3Goj1NQ4")

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
#@timing_decorator
def answer_with_gemini(query: str, context: List[str]) -> str:
    prompt = (
        "You are an expert assistant. Use the following document excerpts to answer the question precisely . keep it **one liner strictly** and dont use markdown just give plain text\n\n"
        "Excerpts:\n" + "\n---\n".join(context) + "\n\n"
        "Question: " + query + "\nAnswer:"
    )

    # Load model (only once ideally, can move this outside function for efficiency)
    
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

def get_chat_dir(chat_id):
    chat_dir = os.path.join(MEDIA_DIR, f"chat_{chat_id}")
    os.makedirs(chat_dir, exist_ok=True)
    return chat_dir

def get_chat_index_path(chat_id):
    return os.path.join(get_chat_dir(chat_id), "faiss_index.idx")

def get_chat_metadata_path(chat_id):
    return os.path.join(get_chat_dir(chat_id), "metadata.json")

def get_chat_metadata(chat_id):
    path = get_chat_metadata_path(chat_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_chat_metadata(chat_id, metadata):
    path = get_chat_metadata_path(chat_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def get_chat_index(chat_id):
    path = get_chat_index_path(chat_id)
    if os.path.exists(path):
        return faiss.read_index(path)
    else:
        return faiss.IndexFlatL2(d)

def save_chat_index(chat_id, index):
    path = get_chat_index_path(chat_id)
    faiss.write_index(index, path)

class UploadPDFToChatView(APIView):
    authentication_classes = []  # Disable authentication
    permission_classes = []  # Disable permissions
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, chat_id):
        # chat = get_object_or_404(Chat, id=chat_id, user=request.user)  # Commented for no auth
        pdf_file = request.FILES.get("file")
        if not pdf_file:
            return Response({"error": "No file uploaded"}, status=400)
        save_path = os.path.join(f"chat_{chat_id}", pdf_file.name)
        relative_path = default_storage.save(save_path, ContentFile(pdf_file.read()))
        file_path = default_storage.path(relative_path)
        try:
            with Timer("PDF Upload and Processing"):
                # Load or create per-chat index/metadata
                index = get_chat_index(chat_id)
                metadata = get_chat_metadata(chat_id)
                # Ingest PDF
                chunks, full_text = extract_and_chunk(file_path)
                new_metadata = [{"source": pdf_file.name, "chunk_id": i, "chunk_text": chunk} for i, chunk in enumerate(chunks)]
                vecs = embedding_model.encode(chunks, convert_to_numpy=True)
                index.add(vecs.astype("float32"))
                metadata.extend(new_metadata)
                # Save updated index/metadata
                save_chat_index(chat_id, index)
                save_chat_metadata(chat_id, metadata)
                # Knowledge graph creation commented out for now
                # build_graph(full_text, doc_id=pdf_file.name)
                # if hasattr(chat, 'knowledge_graph'):
                #     chat.knowledge_graph.graph_data = {"info": f"Updated with {pdf_file.name}"}
                #     chat.knowledge_graph.save()
                # else:
                #     KnowledgeGraph.objects.create(chat=chat, graph_data={"info": f"Created with {pdf_file.name}"})
        except Exception as e:
            # Optionally, clean up file
            if os.path.exists(file_path):
                os.remove(file_path)
            return Response({"error": f"Ingestion failed: {str(e)}"}, status=500)
        return Response({"message": "PDF uploaded and knowledge graph updated", "chat_id": chat_id})

class ChatQueryView(APIView):
    authentication_classes = []  # Disable authentication
    permission_classes = []  # Disable permissions

    def post(self, request, chat_id):
        # chat = get_object_or_404(Chat, id=chat_id, user=request.user)  # Commented for no auth
        question = request.data.get("question")
        if not question:
            return Response({"error": "No question provided"}, status=400)
        try:
            with Timer("Chat Query Processing"):
                # Load per-chat index/metadata
                index = get_chat_index(chat_id)
                metadata = get_chat_metadata(chat_id)
                if not metadata or index.ntotal == 0:
                    return Response({"error": "No knowledge available for this chat. Upload PDFs first."}, status=400)
                q_emb = embedding_model.encode([question], convert_to_numpy=True).astype('float32')
                top_k = min(TOP_K, len(metadata))
                distances, indices = index.search(q_emb, top_k)
                context = [metadata[idx]["chunk_text"] for idx in indices[0] if idx < len(metadata)]
                answer = answer_with_gemini(question, context)
            
            # Create structured message objects
            user_message = {
                "content": question,
                "sender": "user",
                "timestamp": str(datetime.now())
            }
            ai_message = {
                "content": answer,
                "sender": "ai", 
                "timestamp": str(datetime.now())
            }
            
            # Append messages to chat (commented for no auth)
            # if not chat.messages:
            #     chat.messages = []
            # chat.messages.extend([user_message, ai_message])
            # chat.save()
            
            return Response({"answer": answer})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def get(self, request, chat_id):
        # chat = get_object_or_404(Chat, id=chat_id, user=request.user)  # Commented for no auth
        return Response({"messages": []})  # Return empty messages for no auth

class ChatListCreateView(APIView):
    authentication_classes = []  # Disable authentication
    permission_classes = []  # Disable permissions

    def get(self, request):
        # chats = Chat.objects.filter(user=request.user)  # Commented for no auth
        # serializer = ChatSerializer(chats, many=True)
        return Response({"chats": []})  # Return empty chats for no auth

    def post(self, request):
        # serializer = ChatSerializer(data={**request.data, 'user': request.user.id})  # Commented for no auth
        # if serializer.is_valid():
        #     chat = serializer.save()
        #     return Response(ChatSerializer(chat).data, status=201)
        # return Response(serializer.errors, status=400)
        return Response({"message": "Chat creation disabled for no auth mode"}, status=200)

class KnowledgeGraphRetrieveView(APIView):
    authentication_classes = []  # Disable authentication
    permission_classes = []  # Disable permissions

    def get(self, request, chat_id):
        # chat = get_object_or_404(Chat, id=chat_id, user=request.user)  # Commented for no auth
        # if hasattr(chat, 'knowledge_graph'):
        #     serializer = KnowledgeGraphSerializer(chat.knowledge_graph)
        #     return Response(serializer.data)
        # return Response({'error': 'No knowledge graph for this chat.'}, status=404)
        return Response({'error': 'Knowledge graph disabled for no auth mode'}, status=404)

class ChatMessageView(APIView):
    authentication_classes = []  # Disable authentication
    permission_classes = []  # Disable permissions

    def post(self, request, chat_id):
        # chat = get_object_or_404(Chat, id=chat_id, user=request.user)  # Commented for no auth
        content = request.data.get("content")
        sender = request.data.get("sender", "user")
        
        if not content:
            return Response({"error": "No content provided"}, status=400)
        
        try:
            # Create structured message object
            message = {
                "content": content,
                "sender": sender,
                "timestamp": str(datetime.now())
            }
            
            # Append message to chat (commented for no auth)
            # if not chat.messages:
            #     chat.messages = []
            # chat.messages.append(message)
            # chat.save()
            
            return Response({"message": "Message stored successfully (no auth mode)"})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def get(self, request, chat_id):
        # chat = get_object_or_404(Chat, id=chat_id, user=request.user)  # Commented for no auth
        return Response({"messages": []})  # Return empty messages for no auth



#hackrx
class HackRxRunView(APIView):
    authentication_classes = []  # Disable authentication
    permission_classes = []  # Disable permissions

    def post(self, request, *args, **kwargs):
        """
        Expects format:
        {
            "documents": "https://host/some.pdf",
            "questions": [
                "What ... ?", "Explain ... ?", ...
            ]
        }
        Returns:
        {
            "answers": [ "answer1", "answer2", ... ]
        }
        """
        documents_url = request.data.get('documents')
        questions = request.data.get('questions')

        if not documents_url or not isinstance(questions, list) or not questions:
            return Response({"error": "Payload must include 'documents' (url) and 'questions' (list)."}, status=400)

        # Download PDF (simple version)
        try:
            response = requests.get(documents_url)
            response.raise_for_status()
        except Exception as e:
            return Response({"error": f"Could not download document: {e}"}, status=400)

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(response.content)
            temp_pdf_path = temp_pdf.name

        # 1. Extract, chunk
        try:
            chunks, full_text = extract_and_chunk(temp_pdf_path)
            metadata = [{"source": os.path.basename(temp_pdf_path), "chunk_id": i, "chunk_text": chunk} for i, chunk in enumerate(chunks)]
            vecs = embedding_model.encode(chunks, convert_to_numpy=True)
            temp_index = faiss.IndexFlatL2(embedding_model.get_sentence_embedding_dimension())
            temp_index.add(vecs.astype("float32"))
        except Exception as e:
            os.remove(temp_pdf_path)
            return Response({"error": f"Error processing PDF: {e}"}, status=500)

        # 2. For each question, retrieve context and answer
        answers = []
        for question in questions:
            try:
                q_emb = embedding_model.encode([question], convert_to_numpy=True).astype('float32')
                top_k = min(TOP_K, len(metadata))
                distances, indices = temp_index.search(q_emb, top_k)
                context = [metadata[idx]["chunk_text"] for idx in indices[0] if idx < len(metadata)]
                answer = answer_with_gemini(question, context)
            except Exception as ex:
                answer = f"ERROR: {str(ex)}"
            answers.append(answer)

        # Clean up temp file
        os.remove(temp_pdf_path)

        return Response({"answers": answers})
