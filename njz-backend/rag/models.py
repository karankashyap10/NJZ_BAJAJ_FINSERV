from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    name = models.CharField(max_length=255)
    messages = models.JSONField(default=list, blank=True)  # Store structured message data
    created_at = models.DateTimeField(auto_now_add=True)

class KnowledgeGraph(models.Model):
    chat = models.OneToOneField(Chat, on_delete=models.CASCADE, related_name='knowledge_graph')
    graph_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
