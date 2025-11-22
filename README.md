# Kuberns Django Backend

A Django backend skeleton with django-ninja API framework, field encryption, and AWS integration.

## Quick Start

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

4. **Generate encryption key**
   ```python
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   # Copy this key to FIELD_ENCRYPTION_KEY in .env
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

## API Documentation

Visit `http://localhost:8000/api/docs` for interactive API documentation.

## Apps Structure

- **core**: Shared utilities and encryption helpers
- **accounts**: User management and authentication
- **projects**: Project management with templates and plans
- **integrations**: GitHub and other external service integrations
- **infra**: AWS infrastructure provisioning and management

## Security Notes

- **Never commit secrets**: Keep `.env` file out of version control
- **Field encryption**: Sensitive data is encrypted using `django-fernet-fields`
- **AWS credentials**: Use IAM roles or temporary credentials in production
- **CORS**: Configure `CORS_ALLOWED_ORIGINS` for your frontend domains

## Development

- **Async APIs**: All endpoints are async for better performance and concurrency
- **JWT Authentication**: Uses django-ninja-jwt for secure token-based auth
- **Encrypted Fields**: All sensitive data uses encrypted model fields
- **Modern HTTP Client**: Uses httpx for async HTTP requests to external APIs
- **API Documentation**: Interactive docs with Pydantic schemas
- **AWS Integration**: Provisioning is mocked by default (set `mock_mode = False` for real AWS)
- **Database**: SQLite for local, PostgreSQL for production

## GitHub OAuth Setup

1. **Create GitHub OAuth App**:
   - Go to https://github.com/settings/applications/new
   - Set Application name: `Kuberns`
   - Set Homepage URL: `http://localhost:3000`
   - Set Authorization callback URL: `http://localhost:3000/auth/github/callback`
   - Copy Client ID and Client Secret

2. **Configure Environment Variables**:
   ```bash
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   GITHUB_REDIRECT_URI=http://localhost:3000/auth/github/callback
   ```

## API Endpoints

### JWT Authentication (django-ninja-jwt)
- `POST /api/token/pair` - Get access/refresh token pair
- `POST /api/token/refresh` - Refresh access token
- `POST /api/token/verify` - Verify token validity

### GitHub Authentication (Async)
- `GET /api/accounts/auth/github/url` - Get GitHub OAuth URL
- `POST /api/accounts/auth/github/login` - Login with GitHub code (returns JWT tokens)
- `POST /api/accounts/auth/refresh` - Refresh JWT access token

### User Management (Async + JWT Auth)
- `GET /api/accounts/me` - Get current user (requires JWT Bearer token)

### Authentication Headers
```bash
# Use JWT Bearer token for authenticated requests
Authorization: Bearer <your_access_token>
```

Visit `http://localhost:8000/api/docs` for complete interactive API documentation.

## TODO

- Implement complete business logic in each app
- Add proper authentication and authorization
- Configure production database and caching
- Set up proper logging and monitoring
- Add comprehensive tests
- Configure CI/CD pipeline