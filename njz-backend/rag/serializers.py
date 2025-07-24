from rest_framework import serializers
from .models import Chat, KnowledgeGraph

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = '__all__'

class KnowledgeGraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeGraph
        fields = '__all__' 