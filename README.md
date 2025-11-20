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

- All models use encrypted fields for sensitive data
- API uses django-ninja with Pydantic schemas
- AWS provisioning is mocked by default (set `mock_mode = False` to use real AWS)
- Database uses SQLite by default (configure PostgreSQL for production)

## TODO

- Implement complete business logic in each app
- Add proper authentication and authorization
- Configure production database and caching
- Set up proper logging and monitoring
- Add comprehensive tests
- Configure CI/CD pipeline