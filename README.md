# NJZ BAJAJ FINSERV - Django Backend

A Django REST Framework backend for the NJZ BAJAJ FINSERV application.

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd NJZ_BAJAJ_FINSERV
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
NJZ_BAJAJ_FINSERV/
├── backend/                 # Django project settings
│   ├── settings.py         # Main settings file
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── api/                    # API application
│   ├── views.py           # API views
│   ├── urls.py            # API URL patterns
│   └── models.py          # Database models
├── manage.py              # Django management script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## API Endpoints

- `GET /api/health/` - Health check endpoint
- `GET /api/info/` - API information
- `GET /admin/` - Django admin interface

## Features

- **Django REST Framework** - For building REST APIs
- **CORS Headers** - For handling cross-origin requests
- **Django Filters** - For advanced filtering capabilities
- **JWT Authentication** - For secure API authentication
- **SQLite Database** - For development (can be changed to PostgreSQL/MySQL for production)

## Development

The backend is configured with:
- Django 4.2.7
- Django REST Framework 3.14.0
- CORS headers for frontend integration
- JWT authentication support
- Filtering and pagination
- Media file handling

## Next Steps

1. Create database models for your specific use case
2. Implement authentication and authorization
3. Add more API endpoints as needed
4. Configure production settings
5. Set up proper database (PostgreSQL/MySQL) for production