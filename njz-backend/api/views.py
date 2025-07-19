from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify the API is working
    """
    return Response({
        'status': 'success',
        'message': 'Django backend is running successfully!',
        'data': {
            'framework': 'Django REST Framework',
            'version': '4.2.7'
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """
    API information endpoint
    """
    return Response({
        'name': 'NJZ BAJAJ FINSERV API',
        'version': '1.0.0',
        'description': 'Backend API for NJZ BAJAJ FINSERV application',
        'endpoints': {
            'health': '/api/health/',
            'info': '/api/info/',
            'admin': '/admin/'
        }
    }, status=status.HTTP_200_OK)
