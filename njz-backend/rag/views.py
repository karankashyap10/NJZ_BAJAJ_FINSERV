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
import shutil
from datetime import datetime
import requests
import tempfile



# Load local embedding model (downloaded once, then reused)
# Using a better model for improved semantic understanding
embedding_model = SentenceTransformer("all-mpnet-base-v2")  # ~768 dims, better quality

# Initialize Gemini model globally (load once, reuse) - using flash for speed
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# Adjust FAISS index to match model dimensions
d = 768  # Updated dimension for all-mpnet-base-v2
index = faiss.IndexFlatL2(d)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Neo4j connection
driver = GraphDatabase.driver("neo4j+s://e4746836.databases.neo4j.io", auth=("neo4j", "mMEzzIJOOBuXLoc9o-mMOryYRq2YWJU9324ynlsGTi4"))

# Embedding cache for frequently accessed queries
embedding_cache = {}

# Configuration for performance optimization
ENABLE_KNOWLEDGE_GRAPH = True  # Set to False to disable graph construction entirely

# ========== TEXT EXTRACTION & CHUNKING ==========
# ========== TEXT EXTRACTION & SMART CHUNKING ==========

def semantic_chunking(text: str, max_tokens: int = 512) -> List[str]:
    """
    Enhanced semantic chunking with better text preprocessing and overlap.
    """
    # Preprocess text
    text = text.replace('\n\n', '\n').replace('\r\n', '\n')
    text = ' '.join(text.split())  # Normalize whitespace
    
    doc = nlp(text)
    chunks = []
    current_chunk = ""
    current_token_count = 0
    overlap_tokens = 50  # Token overlap between chunks for better context

    for sent in doc.sents:
        sent_text = sent.text.strip()
        sent_token_count = len(sent_text.split())
        
        # If adding this sentence would exceed limit
        if current_token_count + sent_token_count > max_tokens:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap
            if chunks and overlap_tokens > 0:
                # Get last few sentences from previous chunk for overlap
                prev_chunk_words = current_chunk.split()
                overlap_words = prev_chunk_words[-overlap_tokens:] if len(prev_chunk_words) > overlap_tokens else prev_chunk_words
                current_chunk = " ".join(overlap_words) + " " + sent_text
                current_token_count = len(overlap_words) + sent_token_count
            else:
                current_chunk = sent_text
                current_token_count = sent_token_count
        else:
            current_chunk += " " + sent_text
            current_token_count += sent_token_count

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Filter out very short chunks
    chunks = [chunk for chunk in chunks if len(chunk.split()) > 10]
    
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
    # Batch processing with normalization for better performance
    if not chunks:
        return
    
    # Normalize text chunks for better embeddings
    normalized_chunks = [chunk.strip().replace('\n', ' ').replace('\r', ' ') for chunk in chunks]
    
    # Batch encode with progress tracking
    print(f"🔄 Encoding {len(normalized_chunks)} chunks...")
    vecs = embedding_model.encode(
        normalized_chunks, 
        convert_to_numpy=True,
        show_progress_bar=True,
        batch_size=32  # Optimized batch size
    )
    
    # Normalize vectors for better similarity search
    vecs = vecs.astype("float32")
    faiss.normalize_L2(vecs)
    
    index.add(vecs)
    store_metadata(meta)
    print(f"✅ Added {len(normalized_chunks)} embeddings to index")

def save_faiss_index(path="faiss_index.idx"):
    faiss.write_index(index, path)
    print(f"✅ Saved FAISS index to {path}")

# ========== KNOWLEDGE GRAPH ==========
def build_graph(text: str, doc_id: str, enable_graph: bool = True):
    """
    Optimized graph construction with batch processing and filtering.
    """
    if not enable_graph:
        print(f"⏭️ Skipping graph construction for {doc_id}")
        return
        
    print(f"🔄 Building knowledge graph for {doc_id}...")
    
    # Process text in smaller chunks to avoid memory issues
    doc = nlp(text[:50000])  # Limit text size for performance
    
    # Collect entities with deduplication
    entity_pairs = set()
    entity_count = {}
    
    # Process sentences in batches
    batch_size = 50
    sentences = list(doc.sents)
    
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i + batch_size]
        
        for sent in batch:
            entities = list(sent.ents)
            
            # Skip sentences with too many entities (performance optimization)
            if len(entities) > 10:
                continue
                
            # Create entity pairs (avoid duplicates)
            for j, ent1 in enumerate(entities):
                ent1_text = ent1.text.strip()
                if len(ent1_text) < 2 or len(ent1_text) > 50:  # Filter entity size
                    continue
                    
                entity_count[ent1_text] = entity_count.get(ent1_text, 0) + 1
                
                for ent2 in entities[j+1:]:  # Avoid duplicate pairs
                    ent2_text = ent2.text.strip()
                    if len(ent2_text) < 2 or len(ent2_text) > 50:
                        continue
                        
                    # Create sorted pair to avoid duplicates
                    pair = tuple(sorted([ent1_text, ent2_text]))
                    entity_pairs.add(pair)
    
    # Limit the number of relationships for performance
    max_relations = 1000
    if len(entity_pairs) > max_relations:
        # Keep most frequent entity pairs
        entity_pairs = set(list(entity_pairs)[:max_relations])
    
    print(f"📊 Found {len(entity_pairs)} entity relationships")
    
    # Batch insert into Neo4j
    if entity_pairs:
        with driver.session() as session:
            # Prepare batch data
            batch_data = []
            for ent1, ent2 in entity_pairs:
                batch_data.append({
                    "subj": ent1,
                    "obj": ent2,
                    "rel": "co_occurs_with",
                    "doc_id": doc_id
                })
            
            # Execute batch operation
            session.run("""
                UNWIND $batch as row
                MERGE (a:Entity {name: row.subj})
                MERGE (b:Entity {name: row.obj})
                MERGE (a)-[:REL {type: row.rel, source: row.doc_id}]->(b)
            """, {"batch": batch_data})
    
    print(f"✅ Knowledge graph updated with {len(entity_pairs)} relationships")

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
EMBEDDING_MODEL_NAME = "all-mpnet-base-v2"
TOP_K = 5

