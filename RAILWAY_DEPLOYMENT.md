# Railway Deployment Guide for Django Grooming Salon

## Overview
This project is configured for Railway deployment with:
- **PostgreSQL Database**: Automatic via Railway's DATABASE_URL
- **Persistent Media Storage**: Railway Volumes for groomer images
- **Static Files**: WhiteNoise for production static file serving

## Deployment Steps

### 1. Push to GitHub
Ensure your code is pushed to a GitHub repository ( Railway requires Git).

```bash
git init
git add .
git commit -m "Configure for Railway deployment"
git push origin main
```

### 2. Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Python and create the service

### 3. Add PostgreSQL Database
1. In the Railway project, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically provide `DATABASE_URL` environment variable

### 4. Add Volume for Media Files
1. Go to your web service settings
2. Click "Volumes" tab
3. Click "New Volume"
4. Mount path: `/data`
5. This creates persistent storage for groomer images

### 5. Configure Environment Variables
In your web service settings, add these variables:

```
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-project-name.railway.app,localhost
DJANGO_SETTINGS_MODULE=myproject.settings.production
```

**Generate a secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 6. Run Migrations
After deployment, run migrations via the Railway console:
1. Go to your web service → "Console" tab
2. Click "New Console" → select "Web Service"
3. Run: `python manage.py migrate`

### 7. Create Superuser (Admin)
In the Railway console:
```bash
python manage.py createsuperuser
```

### 8. Verify Deployment
1. Check the Railway dashboard logs
2. Visit your app URL: `https://your-project-name.railway.app`
3. Test admin login at `https://your-project-name.railway.app/admin/pricing/`

## Troubleshooting

### Database Connection Error
- Verify PostgreSQL service is running
- Check `DATABASE_URL` is set (auto-provided by Railway)

### Media Files Not Persisting
- Ensure volume is mounted at `/data`
- Check volume has sufficient storage space
- Verify `MEDIA_ROOT` setting is `/data/media`

### Static Files Not Loading
- Run `python manage.py collectstatic` in Railway console
- WhiteNoise is configured for production

### 500 Errors
- Check Railway logs for specific error
- Ensure all environment variables are set
- Verify SECRET_KEY is properly configured

## Cost (Railway Pricing)

Current Railway pricing (as of 2025):
- **Free Tier**: $5/month credit (1 service)
- **Web Service**: ~$5/month (usage-based)
- **PostgreSQL**: Included in free tier or ~$5/month
- **Volumes**: $0.10/GB-month (very affordable for groomer images)

**Estimated Monthly Cost**: ~$10-15 for full stack with media storage

## Alternative: Google Cloud Storage

If you prefer GCS over Railway Volumes:

1. Install: `pip install google-cloud-storage`
2. Set in `.env`:
   ```
   GS_BUCKET_NAME=your-bucket-name
   GS_CREDENTIALS=path/to/credentials.json
   ```
3. Update settings.py to use `google-cloud-storage` backend
4. GCS pricing: First 5GB free, then ~$0.026/GB-month

**Recommendation**: Railway Volumes is simpler and cheaper for this use case.
