# GitHub Actions Setup for Auto-Termination

The workflow at `.github/workflows/terminate-instances.yml` automatically terminates expired demo instances every 5 minutes.

## Required GitHub Secrets

You need to add these secrets to your repository:

### Go to: Settings → Secrets and variables → Actions → New repository secret

### 1. DJANGO_SECRET_KEY
Your Django secret key
```
Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. DB_NAME
Your database name
```
Example: kuberns_db
```

### 3. DB_USER
Your database username
```
Example: kuberns_user
```

### 4. DB_PASSWORD
Your database password
```
Example: your_secure_password
```

### 5. DB_HOST
Your database host
```
Example: db.example.com or 127.0.0.1
```

### 6. DB_PORT
Your database port
```
Example: 5432
```

### 7. AWS_DEMO_ACCESS_KEY
Your AWS access key for demo credentials
```
Example: AKIAIOSFODNN7EXAMPLE
```

### 8. AWS_DEMO_SECRET_KEY
Your AWS secret key for demo credentials
```
Example: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### 9. FIELD_ENCRYPTION_KEY
Your Fernet encryption key for credentials
```
Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## How to Add Secrets

1. Go to your GitHub repository
2. Click **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret with the name and value
6. Click **Add secret**

## Testing the Workflow

### Manual Test (Before Cron Runs)
1. Go to **Actions** tab in your GitHub repository
2. Click on "Terminate Expired Demo Instances" workflow
3. Click **Run workflow** button
4. Select branch (usually `main`)
5. Click **Run workflow**
6. Watch the logs to see if it works

### Automatic Runs
The workflow runs automatically every 5 minutes via cron.

Check the **Actions** tab to see:
- When it last ran
- If it succeeded or failed
- Logs of what was terminated

## Adjusting the Schedule

Edit `.github/workflows/terminate-instances.yml` and change the cron:

```yaml
schedule:
  - cron: '*/5 * * * *'  # Every 5 minutes (current)
  # - cron: '* * * * *'    # Every minute (not recommended, GitHub has ~5min minimum)
  # - cron: '*/10 * * * *' # Every 10 minutes
  # - cron: '0 * * * *'    # Every hour
```

## Troubleshooting

### Workflow not running
- Check that secrets are added correctly
- Verify DATABASE_URL is correct
- Check Actions tab for error messages

### Database connection errors
- Make sure all DB_* secrets are set correctly (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
- Verify database allows connections from GitHub Actions IPs
- Check database credentials are correct
- Ensure DB_HOST is accessible from the internet (if using external DB)

### AWS termination errors
- Verify AWS credentials have EC2 termination permissions
- Check AWS_DEMO_ACCESS_KEY and AWS_DEMO_SECRET_KEY are correct
- Ensure instances exist in the same region as configured

## Monitoring

View all workflow runs:
- Go to **Actions** tab
- Click on "Terminate Expired Demo Instances"
- See history of all runs

Each run shows:
- How many instances were found
- Which instances were terminated
- Any errors that occurred

## Alternative: Self-Hosted Cron

If you need **real-time** termination (GitHub Actions has 5-15 min delays), run this on your production server:

```bash
# Edit crontab
crontab -e

# Add this line (runs every minute)
* * * * * cd /path/to/kubern-backend && python manage.py terminate_expired_instances
```

## Cost

GitHub Actions is **free** for public repositories.

For private repositories:
- Free tier: 2,000 minutes/month
- This workflow uses ~1 minute per run
- Running every 5 minutes = ~8,640 minutes/month
- You may need a paid plan

Consider self-hosted cron for private repos to stay within free tier.

