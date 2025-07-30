from django.urls import path
from .views import (
    ChatListCreateView,
    UploadPDFToChatView,
    ChatQueryView,
    KnowledgeGraphRetrieveView,
    ChatMessageView,
    HackRxRunView,
)

app_name = 'rag'

urlpatterns = [
    path('chats/', ChatListCreateView.as_view(), name='chat_list_create'),
    path('chats/<int:chat_id>/upload_pdf/', UploadPDFToChatView.as_view(), name='upload_pdf_to_chat'),
    path('chats/<int:chat_id>/query/', ChatQueryView.as_view(), name='chat_query'),
    path('chats/<int:chat_id>/messages/', ChatMessageView.as_view(), name='chat_message'),
    path('chats/<int:chat_id>/knowledge_graph/', KnowledgeGraphRetrieveView.as_view(), name='knowledge_graph_retrieve'),
    path('hackrx/run', HackRxRunView.as_view(), name='hackrx_run'),
]