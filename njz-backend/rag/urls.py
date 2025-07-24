from django.urls import path
from . import views
from .views import RagQueryView, UploadPDFView, ChatListCreateView, KnowledgeGraphRetrieveView

app_name = 'rag'

urlpatterns = [
    path('query/', RagQueryView.as_view(), name='rag_query'),
    path('upload_pdf/', UploadPDFView.as_view(), name='upload_pdf'),
    path('chats/', ChatListCreateView.as_view(), name='chat_list_create'),
    path('chats/<int:chat_id>/knowledge_graph/', KnowledgeGraphRetrieveView.as_view(), name='knowledge_graph_retrieve'),
]