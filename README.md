# AWS Infrastructure Management API

A Django-based REST API for automated AWS EC2 instance provisioning with dual credential support, auto-termination for demo instances, and comprehensive deployment tracking.

**Live API:** https://kuberns-backend.onrender.com  
**Swagger Docs:** https://kuberns-backend.onrender.com/api/docs

---

## 🚀 Quick Setup

### Prerequisites
- Python 3.8+
- PostgreSQL (or SQLite for local)
- AWS credentials (optional for demo mode)

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd kubern-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate required keys
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Configure environment (.env file)
SECRET_KEY=<generated-key>
DEBUG=True
FIELD_ENCRYPTION_KEY=<generated-fernet-key>
AWS_DEMO_ACCESS_KEY=<your-aws-key>  # Optional for demo mode
AWS_DEMO_SECRET_KEY=<your-aws-secret>

# Run migrations and start server
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**Access API:** http://localhost:8000/api/docs

---

## 🏗️ Architecture & ER Diagram

### System Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ JWT Auth
       ▼
┌──────────────────────────────┐
│    Django API (Ninja)        │
│  ┌────────────────────────┐  │
│  │  API Layer (api.py)    │  │
│  │  - Request validation  │  │
│  │  - Authentication      │  │
│  └──────────┬─────────────┘  │
│             ▼                │
│  ┌────────────────────────┐  │
│  │ Service Layer          │  │
│  │ (services.py)          │  │
│  │ - Business logic       │  │
│  └──────┬──────┬──────────┘  │
│         │      │              │
│  ┌──────▼───┐ ┌▼──────────┐  │
│  │ AWS Utils│ │ DB Models │  │
│  │ (boto3)  │ │           │  │
│  └──────────┘ └───────────┘  │
└──────┬───────────┬───────────┘
       │           │
   ┌───▼───┐   ┌───▼──────┐
   │AWS EC2│   │PostgreSQL│
   └───────┘   └──────────┘
```

### Database Schema (ER Diagram)

```
┌─────────────────┐
│      User       │
│─────────────────│
│ PK│ id          │
│   │ username    │
│   │ email       │
│   │ password    │
└────┬────────────┘
     │ 1
     │
     ├─────────────────┬──────────────────┐
     │ *               │ *                │ *
┌────▼────────────┐ ┌──▼─────────────┐ ┌──▼──────────────┐
│  AWSCredential  │ │    Project     │ │    Instance     │
│─────────────────│ │────────────────│ │─────────────────│
│PK│ id           │ │PK│ id (UUID)   │ │PK│ id           │
│FK│ user_id      │ │FK│ owner_id    │ │FK│ project_id   │
│  │ name         │ │  │ name        │ │FK│ credential_id│
│  │ access_key🔒 │ │  │ description │ │FK│ user_id      │
│  │ secret_key🔒 │ │  │ region      │ │  │ instance_id  │
│  │ region       │ │  │ port        │ │  │ public_ip    │
│  │ is_active    │ └────────────────┘ │  │ port         │
└─────────────────┘                    │  │ status       │
                                       │  │ region       │
                                       │  │ auto_term_at │
                                       └──┬───────────────┘
                                          │ 1
                                          │
                                          │ *
                                     ┌────▼──────────┐
                                     │DeploymentLog  │
                                     │───────────────│
                                     │PK│ id         │
                                     │FK│ instance_id│
                                     │  │ status     │
                                     │  │ output     │
                                     │  │ timestamp  │
                                     └───────────────┘

