# Railway Deployment Guide for Django Grooming Salon

## Overview
This project is configured for Railway deployment with:
- **PostgreSQL Database**: Automatic via Railway's DATABASE_URL
- **Persistent Media Storage**: Railway Volumes for groomer images
- **Static Files**: WhiteNoise for production static file serving

## Pre-Deployment Checklist

### Code Changes Required
- [x] `django-debug-toolbar` moved to `requirements-dev.txt` (not in production)
- [x] Deleted deprecated `myproject/settings.py` (use `myproject/settings/production.py`)
- [x] Added `anymail` to `INSTALLED_APPS` in `base.py` (required for email)
- [x] Added `whitenoise.middleware.WhiteNoiseMiddleware` to `MIDDLEWARE` in `base.py`
- [x] Configured proper Whitenoise settings in `production.py`
- [x] Removed `unsafe-inline` and `unsafe-eval` from CSP in production
- [x] Tested `collectstatic` works correctly
- [x] Configured `DJANGO_SETTINGS_MODULE=myproject.settings.development` in `manage.py`

### Environment Variables Required
Create these in Railway dashboard for your web service:

**Required:**
```
DEBUG=False
SECRET_KEY=<generate secure key using: python -c "import secrets; print(secrets.token_urlsafe(50))">
ALLOWED_HOSTS=your-project-name.railway.app
DJANGO_SETTINGS_MODULE=myproject.settings.production
```

**Optional (for email functionality):**
```
EMAIL_BACKEND=anymail.backends.sendgrid.EmailBackend
DEFAULT_FROM_EMAIL=noreply@shampooches.com
SENDGRID_API_KEY=<your-sendgrid-api-key>
```

**Optional (for Sentry error tracking):**
```
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=production
```

### Railway Services Required

#### 1. Web Service (Python)
- Build command: Automatic (Nixpacks)
- Start command: `python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn myproject.wsgi:application`
- Environment variables: See above

#### 2. PostgreSQL Database
- Add new service → Database → PostgreSQL
- Railway automatically provides `DATABASE_URL` environment variable

#### 3. Volume (Persistent Storage)
- Go to web service → Settings → Volumes
- Create new volume
- Mount path: `/data`
- This will store groomer images persistently

## Deployment Steps

### 1. Push Code to GitHub
```bash
git add .
git commit -m "Ready for Railway deployment"
git push origin master  # or your branch name
```

### 2. Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository and branch
4. Railway will auto-detect Python and create the web service

### 3. Configure Web Service
1. Go to web service → Settings → Variables
2. Add all environment variables listed above
3. Click "Variables" → "New Variable" for each one

### 4. Add PostgreSQL Database
1. In the Railway project, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create it and provide `DATABASE_URL`

### 5. Add Volume for Media Storage
1. Go to your web service → Settings → Volumes
2. Click "New Volume"
3. Mount path: `/data`
4. Size: Start with 1GB (can scale as needed)

### 6. Deploy
1. Click "Deploy" on your web service
2. Watch the build process in the logs
3. Railway will automatically:
   - Install dependencies from `requirements.txt`
   - Run `collectstatic`
   - Run migrations
   - Start the Gunicorn server

### 7. Create Superuser (Optional - for admin access)
After successful deployment, create admin superuser:
1. Go to web service → Console
2. Click "New Console" → "Web Service"
3. Run:
```bash
python manage.py createsuperuser
```

### 8. Verify Deployment
1. Visit your Railway URL: `https://your-project-name.railway.app`
2. Check health endpoint: `https://your-project-name.railway.app/health/`
3. Test customer landing page
4. Test admin panel (if superuser created)

## Troubleshooting

### Build Fails
**Symptoms:** Build process fails with package errors
**Solutions:**
- Check `requirements.txt` has correct versions
- Ensure no development-only packages in production requirements
- Check Railway build logs for specific errors

### Database Connection Error
**Symptoms:** `Database connection failed` or similar
**Solutions:**
- Verify PostgreSQL service is running in Railway
- Check `DATABASE_URL` environment variable is set (auto-provided by Railway)
- Try restarting the web service after PostgreSQL is ready

### Media Files Not Persisting
**Symptoms:** Uploaded images disappear after redeploy
**Solutions:**
- Verify volume is created and mounted at `/data`
- Check `MEDIA_ROOT` setting in `production.py` (`/data/media`)
- Ensure sufficient disk space on the volume
- Try manually creating `/data/media` directory in console

### Static Files Not Loading
**Symptoms:** CSS/JS files 404 or not applied
**Solutions:**
- Check `collectstatic` ran successfully (should be in logs)
- Verify `STATIC_ROOT` and `STATIC_URL` settings
- Check Railway build logs for collectstatic errors
- Try running `python manage.py collectstatic --noinput` in console

### 500 Internal Server Error
**Symptoms:** All pages return 500 error
**Solutions:**
- Check Railway logs for specific error traceback
- Verify all environment variables are set correctly
- Check `SECRET_KEY` is properly set (not using the placeholder)
- Verify `ALLOWED_HOSTS` includes your Railway domain
- Ensure database migrations have run successfully

### CSP/Security Errors
**Symptoms:** Console shows CSP violations, resources blocked
**Solutions:**
- Check CSP settings in `production.py`
- Verify CDN domains are allowed (Tailwind, jsDelivr, etc.)
- Temporarily disable CSP by setting `CSP_ENFORCE=False` to debug
- Check Railway logs for CSP-related errors

### Email Not Sending
**Symptoms:** Email functionality doesn't work
**Solutions:**
- Verify `SENDGRID_API_KEY` is set correctly
- Check SendGrid API key has proper permissions
- Test email backend in Railway console:
```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])
>>> # Check response
```

## Cost Breakdown (Railway Pricing)

Current Railway pricing (as of 2025):
- **Free Tier**: $5/month credit
- **Web Service**: ~$5/month (usage-based, includes free tier)
- **PostgreSQL**: Included in free tier or ~$5/month
- **Volumes**: $0.10/GB-month

**Estimated Monthly Cost**: ~$10-15 for full stack with media storage

## Security Checklist

- [x] `DEBUG=False` in production
- [x] `SECRET_KEY` is randomly generated (not hardcoded)
- [x] `ALLOWED_HOSTS` restricted to Railway domain only
- [x] HTTPS required (SECURE_SSL_REDIRECT=True)
- [x] Secure cookies (SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
- [x] HSTS enabled (SECURE_HSTS_SECONDS=31536000)
- [x] CSP headers configured (no unsafe-inline/eval)
- [x] Database connection with health checks
- [ ] Sentry monitoring configured (optional)
- [ ] SendGrid for email (configured in environment)

## Performance Optimization

- [x] WhiteNoise for static file serving
- [x] GZIP compression enabled
- [x] Long cache headers for static assets
- [x] Connection pooling for PostgreSQL (CONN_MAX_AGE=600)
- [ ] Redis cache (optional, for production)

## Alternative: Google Cloud Storage

If you prefer GCS over Railway Volumes:

1. Install: `pip install google-cloud-storage` (add to requirements.txt)
2. Create a Google Cloud Storage bucket
3. Set environment variables:
   ```
   GS_BUCKET_NAME=your-bucket-name
   GS_CREDENTIALS=/path/to/credentials.json (upload credentials as file in Railway)
   ```
4. Update `production.py` to use GCS backend

**Recommendation**: Railway Volumes is simpler and cheaper for this use case unless you expect large scale (>10GB of media).