genai.configure(api_key="AIzaSyCiAWJw41BYAPi6qs4aJqjID_P3Goj1NQ4")
# Load FAISS index and metadata

def load_resources() -> Tuple[faiss.IndexFlatL2, List[dict], SentenceTransformer]:
    # load FAISS index with updated dimensions
    d = 768  # Updated embedding dimension for all-mpnet-base-v2
    if os.path.exists(INDEX_PATH):
        try:
            index = faiss.read_index(INDEX_PATH)
            print(f"✅ Loaded existing FAISS index with {index.ntotal} vectors")
        except Exception as e:
            print(f"⚠️ Error loading index, creating new one: {e}")
            index = faiss.IndexFlatL2(d)
    else:
        index = faiss.IndexFlatL2(d)
        print("🆕 Created new FAISS index")

    # load metadata
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        print(f"✅ Loaded {len(metadata)} metadata entries")
    else:
        metadata = []
        print("🆕 No existing metadata found")

    # load embedding model (reuse global instance)
    embedder = embedding_model  # Use the global instance
    return index, metadata, embedder

# --------------------------------------------------
# Retrieve context chunks by similarity
# --------------------------------------------------
def retrieve_context(query: str,
                     index: faiss.IndexFlatL2,
                     metadata: List[dict],
                     embedder: SentenceTransformer,
                     top_k: int = TOP_K) -> List[str]:
    # Normalize query for better embedding
    normalized_query = query.strip().replace('\n', ' ').replace('\r', ' ')
    
    # Check cache first
    cache_key = hash(normalized_query)
    if cache_key in embedding_cache:
        q_emb = embedding_cache[cache_key]
    else:
        # encode query with same normalization as chunks
        q_emb = embedder.encode([normalized_query], convert_to_numpy=True).astype('float32')
        # Cache the embedding (limit cache size)
        if len(embedding_cache) < 1000:  # Prevent memory issues
            embedding_cache[cache_key] = q_emb
    
    # Normalize query vector for cosine similarity
    faiss.normalize_L2(q_emb)
    
    # search with improved parameters
    distances, indices = index.search(q_emb, min(top_k, len(metadata)))
    
    # gather chunk texts with distance filtering
    chunks = []
    for i, idx in enumerate(indices[0]):
        if idx < len(metadata) and distances[0][i] < 1.5:  # Distance threshold
            chunks.append(metadata[idx]["chunk_text"])
    
    # If no good matches, return top result anyway
    if not chunks and indices[0].size > 0:
        chunks.append(metadata[indices[0][0]]["chunk_text"])
    
    return chunks

# --------------------------------------------------
# Ask Gemini with retrieved context
# --------------------------------------------------
def answer_with_gemini(query: str, context: List[str]) -> str:
    # Optimized prompt for faster, more precise responses
    prompt = f"""You are a precise document Q&A assistant. Answer the question using ONLY the provided excerpts.

CONTEXT:
{chr(10).join(f"• {chunk}" for chunk in context)}

QUESTION: {query}

INSTRUCTIONS:
- Answer in 1-2 concise sentences maximum
- Use only information from the provided context
- If the answer isn't in the context, say "The information is not available in the provided documents"
- Be direct and factual

ANSWER:"""

    # Use global model instead of loading each time
    response = gemini_model.generate_content(prompt)
    
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        pdf_file = request.FILES.get("file")
        if not pdf_file:
            return Response({"error": "No file uploaded"}, status=400)
        save_path = os.path.join(f"chat_{chat_id}", pdf_file.name)
        relative_path = default_storage.save(save_path, ContentFile(pdf_file.read()))
        file_path = default_storage.path(relative_path)
        try:
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
            # Update or create knowledge graph (optional for performance)
            if ENABLE_KNOWLEDGE_GRAPH:
                try:
                    build_graph(full_text, doc_id=pdf_file.name, enable_graph=True)
                    if hasattr(chat, 'knowledge_graph'):
                        chat.knowledge_graph.graph_data = {"info": f"Updated with {pdf_file.name}"}
                        chat.knowledge_graph.save()
                    else:
                        KnowledgeGraph.objects.create(chat=chat, graph_data={"info": f"Created with {pdf_file.name}"})
                except Exception as e:
                    print(f"⚠️ Graph construction failed: {e}")
                    # Continue without graph if it fails
        except Exception as e:
            # Optionally, clean up file
            if os.path.exists(file_path):
                os.remove(file_path)
            return Response({"error": f"Ingestion failed: {str(e)}"}, status=500)
        return Response({"message": "PDF uploaded and knowledge graph updated", "chat_id": chat.id})

class ChatQueryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        question = request.data.get("question")
        if not question:
            return Response({"error": "No question provided"}, status=400)
        try:
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
            
            # Append messages to chat
            if not chat.messages:
                chat.messages = []
            chat.messages.extend([user_message, ai_message])
            chat.save()
            
            return Response({"answer": answer})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        return Response({"messages": chat.messages or []})

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

class ChatMessageView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
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
            
            # Append message to chat
            if not chat.messages:
                chat.messages = []
            chat.messages.append(message)
            chat.save()
            
            return Response({"message": "Message stored successfully"})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        return Response({"messages": chat.messages or []})



#hackrx
class HackRxRunView(APIView):
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

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
