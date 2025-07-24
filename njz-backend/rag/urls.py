from django.urls import path
from . import views

app_name = 'rag'

urlpatterns = [
    path('ingestion/', views.ingestion, name='ingestion'),
]