Legend: PK=Primary Key, FK=Foreign Key, 🔒=Encrypted
```

**Key Relationships:**
- User → AWSCredential (1:Many): Users save multiple AWS accounts
- User → Project (1:Many): Users own multiple projects
- Project → Instance (1:Many): Projects contain multiple EC2 instances
- AWSCredential → Instance (1:Many, Optional): Track which credentials provisioned instances
- Instance → DeploymentLog (1:Many): Audit trail for each instance

---

## 🎯 Design Decisions

### 1. Dual Credential System
**Problem:** Not all users have AWS accounts for testing.  
**Solution:** Two modes:
- **Demo Mode:** Uses platform AWS credentials (from env variables)
- **User Mode:** Uses user-provided encrypted AWS credentials

**Benefit:** Easy testing without requiring AWS accounts.

### 2. Minimal User Input
**Problem:** AWS configuration is complex with 20+ parameters.  
**Solution:** Users provide only:
- `region` (where to deploy)
- `port` (single application port)

Everything else hardcoded:
- Instance Type: `t3.micro` (minimal cost ~$8/month)
- Disk: `8GB` (minimum)
- AMI: Auto-selected Ubuntu 22.04 LTS per region
- Ports: SSH (22) + user's port

**Benefit:** Simplified UX, faster deployment, predictable costs.

### 3. Auto-Termination for Demo Instances
**Problem:** Demo instances running 24/7 cost $8/month.  
**Solution:** 
- Demo instances terminate after 5 minutes
- GitHub Actions cron (every 5 min) checks `auto_terminate_at` field
- Calls boto3 to terminate expired instances

**Benefit:** Cost reduced from $8/month to ~$0.0009/use (99.9% savings).

### 4. Automatic Web Server Setup
**Problem:** Bare EC2 instances show "connection refused".  
**Solution:** User data script auto-installs Nginx with welcome page.  
**Benefit:** Instant working URL - users see results immediately.

### 5. Encrypted Credential Storage
**Problem:** Storing AWS keys in plain text is insecure.  
**Solution:** `django-encrypted-model-fields` with Fernet (AES-128).  
**Benefit:** Credentials encrypted at rest; key in environment only.

### 6. Project ID-Based Security Groups
**Problem:** Using project names for security groups caused "already exists" errors due to AWS eventual consistency.  
**Solution:** Security groups named with first 8 chars of project UUID (e.g., `kuberns-7c5272e4`).  
**Benefit:** Guaranteed uniqueness - no naming conflicts, automatic cleanup on termination.

---

## 📡 API Structure & Payloads

### Authentication
All endpoints require JWT token:
```bash
POST /api/token/pair
{"username": "admin", "password": "admin"}
→ {"access": "eyJ0eXAi...", "refresh": "eyJ0eXAi..."}
```

### Endpoints

#### 1. Create Instance
```bash
POST /api/infra/instances/create
Authorization: Bearer <token>

# Demo Mode
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "credential_mode": "demo",
  "region": "us-east-1",
  "port": 80
}

# User Mode
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "credential_mode": "user",
  "aws_access_key": "AKIAIOSFODNN7EXAMPLE",
  "aws_secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "region": "us-west-2",
  "port": 8080
}

# Response
{
  "success": true,
  "instance_id": 1,
  "aws_instance_id": "i-0123456789abcdef0",
  "url": "http://54.123.45.67:80",
  "public_ip": "54.123.45.67",
  "port": 80,
  "message": "Instance created successfully",
  "deployment_log_id": 42
}
```

#### 2. Get Instance Status
```bash
GET /api/infra/instances/{id}/status
→ {
  "instance_id": 1,
  "aws_instance_id": "i-xxx",
  "url": "http://54.123.45.67:80",
  "status": "running",
  "public_ip": "54.123.45.67",
  "instance_type": "t3.micro",
  "region": "us-east-1",
  "auto_terminate_at": "2025-11-23T21:15:00Z",
  "logs": [...]
}
```

#### 3. List Instances
```bash
GET /api/infra/instances
GET /api/infra/instances?project_id={uuid}  # Filter by project
→ [{"id": 1, "url": "http://...", "status": "running", ...}]
```

#### 4. Get Instance Logs
```bash
GET /api/infra/instances/{id}/logs?limit=50
→ [{"id": 42, "status": "completed", "output": "...", "timestamp": "..."}]
```

#### 5. Get All Logs
```bash
GET /api/infra/logs?limit=50
→ [{"id": 42, "project_name": "...", "instance_id": 1, ...}]
```

#### 6. Save AWS Credentials
```bash
POST /api/infra/credentials
{
  "name": "My AWS Account",
  "aws_access_key": "AKIA...",
  "aws_secret_key": "wJal...",
  "region": "us-east-1"
}
→ {"id": 5, "name": "My AWS Account", "is_active": true}
```

**Status Values:** `pending`, `running`, `stopped`, `terminated`, `failed`

---

## 📚 Swagger & Postman

### Swagger UI (Interactive)
- **Local:** http://localhost:8000/api/docs
- **Production:** https://kuberns-backend.onrender.com/api/docs

### Postman Collection
Import OpenAPI schema directly into Postman:
1. Open Postman → Import → Link
2. Paste: `https://kuberns-backend.onrender.com/api/openapi.json`
3. Click Import

All endpoints automatically available with schemas!

### Testing Example
```bash
# Get token
curl -X POST https://kuberns-backend.onrender.com/api/token/pair \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Create instance
curl -X POST https://kuberns-backend.onrender.com/api/infra/instances/create \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "uuid",
    "credential_mode": "demo",
    "region": "us-east-1",
    "port": 80
  }'
```

---

## 🚀 Deployment

### Current Production Setup
**Platform:** Render.com  
**Database:** Supabase (PostgreSQL)  
**URL:** https://kuberns-backend.onrender.com  
**Status:** ✅ Live and operational

### Kuberns Deployment Note
⚠️ **Important:** This project was intended for Kuberns deployment, but Kuberns requires a **$10 activation fee** to enable their service. Since this is an assessment project without budget allocation, I deployed to **Render.com** (free tier) as an alternative, which provides similar containerized deployment capabilities.

