# Movie Recommendation System

A comprehensive movie recommendation system built with Django and React, featuring advanced recommendation algorithms and a modern user interface.

## Features

- Advanced movie recommendation algorithms
- User authentication and profile management
- Movie search and filtering
- Rating and review system
- Personalized recommendations
- Real-time search suggestions
- Responsive design

## Tech Stack

### Backend

- Django 4.0+
- PostgreSQL
- Elasticsearch
- Redis
- Celery

### Frontend

- React 18+
- Redux Toolkit
- React Query
- Tailwind CSS
- TypeScript

## Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Elasticsearch 7+
- Redis 6+

## Setup Instructions

### Backend Setup

1. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Set up database:

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Start development server:

```bash
python manage.py runserver
```

### Frontend Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Start development server:

```bash
npm start
```

## Project Structure

### Backend

```
movie_recommendation/
├── core/                 # Core functionality and utilities
├── movies/              # Movie-related models and views
├── metadata/            # Genre, person, and crew information
├── users/               # User management and authentication
├── recommendations/     # Recommendation algorithms
└── api/                 # REST API endpoints
```

### Frontend

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/          # Page components
│   ├── hooks/          # Custom React hooks
│   ├── store/          # Redux store
│   ├── api/            # API client and endpoints
│   └── utils/          # Utility functions
```

## Development Guidelines

Please refer to `PROJECT_RULES.md` for detailed development guidelines, including:

- Code standards
- Testing requirements
- Security practices
- Performance optimization
- Documentation requirements

## API Documentation

API documentation is available at `/api/docs/` when running the development server.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