**If Kuberns access becomes available**, deployment would be:
```bash
# Kuberns deployment (if activated)
kuberns apps create kubern-backend
kuberns config:set SECRET_KEY=xxx DB_NAME=xxx AWS_DEMO_ACCESS_KEY=xxx
kuberns git:remote -a kubern-backend
git push kuberns main
kuberns run python manage.py migrate
```

Full Kuberns documentation available at their platform docs.

### Environment Variables (Production)
```bash
SECRET_KEY=<django-secret>
DEBUG=False
ENVIRONMENT=production
DB_NAME=<db-name>
DB_USER=<db-user>
DB_PASSWORD=<db-password>
DB_HOST=<db-host>
DB_PORT=5432
FIELD_ENCRYPTION_KEY=<fernet-key>
AWS_DEMO_ACCESS_KEY=<aws-key>
AWS_DEMO_SECRET_KEY=<aws-secret>
```

### Alternative Platforms
- **AWS EC2:** Self-hosted with full control
- **Heroku:** `git push heroku main`
- **Railway.app:** GitHub auto-deploy
- **DigitalOcean:** App Platform

### GitHub Actions (Auto-Termination)
Cron job runs every 5 minutes at `.github/workflows/terminate-instances.yml`:
```yaml
on:
  schedule:
    - cron: '*/5 * * * *'
```

Calls `python manage.py terminate_expired_instances` to clean up demo instances.

---

## ⏱️ Time Taken

**Total Development Time:** ~12-15 hours

**Breakdown:**
- API structure & models: 2 hours
- AWS boto3 integration: 3 hours
- Credential encryption: 2 hours
- Auto-termination system: 2 hours
- Nginx automation: 1 hour
- GitHub Actions: 1 hour
- API endpoints: 2 hours
- Testing & documentation: 2-3 hours

---

## 🚧 Limitations

1. **No Manual Termination:** No API to manually stop/terminate instances (workaround: wait for auto-termination or use AWS console)
2. **Single Port:** Only one application port per instance (SSH port 22 always included)
3. **Hardcoded Instance Type:** Always `t3.micro` - no user choice (design decision for cost control)
4. **GitHub Actions Delay:** Cron runs every 5 min, but GitHub may delay 5-15 min (demo instances may run 5-20 min total)
5. **No Cost Estimation:** API doesn't show cost before provisioning
6. **No Instance Operations:** No start/stop/restart endpoints
7. **Limited Error Recovery:** Failed instances stay in "failed" state, no auto-retry
8. **No Multi-Region Deployment:** Each instance is single-region, no load balancing

### Future Enhancements
- Manual lifecycle management (stop/start/terminate)
- Multiple ports per instance
- Cost calculator
- Real-time termination (webhooks vs cron)
- Instance metrics (CPU, memory, network)
- Custom instance types
- Auto-scaling support

---

## 🧪 Testing

### Local Testing
```bash
# Create superuser
python manage.py createsuperuser

# Get token
curl -X POST http://localhost:8000/api/token/pair \
  -d '{"username":"admin","password":"admin"}'

# Create instance
curl -X POST http://localhost:8000/api/infra/instances/create \
  -H "Authorization: Bearer <token>" \
  -d '{...}'
```

### Test Auto-Termination
```bash
# Dry run (shows what would be terminated)
python manage.py terminate_expired_instances --dry-run

# Actually terminate
python manage.py terminate_expired_instances
```

---

## 📊 Features

✅ Dual credential system (demo/user)  
✅ AWS EC2 instance provisioning  
✅ Auto-termination (5-min demo instances)  
✅ Region-based AMI mapping (16 AWS regions)  
✅ Encrypted credential storage (Fernet/AES-128)  
✅ Comprehensive deployment logging  
✅ Real-time status tracking  
✅ Automatic Nginx installation  
✅ GitHub Actions cron job  
✅ JWT authentication  
✅ Project-based filtering  
✅ Interactive Swagger UI  
✅ Postman-ready OpenAPI spec  

---

## 🛠️ Technology Stack

**Backend:** Django 4.2, Django Ninja Extra  
**Database:** PostgreSQL (Supabase for production, SQLite for local)  
**Cloud:** AWS EC2, Render.com  
**Security:** Fernet encryption, JWT auth  
**AWS SDK:** boto3/aioboto3  
**Validation:** Pydantic schemas  
**DevOps:** GitHub Actions, Docker-ready  
**Documentation:** OpenAPI 3.0, Swagger UI  

---

## 📞 Support

**Live API Docs:** https://kuberns-backend.onrender.com/api/docs  
**OpenAPI Schema:** https://kuberns-backend.onrender.com/api/openapi.json  
**Repository:** [GitHub URL]

For issues:
1. Check Swagger docs for endpoint details
2. Review error messages in API responses
3. Check deployment logs in Render dashboard
4. Test locally following setup instructions

---

## 📝 License

Developed for assessment purposes.

---

**Last Updated:** November 23, 2025  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
